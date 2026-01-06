"""
Tools MCP pour Active Directory.

Ce module expose les outils de gestion AD aux agents IA:
- Vérification et consultation d'utilisateurs
- Reset de mots de passe
- Déverrouillage de comptes
- Création et gestion de comptes
- Gestion des groupes
"""

from typing import Any, Optional

from ..clients.activedirectory import ad_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    bool_param,
)


# =============================================================================
# Tools de consultation
# =============================================================================


@tool_registry.register_function(
    name="ad_check_user",
    description="""Vérifie si un utilisateur existe dans Active Directory.
Retourne des infos de base: existence, nom affiché, email, état du compte (actif/verrouillé).
Utilise ce tool en premier pour vérifier qu'un utilisateur existe avant d'autres opérations.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur (sAMAccountName)",
            required=True,
        ),
    },
)
def ad_check_user(username: str) -> dict[str, Any]:
    """Vérifie si un utilisateur existe."""
    result = ad_client.check_user(username)
    result["operation"] = "check_user"
    return result


@tool_registry.register_function(
    name="ad_get_user_info",
    description="""Récupère les informations complètes d'un utilisateur Active Directory.
Retourne: nom, prénom, email, téléphone, titre, département, entreprise,
état du compte, dernière connexion, groupes AD.
Utile pour obtenir le contexte complet d'un utilisateur.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur (sAMAccountName)",
            required=True,
        ),
    },
)
def ad_get_user_info(username: str) -> dict[str, Any]:
    """Récupère les infos complètes d'un utilisateur."""
    result = ad_client.get_user_info(username)
    result["operation"] = "get_user_info"
    return result


# =============================================================================
# Tools de support (niveau 1)
# =============================================================================


@tool_registry.register_function(
    name="ad_reset_password",
    description="""Réinitialise le mot de passe d'un utilisateur Active Directory.
Génère un nouveau mot de passe sécurisé (14 caractères, mixte) et déverrouille le compte.
Le mot de passe temporaire doit être transmis de façon sécurisée (MySecret).
ATTENTION: Action sensible, nécessite validation si politique Safeguard L3.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur (sAMAccountName)",
            required=True,
        ),
        "new_password": string_param(
            "Nouveau mot de passe (si non fourni, sera généré automatiquement)",
            required=False,
        ),
    },
)
def ad_reset_password(
    username: str,
    new_password: Optional[str] = None,
) -> dict[str, Any]:
    """Reset le mot de passe d'un utilisateur."""
    result = ad_client.reset_password(username, new_password)
    result["operation"] = "reset_password"
    return result


@tool_registry.register_function(
    name="ad_unlock_account",
    description="""Déverrouille un compte Active Directory verrouillé suite à des échecs de connexion.
N'affecte pas le mot de passe, uniquement le statut de verrouillage.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur (sAMAccountName)",
            required=True,
        ),
    },
)
def ad_unlock_account(username: str) -> dict[str, Any]:
    """Déverrouille un compte AD."""
    result = ad_client.unlock_account(username)
    result["operation"] = "unlock_account"
    return result


# =============================================================================
# Tools de création/gestion (niveau 2-3)
# =============================================================================


@tool_registry.register_function(
    name="ad_create_user",
    description="""Crée un nouvel utilisateur dans Active Directory.
Génère automatiquement le mot de passe si non fourni.
Peut utiliser un compte référent pour déterminer l'OU et copier les groupes.
ATTENTION: Action sensible, nécessite validation Safeguard L3.""",
    parameters={
        "username": string_param(
            "Identifiant de connexion (sAMAccountName)",
            required=True,
        ),
        "firstname": string_param(
            "Prénom",
            required=True,
        ),
        "lastname": string_param(
            "Nom de famille",
            required=True,
        ),
        "password": string_param(
            "Mot de passe (si non fourni, sera généré)",
            required=False,
        ),
        "email": string_param(
            "Adresse email (si non fourni: username@widip.fr)",
            required=False,
        ),
        "title": string_param(
            "Poste / Fonction",
            required=False,
        ),
        "department": string_param(
            "Service / Département",
            required=False,
        ),
        "company": string_param(
            "Établissement / Entreprise",
            required=False,
        ),
        "ou_path": string_param(
            "OU cible (ex: OU=Utilisateurs,DC=widip,DC=local)",
            required=False,
        ),
        "referent_username": string_param(
            "Compte modèle pour l'OU et les groupes",
            required=False,
        ),
        "copy_groups": bool_param(
            "Copier les groupes du référent",
            required=False,
            default=False,
        ),
    },
)
def ad_create_user(
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
    """Crée un utilisateur AD."""
    result = ad_client.create_user(
        username=username,
        firstname=firstname,
        lastname=lastname,
        password=password,
        email=email,
        title=title,
        department=department,
        company=company,
        ou_path=ou_path,
        referent_username=referent_username,
        copy_groups=copy_groups,
    )
    result["operation"] = "create_user"
    return result


@tool_registry.register_function(
    name="ad_disable_account",
    description="""Désactive un compte Active Directory.
Peut optionnellement déplacer le compte vers une OU de comptes désactivés.
Utilise ce tool lors d'un offboarding ou pour désactiver un compte compromis.
ATTENTION: Action sensible, nécessite validation Safeguard L3.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur à désactiver",
            required=True,
        ),
        "target_ou": string_param(
            "OU de destination pour les comptes désactivés (optionnel)",
            required=False,
        ),
    },
)
def ad_disable_account(
    username: str,
    target_ou: Optional[str] = None,
) -> dict[str, Any]:
    """Désactive un compte AD."""
    result = ad_client.disable_account(username, target_ou)
    result["operation"] = "disable_account"
    return result


@tool_registry.register_function(
    name="ad_enable_account",
    description="""Réactive un compte Active Directory désactivé.
Utilise ce tool pour réactiver un compte précédemment désactivé.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur à réactiver",
            required=True,
        ),
    },
)
def ad_enable_account(username: str) -> dict[str, Any]:
    """Réactive un compte AD."""
    result = ad_client.enable_account(username)
    result["operation"] = "enable_account"
    return result


@tool_registry.register_function(
    name="ad_move_to_ou",
    description="""Déplace un utilisateur vers une autre Unité d'Organisation (OU).
Utilise ce tool lors de changements de service ou de site.""",
    parameters={
        "username": string_param(
            "Identifiant de l'utilisateur",
            required=True,
        ),
        "target_ou": string_param(
            "OU de destination (ex: OU=Marketing,OU=Utilisateurs,DC=widip,DC=local)",
            required=True,
        ),
    },
)
def ad_move_to_ou(
    username: str,
    target_ou: str,
) -> dict[str, Any]:
    """Déplace un utilisateur vers une autre OU."""
    result = ad_client.move_to_ou(username, target_ou)
    result["operation"] = "move_to_ou"
    return result


@tool_registry.register_function(
    name="ad_copy_groups_from",
    description="""Copie les groupes AD d'un utilisateur référent vers un autre utilisateur.
Utilise ce tool pour donner les mêmes droits qu'un collègue existant.
Ne supprime pas les groupes existants, ajoute uniquement.""",
    parameters={
        "username": string_param(
            "Utilisateur cible qui recevra les groupes",
            required=True,
        ),
        "referent_username": string_param(
            "Utilisateur source dont on copie les groupes",
            required=True,
        ),
    },
)
def ad_copy_groups_from(
    username: str,
    referent_username: str,
) -> dict[str, Any]:
    """Copie les groupes d'un référent."""
    result = ad_client.copy_groups_from(username, referent_username)
    result["operation"] = "copy_groups_from"
    return result
