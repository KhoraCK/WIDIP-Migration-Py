# WIDIP MCP Server

Serveur MCP (Model Context Protocol) centralisé pour WIDIP. Remplace les sub-workflows N8N par un serveur Python unifié.

## Tools Disponibles

### GLPI (13 tools)
- `glpi_search_client` - Rechercher un client
- `glpi_create_ticket` - Créer un ticket
- `glpi_get_ticket_details` - Détails d'un ticket
- `glpi_get_ticket_status` - Statut d'un ticket
- `glpi_add_ticket_followup` - Ajouter un suivi
- `glpi_update_ticket_status` - Mettre à jour le statut
- `glpi_close_ticket` - Clôturer un ticket
- `glpi_search_new_tickets` - Rechercher les nouveaux tickets
- `glpi_get_ticket_history` - Historique des modifications
- `glpi_create_user` - Créer un utilisateur GLPI
- `glpi_get_user` - Récupérer un utilisateur
- `glpi_update_user` - Mettre à jour un utilisateur
- `glpi_disable_user` - Désactiver un utilisateur

### Observium (4 tools)
- `observium_get_device_status` - État d'un équipement
- `observium_get_device_metrics` - Métriques (ports, bande passante)
- `observium_get_device_alerts` - Alertes actives
- `observium_get_device_history` - Historique des incidents

### Active Directory (9 tools)
- `ad_check_user` - Vérifier si un utilisateur existe
- `ad_get_user_info` - Informations complètes
- `ad_reset_password` - Reset mot de passe
- `ad_unlock_account` - Déverrouiller un compte
- `ad_create_user` - Créer un utilisateur
- `ad_disable_account` - Désactiver un compte
- `ad_enable_account` - Réactiver un compte
- `ad_move_to_ou` - Déplacer vers une OU
- `ad_copy_groups_from` - Copier les groupes d'un référent

### MySecret (1 tool)
- `mysecret_create_secret` - Créer un lien sécurisé

### Memory/RAG (3 tools)
- `memory_search_similar_cases` - Rechercher des cas similaires
- `memory_add_knowledge` - Ajouter une connaissance
- `memory_get_stats` - Statistiques de la base

## Installation

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer .env avec vos valeurs

# Démarrer avec Docker Compose
docker compose up -d
```

## Configuration

Variables d'environnement requises (voir `.env.example`):
- GLPI : `GLPI_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`
- Observium : `OBSERVIUM_URL`, `OBSERVIUM_USER`, `OBSERVIUM_PASS`
- LDAP/AD : `LDAP_SERVER`, `LDAP_BASE_DN`, `LDAP_BIND_USER`, `LDAP_BIND_PASS`
- MySecret : `MYSECRET_URL`
- PostgreSQL : `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASS`
- Ollama : `OLLAMA_URL`

## Architecture

```
widip-mcp-server/
├── src/
│   ├── clients/           # Clients API (GLPI, Observium, AD, etc.)
│   ├── mcp/               # Protocole MCP (server, registry, protocol)
│   ├── tools/             # Définition des tools MCP
│   ├── utils/             # Utilitaires (logging, retry)
│   ├── config.py          # Configuration
│   └── main.py            # Point d'entrée
├── Dockerfile
├── docker-compose.yml
└── init-db.sql            # Init PostgreSQL pgvector
```

## Intégration N8N

Configurer le node MCP Client dans N8N:
- URL: `http://widip-mcp-server:3001`
- Transport: SSE

## Endpoints

- `GET /health` - Health check
- `GET /sse` - SSE endpoint MCP (listing tools)
- `POST /messages` - Exécution des tools
