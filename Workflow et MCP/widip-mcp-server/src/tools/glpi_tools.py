"""
Tools MCP pour GLPI.

Ce module expose les outils de gestion GLPI aux agents IA:
- Gestion des tickets (création, suivi, clôture)
- Recherche de clients
- Gestion des utilisateurs GLPI
"""

from typing import Any, Optional

from ..clients.glpi import glpi_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
    bool_param,
)


# =============================================================================
# Tools de recherche
# =============================================================================


@tool_registry.register_function(
    name="glpi_search_client",
    description="""Recherche un client/utilisateur dans GLPI par nom, email ou téléphone.
Utilise ce tool pour trouver les informations d'un client avant de créer un ticket.
Retourne l'ID client, nom, email et téléphone si trouvé.""",
    parameters={
        "name": string_param(
            "Nom du client à rechercher (recherche partielle)",
            required=False,
        ),
        "email": string_param(
            "Email du client à rechercher",
            required=False,
        ),
        "phone": string_param(
            "Numéro de téléphone du client",
            required=False,
        ),
    },
)
async def glpi_search_client(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> dict[str, Any]:
    """Recherche un client dans GLPI."""
    return await glpi_client.search_client(name=name, email=email, phone=phone)


# =============================================================================
# Tools de gestion des tickets
# =============================================================================


@tool_registry.register_function(
    name="glpi_create_ticket",
    description="""Crée un nouveau ticket d'incident dans GLPI.
Utilise ce tool pour ouvrir un ticket suite à une alerte ou une demande utilisateur.
Retourne l'ID du ticket créé.""",
    parameters={
        "title": string_param(
            "Titre du ticket (résumé du problème)",
            required=True,
        ),
        "description": string_param(
            "Description détaillée du problème",
            required=True,
        ),
        "client_name": string_param(
            "Nom du client concerné (pour rechercher son ID)",
            required=False,
        ),
        "priority": int_param(
            "Priorité du ticket (1=très basse, 2=basse, 3=moyenne, 4=haute, 5=très haute)",
            required=False,
            default=3,
        ),
        "urgency": int_param(
            "Urgence du ticket (1-5, 3=moyenne)",
            required=False,
            default=3,
        ),
        "impact": int_param(
            "Impact du ticket (1-5, 3=moyen)",
            required=False,
            default=3,
        ),
    },
)
async def glpi_create_ticket(
    title: str,
    description: str,
    client_name: Optional[str] = None,
    priority: int = 3,
    urgency: int = 3,
    impact: int = 3,
) -> dict[str, Any]:
    """Crée un ticket GLPI."""
    return await glpi_client.create_ticket(
        title=title,
        description=description,
        client_name=client_name or "",
        priority=priority,
        urgency=urgency,
        impact=impact,
    )


@tool_registry.register_function(
    name="glpi_get_ticket_details",
    description="""Récupère les détails complets d'un ticket GLPI.
Utilise ce tool pour obtenir toutes les informations sur un ticket:
titre, description, statut, priorité, historique des suivis, etc.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket à consulter",
            required=True,
        ),
    },
)
async def glpi_get_ticket_details(ticket_id: int) -> dict[str, Any]:
    """Récupère les détails d'un ticket."""
    return await glpi_client.get_ticket_details(ticket_id)


@tool_registry.register_function(
    name="glpi_get_ticket_status",
    description="""Récupère le statut actuel d'un ticket GLPI.
Retourne le statut (Nouveau, En cours, En attente, Résolu, Clos) et les infos de base.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket",
            required=True,
        ),
    },
)
async def glpi_get_ticket_status(ticket_id: int) -> dict[str, Any]:
    """Récupère le statut d'un ticket."""
    details = await glpi_client.get_ticket_details(ticket_id)
    if not details.get("found"):
        return details

    status_map = {
        1: "Nouveau",
        2: "En cours (attribué)",
        3: "En cours (planifié)",
        4: "En attente",
        5: "Résolu",
        6: "Clos",
    }

    return {
        "success": True,
        "ticket_id": details.get("ticket_id"),
        "title": details.get("title"),
        "status": status_map.get(details.get("status", 0), "Inconnu"),
        "status_code": details.get("status"),
    }


@tool_registry.register_function(
    name="glpi_add_ticket_followup",
    description="""Ajoute un commentaire/suivi à un ticket GLPI existant.
Utilise ce tool pour documenter les actions entreprises ou communiquer avec le client.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket",
            required=True,
        ),
        "content": string_param(
            "Contenu du suivi/commentaire",
            required=True,
        ),
        "is_private": bool_param(
            "Si vrai, le suivi est privé (non visible par le client)",
            required=False,
            default=False,
        ),
    },
)
async def glpi_add_ticket_followup(
    ticket_id: int,
    content: str,
    is_private: bool = False,
) -> dict[str, Any]:
    """Ajoute un suivi à un ticket."""
    return await glpi_client.add_ticket_followup(
        ticket_id=ticket_id,
        content=content,
        is_private=is_private,
    )


@tool_registry.register_function(
    name="glpi_update_ticket_status",
    description="""Met à jour le statut d'un ticket GLPI.
Statuts disponibles: 1=Nouveau, 2=En cours (attribué), 3=Planifié, 4=En attente, 5=Résolu, 6=Clos""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket",
            required=True,
        ),
        "status": int_param(
            "Nouveau statut (1-6)",
            required=True,
        ),
    },
)
async def glpi_update_ticket_status(
    ticket_id: int,
    status: int,
) -> dict[str, Any]:
    """Met à jour le statut d'un ticket."""
    return await glpi_client.update_ticket_status(ticket_id=ticket_id, status=status)


@tool_registry.register_function(
    name="glpi_close_ticket",
    description="""Clôture un ticket GLPI avec une solution.
Ajoute la solution comme suivi et passe le statut à Résolu.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket à clôturer",
            required=True,
        ),
        "solution": string_param(
            "Description de la solution apportée",
            required=True,
        ),
    },
)
async def glpi_close_ticket(
    ticket_id: int,
    solution: str,
) -> dict[str, Any]:
    """Clôture un ticket avec solution."""
    return await glpi_client.close_ticket(ticket_id=ticket_id, solution=solution)


@tool_registry.register_function(
    name="glpi_search_new_tickets",
    description="""Recherche les tickets récemment créés avec statut 'Nouveau'.
Utilise ce tool pour identifier les tickets nécessitant un traitement.""",
    parameters={
        "minutes_since": int_param(
            "Rechercher les tickets des X dernières minutes",
            required=False,
            default=10,
        ),
        "limit": int_param(
            "Nombre maximum de tickets à retourner",
            required=False,
            default=20,
        ),
    },
)
async def glpi_search_new_tickets(
    minutes_since: int = 10,
    limit: int = 20,
) -> dict[str, Any]:
    """Recherche les nouveaux tickets."""
    return await glpi_client.search_new_tickets(minutes_since=minutes_since, limit=limit)


@tool_registry.register_function(
    name="glpi_get_ticket_history",
    description="""Récupère l'historique des modifications d'un ticket.
Retourne les changements de statut, assignations, etc.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket",
            required=True,
        ),
    },
)
async def glpi_get_ticket_history(ticket_id: int) -> dict[str, Any]:
    """Récupère l'historique d'un ticket."""
    await glpi_client._ensure_session()

    try:
        response = await glpi_client.client.get(
            f"{glpi_client.base_url}/Ticket/{ticket_id}/Log",
            headers=glpi_client._get_headers(),
        )

        if not response.is_success:
            return {"success": False, "error": f"Error: {response.status_code}"}

        logs = response.json()

        if isinstance(logs, list):
            history = [
                {
                    "id": log.get("id"),
                    "date": log.get("date_mod") or log.get("date_creation"),
                    "user": log.get("user_name"),
                    "field": log.get("id_search_option"),
                    "old_value": log.get("old_value"),
                    "new_value": log.get("new_value"),
                }
                for log in logs
            ]
            return {
                "success": True,
                "ticket_id": ticket_id,
                "count": len(history),
                "history": history,
            }

        return {"success": True, "ticket_id": ticket_id, "count": 0, "history": []}

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Tools de gestion des utilisateurs GLPI
# =============================================================================


@tool_registry.register_function(
    name="glpi_create_user",
    description="""Crée un nouvel utilisateur dans GLPI.
Utilise ce tool lors de l'onboarding pour créer le compte GLPI associé.""",
    parameters={
        "login": string_param(
            "Identifiant de connexion (SamAccountName)",
            required=True,
        ),
        "realname": string_param(
            "Nom de famille",
            required=True,
        ),
        "firstname": string_param(
            "Prénom",
            required=False,
        ),
        "password": string_param(
            "Mot de passe (si non fourni, sera généré)",
            required=False,
        ),
        "email": string_param(
            "Adresse email",
            required=False,
        ),
        "profiles_id": int_param(
            "ID du profil/rôle GLPI",
            required=False,
            default=0,
        ),
        "entities_id": int_param(
            "ID de l'entité GLPI",
            required=False,
            default=0,
        ),
        "is_active": bool_param(
            "Compte actif",
            required=False,
            default=True,
        ),
    },
)
async def glpi_create_user(
    login: str,
    realname: str,
    firstname: Optional[str] = None,
    password: Optional[str] = None,
    email: Optional[str] = None,
    profiles_id: int = 0,
    entities_id: int = 0,
    is_active: bool = True,
) -> dict[str, Any]:
    """Crée un utilisateur GLPI."""
    await glpi_client._ensure_session()

    user_input: dict[str, Any] = {
        "name": login,
        "realname": realname,
        "is_active": 1 if is_active else 0,
        "entities_id": entities_id,
        "profiles_id": profiles_id,
    }

    if firstname:
        user_input["firstname"] = firstname
    if email:
        user_input["email"] = email
    if password:
        user_input["password"] = password
        user_input["password2"] = password

    try:
        response = await glpi_client.client.post(
            f"{glpi_client.base_url}/User",
            json={"input": user_input},
            headers=glpi_client._get_headers(),
        )

        if not response.is_success:
            return {"success": False, "error": response.text[:200]}

        data = response.json()
        return {
            "success": True,
            "user_id": str(data.get("id")),
            "login": login,
            "realname": realname,
            "message": "Utilisateur GLPI créé avec succès",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool_registry.register_function(
    name="glpi_get_user",
    description="""Récupère les informations d'un utilisateur GLPI par son ID.""",
    parameters={
        "user_id": int_param(
            "ID de l'utilisateur GLPI",
            required=True,
        ),
    },
)
async def glpi_get_user(user_id: int) -> dict[str, Any]:
    """Récupère un utilisateur GLPI."""
    await glpi_client._ensure_session()

    try:
        response = await glpi_client.client.get(
            f"{glpi_client.base_url}/User/{user_id}",
            params={"expand_dropdowns": "true"},
            headers=glpi_client._get_headers(),
        )

        if not response.is_success:
            return {"success": False, "error": "Utilisateur non trouvé"}

        user = response.json()
        return {
            "success": True,
            "user": {
                "id": user.get("id"),
                "login": user.get("name"),
                "realname": user.get("realname"),
                "firstname": user.get("firstname"),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "is_active": user.get("is_active") == 1,
                "entities_id": user.get("entities_id"),
                "profiles_id": user.get("profiles_id"),
                "date_creation": user.get("date_creation"),
                "date_mod": user.get("date_mod"),
                "last_login": user.get("last_login"),
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool_registry.register_function(
    name="glpi_update_user",
    description="""Met à jour un utilisateur GLPI existant.""",
    parameters={
        "user_id": int_param(
            "ID de l'utilisateur à modifier",
            required=True,
        ),
        "realname": string_param("Nouveau nom", required=False),
        "firstname": string_param("Nouveau prénom", required=False),
        "email": string_param("Nouvel email", required=False),
        "phone": string_param("Nouveau téléphone", required=False),
        "is_active": bool_param("Activer/désactiver", required=False),
    },
)
async def glpi_update_user(
    user_id: int,
    realname: Optional[str] = None,
    firstname: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict[str, Any]:
    """Met à jour un utilisateur GLPI."""
    await glpi_client._ensure_session()

    update_fields: dict[str, Any] = {"id": user_id}

    if realname is not None:
        update_fields["realname"] = realname
    if firstname is not None:
        update_fields["firstname"] = firstname
    if email is not None:
        update_fields["email"] = email
    if phone is not None:
        update_fields["phone"] = phone
    if is_active is not None:
        update_fields["is_active"] = 1 if is_active else 0

    try:
        response = await glpi_client.client.put(
            f"{glpi_client.base_url}/User/{user_id}",
            json={"input": update_fields},
            headers=glpi_client._get_headers(),
        )

        if not response.is_success:
            return {"success": False, "error": response.text[:200]}

        return {
            "success": True,
            "user_id": user_id,
            "message": "Utilisateur GLPI mis à jour avec succès",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool_registry.register_function(
    name="glpi_disable_user",
    description="""Désactive un utilisateur GLPI (is_active = 0).""",
    parameters={
        "user_id": int_param(
            "ID de l'utilisateur à désactiver",
            required=True,
        ),
    },
)
async def glpi_disable_user(user_id: int) -> dict[str, Any]:
    """Désactive un utilisateur GLPI."""
    return await glpi_update_user(user_id=user_id, is_active=False)


# =============================================================================
# Tools d'assignation et communication
# =============================================================================


@tool_registry.register_function(
    name="glpi_assign_ticket",
    description="""Assigne un ticket GLPI à un technicien ou un groupe.
Utilise ce tool pour affecter un ticket à un technicien spécifique ou à un groupe de support.
SAFEGUARD: L2 (MODERATE) - Modification d'assignation.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket à assigner",
            required=True,
        ),
        "user_id": int_param(
            "ID du technicien à assigner (optionnel si group_id fourni)",
            required=False,
        ),
        "group_id": int_param(
            "ID du groupe à assigner (optionnel si user_id fourni)",
            required=False,
        ),
    },
)
async def glpi_assign_ticket(
    ticket_id: int,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> dict[str, Any]:
    """Assigne un ticket à un technicien ou groupe."""
    if not user_id and not group_id:
        return {"success": False, "error": "user_id ou group_id requis"}

    await glpi_client._ensure_session()

    try:
        assignments = []

        # Assigner à un utilisateur
        if user_id:
            response = await glpi_client.client.post(
                f"{glpi_client.base_url}/Ticket/{ticket_id}/Ticket_User",
                json={"input": {"tickets_id": ticket_id, "users_id": user_id, "type": 2}},  # type 2 = technicien
                headers=glpi_client._get_headers(),
            )
            if response.is_success:
                assignments.append({"type": "user", "id": user_id})

        # Assigner à un groupe
        if group_id:
            response = await glpi_client.client.post(
                f"{glpi_client.base_url}/Ticket/{ticket_id}/Group_Ticket",
                json={"input": {"tickets_id": ticket_id, "groups_id": group_id, "type": 2}},  # type 2 = technicien
                headers=glpi_client._get_headers(),
            )
            if response.is_success:
                assignments.append({"type": "group", "id": group_id})

        if not assignments:
            return {"success": False, "error": "Échec de l'assignation"}

        return {
            "success": True,
            "ticket_id": ticket_id,
            "assignments": assignments,
            "message": "Ticket assigné avec succès",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool_registry.register_function(
    name="glpi_send_email",
    description="""Envoie un email via GLPI lié à un ticket.
Utilise ce tool pour envoyer un email au demandeur ou à un destinataire spécifique.
L'email sera lié au ticket dans GLPI pour traçabilité.
SAFEGUARD: L1 (MINOR) - Communication client.""",
    parameters={
        "ticket_id": int_param(
            "ID du ticket lié à l'email",
            required=True,
        ),
        "to_email": string_param(
            "Adresse email du destinataire",
            required=True,
        ),
        "subject": string_param(
            "Sujet de l'email",
            required=True,
        ),
        "body": string_param(
            "Corps de l'email (HTML supporté)",
            required=True,
        ),
    },
)
async def glpi_send_email(
    ticket_id: int,
    to_email: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Envoie un email via GLPI lié à un ticket."""
    await glpi_client._ensure_session()

    try:
        # Ajouter un suivi au ticket avec l'email envoyé
        followup_content = f"""📧 **Email envoyé**

**À:** {to_email}
**Sujet:** {subject}

---
{body}
"""
        # Ajouter le suivi de l'email dans le ticket
        await glpi_client.add_ticket_followup(
            ticket_id=ticket_id,
            content=followup_content,
            is_private=False,
        )

        # Note: L'envoi réel de l'email se fait via le module notification
        # GLPI peut être configuré pour envoyer automatiquement les notifications
        # Ici on log juste le suivi pour traçabilité

        return {
            "success": True,
            "ticket_id": ticket_id,
            "to_email": to_email,
            "subject": subject,
            "message": "Email documenté dans le ticket. L'envoi réel passe par le module notification.",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
