"""
Client pour l'API GLPI.

GLPI (Gestionnaire Libre de Parc Informatique) est utilisé pour:
- Gestion des tickets de support
- Base de données clients
- Inventaire informatique
"""

from typing import Any, Optional

import structlog

from ..config import settings
from .base import BaseClient, NotFoundError

logger = structlog.get_logger(__name__)


class GLPIClient(BaseClient):
    """
    Client pour l'API REST GLPI.

    Documentation API: https://glpi-project.org/DOC/FR/index.php?title=API_REST
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.glpi_url,
            timeout=30.0,
        )
        self._session_token: Optional[str] = None
        self._app_token = settings.glpi_app_token.get_secret_value()
        self._user_token = settings.glpi_user_token.get_secret_value()

    def _get_headers(self) -> dict[str, str]:
        """Retourne les headers GLPI."""
        headers = {
            "App-Token": self._app_token,
            "Content-Type": "application/json",
        }
        if self._session_token:
            headers["Session-Token"] = self._session_token
        return headers

    async def _ensure_session(self) -> None:
        """S'assure qu'une session est active."""
        if self._session_token:
            return

        logger.info("glpi_init_session")

        response = await self.client.get(
            f"{self.base_url}/initSession",
            headers={
                "App-Token": self._app_token,
                "Authorization": f"user_token {self._user_token}",
            },
        )

        if not response.is_success:
            raise Exception(f"GLPI session init failed: {response.status_code}")

        data = response.json()
        self._session_token = data.get("session_token")
        logger.info("glpi_session_created", session_token=self._session_token[:10] + "...")

    async def kill_session(self) -> None:
        """Termine la session GLPI."""
        if not self._session_token:
            return

        try:
            await self.client.get(
                f"{self.base_url}/killSession",
                headers=self._get_headers(),
            )
            logger.info("glpi_session_killed")
        except Exception as e:
            logger.warning("glpi_session_kill_failed", error=str(e))
        finally:
            self._session_token = None

    # =========================================================================
    # Opérations sur les clients/utilisateurs
    # =========================================================================

    async def search_client(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Recherche un client/utilisateur dans GLPI.

        Args:
            name: Nom du client (recherche partielle)
            email: Email du client
            phone: Téléphone du client

        Returns:
            Informations du client trouvé ou None
        """
        await self._ensure_session()

        # Construire les critères de recherche
        criteria = []
        search_fields = []

        if name:
            # Field 1 = name dans User
            criteria.append({
                "field": 1,
                "searchtype": "contains",
                "value": name,
            })
            search_fields.append(f"name={name}")

        if email:
            # Field 5 = email dans User
            criteria.append({
                "field": 5,
                "searchtype": "contains",
                "value": email,
            })
            search_fields.append(f"email={email}")

        if phone:
            # Field 6 = phone dans User
            criteria.append({
                "field": 6,
                "searchtype": "contains",
                "value": phone,
            })
            search_fields.append(f"phone={phone}")

        if not criteria:
            return {"found": False, "error": "No search criteria provided"}

        logger.info("glpi_search_client", criteria=search_fields)

        # Effectuer la recherche
        try:
            params = {
                "criteria[0][field]": criteria[0]["field"],
                "criteria[0][searchtype]": criteria[0]["searchtype"],
                "criteria[0][value]": criteria[0]["value"],
            }

            response = await self.client.get(
                f"{self.base_url}/search/User",
                params=params,
                headers=self._get_headers(),
            )

            if not response.is_success:
                return {"found": False, "error": f"Search failed: {response.status_code}"}

            data = response.json()
            results = data.get("data", [])

            if not results:
                return {"found": False, "message": "No client found"}

            # Prendre le premier résultat
            client = results[0]
            return {
                "found": True,
                "client_id": client.get("2"),  # ID
                "client_name": client.get("1"),  # Name
                "client_email": client.get("5", ""),  # Email
                "client_phone": client.get("6", ""),  # Phone
            }

        except Exception as e:
            logger.exception("glpi_search_client_error", error=str(e))
            return {"found": False, "error": str(e)}

    # =========================================================================
    # Opérations sur les tickets
    # =========================================================================

    async def create_ticket(
        self,
        title: str,
        description: str,
        client_name: str,
        priority: int = 3,
        urgency: int = 3,
        impact: int = 3,
        category_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Crée un nouveau ticket GLPI.

        Args:
            title: Titre du ticket
            description: Description détaillée
            client_name: Nom du client (pour rechercher son ID)
            priority: Priorité (1-5, 3=moyenne)
            urgency: Urgence (1-5, 3=moyenne)
            impact: Impact (1-5, 3=moyen)
            category_id: ID de la catégorie (optionnel)

        Returns:
            Informations du ticket créé
        """
        await self._ensure_session()

        logger.info("glpi_create_ticket", title=title, client_name=client_name)

        # Rechercher le client
        client_info = await self.search_client(name=client_name)
        requester_id = client_info.get("client_id") if client_info.get("found") else None

        # Préparer les données du ticket
        ticket_input: dict[str, Any] = {
            "name": title,
            "content": description,
            "priority": priority,
            "urgency": urgency,
            "impact": impact,
            "type": 1,  # Incident
            "status": 1,  # New
        }

        if requester_id:
            ticket_input["_users_id_requester"] = requester_id

        if category_id:
            ticket_input["itilcategories_id"] = category_id

        # Créer le ticket
        response = await self.client.post(
            f"{self.base_url}/Ticket",
            json={"input": ticket_input},
            headers=self._get_headers(),
        )

        if not response.is_success:
            error_msg = response.text[:200] if response.text else "Unknown error"
            logger.error("glpi_create_ticket_failed", error=error_msg)
            return {"success": False, "error": error_msg}

        data = response.json()
        ticket_id = data.get("id")

        logger.info("glpi_ticket_created", ticket_id=ticket_id)

        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"Ticket #{ticket_id} créé avec succès",
        }

    async def get_ticket_details(self, ticket_id: int) -> dict[str, Any]:
        """
        Récupère les détails complets d'un ticket.

        Args:
            ticket_id: ID du ticket

        Returns:
            Détails du ticket
        """
        await self._ensure_session()

        logger.info("glpi_get_ticket", ticket_id=ticket_id)

        try:
            response = await self.client.get(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers(),
            )

            if response.status_code == 404:
                return {"found": False, "error": f"Ticket #{ticket_id} not found"}

            if not response.is_success:
                return {"found": False, "error": f"Error: {response.status_code}"}

            ticket = response.json()

            # Récupérer aussi les followups
            followups = await self._get_ticket_followups(ticket_id)

            return {
                "found": True,
                "ticket_id": ticket.get("id"),
                "title": ticket.get("name"),
                "description": ticket.get("content"),
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "urgency": ticket.get("urgency"),
                "impact": ticket.get("impact"),
                "date_creation": ticket.get("date"),
                "date_modification": ticket.get("date_mod"),
                "followups": followups,
            }

        except Exception as e:
            logger.exception("glpi_get_ticket_error", error=str(e))
            return {"found": False, "error": str(e)}

    async def _get_ticket_followups(self, ticket_id: int) -> list[dict[str, Any]]:
        """Récupère les followups d'un ticket."""
        try:
            response = await self.client.get(
                f"{self.base_url}/Ticket/{ticket_id}/ITILFollowup",
                headers=self._get_headers(),
            )

            if not response.is_success:
                return []

            followups = response.json()
            return [
                {
                    "id": f.get("id"),
                    "content": f.get("content"),
                    "date": f.get("date"),
                    "is_private": f.get("is_private", 0) == 1,
                }
                for f in followups
            ]
        except Exception:
            return []

    async def add_ticket_followup(
        self,
        ticket_id: int,
        content: str,
        is_private: bool = False,
    ) -> dict[str, Any]:
        """
        Ajoute un suivi à un ticket.

        Args:
            ticket_id: ID du ticket
            content: Contenu du suivi
            is_private: Si True, suivi privé (non visible par le client)

        Returns:
            Résultat de l'ajout
        """
        await self._ensure_session()

        logger.info("glpi_add_followup", ticket_id=ticket_id, is_private=is_private)

        response = await self.client.post(
            f"{self.base_url}/Ticket/{ticket_id}/ITILFollowup",
            json={
                "input": {
                    "content": content,
                    "is_private": 1 if is_private else 0,
                    "itemtype": "Ticket",
                    "items_id": ticket_id,
                }
            },
            headers=self._get_headers(),
        )

        if not response.is_success:
            error_msg = response.text[:200] if response.text else "Unknown error"
            return {"success": False, "error": error_msg}

        data = response.json()
        followup_id = data.get("id")

        logger.info("glpi_followup_added", ticket_id=ticket_id, followup_id=followup_id)

        return {
            "success": True,
            "followup_id": followup_id,
            "message": f"Followup added to ticket #{ticket_id}",
        }

    async def update_ticket_status(
        self,
        ticket_id: int,
        status: int,
    ) -> dict[str, Any]:
        """
        Met à jour le statut d'un ticket.

        Args:
            ticket_id: ID du ticket
            status: Nouveau statut (1=new, 2=assigned, 3=planned, 4=pending, 5=solved, 6=closed)

        Returns:
            Résultat de la mise à jour
        """
        await self._ensure_session()

        status_names = {
            1: "New",
            2: "Assigned",
            3: "Planned",
            4: "Pending",
            5: "Solved",
            6: "Closed",
        }

        logger.info(
            "glpi_update_status",
            ticket_id=ticket_id,
            status=status,
            status_name=status_names.get(status, "Unknown"),
        )

        response = await self.client.put(
            f"{self.base_url}/Ticket/{ticket_id}",
            json={"input": {"status": status}},
            headers=self._get_headers(),
        )

        if not response.is_success:
            error_msg = response.text[:200] if response.text else "Unknown error"
            return {"success": False, "error": error_msg}

        return {
            "success": True,
            "ticket_id": ticket_id,
            "new_status": status,
            "status_name": status_names.get(status, "Unknown"),
        }

    async def close_ticket(
        self,
        ticket_id: int,
        solution: str,
    ) -> dict[str, Any]:
        """
        Clôture un ticket avec une solution.

        Args:
            ticket_id: ID du ticket
            solution: Description de la solution

        Returns:
            Résultat de la clôture
        """
        await self._ensure_session()

        logger.info("glpi_close_ticket", ticket_id=ticket_id)

        # Ajouter la solution
        solution_response = await self.client.post(
            f"{self.base_url}/Ticket/{ticket_id}/ITILSolution",
            json={
                "input": {
                    "content": solution,
                    "itemtype": "Ticket",
                    "items_id": ticket_id,
                    "status": 2,  # Accepted
                }
            },
            headers=self._get_headers(),
        )

        if not solution_response.is_success:
            error_msg = solution_response.text[:200] if solution_response.text else "Unknown error"
            logger.warning("glpi_solution_failed", error=error_msg)

        # Mettre le statut à Closed
        status_result = await self.update_ticket_status(ticket_id, 6)

        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"Ticket #{ticket_id} closed",
            "solution_added": solution_response.is_success,
        }

    async def search_new_tickets(
        self,
        minutes_since: int = 5,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Recherche les tickets créés récemment.

        Args:
            minutes_since: Tickets des X dernières minutes
            limit: Nombre max de tickets

        Returns:
            Liste des tickets récents
        """
        await self._ensure_session()

        logger.info("glpi_search_new_tickets", minutes_since=minutes_since, limit=limit)

        from datetime import datetime, timedelta

        since = (datetime.utcnow() - timedelta(minutes=minutes_since)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            params = {
                "criteria[0][field]": 15,  # date de création
                "criteria[0][searchtype]": "morethan",
                "criteria[0][value]": since,
                "criteria[1][field]": 12,  # status
                "criteria[1][searchtype]": "equals",
                "criteria[1][value]": 1,  # New
                "criteria[1][link]": "AND",
                "range": f"0-{limit - 1}",
            }

            response = await self.client.get(
                f"{self.base_url}/search/Ticket",
                params=params,
                headers=self._get_headers(),
            )

            if not response.is_success:
                return {"success": False, "tickets": [], "error": f"Error: {response.status_code}"}

            data = response.json()
            tickets = data.get("data", [])

            return {
                "success": True,
                "count": len(tickets),
                "tickets": [
                    {
                        "id": t.get("2"),
                        "title": t.get("1"),
                        "status": t.get("12"),
                        "date": t.get("15"),
                    }
                    for t in tickets
                ],
            }

        except Exception as e:
            logger.exception("glpi_search_new_tickets_error", error=str(e))
            return {"success": False, "tickets": [], "error": str(e)}

    async def get_resolved_tickets(
        self,
        hours_since: int = 24,
        limit: int = 50,
        exclude_already_processed: bool = True,
    ) -> dict[str, Any]:
        """
        Récupère les tickets résolus/clôturés récemment pour enrichissement RAG.

        Args:
            hours_since: Tickets résolus dans les X dernières heures
            limit: Nombre max de tickets à retourner
            exclude_already_processed: Exclure les tickets déjà dans la base RAG

        Returns:
            Liste des tickets résolus avec leurs solutions
        """
        await self._ensure_session()

        logger.info("glpi_get_resolved_tickets", hours_since=hours_since, limit=limit)

        from datetime import datetime, timedelta

        since = (datetime.utcnow() - timedelta(hours=hours_since)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Rechercher les tickets résolus (status=5) ou clôturés (status=6)
            params = {
                "criteria[0][field]": 17,  # date de résolution/clôture
                "criteria[0][searchtype]": "morethan",
                "criteria[0][value]": since,
                "criteria[1][field]": 12,  # status
                "criteria[1][searchtype]": "equals",
                "criteria[1][value]": 5,  # Solved
                "criteria[1][link]": "AND",
                "criteria[2][field]": 12,  # status
                "criteria[2][searchtype]": "equals",
                "criteria[2][value]": 6,  # Closed
                "criteria[2][link]": "OR",
                "range": f"0-{limit - 1}",
                "forcedisplay[0]": 2,   # ID
                "forcedisplay[1]": 1,   # Title
                "forcedisplay[2]": 21,  # Content
                "forcedisplay[3]": 12,  # Status
                "forcedisplay[4]": 17,  # Solve date
            }

            response = await self.client.get(
                f"{self.base_url}/search/Ticket",
                params=params,
                headers=self._get_headers(),
            )

            if not response.is_success:
                return {"success": False, "tickets": [], "error": f"Error: {response.status_code}"}

            data = response.json()
            raw_tickets = data.get("data", [])

            # Récupérer les détails complets avec solutions pour chaque ticket
            enriched_tickets = []
            for t in raw_tickets:
                ticket_id = t.get("2")
                if not ticket_id:
                    continue

                # Récupérer la solution du ticket
                solution = await self._get_ticket_solution(int(ticket_id))

                # Récupérer les détails complets
                details = await self.get_ticket_details(int(ticket_id))

                enriched_tickets.append({
                    "id": ticket_id,
                    "title": t.get("1", ""),
                    "description": details.get("description", ""),
                    "status": t.get("12"),
                    "solve_date": t.get("17"),
                    "solution": solution,
                    "followups": details.get("followups", []),
                })

            logger.info("glpi_resolved_tickets_found", count=len(enriched_tickets))

            return {
                "success": True,
                "count": len(enriched_tickets),
                "hours_since": hours_since,
                "tickets": enriched_tickets,
            }

        except Exception as e:
            logger.exception("glpi_get_resolved_tickets_error", error=str(e))
            return {"success": False, "tickets": [], "error": str(e)}

    async def _get_ticket_solution(self, ticket_id: int) -> Optional[str]:
        """Récupère la solution d'un ticket."""
        try:
            response = await self.client.get(
                f"{self.base_url}/Ticket/{ticket_id}/ITILSolution",
                headers=self._get_headers(),
            )

            if not response.is_success:
                return None

            solutions = response.json()
            if solutions and isinstance(solutions, list) and len(solutions) > 0:
                # Prendre la dernière solution (la plus récente)
                return solutions[-1].get("content", "")

            return None

        except Exception:
            return None

    async def get_ticket_categories(self) -> dict[str, Any]:
        """Récupère les catégories de tickets disponibles."""
        await self._ensure_session()

        try:
            response = await self.client.get(
                f"{self.base_url}/ITILCategory",
                params={"range": "0-100"},
                headers=self._get_headers(),
            )

            if not response.is_success:
                return {"success": False, "categories": []}

            categories = response.json()
            return {
                "success": True,
                "categories": [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "completename": c.get("completename"),
                    }
                    for c in categories
                ],
            }

        except Exception as e:
            logger.exception("glpi_get_categories_error", error=str(e))
            return {"success": False, "categories": [], "error": str(e)}


# Instance singleton
glpi_client = GLPIClient()
