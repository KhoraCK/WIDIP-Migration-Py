"""
Client pour Active Directory via LDAP.

Ce client gère les opérations sur Active Directory avec niveaux SAFEGUARD:

LECTURE (L0 - READ_ONLY):
- check_user: Vérifier l'existence d'un utilisateur
- get_user_info: Récupérer les informations complètes
- search_users: Rechercher des utilisateurs

MODIFICATION MODÉRÉE (L2 - MODERATE):
- unlock_account: Déverrouiller un compte
- enable_account: Réactiver un compte désactivé
- move_to_ou: Déplacer vers une autre OU

ACTIONS SENSIBLES (L3 - SENSITIVE) - Validation humaine OBLIGATOIRE:
- reset_password: Réinitialiser le mot de passe
- disable_account: Désactiver un compte
- copy_groups_from: Copier les groupes d'un référent

ACTIONS INTERDITES (L4 - FORBIDDEN) - Réservées aux humains:
- create_user: Création de compte (processus RH manuel)
- modify_groups: Modification directe des groupes

SÉCURITÉ:
- Connexion LDAPS avec validation de certificat (ssl.CERT_REQUIRED)
- Mots de passe générés non-ambigus (14 chars min)
- Secrets temporaires (_temp_password) chiffrés dans Redis
"""

import secrets
import ssl
import string
from typing import Any, Optional

import structlog
from ldap3 import (
    Server,
    Connection,
    ALL,
    MODIFY_REPLACE,
    MODIFY_ADD,
    NTLM,
    SUBTREE,
    Tls,
)
from ldap3.core.exceptions import LDAPException

from ..config import settings

logger = structlog.get_logger(__name__)


class ActiveDirectoryClient:
    """
    Client pour Active Directory via LDAP3.

    Gère l'authentification et les opérations AD.
    """

    def __init__(self) -> None:
        self._server: Optional[Server] = None
        self._connection: Optional[Connection] = None

    def _get_server(self) -> Server:
        """Retourne le serveur LDAP (lazy init) avec configuration TLS sécurisée."""
        if self._server is None:
            tls_config = None

            # Configuration TLS pour LDAPS
            if settings.ldap_use_ssl:
                # Déterminer le niveau de vérification
                if settings.ldap_verify_ssl:
                    # Vérification activée (RECOMMANDÉ en production)
                    validate = ssl.CERT_REQUIRED
                    logger.info("ldaps_ssl_verification_enabled")
                else:
                    # Vérification désactivée (dev uniquement)
                    validate = ssl.CERT_NONE
                    logger.warning(
                        "ldaps_ssl_verification_disabled",
                        warning="INSECURE: Certificate verification is disabled. "
                                "Enable LDAP_VERIFY_SSL=true in production!"
                    )

                # Créer la configuration TLS
                tls_config = Tls(
                    validate=validate,
                    ca_certs_file=settings.ldap_ca_cert_path or None,
                    version=ssl.PROTOCOL_TLS,  # Utiliser la version TLS la plus récente
                )

            self._server = Server(
                settings.ldap_server,
                use_ssl=settings.ldap_use_ssl,
                tls=tls_config,
                get_info=ALL,
            )
        return self._server

    def _get_connection(self) -> Connection:
        """Retourne une connexion LDAP authentifiée."""
        if self._connection is None or self._connection.closed:
            self._connection = Connection(
                self._get_server(),
                user=settings.ldap_bind_user,
                password=settings.ldap_bind_pass.get_secret_value(),
                authentication=NTLM,
                auto_bind=True,
            )
            logger.info("ldap_connection_established")
        return self._connection

    def close(self) -> None:
        """Ferme la connexion LDAP."""
        if self._connection and not self._connection.closed:
            self._connection.unbind()
            self._connection = None
            logger.info("ldap_connection_closed")

    @staticmethod
    def generate_password(length: int = 14) -> str:
        """
        Génère un mot de passe sécurisé compatible AD.

        Caractères sans ambiguïté (pas de I, l, O, 0, 1).
        """
        upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        lower = "abcdefghjkmnpqrstuvwxyz"
        digits = "23456789"
        special = "!@$*"

        # Au moins un de chaque type
        password = [
            secrets.choice(upper),
            secrets.choice(lower),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Compléter avec des caractères aléatoires
        all_chars = upper + lower + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Mélanger
        secrets.SystemRandom().shuffle(password)
        return "".join(password)

    def _find_user_dn(self, username: str) -> Optional[str]:
        """Trouve le DN d'un utilisateur par son sAMAccountName."""
        conn = self._get_connection()
        search_base = settings.ldap_user_search_base or settings.ldap_base_dn

        conn.search(
            search_base=search_base,
            search_filter=f"(sAMAccountName={username})",
            search_scope=SUBTREE,
            attributes=["distinguishedName"],
        )

        if conn.entries:
            return str(conn.entries[0].distinguishedName)
        return None

    # =========================================================================
    # Opérations de lecture
    # =========================================================================

    def check_user(self, username: str) -> dict[str, Any]:
        """
        Vérifie si un utilisateur existe dans AD.

        Args:
            username: sAMAccountName de l'utilisateur

        Returns:
            Informations de base si trouvé
        """
        try:
            conn = self._get_connection()
            search_base = settings.ldap_user_search_base or settings.ldap_base_dn

            conn.search(
                search_base=search_base,
                search_filter=f"(sAMAccountName={username})",
                search_scope=SUBTREE,
                attributes=[
                    "sAMAccountName",
                    "displayName",
                    "mail",
                    "userAccountControl",
                    "lockoutTime",
                ],
            )

            if not conn.entries:
                return {"exists": False, "error": "User not found"}

            entry = conn.entries[0]

            # Vérifier si le compte est activé (bit 2 de userAccountControl)
            uac = int(entry.userAccountControl.value) if entry.userAccountControl else 0
            is_enabled = not (uac & 2)  # ACCOUNTDISABLE = 2

            # Vérifier si verrouillé
            lockout_time = entry.lockoutTime.value if entry.lockoutTime else None
            is_locked = lockout_time is not None and lockout_time != "0"

            return {
                "exists": True,
                "samAccountName": str(entry.sAMAccountName),
                "displayName": str(entry.displayName) if entry.displayName else None,
                "email": str(entry.mail) if entry.mail else None,
                "enabled": is_enabled,
                "lockedOut": is_locked,
            }

        except LDAPException as e:
            logger.exception("ad_check_user_error", username=username, error=str(e))
            return {"exists": False, "error": str(e)}

    def get_user_info(self, username: str) -> dict[str, Any]:
        """
        Récupère les informations complètes d'un utilisateur AD.

        Args:
            username: sAMAccountName de l'utilisateur

        Returns:
            Informations détaillées de l'utilisateur
        """
        try:
            conn = self._get_connection()
            search_base = settings.ldap_user_search_base or settings.ldap_base_dn

            conn.search(
                search_base=search_base,
                search_filter=f"(sAMAccountName={username})",
                search_scope=SUBTREE,
                attributes=[
                    "sAMAccountName",
                    "displayName",
                    "givenName",
                    "sn",
                    "mail",
                    "title",
                    "department",
                    "company",
                    "telephoneNumber",
                    "userAccountControl",
                    "lockoutTime",
                    "lastLogonTimestamp",
                    "whenCreated",
                    "distinguishedName",
                    "memberOf",
                ],
            )

            if not conn.entries:
                return {"success": False, "error": "User not found"}

            entry = conn.entries[0]

            # Extraire les noms de groupes
            groups = []
            if entry.memberOf:
                for group_dn in entry.memberOf.values:
                    # Extraire le CN du DN
                    cn = group_dn.split(",")[0].replace("CN=", "")
                    groups.append(cn)

            uac = int(entry.userAccountControl.value) if entry.userAccountControl else 0
            is_enabled = not (uac & 2)

            lockout_time = entry.lockoutTime.value if entry.lockoutTime else None
            is_locked = lockout_time is not None and str(lockout_time) != "0"

            return {
                "success": True,
                "samAccountName": str(entry.sAMAccountName),
                "displayName": str(entry.displayName) if entry.displayName else None,
                "firstName": str(entry.givenName) if entry.givenName else None,
                "lastName": str(entry.sn) if entry.sn else None,
                "email": str(entry.mail) if entry.mail else None,
                "title": str(entry.title) if entry.title else None,
                "department": str(entry.department) if entry.department else None,
                "company": str(entry.company) if entry.company else None,
                "phone": str(entry.telephoneNumber) if entry.telephoneNumber else None,
                "enabled": is_enabled,
                "lockedOut": is_locked,
                "lastLogon": str(entry.lastLogonTimestamp) if entry.lastLogonTimestamp else None,
                "created": str(entry.whenCreated) if entry.whenCreated else None,
                "distinguishedName": str(entry.distinguishedName),
                "memberOf": groups,
            }

        except LDAPException as e:
            logger.exception("ad_get_user_info_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Opérations de modification
    # =========================================================================

    def reset_password(
        self,
        username: str,
        new_password: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Réinitialise le mot de passe d'un utilisateur.

        Args:
            username: sAMAccountName de l'utilisateur
            new_password: Nouveau mot de passe (généré si non fourni)

        Returns:
            Résultat avec le mot de passe temporaire
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": "User not found"}

            password = new_password or self.generate_password()
            conn = self._get_connection()

            # Encoder le mot de passe pour AD (UTF-16-LE entre guillemets)
            encoded_password = f'"{password}"'.encode("utf-16-le")

            # Modifier le mot de passe
            conn.modify(
                user_dn,
                {"unicodePwd": [(MODIFY_REPLACE, [encoded_password])]},
            )

            if not conn.result["result"] == 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "Password reset failed"),
                }

            # Déverrouiller le compte si nécessaire
            conn.modify(user_dn, {"lockoutTime": [(MODIFY_REPLACE, [0])]})

            logger.info("ad_password_reset", username=username)

            return {
                "success": True,
                "username": username,
                "message": "Password reset successful",
                "_temp_password": password,  # Pour envoi via MySecret
            }

        except LDAPException as e:
            logger.exception("ad_reset_password_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def unlock_account(self, username: str) -> dict[str, Any]:
        """
        Déverrouille un compte AD.

        Args:
            username: sAMAccountName de l'utilisateur

        Returns:
            Résultat de l'opération
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": "User not found"}

            conn = self._get_connection()
            conn.modify(user_dn, {"lockoutTime": [(MODIFY_REPLACE, [0])]})

            if conn.result["result"] != 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "Unlock failed"),
                }

            logger.info("ad_account_unlocked", username=username)
            return {
                "success": True,
                "username": username,
                "message": "Account unlocked",
            }

        except LDAPException as e:
            logger.exception("ad_unlock_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def create_user(
        self,
        username: str,
        firstname: str,
        lastname: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        company: Optional[str] = None,
        ou_path: Optional[str] = None,
        referent_username: Optional[str] = None,
        copy_groups: bool = False,
    ) -> dict[str, Any]:
        """
        Crée un nouvel utilisateur AD.

        Args:
            username: sAMAccountName
            firstname: Prénom
            lastname: Nom de famille
            password: Mot de passe (généré si non fourni)
            email: Email (généré si non fourni)
            title: Poste
            department: Service
            company: Établissement
            ou_path: OU cible (sinon utilise celle du référent ou défaut)
            referent_username: Compte modèle
            copy_groups: Copier les groupes du référent

        Returns:
            Résultat avec infos du compte créé
        """
        try:
            # Vérifier que l'utilisateur n'existe pas
            existing = self._find_user_dn(username)
            if existing:
                return {"success": False, "error": "User already exists"}

            conn = self._get_connection()

            # Déterminer l'OU
            target_ou = ou_path
            referent_groups = []

            if referent_username:
                referent_info = self.get_user_info(referent_username)
                if referent_info.get("success"):
                    # Utiliser l'OU du référent si pas spécifiée
                    if not target_ou:
                        ref_dn = referent_info.get("distinguishedName", "")
                        target_ou = ",".join(ref_dn.split(",")[1:])

                    # Récupérer les groupes si demandé
                    if copy_groups:
                        referent_groups = referent_info.get("memberOf", [])

            if not target_ou:
                target_ou = settings.ldap_user_search_base or settings.ldap_base_dn

            # Formater le nom
            formatted_firstname = firstname.capitalize()
            formatted_lastname = lastname.upper()
            display_name = f"{formatted_lastname} {formatted_firstname}"

            # Générer email et mot de passe
            user_email = email or f"{username}@widip.fr"
            user_password = password or self.generate_password()
            upn = f"{username}@{settings.ldap_base_dn.replace('DC=', '').replace(',', '.')}"

            # DN du nouvel utilisateur
            user_dn = f"CN={display_name},{target_ou}"

            # Attributs de l'utilisateur
            user_attrs = {
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "sAMAccountName": username,
                "userPrincipalName": upn,
                "givenName": formatted_firstname,
                "sn": formatted_lastname,
                "displayName": display_name,
                "mail": user_email,
                "userAccountControl": 544,  # Normal account + Password not required (temporaire)
            }

            if title:
                user_attrs["title"] = title
            if department:
                user_attrs["department"] = department
            if company:
                user_attrs["company"] = company

            # Créer l'utilisateur
            conn.add(user_dn, attributes=user_attrs)

            if conn.result["result"] != 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "User creation failed"),
                }

            # Définir le mot de passe
            encoded_password = f'"{user_password}"'.encode("utf-16-le")
            conn.modify(
                user_dn,
                {"unicodePwd": [(MODIFY_REPLACE, [encoded_password])]},
            )

            # Activer le compte
            conn.modify(
                user_dn,
                {"userAccountControl": [(MODIFY_REPLACE, [512])]},  # Normal account, enabled
            )

            # Copier les groupes du référent
            groups_added = []
            if copy_groups and referent_groups:
                for group_name in referent_groups:
                    try:
                        # Trouver le DN du groupe
                        conn.search(
                            search_base=settings.ldap_base_dn,
                            search_filter=f"(&(objectClass=group)(cn={group_name}))",
                            search_scope=SUBTREE,
                            attributes=["distinguishedName"],
                        )
                        if conn.entries:
                            group_dn = str(conn.entries[0].distinguishedName)
                            conn.modify(
                                group_dn,
                                {"member": [(MODIFY_ADD, [user_dn])]},
                            )
                            if conn.result["result"] == 0:
                                groups_added.append(group_name)
                    except Exception:
                        pass  # Ignorer les erreurs de groupe

            logger.info("ad_user_created", username=username, ou=target_ou)

            return {
                "success": True,
                "username": username,
                "displayName": display_name,
                "email": user_email,
                "ou": target_ou,
                "groupsAdded": groups_added,
                "message": "User created successfully",
                "_temp_password": user_password,
            }

        except LDAPException as e:
            logger.exception("ad_create_user_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def disable_account(
        self,
        username: str,
        target_ou: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Désactive un compte AD et optionnellement le déplace.

        Args:
            username: sAMAccountName de l'utilisateur
            target_ou: OU de destination (comptes désactivés)

        Returns:
            Résultat de l'opération
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": "User not found"}

            conn = self._get_connection()

            # Désactiver le compte (bit ACCOUNTDISABLE)
            conn.modify(
                user_dn,
                {"userAccountControl": [(MODIFY_REPLACE, [514])]},  # 512 + 2 (disabled)
            )

            if conn.result["result"] != 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "Disable failed"),
                }

            # Déplacer vers l'OU cible si spécifiée
            moved_to = None
            if target_ou:
                cn = user_dn.split(",")[0]
                conn.modify_dn(user_dn, cn, new_superior=target_ou)
                if conn.result["result"] == 0:
                    moved_to = target_ou

            logger.info("ad_account_disabled", username=username, moved_to=moved_to)

            return {
                "success": True,
                "username": username,
                "enabled": False,
                "movedTo": moved_to,
                "message": "Account disabled",
            }

        except LDAPException as e:
            logger.exception("ad_disable_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def enable_account(self, username: str) -> dict[str, Any]:
        """
        Réactive un compte AD désactivé.

        Args:
            username: sAMAccountName de l'utilisateur

        Returns:
            Résultat de l'opération
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": "User not found"}

            conn = self._get_connection()

            # Activer le compte
            conn.modify(
                user_dn,
                {"userAccountControl": [(MODIFY_REPLACE, [512])]},  # Normal account
            )

            if conn.result["result"] != 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "Enable failed"),
                }

            logger.info("ad_account_enabled", username=username)

            return {
                "success": True,
                "username": username,
                "enabled": True,
                "message": "Account enabled",
            }

        except LDAPException as e:
            logger.exception("ad_enable_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def move_to_ou(
        self,
        username: str,
        target_ou: str,
    ) -> dict[str, Any]:
        """
        Déplace un utilisateur vers une autre OU.

        Args:
            username: sAMAccountName de l'utilisateur
            target_ou: OU de destination

        Returns:
            Résultat de l'opération
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": "User not found"}

            conn = self._get_connection()

            # Extraire le CN
            cn = user_dn.split(",")[0]
            current_ou = ",".join(user_dn.split(",")[1:])

            if current_ou == target_ou:
                return {
                    "success": True,
                    "username": username,
                    "message": "User already in target OU",
                    "ou": target_ou,
                }

            # Déplacer
            conn.modify_dn(user_dn, cn, new_superior=target_ou)

            if conn.result["result"] != 0:
                return {
                    "success": False,
                    "error": conn.result.get("description", "Move failed"),
                }

            logger.info("ad_user_moved", username=username, from_ou=current_ou, to_ou=target_ou)

            return {
                "success": True,
                "username": username,
                "previousOU": current_ou,
                "newOU": target_ou,
                "message": "User moved to new OU",
            }

        except LDAPException as e:
            logger.exception("ad_move_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}

    def copy_groups_from(
        self,
        username: str,
        referent_username: str,
    ) -> dict[str, Any]:
        """
        Copie les groupes d'un utilisateur référent vers un autre utilisateur.

        Args:
            username: Utilisateur cible
            referent_username: Utilisateur source des groupes

        Returns:
            Résultat avec les groupes ajoutés
        """
        try:
            user_dn = self._find_user_dn(username)
            if not user_dn:
                return {"success": False, "error": f"User '{username}' not found"}

            referent_info = self.get_user_info(referent_username)
            if not referent_info.get("success"):
                return {"success": False, "error": f"Referent '{referent_username}' not found"}

            referent_groups = referent_info.get("memberOf", [])
            if not referent_groups:
                return {
                    "success": True,
                    "username": username,
                    "message": "Referent has no groups",
                    "groupsAdded": [],
                }

            conn = self._get_connection()
            groups_added = []
            groups_failed = []

            for group_name in referent_groups:
                try:
                    # Trouver le DN du groupe
                    conn.search(
                        search_base=settings.ldap_base_dn,
                        search_filter=f"(&(objectClass=group)(cn={group_name}))",
                        search_scope=SUBTREE,
                        attributes=["distinguishedName"],
                    )
                    if conn.entries:
                        group_dn = str(conn.entries[0].distinguishedName)
                        conn.modify(
                            group_dn,
                            {"member": [(MODIFY_ADD, [user_dn])]},
                        )
                        if conn.result["result"] == 0:
                            groups_added.append(group_name)
                        else:
                            groups_failed.append(group_name)
                except Exception:
                    groups_failed.append(group_name)

            logger.info(
                "ad_groups_copied",
                username=username,
                referent=referent_username,
                added=len(groups_added),
            )

            return {
                "success": True,
                "username": username,
                "referent": referent_username,
                "groupsAdded": groups_added,
                "groupsFailed": groups_failed,
                "totalAdded": len(groups_added),
            }

        except LDAPException as e:
            logger.exception("ad_copy_groups_error", username=username, error=str(e))
            return {"success": False, "error": str(e)}


# Instance singleton
ad_client = ActiveDirectoryClient()
