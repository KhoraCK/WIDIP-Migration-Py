"""
Clients API pour les systèmes externes.

Ce module fournit des clients HTTP pour interagir avec:
- GLPI (Gestion de tickets)
- Observium (Monitoring réseau)
- Active Directory (Gestion de comptes)
- SMTP (Envoi d'emails)
- MySecret (Liens sécurisés)
- Memory/RAG (Base vectorielle PostgreSQL)
- Notification (Email + Teams/Slack)
"""

from .base import BaseClient
from .glpi import GLPIClient
from .observium import ObserviumClient
from .activedirectory import ActiveDirectoryClient
from .smtp import SMTPClient
from .mysecret import MySecretClient
from .memory import MemoryClient
from .notification import NotificationClient, notification_client

__all__ = [
    "BaseClient",
    "GLPIClient",
    "ObserviumClient",
    "ActiveDirectoryClient",
    "SMTPClient",
    "MySecretClient",
    "MemoryClient",
    "NotificationClient",
    "notification_client",
]
