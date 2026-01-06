# WIDIP MCP Server v15.3
## Serveur Centralisé Tools - Model Context Protocol

> **Version** : 15.3 | **Type** : FastAPI Server | **Port** : 3001

---

## 🎯 Rôle

Le MCP Server est le serveur centralisé qui expose tous les tools (outils) utilisables par les agents IA. Il implémente le protocole MCP (Model Context Protocol) et gère les connexions vers GLPI, Observium, Active Directory, PostgreSQL, Redis, etc.

**Positionnement** : Cœur technique WIDIP, centralise toutes les intégrations externes.

---

## 📊 Architecture

```
[Agents IA n8n]
    ↓ HTTP/SSE
[MCP Server :3001]
    ├─ /mcp/call (HTTP POST)
    ├─ /mcp/sse (Server-Sent Events)
    └─ /safeguard/* (Endpoints validation)
    ↓
[Tools Modules]
    ├─ glpi_tools.py (10 tools)
    ├─ observium_tools.py (4 tools)
    ├─ ad_tools.py (9 tools)
    ├─ memory_tools.py (RAG, 5 tools)
    ├─ enrichisseur_tools.py (3 tools)
    ├─ notification_tools.py (3 tools)
    └─ mysecret_tools.py (1 tool)
    ↓
[Services Externes]
    ├─ GLPI API (REST)
    ├─ Observium API (REST)
    ├─ Active Directory (LDAP)
    ├─ PostgreSQL + pgvector (RAG)
    ├─ Redis (Cache)
    ├─ Ollama (Embeddings)
    ├─ Teams Webhook (Notifications)
    └─ MySecret API (Passwords)
```

---

## 🔧 Tools Disponibles (40+)

### GLPI Tools (10)
```python
glpi_search_new_tickets()        # L0 - Polling tickets
glpi_get_ticket_details(id)      # L0 - Détails ticket
glpi_search_client(name)          # L0 - Recherche client
glpi_create_ticket(...)           # L1 - Création ticket
glpi_add_ticket_followup(...)     # L1 - Ajout suivi
glpi_update_ticket_status(...)    # L2 - Changement statut
glpi_assign_ticket(...)           # L2 - Assignation
glpi_close_ticket(id)             # L3 - Clôture (validation)
glpi_send_email(...)              # L1 - Email client
glpi_get_resolved_tickets(hours)  # L0 - Pour enrichisseur
```

### Observium Tools (4)
```python
observium_get_device_status(device, ip)   # L0 - État device
observium_get_device_metrics(device, ip)  # L0 - Ports, trafic
observium_get_device_alerts(device)       # L0 - Alertes actives
observium_get_device_history(device, h)   # L0 - Historique
```

### Active Directory Tools (9)
```python
ad_check_user(username)                   # L0 - Vérifier existence
ad_get_user_info(username)                # L0 - Détails compte
ad_unlock_account(username)               # L2 - Déverrouillage
ad_reset_password(user, temp_pass)        # L3 - Reset MDP (validation)
ad_create_user(...)                       # L4 - Création (INTERDIT IA)
ad_disable_account(username)              # L3 - Désactivation (validation)
ad_enable_account(username)               # L2 - Réactivation
ad_move_to_ou(user, ou)                   # L2 - Déplacement OU
ad_copy_groups_from(src, dst)             # L3 - Copie groupes (validation)
```

### Memory/RAG Tools (5)
```python
memory_search_similar_cases(symptom)      # L0 - Recherche vectorielle
memory_add_knowledge(problem, solution)   # L1 - Ajout RAG
memory_check_exists(ticket_id)            # L0 - Déduplication
memory_get_stats()                        # L0 - Stats base
enrichisseur_get_stats()                  # L0 - Stats enrichisseur
```

### Enrichisseur Tools (3)
```python
enrichisseur_run_batch(hours, max, dry)   # L1 - Batch quotidien
enrichisseur_extract_knowledge(ticket)    # L0 - Extraction
enrichisseur_get_stats()                  # L0 - Métriques
```

### Notification Tools (3)
```python
notify_client(email, subject, body)       # L1 - Email client
notify_technician(subject, message, ...)  # L1 - Teams/Slack
request_human_validation(...)             # L1 - Demande validation
```

### MySecret Tools (1)
```python
mysecret_create_secret(value, ttl)        # L1 - Mot de passe temporaire
```

---

## 🔒 Sécurité

### Authentification
- **API Key** : Header `X-API-Key` requis (sauf dev)
- **Production** : Validation stricte au startup (src/config.py)

### SAFEGUARD Intégré
- Chaque tool a un niveau L0-L4
- L3/L4 → Routage vers WIDIP_Safeguard_v2

### CORS
- Origins autorisées configurables (.env)

---

## ⚙️ Configuration

### Variables (.env)
```bash
# Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3001
MCP_API_KEY=*** (REQUIRED en prod)
ENVIRONMENT=production

# GLPI
GLPI_URL=https://glpi.example.com/apirest.php
GLPI_APP_TOKEN=***
GLPI_USER_TOKEN=***

# Observium
OBSERVIUM_URL=https://observium.example.com/api/v0
OBSERVIUM_USER=api_user
OBSERVIUM_PASS=***

# Active Directory
LDAP_SERVER=ldaps://dc.example.com:636
LDAP_BIND_USER=CN=svc_widip,OU=ServiceAccounts,DC=example,DC=com
LDAP_BIND_PASS=***

# PostgreSQL + pgvector
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=widip
POSTGRES_PASS=***
POSTGRES_DB=widip_knowledge

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=***
REDIS_SECRET_KEY=*** (Fernet AES-128)

# Ollama (Embeddings)
OLLAMA_URL=http://ollama:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_EMBED_DIMENSIONS=768

# RAG
RAG_MIN_SIMILARITY=0.6
RAG_MAX_RESULTS=3
RAG_QUALITY_THRESHOLD=0.4

# Teams
TEAMS_WEBHOOK_URL=https://example.webhook.office.com/***
```

---

## 🚀 Démarrage

```bash
cd widip-mcp-server

# Installer dépendances
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env
nano .env  # Remplir les valeurs

# Valider config
python -m src.main --validate-config

# Démarrer serveur
python -m src.main
# → Server running on http://0.0.0.0:3001
```

---

## 📚 Structure Fichiers

```
widip-mcp-server/
├── src/
│   ├── main.py                 # Entrypoint FastAPI
│   ├── config.py               # Configuration + SAFEGUARD
│   ├── mcp/
│   │   └── server.py           # Serveur MCP
│   ├── tools/
│   │   ├── glpi_tools.py       # GLPI
│   │   ├── observium_tools.py  # Observium
│   │   ├── ad_tools.py         # Active Directory
│   │   ├── memory_tools.py     # RAG
│   │   ├── enrichisseur_tools.py
│   │   ├── notification_tools.py
│   │   └── mysecret_tools.py
│   └── routes/
│       └── safeguard.py        # Endpoints validation
├── .env.example                # Template configuration
├── requirements.txt            # Dépendances Python
└── migrations/
    └── 001_add_quality_score.sql
```

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 15.3
