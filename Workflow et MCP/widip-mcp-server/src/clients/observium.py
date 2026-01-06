"""
Client pour l'API Observium.

Observium est utilisé pour le monitoring réseau:
- État des devices (switches, routeurs, serveurs)
- Métriques (CPU, RAM, bande passante)
- Alertes et historique
"""

from typing import Any, Optional

import structlog

from ..config import settings
from .base import BaseClient

logger = structlog.get_logger(__name__)


class ObserviumClient(BaseClient):
    """
    Client pour l'API REST Observium.

    Documentation API: https://docs.observium.org/api/
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.observium_url,
            timeout=30.0,
        )
        self._user = settings.observium_user
        self._password = settings.observium_pass.get_secret_value()

    def _get_headers(self) -> dict[str, str]:
        """Retourne les headers Observium (Basic Auth)."""
        import base64

        credentials = base64.b64encode(f"{self._user}:{self._password}".encode()).decode()
        return {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
        }

    # =========================================================================
    # Opérations sur les devices
    # =========================================================================

    async def get_device_status(self, device_name: str) -> dict[str, Any]:
        """
        Récupère l'état complet d'un device.

        Args:
            device_name: Nom ou hostname du device

        Returns:
            État du device (up/down, uptime, infos)
        """
        logger.info("observium_get_device_status", device_name=device_name)

        try:
            # Rechercher le device par nom
            device = await self._find_device(device_name)

            if not device:
                return {
                    "found": False,
                    "device_name": device_name,
                    "error": f"Device '{device_name}' not found",
                }

            # Déterminer le statut
            status = device.get("status", 0)
            status_text = "up" if status == 1 else "down"

            # Calculer l'uptime
            uptime_seconds = device.get("uptime", 0)
            uptime_days = uptime_seconds // 86400 if uptime_seconds else 0

            return {
                "found": True,
                "device_id": device.get("device_id"),
                "device_name": device.get("hostname"),
                "status": status_text,
                "status_code": status,
                "uptime_seconds": uptime_seconds,
                "uptime_days": uptime_days,
                "location": device.get("location", ""),
                "hardware": device.get("hardware", ""),
                "os": device.get("os", ""),
                "version": device.get("version", ""),
                "type": device.get("type", ""),
                "ip": device.get("ip", ""),
                "last_polled": device.get("last_polled", ""),
            }

        except Exception as e:
            logger.exception("observium_get_device_status_error", error=str(e))
            return {
                "found": False,
                "device_name": device_name,
                "error": str(e),
            }

    async def get_device_metrics(self, device_name: str) -> dict[str, Any]:
        """
        Récupère les métriques d'un device (ports, CPU, RAM).

        Args:
            device_name: Nom du device

        Returns:
            Métriques détaillées
        """
        logger.info("observium_get_device_metrics", device_name=device_name)

        try:
            device = await self._find_device(device_name)

            if not device:
                return {"found": False, "error": f"Device '{device_name}' not found"}

            device_id = device.get("device_id")

            # Récupérer les ports
            ports = await self._get_device_ports(device_id)

            # Compter les ports up/down
            ports_up = sum(1 for p in ports if p.get("ifOperStatus") == "up")
            ports_down = sum(1 for p in ports if p.get("ifOperStatus") == "down")
            total_ports = len(ports)

            # Lister les ports down
            down_ports = [
                {
                    "port_id": p.get("port_id"),
                    "name": p.get("ifName") or p.get("ifDescr"),
                    "status": p.get("ifOperStatus"),
                }
                for p in ports
                if p.get("ifOperStatus") == "down"
            ]

            return {
                "found": True,
                "device_id": device_id,
                "device_name": device.get("hostname"),
                "ports_total": total_ports,
                "ports_up": ports_up,
                "ports_down": ports_down,
                "down_ports": down_ports[:10],  # Limiter à 10
                "cpu_usage": device.get("processor_usage", 0),
                "memory_usage": device.get("memory_usage", 0),
            }

        except Exception as e:
            logger.exception("observium_get_device_metrics_error", error=str(e))
            return {"found": False, "error": str(e)}

    async def get_device_alerts(self, device_name: str) -> dict[str, Any]:
        """
        Récupère les alertes actives d'un device.

        Args:
            device_name: Nom du device

        Returns:
            Liste des alertes actives
        """
        logger.info("observium_get_device_alerts", device_name=device_name)

        try:
            device = await self._find_device(device_name)

            if not device:
                return {"found": False, "error": f"Device '{device_name}' not found"}

            device_id = device.get("device_id")

            # Récupérer les alertes
            response = await self._get(f"alerts?device_id={device_id}&status=failed")
            alerts = response if isinstance(response, list) else response.get("alerts", [])

            return {
                "found": True,
                "device_id": device_id,
                "device_name": device.get("hostname"),
                "alert_count": len(alerts),
                "alerts": [
                    {
                        "alert_id": a.get("alert_id"),
                        "message": a.get("alert_message"),
                        "severity": a.get("severity"),
                        "timestamp": a.get("timestamp"),
                    }
                    for a in alerts[:20]  # Limiter à 20
                ],
            }

        except Exception as e:
            logger.exception("observium_get_device_alerts_error", error=str(e))
            return {"found": False, "error": str(e)}

    async def get_device_history(
        self,
        device_name: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        """
        Récupère l'historique des incidents d'un device.

        Args:
            device_name: Nom du device
            hours: Nombre d'heures à regarder en arrière

        Returns:
            Historique des incidents
        """
        logger.info("observium_get_device_history", device_name=device_name, hours=hours)

        try:
            device = await self._find_device(device_name)

            if not device:
                return {"found": False, "error": f"Device '{device_name}' not found"}

            device_id = device.get("device_id")

            # Récupérer l'historique des événements
            from datetime import datetime, timedelta

            since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

            response = await self._get(f"eventlog?device_id={device_id}&from={since}")
            events = response if isinstance(response, list) else response.get("events", [])

            # Filtrer les événements pertinents (down, up, etc.)
            relevant_events = [
                e for e in events
                if any(
                    keyword in str(e.get("message", "")).lower()
                    for keyword in ["down", "up", "failed", "recovered", "alert"]
                )
            ]

            return {
                "found": True,
                "device_id": device_id,
                "device_name": device.get("hostname"),
                "hours_analyzed": hours,
                "incident_count": len(relevant_events),
                "incidents": [
                    {
                        "event_id": e.get("event_id"),
                        "message": e.get("message"),
                        "type": e.get("type"),
                        "timestamp": e.get("datetime"),
                    }
                    for e in relevant_events[:50]  # Limiter à 50
                ],
            }

        except Exception as e:
            logger.exception("observium_get_device_history_error", error=str(e))
            return {"found": False, "error": str(e)}

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _find_device(self, device_name: str) -> Optional[dict[str, Any]]:
        """
        Recherche un device par nom.

        Args:
            device_name: Nom, hostname ou partie du nom

        Returns:
            Device trouvé ou None
        """
        try:
            response = await self._get(f"devices?hostname={device_name}")
            devices = response if isinstance(response, list) else response.get("devices", [])

            if devices:
                # Retourner le premier match
                return devices[0] if isinstance(devices, list) else list(devices.values())[0]

            # Essayer une recherche plus large
            response = await self._get("devices")
            all_devices = response if isinstance(response, list) else response.get("devices", {})

            if isinstance(all_devices, dict):
                all_devices = list(all_devices.values())

            # Chercher par correspondance partielle
            device_name_lower = device_name.lower()
            for device in all_devices:
                hostname = device.get("hostname", "").lower()
                if device_name_lower in hostname or hostname in device_name_lower:
                    return device

            return None

        except Exception as e:
            logger.warning("observium_find_device_error", device_name=device_name, error=str(e))
            return None

    async def _get_device_ports(self, device_id: int) -> list[dict[str, Any]]:
        """Récupère les ports d'un device."""
        try:
            response = await self._get(f"ports?device_id={device_id}")
            ports = response if isinstance(response, list) else response.get("ports", [])

            if isinstance(ports, dict):
                ports = list(ports.values())

            return ports

        except Exception as e:
            logger.warning("observium_get_ports_error", device_id=device_id, error=str(e))
            return []


# Instance singleton
observium_client = ObserviumClient()
