# Guide de Déploiement WIDIP v15.1

> **Version** : 1.0
> **Date** : 23 Décembre 2025
> **Durée estimée** : 2-4 heures (première installation)

---

## Table des Matières

1. [Prérequis](#1-prérequis)
2. [Architecture de Déploiement](#2-architecture-de-déploiement)
3. [Installation des Composants](#3-installation-des-composants)
4. [Configuration](#4-configuration)
5. [Initialisation Base de Données](#5-initialisation-base-de-données)
6. [Démarrage des Services](#6-démarrage-des-services)
7. [Tests de Validation](#7-tests-de-validation)
8. [Configuration n8n](#8-configuration-n8n)
9. [Checklist Production](#9-checklist-production)
10. [Dépannage](#10-dépannage)

---

# 1. Prérequis

## 1.1 Serveur

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| **CPU** | 2 cores | 4 cores |
| **RAM** | 4 GB | 8 GB |
| **Disque** | 20 GB SSD | 50 GB SSD |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

## 1.2 Logiciels Requis

```bash
# Vérifier les versions
python3 --version    # >= 3.11
docker --version     # >= 24.0
docker-compose --version  # >= 2.20
git --version        # >= 2.34
```

### Installation des dépendances (Ubuntu)

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose (plugin)
sudo apt install -y docker-compose-plugin

# Utilitaires
sudo apt install -y git curl jq postgresql-client
```

## 1.3 Accès Réseau Requis

| Service | Port | Direction | Description |
|---------|------|-----------|-------------|
| **GLPI API** | 443 | Sortant | API REST GLPI |
| **Observium API** | 443 | Sortant | API monitoring |
| **LDAPS (AD)** | 636 | Sortant | Active Directory |
| **SMTP** | 587 | Sortant | Envoi emails |
| **Teams Webhook** | 443 | Sortant | Notifications |
| **MCP Server** | 3001 | Entrant | API MCP (depuis n8n) |

## 1.4 Credentials Nécessaires

Avant de commencer, rassemblez :

| Credential | Où l'obtenir | Format |
|------------|--------------|--------|
| **GLPI App-Token** | GLPI > Configuration > API | `xxxxxxxxxx` |
| **GLPI User-Token** | GLPI > Mon profil > API | `xxxxxxxxxx` |
| **Observium API** | Admin Observium | user:password |
| **AD Service Account** | Admin AD | `CN=svc_widip,OU=...` |
| **SMTP Credentials** | Admin Mail | user:password |
| **Teams Webhook URL** | Teams > Connecteurs | `https://...webhook.office.com/...` |

---

# 2. Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────────┐
│                     SERVEUR WIDIP                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   n8n        │  │  MCP Server  │  │   Ollama     │           │
│  │  :5678       │──│   :3001      │──│   :11434     │           │
│  └──────────────┘  └──────┬───────┘  └──────────────┘           │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                    │
│  ┌──────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐             │
│  │ PostgreSQL  │  │    Redis     │  │   Nginx     │             │
│  │   :5432     │  │    :6379     │  │   :443      │             │
│  │  + pgvector │  │  (secrets)   │  │  (reverse)  │             │
│  └─────────────┘  └──────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │  GLPI   │         │   AD    │         │Observium│
    │  :443   │         │  :636   │         │  :443   │
    └─────────┘         └─────────┘         └─────────┘
```

---

# 3. Installation des Composants

## 3.1 Cloner le Repository

```bash
# Créer le répertoire de travail
sudo mkdir -p /opt/widip
sudo chown $USER:$USER /opt/widip
cd /opt/widip

# Cloner le repo (remplacer par votre URL)
git clone https://github.com/votre-org/widip-mcp-server.git
cd widip-mcp-server
```

## 3.2 Structure des Fichiers

```
/opt/widip/widip-mcp-server/
├── .env                    # Configuration (à créer)
├── .env.example            # Template de configuration
├── docker-compose.yml      # Stack Docker
├── init-db.sql            # Schéma PostgreSQL
├── requirements.txt        # Dépendances Python
└── src/
    ├── main.py            # Point d'entrée
    ├── config.py          # Configuration centralisée
    ├── clients/           # Clients API
    │   ├── glpi.py
    │   ├── activedirectory.py
    │   ├── observium.py
    │   └── notification.py
    ├── tools/             # MCP Tools
    │   ├── glpi_tools.py
    │   ├── ad_tools.py
    │   └── notification_tools.py
    ├── mcp/               # Core MCP
    │   ├── registry.py
    │   └── safeguard_queue.py
    └── utils/
        └── secrets.py
```

## 3.3 Créer le docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # ==========================================================================
  # PostgreSQL avec pgvector
  # ==========================================================================
  postgres:
    image: pgvector/pgvector:pg16
    container_name: widip-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-widip}
      POSTGRES_PASSWORD: ${POSTGRES_PASS}
      POSTGRES_DB: ${POSTGRES_DB:-widip_knowledge}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-widip}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================================================
  # Redis (cache + secrets chiffrés)
  # ==========================================================================
  redis:
    image: redis:7-alpine
    container_name: widip-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================================================
  # Ollama (Embeddings)
  # ==========================================================================
  ollama:
    image: ollama/ollama:latest
    container_name: widip-ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # Si pas de GPU, commenter le bloc deploy ci-dessus

  # ==========================================================================
  # MCP Server Python
  # ==========================================================================
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: widip-mcp
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:3001:3001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==========================================================================
  # n8n (Orchestration)
  # ==========================================================================
  n8n:
    image: n8nio/n8n:latest
    container_name: widip-n8n
    restart: unless-stopped
    environment:
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=${N8N_WEBHOOK_URL:-http://localhost:5678}
      - GENERIC_TIMEZONE=Europe/Paris
    volumes:
      - n8n_data:/home/node/.n8n
    ports:
      - "5678:5678"
    depends_on:
      - mcp-server

volumes:
  postgres_data:
  redis_data:
  ollama_data:
  n8n_data:

networks:
  default:
    name: widip-network
EOF
```

## 3.4 Créer le Dockerfile

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY src/ ./src/

# Port exposé
EXPOSE 3001

# Démarrage
CMD ["python", "-m", "src.main"]
EOF
```

## 3.5 Créer le requirements.txt

```bash
cat > requirements.txt << 'EOF'
# Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Base de données
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
redis>=5.0.0
pgvector>=0.2.4

# LDAP / Active Directory
ldap3>=2.9.1

# HTTP Client
httpx>=0.25.0

# Crypto
cryptography>=41.0.0

# Logging
structlog>=23.2.0

# Embeddings
ollama>=0.1.0

# Email
aiosmtplib>=3.0.0

# Utils
python-dotenv>=1.0.0
EOF
```

---

# 4. Configuration

## 4.1 Créer le fichier .env

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

## 4.2 Configuration Complète (.env)

Remplissez chaque section avec vos valeurs :

```bash
# =============================================================================
# WIDIP MCP Server - Configuration Production
# =============================================================================

# =============================================================================
# 1. SERVER CONFIGURATION
# =============================================================================
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3001
MCP_SERVER_DEBUG=false
LOG_LEVEL=INFO

# =============================================================================
# 2. SECURITY (OBLIGATOIRE)
# =============================================================================
# Générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
MCP_API_KEY=VOTRE_CLE_API_ICI_MIN_32_CHARS
MCP_REQUIRE_AUTH=true
CORS_ALLOWED_ORIGINS=http://localhost:5678,http://n8n:5678
SAFEGUARD_ENABLED=true

# =============================================================================
# 3. GLPI API
# =============================================================================
# URL de base de l'API GLPI (sans /apirest.php)
GLPI_URL=https://glpi.votre-domaine.fr/apirest.php

# App-Token: GLPI > Configuration > Générale > API
GLPI_APP_TOKEN=VOTRE_APP_TOKEN_GLPI

# User-Token: GLPI > Mon profil > Clés d'accès distant
GLPI_USER_TOKEN=VOTRE_USER_TOKEN_GLPI

# =============================================================================
# 4. OBSERVIUM API
# =============================================================================
OBSERVIUM_URL=https://observium.votre-domaine.fr/api/v0
OBSERVIUM_USER=api_widip
OBSERVIUM_PASS=MOT_DE_PASSE_OBSERVIUM

# =============================================================================
# 5. ACTIVE DIRECTORY / LDAP
# =============================================================================
# Format: ldaps://serveur:636 pour LDAPS (recommandé)
LDAP_SERVER=ldaps://dc01.votre-domaine.local:636
LDAP_USE_SSL=true

# IMPORTANT: Toujours true en production!
LDAP_VERIFY_SSL=true

# Optionnel: Chemin vers le certificat CA si pas dans le système
# LDAP_CA_CERT_PATH=/etc/ssl/certs/votre-ca.crt

# Base DN de votre domaine
LDAP_BASE_DN=DC=votre-domaine,DC=local

# Compte de service AD (droits: lecture + reset password + unlock)
LDAP_BIND_USER=CN=svc_widip,OU=ServiceAccounts,DC=votre-domaine,DC=local
LDAP_BIND_PASS=MOT_DE_PASSE_SERVICE_AD

# OU où chercher les utilisateurs
LDAP_USER_SEARCH_BASE=OU=Utilisateurs,DC=votre-domaine,DC=local

# =============================================================================
# 6. SMTP (Notifications Email)
# =============================================================================
SMTP_HOST=smtp.votre-domaine.fr
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=widip@votre-domaine.fr
SMTP_PASS=MOT_DE_PASSE_SMTP
SMTP_FROM_NAME=WIDIP Support
SMTP_FROM_EMAIL=widip@votre-domaine.fr

# =============================================================================
# 7. MICROSOFT TEAMS (Notifications)
# =============================================================================
# Teams > Canal > ... > Connecteurs > Webhook entrant
TEAMS_WEBHOOK_URL=https://votre-tenant.webhook.office.com/webhookb2/xxx/IncomingWebhook/yyy/zzz

# URL pour les liens dans les notifications
GLPI_TICKET_BASE_URL=https://glpi.votre-domaine.fr/front/ticket.form.php?id=
SAFEGUARD_DASHBOARD_URL=https://widip.votre-domaine.fr/safeguard

# =============================================================================
# 8. MYSECRET (Partage sécurisé de mots de passe)
# =============================================================================
MYSECRET_URL=https://mysecret.votre-domaine.fr
MYSECRET_API_KEY=VOTRE_CLE_API_MYSECRET

# =============================================================================
# 9. POSTGRESQL
# =============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=widip
POSTGRES_PASS=MOT_DE_PASSE_POSTGRES_FORT
POSTGRES_DB=widip_knowledge

# =============================================================================
# 10. REDIS
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=MOT_DE_PASSE_REDIS_FORT
REDIS_DB=0

# Clé de chiffrement pour les secrets temporaires (OBLIGATOIRE)
# Générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
REDIS_SECRET_KEY=VOTRE_CLE_CHIFFREMENT_REDIS_32_CHARS

# =============================================================================
# 11. OLLAMA (Embeddings)
# =============================================================================
OLLAMA_URL=http://ollama:11434
OLLAMA_EMBED_MODEL=intfloat/multilingual-e5-large
OLLAMA_EMBED_DIMENSIONS=1024

# =============================================================================
# 12. N8N
# =============================================================================
N8N_HOST=n8n.votre-domaine.fr
N8N_WEBHOOK_URL=https://n8n.votre-domaine.fr
```

## 4.3 Générer les Clés Sécurisées

```bash
# Générer MCP_API_KEY
echo "MCP_API_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Générer REDIS_SECRET_KEY
echo "REDIS_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Générer POSTGRES_PASS
echo "POSTGRES_PASS=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

# Générer REDIS_PASSWORD
echo "REDIS_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
```

## 4.4 Vérifier la Configuration

```bash
# Vérifier que toutes les variables obligatoires sont définies
grep -E "^[A-Z].*=$" .env | grep -v "^#" | while read line; do
    var=$(echo $line | cut -d= -f1)
    val=$(echo $line | cut -d= -f2-)
    if [[ -z "$val" || "$val" == "VOTRE_"* ]]; then
        echo "⚠️  $var non configuré"
    else
        echo "✅ $var configuré"
    fi
done
```

---

# 5. Initialisation Base de Données

## 5.1 Démarrer PostgreSQL

```bash
# Démarrer uniquement PostgreSQL
docker compose up -d postgres

# Attendre que PostgreSQL soit prêt
docker compose logs -f postgres
# Attendre "database system is ready to accept connections"
# Ctrl+C pour quitter les logs
```

## 5.2 Vérifier l'Initialisation

```bash
# Se connecter à PostgreSQL
docker compose exec postgres psql -U widip -d widip_knowledge

# Vérifier les tables créées
\dt

# Résultat attendu:
#                    List of relations
#  Schema |            Name            | Type  | Owner
# --------+----------------------------+-------+-------
#  public | incident_logs              | table | widip
#  public | safeguard_audit_log        | table | widip
#  public | safeguard_pending_approvals| table | widip
#  public | widip_agent_logs           | table | widip
#  public | widip_knowledge_base       | table | widip

# Vérifier pgvector
SELECT * FROM pg_extension WHERE extname = 'vector';

# Quitter
\q
```

## 5.3 (Optionnel) Réinitialiser la Base

```bash
# Si besoin de réinitialiser
docker compose down -v  # Supprime les volumes
docker compose up -d postgres
```

---

# 6. Démarrage des Services

## 6.1 Démarrer la Stack Complète

```bash
# Construire et démarrer tous les services
docker compose up -d --build

# Vérifier le statut
docker compose ps

# Résultat attendu:
# NAME             STATUS          PORTS
# widip-mcp        Up (healthy)    127.0.0.1:3001->3001/tcp
# widip-n8n        Up              0.0.0.0:5678->5678/tcp
# widip-ollama     Up              127.0.0.1:11434->11434/tcp
# widip-postgres   Up (healthy)    127.0.0.1:5432->5432/tcp
# widip-redis      Up (healthy)    127.0.0.1:6379->6379/tcp
```

## 6.2 Télécharger le Modèle d'Embeddings

```bash
# Télécharger e5-multilingual-large (première fois uniquement)
docker compose exec ollama ollama pull intfloat/multilingual-e5-large

# Vérifier
docker compose exec ollama ollama list
```

## 6.3 Voir les Logs

```bash
# Tous les logs
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f mcp-server
docker compose logs -f n8n
```

## 6.4 Arrêter les Services

```bash
# Arrêter sans supprimer les données
docker compose stop

# Arrêter et supprimer les conteneurs
docker compose down

# Arrêter et supprimer TOUT (données incluses)
docker compose down -v
```

---

# 7. Tests de Validation

## 7.1 Test de Santé MCP Server

```bash
# Health check
curl http://localhost:3001/health

# Résultat attendu:
# {"status":"healthy","version":"1.0.0"}
```

## 7.2 Test d'Authentification

```bash
# Remplacer par votre MCP_API_KEY
API_KEY="votre-mcp-api-key"

# Test sans API Key (doit échouer)
curl http://localhost:3001/mcp/tools
# Résultat: {"detail":"API Key required"}

# Test avec API Key (doit réussir)
curl -H "X-API-Key: $API_KEY" http://localhost:3001/mcp/tools
# Résultat: Liste des tools disponibles
```

## 7.3 Test GLPI

```bash
API_KEY="votre-mcp-api-key"

# Rechercher un client
curl -X POST http://localhost:3001/mcp/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "tool": "glpi_search_client",
    "arguments": {"name": "test"}
  }'
```

## 7.4 Test Active Directory

```bash
API_KEY="votre-mcp-api-key"

# Vérifier un utilisateur
curl -X POST http://localhost:3001/mcp/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "tool": "ad_check_user",
    "arguments": {"username": "jdupont"}
  }'
```

## 7.5 Test Complet

```bash
#!/bin/bash
# save as test_widip.sh

API_KEY="votre-mcp-api-key"
BASE_URL="http://localhost:3001"

echo "=== Test WIDIP MCP Server ==="

echo -e "\n1. Health Check..."
curl -s "$BASE_URL/health" | jq .

echo -e "\n2. Liste des Tools..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/mcp/tools" | jq '.tools | length'
echo "tools disponibles"

echo -e "\n3. Test GLPI Search..."
curl -s -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"tool": "glpi_search_new_tickets", "arguments": {"minutes_since": 60}}' | jq .

echo -e "\n4. Test Observium..."
curl -s -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"tool": "observium_get_device_alerts", "arguments": {}}' | jq .

echo -e "\n=== Tests terminés ==="
```

---

# 8. Configuration n8n

## 8.1 Accéder à n8n

```
URL: http://votre-serveur:5678
```

Créez un compte administrateur lors du premier accès.

## 8.2 Configurer les Credentials

### MCP Server API

1. **Settings > Credentials > Add Credential**
2. Type: **Header Auth**
3. Name: `WIDIP MCP API`
4. Header Name: `X-API-Key`
5. Header Value: `votre-mcp-api-key`

### Importer les Workflows

1. **Workflows > Import from File**
2. Importer dans l'ordre :
   - `WIDIP_Proactif_Observium_v9.json`
   - `WIDIP_Assist_ticket_v6.1.json`
   - `WIDIP_Enrichisseur_v1.json`
   - `WIDIP_Safeguard_v2.json`
   - `WIDIP_Human_Validation_v1.json`

### Configurer les Webhooks

Pour chaque workflow, vérifier que les nodes HTTP Request pointent vers :

```
URL: http://mcp-server:3001/mcp/call
Method: POST
Headers: X-API-Key = {{$credentials.widip_mcp_api}}
```

## 8.3 Activer les Workflows

1. Ouvrir chaque workflow
2. Cliquer sur le toggle **Active** en haut à droite
3. Vérifier que le trigger démarre (Cron ou Webhook)

---

# 9. Checklist Production

## 9.1 Sécurité

- [ ] `MCP_API_KEY` générée et unique (32+ caractères)
- [ ] `REDIS_SECRET_KEY` générée et unique (32+ caractères)
- [ ] `LDAP_VERIFY_SSL=true` activé
- [ ] Mots de passe forts pour PostgreSQL et Redis
- [ ] Ports exposés uniquement sur 127.0.0.1 (sauf n8n si accès externe)
- [ ] Firewall configuré (ufw ou iptables)
- [ ] Certificats SSL pour accès externe (Nginx/Traefik)

## 9.2 Monitoring

- [ ] Logs centralisés (Loki, ELK, ou similaire)
- [ ] Alertes sur containers down
- [ ] Métriques CPU/RAM/Disk
- [ ] Backup PostgreSQL automatisé

## 9.3 Backup

```bash
# Script de backup quotidien
#!/bin/bash
BACKUP_DIR="/opt/widip/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U widip widip_knowledge | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup Redis
docker compose exec -T redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Backup configuration
cp /opt/widip/widip-mcp-server/.env "$BACKUP_DIR/env_$DATE.bak"

# Garder 7 jours
find "$BACKUP_DIR" -mtime +7 -delete
```

## 9.4 Validation Finale

```bash
# Checklist de validation
echo "=== Validation Production WIDIP ==="

# 1. Services up
docker compose ps --format "{{.Name}}: {{.Status}}" | grep -v "Up" && echo "❌ Services down!" || echo "✅ Tous les services UP"

# 2. Health checks
curl -sf http://localhost:3001/health > /dev/null && echo "✅ MCP Server healthy" || echo "❌ MCP Server down"

# 3. Connexion PostgreSQL
docker compose exec -T postgres pg_isready && echo "✅ PostgreSQL ready" || echo "❌ PostgreSQL down"

# 4. Connexion Redis
docker compose exec -T redis redis-cli -a $REDIS_PASSWORD ping | grep -q PONG && echo "✅ Redis ready" || echo "❌ Redis down"

# 5. Ollama model
docker compose exec -T ollama ollama list | grep -q "e5" && echo "✅ Embedding model loaded" || echo "❌ Embedding model missing"

echo "=== Validation terminée ==="
```

---

# 10. Dépannage

## 10.1 Problèmes Courants

### MCP Server ne démarre pas

```bash
# Voir les logs
docker compose logs mcp-server

# Erreurs courantes:
# - "MCP_API_KEY required" → Vérifier .env
# - "Connection refused postgres" → PostgreSQL pas prêt
# - "LDAP connection failed" → Vérifier credentials AD
```

### Erreur LDAPS Certificate

```bash
# Si LDAP_VERIFY_SSL=true échoue
# 1. Vérifier le certificat CA
openssl s_client -connect dc01.votre-domaine.local:636 -showcerts

# 2. Exporter le certificat CA
echo | openssl s_client -connect dc01.votre-domaine.local:636 2>/dev/null | openssl x509 > ca.crt

# 3. Monter le certificat dans le container
# docker-compose.yml:
#   mcp-server:
#     volumes:
#       - ./ca.crt:/etc/ssl/certs/ad-ca.crt:ro
# .env:
#   LDAP_CA_CERT_PATH=/etc/ssl/certs/ad-ca.crt
```

### GLPI API Erreur 401

```bash
# Vérifier les tokens
curl -X GET "https://glpi.votre-domaine.fr/apirest.php/initSession" \
  -H "App-Token: $GLPI_APP_TOKEN" \
  -H "Authorization: user_token $GLPI_USER_TOKEN"

# Si erreur, régénérer les tokens dans GLPI
```

### Redis Connection Refused

```bash
# Vérifier que Redis est démarré
docker compose ps redis

# Tester la connexion
docker compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Embeddings Lents

```bash
# Vérifier si Ollama utilise le GPU
docker compose exec ollama nvidia-smi

# Si pas de GPU, les embeddings seront plus lents (~2-5s vs 0.1s)
```

## 10.2 Logs Utiles

```bash
# Logs structurés MCP Server
docker compose logs mcp-server 2>&1 | grep -E "(ERROR|WARNING|CRITICAL)"

# Logs SAFEGUARD
docker compose exec postgres psql -U widip -d widip_knowledge -c \
  "SELECT * FROM safeguard_audit_log ORDER BY timestamp DESC LIMIT 10;"

# Logs d'activité agents
docker compose exec postgres psql -U widip -d widip_knowledge -c \
  "SELECT * FROM widip_agent_logs ORDER BY timestamp DESC LIMIT 10;"
```

## 10.3 Reset Complet

```bash
# En cas de problème majeur, reset complet
cd /opt/widip/widip-mcp-server

# Arrêter et supprimer tout
docker compose down -v

# Supprimer les images
docker compose down --rmi all

# Reconstruire
docker compose up -d --build
```

---

# Annexes

## A. Commandes Utiles

```bash
# Statut rapide
docker compose ps

# Restart un service
docker compose restart mcp-server

# Shell dans un container
docker compose exec mcp-server /bin/bash

# Voir l'utilisation ressources
docker stats

# Nettoyer Docker
docker system prune -af
```

## B. Contacts Support

| Rôle | Contact |
|------|---------|
| Admin Système | admin@votre-domaine.fr |
| Support GLPI | glpi-admin@votre-domaine.fr |
| Support AD | ad-admin@votre-domaine.fr |

---

> **WIDIP v15.1 - Guide de Déploiement**
> *Document technique - Usage interne*
> *23 Décembre 2025*
