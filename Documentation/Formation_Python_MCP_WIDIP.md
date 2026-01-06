# Formation Python & MCP - Projet WIDIP

## Guide complet pour comprendre l'architecture technique

**Version**: 1.0
**Date**: Janvier 2026
**Objectif**: Maîtriser les concepts Python et MCP utilisés dans le projet WIDIP

---

# PARTIE 1 : LES BASES PYTHON ESSENTIELLES

Avant de plonger dans le code MCP, révisons les concepts Python que tu vas rencontrer partout dans le projet.

---

## 1.1 Les Imports et la Structure des Modules

### Comment ça marche ?

```python
# Fichier: src/main.py

import sys                           # Import standard Python
import structlog                      # Import d'une librairie externe
import uvicorn                        # Serveur web ASGI

from .config import settings          # Import depuis le même package (le "." = dossier courant)
from .utils.logging import setup_logging   # Import depuis un sous-package
```

### Le point (.) dans les imports

```
src/
├── main.py          <- On est ici
├── config.py        <- from .config = même dossier
├── utils/
│   └── logging.py   <- from .utils.logging = sous-dossier utils
└── mcp/
    └── server.py    <- from .mcp.server = sous-dossier mcp
```

**Règle simple**:
- `.` = dossier courant
- `..` = dossier parent
- `from X import Y` = importer Y depuis le module X

---

## 1.2 Les Type Hints (Annotations de Types)

Python est "dynamiquement typé", mais on peut ajouter des indications de types pour la lisibilité et les outils de vérification.

### Syntaxe de base

```python
# Sans type hints (ça marche, mais on ne sait pas ce qu'on manipule)
def rechercher_client(nom):
    return {"id": 1, "name": nom}

# Avec type hints (plus clair, plus pro)
def rechercher_client(nom: str) -> dict[str, Any]:
    return {"id": 1, "name": nom}
```

### Les types que tu verras dans WIDIP

```python
from typing import Any, Optional, Callable, Union

# Types simples
nom: str = "WIDIP"
port: int = 3001
actif: bool = True

# Optional = peut être None
email: Optional[str] = None  # Soit une string, soit None

# dict avec types de clés/valeurs
config: dict[str, Any] = {"port": 3001, "debug": True}

# list typée
outils: list[str] = ["glpi_search", "ad_reset"]

# Union = plusieurs types possibles
id_ou_nom: Union[str, int] = 123  # Peut être string OU int
```

### Exemple concret du projet

```python
# Extrait de src/mcp/protocol.py
async def execute(
    self,
    tool_name: str,                           # String obligatoire
    arguments: dict[str, Any],                # Dictionnaire
    context: Optional[ExecutionContext] = None,  # Optionnel, défaut None
) -> MCPResponse:                             # Retourne un MCPResponse
    ...
```

**Pourquoi c'est important** : Quand le dev lira le code, il saura immédiatement :
- Quels paramètres passer
- Ce que la fonction retourne
- Ce qui est optionnel

---

## 1.3 Les Classes en Python

### Structure de base

```python
class Voiture:
    # __init__ = constructeur (appelé quand on crée un objet)
    def __init__(self, marque: str, couleur: str):
        self.marque = marque     # self = l'instance courante
        self.couleur = couleur

    # Méthode normale
    def klaxonner(self) -> str:
        return f"La {self.marque} fait POUET!"

# Utilisation
ma_voiture = Voiture("Renault", "rouge")
print(ma_voiture.klaxonner())  # "La Renault fait POUET!"
```

### Exemple réel du projet : ToolRegistry

```python
# Extrait simplifié de src/mcp/registry.py

class ToolRegistry:
    """Registre centralisé des tools MCP."""

    def __init__(self) -> None:
        # Dictionnaire privé (_tools) pour stocker les outils
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """Enregistre un outil dans le registre."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[MCPTool]:
        """Récupère un outil par son nom."""
        return self._tools.get(name)

    def __len__(self) -> int:
        """Permet d'utiliser len(registry)."""
        return len(self._tools)

# Singleton = une seule instance partagée partout
tool_registry = ToolRegistry()
```

**Point clé** : `tool_registry` est une instance unique (singleton) utilisée dans tout le projet pour enregistrer et récupérer les outils.

---

## 1.4 Les Décorateurs (@)

Les décorateurs sont une syntaxe Python pour "envelopper" une fonction et lui ajouter des comportements.

### Principe de base

```python
# Un décorateur est une fonction qui prend une fonction et retourne une fonction modifiée

def mon_decorateur(func):
    def wrapper(*args, **kwargs):
        print("Avant l'exécution")
        result = func(*args, **kwargs)
        print("Après l'exécution")
        return result
    return wrapper

@mon_decorateur
def dire_bonjour(nom):
    print(f"Bonjour {nom}!")

dire_bonjour("Max")
# Affiche:
# Avant l'exécution
# Bonjour Max!
# Après l'exécution
```

### Décorateurs dans WIDIP

```python
# Extrait de src/tools/glpi_tools.py

@tool_registry.register_function(
    name="glpi_search_client",
    description="Recherche un client dans GLPI par nom, email ou téléphone.",
    parameters={
        "name": string_param("Nom du client", required=False),
        "email": string_param("Email du client", required=False),
    },
)
async def glpi_search_client(
    name: Optional[str] = None,
    email: Optional[str] = None,
) -> dict[str, Any]:
    """Recherche un client dans GLPI."""
    return await glpi_client.search_client(name=name, email=email)
```

**Ce qui se passe** :
1. `@tool_registry.register_function(...)` est un décorateur avec paramètres
2. Il enregistre automatiquement la fonction `glpi_search_client` dans le registre
3. Les métadonnées (name, description, parameters) sont stockées pour MCP
4. La fonction originale reste accessible

---

## 1.5 Async/Await - Programmation Asynchrone

C'est **LE** concept clé du projet. WIDIP fait beaucoup d'appels réseau (GLPI, AD, Observium...) et on ne veut pas bloquer le serveur en attendant les réponses.

### Le problème avec le code synchrone

```python
# Code SYNCHRONE (bloquant) - NE PAS FAIRE
def traiter_3_tickets():
    ticket1 = appeler_glpi(1)     # Attend 500ms
    ticket2 = appeler_glpi(2)     # Attend 500ms
    ticket3 = appeler_glpi(3)     # Attend 500ms
    # Total: 1500ms d'attente (séquentiel)
```

### La solution asynchrone

```python
# Code ASYNCHRONE (non-bloquant) - CE QU'ON FAIT
import asyncio

async def traiter_3_tickets():
    # Lance les 3 appels EN PARALLÈLE
    results = await asyncio.gather(
        appeler_glpi(1),
        appeler_glpi(2),
        appeler_glpi(3),
    )
    # Total: ~500ms (parallèle!)
    return results
```

### Syntaxe async/await

```python
# async def = cette fonction est asynchrone
async def ma_fonction_async():
    # await = "attends le résultat mais laisse les autres tâches s'exécuter"
    result = await une_autre_fonction_async()
    return result
```

### Exemple concret : Appel GLPI

```python
# Extrait de src/tools/glpi_tools.py

async def glpi_get_ticket_details(ticket_id: int) -> dict[str, Any]:
    """Récupère les détails d'un ticket."""
    # await = on attend la réponse HTTP sans bloquer le serveur
    return await glpi_client.get_ticket_details(ticket_id)
```

### Quand utiliser async ?

```
Opérations LENTES (I/O bound) → ASYNC
├── Appels HTTP (GLPI, Observium)
├── Requêtes base de données (PostgreSQL)
├── Lecture/écriture fichiers
└── Connexions LDAP (Active Directory)

Opérations RAPIDES (CPU bound) → PAS BESOIN
├── Calculs mathématiques
├── Manipulation de strings
└── Parsing JSON
```

---

## 1.6 Pydantic - Validation de Données

Pydantic est une librairie qui valide et structure les données automatiquement.

### Pourquoi Pydantic ?

```python
# SANS Pydantic (dangereux)
def creer_utilisateur(data):
    nom = data.get("nom")        # Et si c'est None ?
    age = data.get("age")        # Et si c'est une string ?
    email = data.get("email")    # Et si le format est invalide ?
```

```python
# AVEC Pydantic (sécurisé)
from pydantic import BaseModel, Field

class Utilisateur(BaseModel):
    nom: str = Field(description="Nom complet")
    age: int = Field(ge=0, le=150)  # ge=greater or equal, le=less or equal
    email: str = Field(pattern=r"^[\w.-]+@[\w.-]+\.\w+$")

# Si les données sont invalides → erreur automatique!
user = Utilisateur(nom="Max", age=30, email="max@widip.fr")  # OK
user = Utilisateur(nom="Max", age="trente", email="invalid")  # ERREUR!
```

### Utilisation dans WIDIP : Settings

```python
# Extrait simplifié de src/config.py

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration globale chargée depuis .env"""

    # Chargement automatique depuis le fichier .env
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # Définition des variables avec valeurs par défaut
    mcp_server_host: str = Field(default="0.0.0.0")
    mcp_server_port: int = Field(default=3001)

    # SecretStr = ne s'affiche pas dans les logs (sécurité!)
    mcp_api_key: SecretStr = Field(default="")
    glpi_app_token: SecretStr = Field(default="")

    # Propriété calculée
    @property
    def postgres_dsn(self) -> str:
        """Construit l'URL de connexion PostgreSQL."""
        password = self.postgres_pass.get_secret_value()
        return f"postgresql://{self.postgres_user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
```

**Avantages** :
- Variables d'environnement chargées automatiquement
- Validation des types au démarrage
- Mots de passe masqués avec `SecretStr`
- Erreur claire si une variable obligatoire manque

---

## 1.7 Les Enums (Énumérations)

Les Enums définissent un ensemble fixe de valeurs possibles.

### Exemple : Niveaux de sécurité SAFEGUARD

```python
# Extrait de src/config.py

from enum import Enum

class SecurityLevel(str, Enum):
    """
    Niveaux de sécurité SAFEGUARD pour les tools MCP.

    L0: Lecture seule - toujours autorisé
    L1: Actions mineures - auto si confidence > 80%
    L2: Actions modérées - avec notification
    L3: Actions sensibles - validation humaine OBLIGATOIRE
    L4: Actions interdites - JAMAIS exécutées par l'IA
    """
    L0_READ_ONLY = "L0"
    L1_MINOR = "L1"
    L2_MODERATE = "L2"
    L3_SENSITIVE = "L3"
    L4_FORBIDDEN = "L4"

# Utilisation
niveau = SecurityLevel.L3_SENSITIVE
print(niveau.value)  # "L3"
print(niveau.name)   # "L3_SENSITIVE"

# Comparaison
if niveau == SecurityLevel.L3_SENSITIVE:
    print("Validation humaine requise!")
```

**Pourquoi `(str, Enum)`** : L'héritage de `str` permet de sérialiser directement en JSON (`"L3"` au lieu de `SecurityLevel.L3_SENSITIVE`).

---

## 1.8 Context Managers (with)

Les context managers garantissent le nettoyage des ressources (fichiers, connexions...).

### Syntaxe

```python
# SANS context manager (risque de fuite)
fichier = open("data.txt")
contenu = fichier.read()
fichier.close()  # Et si on oublie ? Et si erreur avant ?

# AVEC context manager (sécurisé)
with open("data.txt") as fichier:
    contenu = fichier.read()
# Le fichier est fermé automatiquement, même si erreur!
```

### Context manager asynchrone dans WIDIP

```python
# Extrait de src/mcp/server.py

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""

    # === STARTUP (au démarrage du serveur) ===
    await memory_client._get_pool()        # Connexion PostgreSQL
    await safeguard_queue.initialize()     # Init queue SAFEGUARD
    logger.info("mcp_server_starting")

    yield  # ← Le serveur tourne ici

    # === SHUTDOWN (à l'arrêt du serveur) ===
    await memory_client.close()
    await safeguard_queue.close()
    logger.info("mcp_server_stopped")
```

---

## 1.9 Gestion des Exceptions

### Try/Except de base

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Division par zéro!")
except Exception as e:
    print(f"Erreur inattendue: {e}")
finally:
    print("Toujours exécuté")
```

### Exceptions personnalisées dans WIDIP

```python
# Extrait de src/clients/base.py

class APIError(Exception):
    """Erreur lors d'un appel API."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

class AuthenticationError(APIError):
    """Erreur d'authentification API."""
    pass

class NotFoundError(APIError):
    """Ressource non trouvée."""
    pass

# Utilisation
def _handle_error(self, response):
    if response.status_code == 401:
        raise AuthenticationError("Token invalide", status_code=401)
    elif response.status_code == 404:
        raise NotFoundError("Ressource introuvable", status_code=404)
```

---

# PARTIE 2 : ARCHITECTURE MCP (Model Context Protocol)

Maintenant que tu maîtrises les bases Python, voyons comment tout s'assemble dans le serveur MCP.

---

## 2.1 Qu'est-ce que MCP ?

### Définition simple

**MCP (Model Context Protocol)** est un protocole standardisé qui permet à une IA (comme Claude, GPT, ou Devstral) d'appeler des fonctions/outils externes de manière structurée.

```
┌─────────────────────────────────────────────────────────────────┐
│                        SANS MCP                                  │
│                                                                  │
│   IA ──────?──────> GLPI     Comment l'IA sait-elle             │
│   IA ──────?──────> AD       quels paramètres passer ?          │
│   IA ──────?──────> Observium Comment parse-t-elle les réponses?│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        AVEC MCP                                  │
│                                                                  │
│   IA ────(JSON-RPC)────> MCP Server ────> GLPI                  │
│                              │                                   │
│   L'IA reçoit:               ├────────────> AD                  │
│   - Liste des outils         │                                   │
│   - Description de chacun    └────────────> Observium           │
│   - Paramètres attendus                                          │
│   - Format des réponses                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Le flux MCP en 4 étapes

```
1. DÉCOUVERTE (GET /mcp/sse)
   L'IA se connecte et reçoit la liste des outils disponibles

2. SÉLECTION
   L'IA choisit l'outil approprié selon la demande utilisateur

3. APPEL (POST /mcp/call)
   L'IA envoie une requête JSON-RPC avec les paramètres

4. RÉPONSE
   Le serveur exécute et retourne le résultat en JSON
```

---

## 2.2 Structure du Serveur MCP WIDIP

### Arborescence des fichiers

```
widip-mcp-server/
├── src/
│   ├── main.py              # Point d'entrée
│   ├── config.py            # Configuration (Settings + SAFEGUARD levels)
│   │
│   ├── mcp/                  # Coeur du protocole MCP
│   │   ├── server.py        # FastAPI app + endpoints
│   │   ├── registry.py      # Registre des outils
│   │   ├── protocol.py      # Structures de données MCP
│   │   └── safeguard_queue.py  # Queue d'approbation L3
│   │
│   ├── tools/                # Définition des outils exposés à l'IA
│   │   ├── glpi_tools.py    # 10 outils GLPI
│   │   ├── ad_tools.py      # 9 outils Active Directory
│   │   ├── observium_tools.py  # 4 outils monitoring
│   │   ├── memory_tools.py  # 5 outils RAG
│   │   └── notification_tools.py  # 3 outils notification
│   │
│   ├── clients/              # Clients API pour les services externes
│   │   ├── base.py          # Client HTTP abstrait
│   │   ├── glpi.py          # Client GLPI
│   │   ├── observium.py     # Client Observium
│   │   ├── activedirectory.py  # Client LDAP/AD
│   │   └── memory.py        # Client PostgreSQL + pgvector
│   │
│   └── utils/
│       ├── logging.py       # Configuration structlog
│       ├── retry.py         # Décorateur de retry
│       └── secrets.py       # Chiffrement Fernet
```

### Schéma des interactions

```
                    ┌─────────────────────────────────────┐
                    │            n8n / Devstral           │
                    │         (Orchestrateur IA)          │
                    └──────────────┬──────────────────────┘
                                   │
                    HTTP + API Key │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     MCP SERVER (FastAPI)                         │
│                         Port 3001                                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    ENDPOINTS                                │ │
│  │                                                             │ │
│  │  GET  /health        → Vérification santé                  │ │
│  │  GET  /mcp/sse       → Découverte outils (SSE)             │ │
│  │  POST /mcp/call      → Exécution outil (JSON-RPC)          │ │
│  │  GET  /mcp/tools     → Liste des outils + niveaux          │ │
│  │  POST /safeguard/*   → Gestion approbations L3             │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  TOOL REGISTRY                              │ │
│  │                                                             │ │
│  │   glpi_search_client    │ L0 │ Recherche client            │ │
│  │   glpi_create_ticket    │ L1 │ Création ticket             │ │
│  │   ad_reset_password     │ L3 │ Reset MDP (validation!)     │ │
│  │   ad_create_user        │ L4 │ INTERDIT à l'IA             │ │
│  │   ...                                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    CLIENTS                                  │ │
│  │                                                             │ │
│  │   GLPIClient        → API GLPI (tickets, users)            │ │
│  │   ObserviumClient   → API Observium (devices)              │ │
│  │   ADClient          → LDAP/Active Directory                │ │
│  │   MemoryClient      → PostgreSQL + pgvector (RAG)          │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                    │              │              │
                    ▼              ▼              ▼
              ┌─────────┐   ┌──────────┐   ┌────────────┐
              │  GLPI   │   │ Observium │   │ Active Dir │
              └─────────┘   └──────────┘   └────────────┘
```

---

## 2.3 Le Point d'Entrée : main.py

```python
# src/main.py - Analyse complète

"""Point d'entrée du serveur MCP WIDIP."""

import sys
import structlog
import uvicorn

from .config import settings
from .utils.logging import setup_logging

# 1. Configuration du logging au format JSON structuré
setup_logging(settings.log_level)
logger = structlog.get_logger(__name__)


def main() -> None:
    """Point d'entrée principal."""

    # 2. Import des tools = DÉCLENCHE L'ENREGISTREMENT AUTOMATIQUE
    #    Chaque fichier tools/*.py contient des @tool_registry.register_function
    #    L'import suffit à exécuter ces décorateurs
    from . import tools  # noqa: F401 (ignorer l'erreur "import non utilisé")

    from .mcp.server import create_mcp_app
    from .mcp.registry import tool_registry

    # 3. Log du démarrage avec infos importantes
    logger.info(
        "starting_mcp_server",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        tools_count=len(tool_registry),  # Nombre d'outils enregistrés
    )

    # 4. Créer l'application FastAPI
    app = create_mcp_app()

    # 5. Démarrer le serveur HTTP avec uvicorn
    uvicorn.run(
        app,
        host=settings.mcp_server_host,  # 0.0.0.0 = écoute sur toutes les interfaces
        port=settings.mcp_server_port,  # 3001
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
```

**Points clés** :
- L'import de `tools` suffit à enregistrer tous les outils (magie des décorateurs)
- `uvicorn` est le serveur ASGI qui fait tourner FastAPI
- `structlog` produit des logs JSON structurés (idéal pour monitoring)

---

## 2.4 La Configuration : config.py

### Les Niveaux SAFEGUARD

```python
# src/config.py

class SecurityLevel(str, Enum):
    """Niveaux de sécurité L0-L4"""
    L0_READ_ONLY = "L0"   # Lecture seule
    L1_MINOR = "L1"       # Actions mineures
    L2_MODERATE = "L2"    # Actions modérées
    L3_SENSITIVE = "L3"   # Validation humaine obligatoire
    L4_FORBIDDEN = "L4"   # INTERDIT à l'IA

# Mapping outil → niveau de sécurité
TOOL_SECURITY_LEVELS: dict[str, SecurityLevel] = {
    # GLPI - Gestion des tickets
    "glpi_search_client": SecurityLevel.L0_READ_ONLY,    # Lecture = safe
    "glpi_create_ticket": SecurityLevel.L1_MINOR,        # Création = mineur
    "glpi_close_ticket": SecurityLevel.L3_SENSITIVE,     # Clôture = sensible!

    # Active Directory - Gestion des comptes
    "ad_check_user": SecurityLevel.L0_READ_ONLY,         # Lecture = safe
    "ad_reset_password": SecurityLevel.L3_SENSITIVE,     # Reset MDP = HUMAIN!
    "ad_create_user": SecurityLevel.L4_FORBIDDEN,        # Création = JAMAIS IA!

    # ... autres outils
}
```

### La classe Settings

```python
class Settings(BaseSettings):
    """Configuration chargée depuis .env"""

    model_config = SettingsConfigDict(
        env_file=".env",           # Fichier source
        case_sensitive=False,       # MCP_API_KEY = mcp_api_key
    )

    # === Serveur ===
    mcp_server_host: str = Field(default="0.0.0.0")
    mcp_server_port: int = Field(default=3001)
    environment: str = Field(default="development")

    # === Sécurité ===
    mcp_api_key: SecretStr = Field(default="")
    mcp_require_auth: bool = Field(default=True)
    safeguard_enabled: bool = Field(default=True)

    # === GLPI ===
    glpi_url: str = Field(default="")
    glpi_app_token: SecretStr = Field(default="")

    # === Active Directory ===
    ldap_server: str = Field(default="")
    ldap_use_ssl: bool = Field(default=True)
    ldap_verify_ssl: bool = Field(default=True)  # OBLIGATOIRE en prod!

    def validate_security(self) -> list[str]:
        """Valide la config de sécurité au démarrage."""
        errors = []

        if self.environment == "production":
            # En production, tout doit être configuré
            if not self.mcp_require_auth:
                errors.append("CRITICAL: Auth required in production")
            if not self.mcp_api_key.get_secret_value():
                errors.append("CRITICAL: API key missing")
            if not self.safeguard_enabled:
                errors.append("CRITICAL: SAFEGUARD must be enabled")

        return errors

# Singleton pour accès global
settings = Settings()
```

---

## 2.5 Le Registre des Outils : registry.py

Le registre est le coeur du système - il stocke tous les outils et les expose à l'IA.

### Structure du registre

```python
# src/mcp/registry.py

class ToolRegistry:
    """Registre centralisé des tools MCP."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """Ajoute un outil au registre."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name)

    def register_function(
        self,
        name: str,
        description: str,
        parameters: Optional[dict[str, ToolParameter]] = None,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """
        DÉCORATEUR pour enregistrer une fonction comme outil MCP.

        C'est LA méthode principale utilisée dans les fichiers tools/*.py
        """
        def decorator(func: ToolHandler) -> ToolHandler:
            tool = MCPTool(
                name=name,
                description=description,
                parameters=parameters or {},
                handler=func,
            )
            self.register(tool)
            return func
        return decorator

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> MCPResponse:
        """Exécute un outil avec les arguments fournis."""

        tool = self.get(tool_name)
        if not tool:
            return MCPResponse.failure(
                request_id=context.request_id,
                code=MCPErrorCode.TOOL_NOT_FOUND,
                message=f"Tool '{tool_name}' not found",
            )

        try:
            # Support sync ET async
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            return MCPResponse.success(
                request_id=context.request_id,
                result=result,
            )

        except Exception as e:
            return MCPResponse.failure(
                request_id=context.request_id,
                code=MCPErrorCode.TOOL_EXECUTION_ERROR,
                message=f"Execution failed: {e}",
            )

# Instance singleton utilisée partout
tool_registry = ToolRegistry()
```

### Helpers pour les paramètres

```python
# Fonctions utilitaires pour créer des paramètres rapidement

def string_param(
    description: str,
    required: bool = False,
    default: Optional[str] = None,
    enum: Optional[list[str]] = None,
) -> ToolParameter:
    """Crée un paramètre de type string."""
    return ToolParameter(
        type=ToolParameterType.STRING,
        description=description,
        required=required,
        default=default,
        enum=enum,  # Liste de valeurs autorisées
    )

def int_param(
    description: str,
    required: bool = False,
    default: Optional[int] = None,
) -> ToolParameter:
    """Crée un paramètre de type integer."""
    return ToolParameter(
        type=ToolParameterType.INTEGER,
        description=description,
        required=required,
        default=default,
    )

def bool_param(
    description: str,
    required: bool = False,
    default: Optional[bool] = None,
) -> ToolParameter:
    """Crée un paramètre de type boolean."""
    return ToolParameter(
        type=ToolParameterType.BOOLEAN,
        description=description,
        required=required,
        default=default,
    )
```

---

## 2.6 Le Protocole MCP : protocol.py

Définit les structures de données conformes au standard MCP.

### Structure d'un outil (MCPTool)

```python
class MCPTool(BaseModel):
    """Définition d'un outil MCP."""

    name: str = Field(description="Nom unique (snake_case)")
    description: str = Field(description="Description pour l'IA")
    parameters: dict[str, ToolParameter] = Field(default_factory=dict)
    handler: Optional[ToolHandler] = Field(default=None, exclude=True)

    def to_mcp_schema(self) -> dict[str, Any]:
        """
        Convertit en schéma JSON pour l'IA.

        Retourne le format standard MCP que l'IA comprend.
        """
        properties = {}
        required = []

        for param_name, param in self.parameters.items():
            properties[param_name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.required:
                required.append(param_name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
```

### Requête MCP (JSON-RPC 2.0)

```python
class MCPRequest(BaseModel):
    """Requête reçue de l'IA."""

    jsonrpc: str = Field(default="2.0")
    id: Union[str, int] = Field(description="ID de la requête")
    method: str = Field(description="Méthode appelée")
    params: Optional[dict[str, Any]] = Field(default=None)

# Exemple de requête JSON reçue:
# {
#     "jsonrpc": "2.0",
#     "id": 1,
#     "method": "call",
#     "params": {
#         "name": "glpi_search_client",
#         "arguments": {"name": "EHPAD du Soleil"}
#     }
# }
```

### Réponse MCP

```python
class MCPResponse(BaseModel):
    """Réponse envoyée à l'IA."""

    jsonrpc: str = Field(default="2.0")
    id: Union[str, int] = Field(description="ID de la requête originale")
    result: Optional[Any] = Field(default=None)
    error: Optional[MCPError] = Field(default=None)

    @classmethod
    def success(cls, request_id, result):
        return cls(id=request_id, result=result)

    @classmethod
    def failure(cls, request_id, code, message, data=None):
        return cls(id=request_id, error=MCPError(code=code, message=message, data=data))

# Exemple de réponse JSON envoyée:
# {
#     "jsonrpc": "2.0",
#     "id": 1,
#     "result": {
#         "found": true,
#         "client_id": 42,
#         "name": "EHPAD du Soleil",
#         "email": "contact@ehpad-soleil.fr"
#     }
# }
```

---

## 2.7 Le Serveur FastAPI : server.py

C'est ici que tout se connecte - FastAPI expose les endpoints HTTP.

### Création de l'application

```python
# src/mcp/server.py

def create_mcp_app() -> FastAPI:
    """Crée et configure l'application FastAPI."""

    settings = get_settings()

    app = FastAPI(
        title="WIDIP MCP Server",
        description="Serveur MCP centralisé pour WIDIP",
        version="2.0.0",
        lifespan=lifespan,  # Gestion startup/shutdown
    )

    # Configuration CORS (qui peut appeler le serveur)
    allowed_origins = settings.cors_allowed_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Enregistrer les routes
    _register_routes(app)

    return app
```

### Authentification par API Key

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """Vérifie la clé API pour les requêtes."""

    settings = get_settings()

    # Mode dev sans auth
    if not settings.mcp_require_auth:
        return None

    # Vérification de la clé
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    if api_key != settings.mcp_api_key.get_secret_value():
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return api_key
```

### Endpoint de découverte (SSE)

```python
@app.get("/mcp/sse")
async def mcp_sse_endpoint(
    request: Request,
    _api_key: Optional[str] = Depends(verify_api_key),
) -> EventSourceResponse:
    """
    Endpoint SSE pour la découverte des outils.

    L'IA se connecte ici pour recevoir la liste des outils disponibles.
    SSE = Server-Sent Events (connexion longue avec push serveur)
    """

    async def event_generator():
        # Envoyer la liste des outils
        tools_schemas = tool_registry.get_schemas()

        # Enrichir avec les niveaux SAFEGUARD
        for tool in tools_schemas:
            tool_name = tool.get("name", "")
            level = TOOL_SECURITY_LEVELS.get(tool_name, SecurityLevel.L0_READ_ONLY)
            tool["security_level"] = level.value

        yield {
            "event": "tools",
            "data": json.dumps(tools_schemas),
        }

        # Maintenir la connexion avec des heartbeats
        while True:
            await asyncio.sleep(30)
            yield {
                "event": "heartbeat",
                "data": json.dumps({"timestamp": datetime.utcnow().isoformat()}),
            }

    return EventSourceResponse(event_generator())
```

### Endpoint d'exécution (JSON-RPC)

```python
@app.post("/mcp/call")
async def mcp_call_endpoint(
    request: Request,
    _api_key: Optional[str] = Depends(verify_api_key),
) -> JSONResponse:
    """
    Endpoint pour l'exécution des outils MCP.

    Reçoit une requête JSON-RPC et exécute l'outil demandé.
    """

    # 1. Parser le body JSON
    body = await request.json()
    mcp_request = MCPRequest(**body)

    # 2. Extraire le nom de l'outil et les arguments
    tool_name = mcp_request.params.get("name")
    tool_arguments = mcp_request.params.get("arguments", {})
    confidence = mcp_request.params.get("confidence", 100.0)

    # 3. SAFEGUARD: Vérifier le niveau de sécurité AVANT exécution
    safeguard_result = check_safeguard(tool_name, confidence)

    if not safeguard_result.allowed:
        # Action bloquée par SAFEGUARD
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": mcp_request.id,
                "error": {
                    "code": -32001,
                    "message": safeguard_result.message,
                    "data": safeguard_result.to_dict(),
                },
            },
            status_code=403,
        )

    # 4. Exécuter l'outil
    response = await tool_registry.execute(
        tool_name=tool_name,
        arguments=tool_arguments,
        context=context,
    )

    return JSONResponse(content=response.model_dump())
```

### Vérification SAFEGUARD

```python
def check_safeguard(tool_name: str, confidence: float = 100.0) -> SafeguardResponse:
    """
    Vérifie si un outil peut être exécuté selon les règles SAFEGUARD.

    C'est le GARDIEN qui protège contre les actions dangereuses.
    """
    settings = get_settings()

    if not settings.safeguard_enabled:
        return SafeguardResponse(allowed=True, level=SecurityLevel.L0_READ_ONLY, message="SAFEGUARD disabled")

    level = TOOL_SECURITY_LEVELS.get(tool_name, SecurityLevel.L0_READ_ONLY)

    # L0: Lecture seule - toujours OK
    if level == SecurityLevel.L0_READ_ONLY:
        return SafeguardResponse(allowed=True, level=level, message="Lecture autorisée")

    # L1: Mineur - OK si confidence >= 80%
    if level == SecurityLevel.L1_MINOR:
        if confidence >= 80.0:
            return SafeguardResponse(allowed=True, level=level, message="Action mineure autorisée")
        return SafeguardResponse(allowed=False, level=level, message="Confidence insuffisante", requires_human=True)

    # L2: Modéré - OK avec notification
    if level == SecurityLevel.L2_MODERATE:
        logger.warning("safeguard_l2_action", tool=tool_name)
        return SafeguardResponse(allowed=True, level=level, message="Action modérée avec notification")

    # L3: Sensible - BLOQUÉ, validation humaine requise
    if level == SecurityLevel.L3_SENSITIVE:
        return SafeguardResponse(
            allowed=False,
            level=level,
            message="ACTION BLOQUÉE. Validation humaine requise.",
            requires_human=True,
        )

    # L4: Interdit - JAMAIS exécuté par l'IA
    if level == SecurityLevel.L4_FORBIDDEN:
        return SafeguardResponse(
            allowed=False,
            level=level,
            message="ACTION INTERDITE. Humain uniquement.",
            requires_human=True,
        )

    # Fallback: refuser par sécurité
    return SafeguardResponse(allowed=False, level=level, message="Niveau inconnu - refusé")
```

---

## 2.8 Exemple Complet : Définition d'un Outil

Voyons comment créer un outil de A à Z.

### Le fichier tools/glpi_tools.py

```python
# src/tools/glpi_tools.py

from typing import Any, Optional

from ..clients.glpi import glpi_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
    bool_param,
)


@tool_registry.register_function(
    name="glpi_search_client",                          # Nom unique
    description="""Recherche un client/utilisateur dans GLPI par nom, email ou téléphone.
Utilise cet outil pour trouver les informations d'un client avant de créer un ticket.
Retourne l'ID client, nom, email et téléphone si trouvé.""",  # Description DÉTAILLÉE pour l'IA
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
```

### Ce qui se passe à l'exécution

```
1. AU DÉMARRAGE DU SERVEUR
   └── main.py importe tools/__init__.py
       └── tools/__init__.py importe glpi_tools.py
           └── Le décorateur @tool_registry.register_function s'exécute
               └── L'outil "glpi_search_client" est enregistré dans tool_registry

2. QUAND L'IA SE CONNECTE (GET /mcp/sse)
   └── Le serveur renvoie la liste des outils avec leurs descriptions
   └── L'IA reçoit:
       {
           "name": "glpi_search_client",
           "description": "Recherche un client/utilisateur dans GLPI...",
           "inputSchema": {
               "type": "object",
               "properties": {
                   "name": {"type": "string", "description": "Nom du client..."},
                   "email": {"type": "string", "description": "Email du client..."},
                   "phone": {"type": "string", "description": "Numéro de téléphone..."}
               },
               "required": []
           },
           "security_level": "L0"
       }

3. QUAND L'IA APPELLE L'OUTIL (POST /mcp/call)
   └── Requête: {"params": {"name": "glpi_search_client", "arguments": {"name": "EHPAD"}}}
   └── SAFEGUARD vérifie: L0 = autorisé
   └── tool_registry.execute() appelle glpi_search_client(name="EHPAD")
   └── glpi_client.search_client() fait l'appel HTTP à GLPI
   └── Réponse renvoyée à l'IA
```

---

## 2.9 Le Client HTTP de Base : base.py

Tous les clients API héritent de cette classe abstraite.

```python
# src/clients/base.py

from abc import ABC, abstractmethod
import httpx

class BaseClient(ABC):
    """Client HTTP de base abstrait."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Client HTTP avec lazy initialization."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Retourne les headers d'authentification - À IMPLÉMENTER."""
        pass

    def _handle_error(self, response: httpx.Response) -> None:
        """Gère les erreurs HTTP."""
        if response.is_success:
            return

        status = response.status_code
        if status == 401 or status == 403:
            raise AuthenticationError(f"Auth failed: {status}")
        elif status == 404:
            raise NotFoundError(f"Not found: {response.url}")
        elif status == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            raise APIError(f"API error {status}")

    @with_retry(max_attempts=3)  # Décorateur de retry automatique
    async def _get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """Effectue une requête GET avec retry."""
        response = await self.client.get(
            f"{self.base_url}/{endpoint}",
            params=params,
            headers=self._get_headers(),
        )
        self._handle_error(response)
        return response.json()

    @with_retry(max_attempts=3)
    async def _post(self, endpoint: str, json_data: Optional[dict] = None) -> Any:
        """Effectue une requête POST avec retry."""
        response = await self.client.post(
            f"{self.base_url}/{endpoint}",
            json=json_data,
            headers=self._get_headers(),
        )
        self._handle_error(response)
        return response.json()
```

---

# PARTIE 3 : SCHÉMAS RÉCAPITULATIFS

## 3.1 Flux complet d'un appel MCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUX D'EXÉCUTION MCP                              │
└─────────────────────────────────────────────────────────────────────────────┘

     UTILISATEUR                    n8n + DEVSTRAL                   MCP SERVER
          │                              │                               │
          │  "Reset le mot de passe      │                               │
          │   de Jean Dupont"            │                               │
          │                              │                               │
          └──────────────────────────────>                               │
                                         │                               │
                                         │  1. L'IA analyse la demande   │
                                         │     et choisit l'outil        │
                                         │     ad_reset_password         │
                                         │                               │
                                         │  POST /mcp/call               │
                                         │  {                            │
                                         │    "name": "ad_reset_password"│
                                         │    "arguments": {             │
                                         │      "username": "jdupont"    │
                                         │    }                          │
                                         │  }                            │
                                         │                               │
                                         └───────────────────────────────>
                                                                         │
                                                        2. SAFEGUARD CHECK
                                                        │
                                                        │ ad_reset_password = L3
                                                        │ L3 = BLOQUÉ!
                                                        │
                                         <───────────────────────────────┘
                                         │
                                         │  Réponse: 403 BLOCKED
                                         │  "Validation humaine requise"
                                         │
          <──────────────────────────────┘
          │
          │  "Cette action nécessite
          │   une validation humaine.
          │   Demande envoyée au
          │   technicien."
          │

     ─ ─ ─ ─ ─ ─ ─ ─ ─ PENDANT CE TEMPS ─ ─ ─ ─ ─ ─ ─ ─ ─

     TECHNICIEN                                           DASHBOARD
          │                                                   │
          │  Notification Teams:                              │
          │  "Demande d'approbation L3"                       │
          │                                                   │
          └──────────────────────────────────────────────────>│
                                                              │
                                                    3. Le tech valide
                                                    POST /safeguard/approve/xxx
                                                              │
                                                    4. POST /safeguard/execute/xxx
                                                              │
                                                    5. AD: Reset du mot de passe
                                                              │
          <───────────────────────────────────────────────────┘
          │
          │  "Mot de passe réinitialisé"
```

## 3.2 Architecture des fichiers Python

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE PYTHON MCP                               │
└─────────────────────────────────────────────────────────────────────────────┘

    COUCHE PRÉSENTATION (HTTP)
    ┌────────────────────────────────────────────────────────────────────────┐
    │  src/mcp/server.py                                                      │
    │  ├── FastAPI application                                                │
    │  ├── Endpoints: /health, /mcp/sse, /mcp/call, /safeguard/*             │
    │  ├── Authentification API Key                                           │
    │  └── Vérification SAFEGUARD                                             │
    └────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    COUCHE MÉTIER (OUTILS)
    ┌────────────────────────────────────────────────────────────────────────┐
    │  src/mcp/registry.py          │  src/tools/*.py                         │
    │  ├── ToolRegistry (singleton) │  ├── glpi_tools.py (10 outils)         │
    │  ├── register_function()      │  ├── ad_tools.py (9 outils)            │
    │  ├── execute()                │  ├── observium_tools.py (4 outils)     │
    │  └── get_schemas()            │  └── memory_tools.py (5 outils)        │
    └────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    COUCHE DONNÉES (CLIENTS API)
    ┌────────────────────────────────────────────────────────────────────────┐
    │  src/clients/base.py          │  src/clients/*.py                       │
    │  ├── BaseClient (abstract)    │  ├── glpi.py → API GLPI                │
    │  ├── _get(), _post(), _put()  │  ├── observium.py → API Observium      │
    │  ├── _handle_error()          │  ├── activedirectory.py → LDAP         │
    │  └── Retry automatique        │  └── memory.py → PostgreSQL + pgvector │
    └────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    COUCHE CONFIGURATION
    ┌────────────────────────────────────────────────────────────────────────┐
    │  src/config.py                                                          │
    │  ├── Settings (Pydantic)       ← Charge .env                            │
    │  ├── SecurityLevel (Enum)      ← L0, L1, L2, L3, L4                     │
    │  ├── TOOL_SECURITY_LEVELS      ← Mapping outil → niveau                 │
    │  └── validate_security()       ← Vérification au démarrage              │
    └────────────────────────────────────────────────────────────────────────┘
```

## 3.3 Niveaux SAFEGUARD - Résumé visuel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAUX SAFEGUARD                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    L0 - READ_ONLY                  L1 - MINOR
    ┌──────────────────┐            ┌──────────────────┐
    │  ✅ AUTO-EXÉCUTÉ  │            │  ✅ AUTO si ≥80%  │
    │                  │            │                  │
    │  Lecture seule   │            │  Actions mineures│
    │  Aucun risque    │            │  Réversibles     │
    │                  │            │                  │
    │  Exemples:       │            │  Exemples:       │
    │  • search_client │            │  • create_ticket │
    │  • get_device    │            │  • add_followup  │
    │  • check_user    │            │  • send_email    │
    └──────────────────┘            └──────────────────┘

    L2 - MODERATE                   L3 - SENSITIVE
    ┌──────────────────┐            ┌──────────────────┐
    │  ⚠️ AUTO + NOTIF  │            │  🔒 BLOQUÉ       │
    │                  │            │                  │
    │  Actions modérées│            │  Validation      │
    │  Notification    │            │  HUMAINE requise │
    │  technicien      │            │                  │
    │                  │            │  TTL: 60 min     │
    │  Exemples:       │            │                  │
    │  • assign_ticket │            │  Exemples:       │
    │  • unlock_account│            │  • reset_password│
    │  • move_to_ou    │            │  • close_ticket  │
    └──────────────────┘            │  • disable_user  │
                                    └──────────────────┘

    L4 - FORBIDDEN
    ┌──────────────────┐
    │  🚫 INTERDIT      │
    │                  │
    │  JAMAIS par IA   │
    │  Humain SEUL     │
    │                  │
    │  Exemples:       │
    │  • create_user   │
    │  • delete_user   │
    │  • purge_data    │
    └──────────────────┘
```

---

# PARTIE 4 : POINTS CLÉS POUR LA RÉUNION

## 4.1 Ce que tu dois retenir

### Sur Python

1. **async/await** : Toutes les fonctions qui font du réseau sont `async` pour ne pas bloquer
2. **Décorateurs** : `@tool_registry.register_function()` enregistre automatiquement les outils
3. **Pydantic** : Valide les données et charge la config depuis `.env`
4. **Type hints** : Documentent le code et aident à la compréhension

### Sur MCP

1. **Protocole standardisé** : JSON-RPC 2.0 sur HTTP
2. **Découverte** : L'IA reçoit la liste des outils via SSE (`/mcp/sse`)
3. **Exécution** : L'IA appelle les outils via POST (`/mcp/call`)
4. **SAFEGUARD** : 5 niveaux de sécurité protègent les actions sensibles

### Sur l'architecture

1. **Centralisé** : Un seul serveur MCP expose tous les outils
2. **Modulaire** : Chaque service (GLPI, AD, Observium) a son client dédié
3. **Sécurisé** : API Key + SAFEGUARD + audit trail
4. **Scalable** : Docker + async = gère beaucoup de requêtes

## 4.2 Questions que le dev pourrait poser

| Question | Réponse courte |
|----------|----------------|
| "Pourquoi FastAPI et pas Flask ?" | FastAPI est async-native, a une validation automatique avec Pydantic, et génère la doc OpenAPI |
| "Comment on ajoute un nouvel outil ?" | On crée une fonction avec `@tool_registry.register_function()` dans `tools/` |
| "Comment on teste ?" | `pytest` avec fixtures async, mocks des clients API |
| "C'est quoi MCP exactement ?" | Un protocole standard pour que les IA appellent des fonctions externes |
| "Pourquoi 5 niveaux SAFEGUARD ?" | Pour graduer les risques : lecture, actions mineures, modérées, sensibles, interdites |
| "Comment on déploie ?" | Docker Compose avec les services PostgreSQL, Redis, Ollama, n8n |

## 4.3 Vocabulaire technique à maîtriser

| Terme | Définition simple |
|-------|-------------------|
| **MCP** | Model Context Protocol - protocole pour que l'IA appelle des fonctions |
| **FastAPI** | Framework Python pour créer des API HTTP rapides |
| **Pydantic** | Librairie de validation de données |
| **async/await** | Programmation asynchrone (non-bloquante) |
| **Décorateur** | Fonction qui modifie une autre fonction (`@quelquechose`) |
| **JSON-RPC** | Format de requête/réponse standardisé |
| **SSE** | Server-Sent Events - push de données du serveur vers le client |
| **SAFEGUARD** | Notre système de niveaux de sécurité L0-L4 |
| **Tool/Outil** | Fonction exposée à l'IA via MCP |
| **Registry** | Registre central qui stocke tous les outils |
| **Client** | Classe Python qui appelle une API externe |

---

# ANNEXE : Devstral 2 - Le LLM qui remplacera Claude

## Caractéristiques techniques

| Caractéristique | Valeur |
|-----------------|--------|
| **Nom** | Devstral 2 |
| **Paramètres** | 123 milliards (dense transformer) |
| **Fenêtre de contexte** | 256K tokens |
| **Score SWE-bench** | 72.2% (state-of-the-art open-weight) |
| **Licence** | MIT modifiée (open-source) |
| **API** | Via API certifiée HDS + ISO 27001 |

## Devstral Small 2

| Caractéristique | Valeur |
|-----------------|--------|
| **Score SWE-bench** | 68.0% |
| **Taille** | ~5x plus petit que Devstral 2 |
| **Déploiement** | Peut tourner sur hardware consommateur |

## Intégration dans WIDIP

Devstral remplacera Claude dans les workflows n8n. L'architecture reste identique :

```
n8n Workflow
    │
    ├── Appel Devstral 2 (via API HDS)
    │   └── Le modèle raisonne et choisit les outils
    │
    └── Appel MCP Server
        └── Exécution des outils choisis par Devstral
```

**Avantages de Devstral** :
- Open-weight (code source disponible)
- Performance proche des meilleurs modèles propriétaires
- API certifiée HDS/ISO 27001 (conformité santé française)
- Coût potentiellement plus faible que Claude

---

**Document généré pour la formation WIDIP - Janvier 2026**
