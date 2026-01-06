# Migration WIBOT : n8n → FastAPI

## 📋 Vue d'ensemble

Ce document décrit la migration du backend WIBOT de n8n (workflows) vers FastAPI (Python pur).

**Objectif :** Simplifier l'architecture, améliorer les performances, et faciliter la maintenance.

---

## 🎯 Périmètre de la migration

### ✅ À MIGRER vers FastAPI

Tous les workflows n8n actuels doivent être convertis en endpoints FastAPI :

#### 1. **Authentification** (`auth_login.json`)
- `POST /webhook/auth/login`
- Validation username/password
- Génération JWT
- Retour : `{success, token, user}`

#### 2. **Chat principal** (`chat_main.json`)
- `POST /webhook/wibot/chat`
- Vérification JWT
- Check quota tokens
- Traitement fichiers (RAG optionnel)
- Appel IA (Mistral)
- Sauvegarde messages + tokens
- Gestion des 3 modes : flash, code, redaction

#### 3. **Gestion conversations**
- `GET /webhook/wibot/conversations` (`get_conversations.json`)
- `POST /webhook/wibot/conversations` (`create_conversation.json`)
- `PATCH /webhook/wibot/conversation/rename` (`rename_conversation.json`)
- `DELETE /webhook/wibot/conversation/delete` (`delete_conversation.json`)

#### 4. **Messages**
- `GET /webhook/wibot/messages` (`get_messages.json`)

#### 5. **Tokens**
- `GET /webhook/wibot/user/tokens` (`get_user_tokens.json`)

#### 6. **Analytics** (Admin only)
- `GET /webhook/wibot/analytics` (`analytics.json`)
- Stats globales, par mode, par jour
- Requiert rôle admin

#### 7. **Admin Users** (Admin only)
- `GET /webhook/wibot/admin/users` (`admin_users.json`)
- `POST /webhook/wibot/admin/users` (create)
- `PUT /webhook/wibot/admin/users` (update)
- `DELETE /webhook/wibot/admin/users` (delete)

### ⚠️ À CONSERVER sur n8n (optionnel)

**Uniquement si besoin futur :**
- Workflows d'automatisation métier
- Intégrations tierces complexes
- Tâches planifiées (cron-like)

**Pour cette migration :** On peut **désactiver complètement n8n** ou le garder en standby.

---

## 🏗️ Architecture cible FastAPI

### Structure du projet

```
wibot-backend/
├── main.py                      # Point d'entrée FastAPI
├── requirements.txt             # Dépendances Python
├── .env                         # Configuration (clés API, DB, etc.)
│
├── app/
│   ├── __init__.py
│   ├── config.py               # Configuration (lecture .env)
│   │
│   ├── routes/                 # Endpoints API
│   │   ├── __init__.py
│   │   ├── auth.py            # POST /auth/login
│   │   ├── chat.py            # POST /chat, gestion IA
│   │   ├── conversations.py   # CRUD conversations
│   │   ├── messages.py        # GET messages
│   │   ├── tokens.py          # GET user tokens
│   │   ├── analytics.py       # GET analytics (admin)
│   │   └── admin_users.py     # CRUD users (admin)
│   │
│   ├── services/               # Logique métier
│   │   ├── __init__.py
│   │   ├── auth_service.py    # JWT, bcrypt
│   │   ├── ai_service.py      # Appels Mistral API
│   │   ├── rag_service.py     # Ingestion + RAG (Qdrant)
│   │   ├── db_service.py      # Requêtes PostgreSQL
│   │   └── quota_service.py   # Gestion quotas tokens
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── chat.py
│   │   └── analytics.py
│   │
│   ├── middleware/             # Middleware FastAPI
│   │   ├── __init__.py
│   │   ├── auth.py            # Vérification JWT
│   │   └── cors.py            # CORS
│   │
│   └── utils/                  # Utilitaires
│       ├── __init__.py
│       ├── jwt_utils.py
│       ├── db_utils.py
│       └── file_utils.py
│
└── tests/                      # Tests unitaires
    ├── test_auth.py
    ├── test_chat.py
    └── test_admin.py
```

---

## 🗄️ Base de données PostgreSQL

### Schéma actuel (à conserver)

**Tables existantes :**
- `users` (user_id, username, password_hash, email, role, created_at, is_active)
- `conversations` (conversation_id UUID, user_id, title, created_at, updated_at)
- `messages` (message_id, conversation_id, user_id, role, content, tokens, attachments, mode, rag_used, files_count, created_at)
- `user_token_usage` (usage_id, user_id, month, used_tokens, quota_tokens)

**Pas de changement de schéma nécessaire** - Les tables actuelles sont compatibles.

---

## 🔑 Fonctionnalités clés à implémenter

### 1. Authentification JWT

**Actuel (n8n) :**
```javascript
// Node "Verify JWT" - Code JavaScript
const token = authHeader.substring(7);
const parts = token.split('.');
const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
```

**Cible (FastAPI) :**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Appel IA Mistral

**Actuel (n8n) :**
- Node "Mistral AI Chat Model" avec LangChain
- 3 modèles selon le mode :
  - `flash` → `mistral-small-latest`
  - `code` → `codestral-latest`
  - `redaction` → `mistral-large-latest`

**Cible (FastAPI) :**
```python
from mistralai import Mistral

client = Mistral(api_key=MISTRAL_API_KEY)

async def call_mistral(messages: list, mode: str = "flash"):
    model_map = {
        "flash": "mistral-small-latest",
        "code": "codestral-latest",
        "redaction": "mistral-large-latest"
    }

    response = await client.chat.complete_async(
        model=model_map[mode],
        messages=messages
    )

    return response.choices[0].message.content
```

### 3. RAG avec Qdrant

**Actuel (n8n) :**
- Workflow `rag_ingestion.json` (séparé)
- Sauvegarde fichiers → Embedding → Qdrant

**Cible (FastAPI) :**
```python
from qdrant_client import QdrantClient
from langchain_mistralai import MistralAIEmbeddings

qdrant = QdrantClient(url=QDRANT_URL)
embeddings = MistralAIEmbeddings(api_key=MISTRAL_API_KEY)

async def ingest_files(files: list, conversation_id: str):
    # Traitement fichiers
    # Chunking
    # Embedding
    # Upsert Qdrant
    pass

async def search_rag(query: str, conversation_id: str):
    # Recherche dans Qdrant
    # Retour contexte pertinent
    pass
```

### 4. Gestion quota tokens

**Actuel (n8n) :**
- Node "Check Quota" : vérification avant appel IA
- Node "UPDATE Token Usage" : incrémentation après réponse

**Cible (FastAPI) :**
```python
async def check_quota(user_id: int) -> dict:
    # SELECT LEFT JOIN user_token_usage
    # Retourner {used_tokens, quota_tokens, quota_exceeded}
    pass

async def update_quota(user_id: int, tokens_used: int):
    # UPSERT user_token_usage
    # Incrémenter used_tokens
    pass
```

---

## 📦 Dépendances Python requises

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0
pydantic-settings==2.6.0

# Database
psycopg2-binary==2.9.10
asyncpg==0.30.0

# Auth
pyjwt==2.10.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20

# IA & RAG
mistralai==1.2.4
langchain==0.3.14
langchain-mistralai==0.2.4
qdrant-client==1.12.1
pypdf==5.1.0
python-docx==1.1.2

# Utils
python-dotenv==1.0.1
```

---

## 🚀 Plan de migration (étapes)

### Phase 1 : Setup FastAPI (Jour 1)
1. ✅ Créer la structure `wibot-backend/app/`
2. ✅ Configurer `main.py` avec FastAPI
3. ✅ Installer dépendances (`requirements.txt`)
4. ✅ Configuration `.env` (clés API, DB)
5. ✅ Tester démarrage : `uvicorn main:app --reload`

### Phase 2 : Auth & Users (Jour 1-2)
1. ✅ Endpoint `POST /auth/login`
2. ✅ Middleware JWT (`verify_jwt`)
3. ✅ Endpoints admin users (CRUD)
4. ✅ Tests authentification

### Phase 3 : Chat & IA (Jour 2)
1. ✅ Endpoint `POST /chat`
2. ✅ Service Mistral AI (3 modes)
3. ✅ Check quota + update
4. ✅ Sauvegarde messages (mode, rag_used, files_count)
5. ✅ Gestion conversations (CRUD)

### Phase 4 : RAG (Jour 2-3)
1. ✅ Service RAG (ingestion fichiers)
2. ✅ Recherche Qdrant
3. ✅ Intégration dans `/chat`

### Phase 5 : Analytics (Jour 3)
1. ✅ Endpoint `GET /analytics`
2. ✅ Stats tokens, messages, modes
3. ✅ Middleware admin-only

### Phase 6 : Tests & Deploy (Jour 3)
1. ✅ Tests unitaires
2. ✅ Mise à jour `docker-compose.yml`
3. ✅ Désactiver n8n
4. ✅ Tests end-to-end

---

## 🐳 Docker Compose (après migration)

### Avant (avec n8n)
```yaml
services:
  postgres:
    # ...
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
  nginx:
    # ...
```

### Après (FastAPI uniquement)
```yaml
services:
  postgres:
    # ... (inchangé)

  backend:
    build: ./wibot-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://widip:widipbot2024@postgres:5432/wibot
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - QDRANT_URL=${QDRANT_URL}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./wibot-backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  nginx:
    # Proxy vers backend:8000 au lieu de n8n:5678
```

---

## 🔄 Mapping n8n → FastAPI

| n8n Workflow | Endpoint FastAPI | Méthode | Auth |
|--------------|------------------|---------|------|
| `auth_login.json` | `/auth/login` | POST | ❌ |
| `chat_main.json` | `/chat` | POST | ✅ JWT |
| `get_conversations.json` | `/conversations` | GET | ✅ JWT |
| `create_conversation.json` | `/conversations` | POST | ✅ JWT |
| `rename_conversation.json` | `/conversations/{id}` | PATCH | ✅ JWT |
| `delete_conversation.json` | `/conversations/{id}` | DELETE | ✅ JWT |
| `get_messages.json` | `/messages` | GET | ✅ JWT |
| `get_user_tokens.json` | `/user/tokens` | GET | ✅ JWT |
| `analytics.json` | `/analytics` | GET | ✅ Admin |
| `admin_users.json` (GET) | `/admin/users` | GET | ✅ Admin |
| `admin_users.json` (POST) | `/admin/users` | POST | ✅ Admin |
| `admin_users.json` (PUT) | `/admin/users/{id}` | PUT | ✅ Admin |
| `admin_users.json` (DELETE) | `/admin/users/{id}` | DELETE | ✅ Admin |
| `rag_ingestion.json` | `/rag/ingest` | POST | ✅ JWT |

---

## 📝 Configuration (.env)

```env
# Database
DATABASE_URL=postgresql://widip:widipbot2024@localhost:5432/wibot

# Mistral AI
MISTRAL_API_KEY=votre_cle_mistral

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optionnel

# JWT
JWT_SECRET=votre_secret_jwt_256_bits
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Quotas
DEFAULT_QUOTA_TOKENS=50000

# Files
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=10
```

---

## ✅ Validation post-migration

### Tests à effectuer :

1. **Auth**
   - ✅ Login avec username/password valides
   - ✅ Réception JWT
   - ✅ Rejet token invalide/expiré

2. **Chat**
   - ✅ Envoi message mode flash
   - ✅ Envoi message mode code
   - ✅ Envoi message mode redaction
   - ✅ Quota dépassé → erreur
   - ✅ Fichier joint → RAG activé

3. **Conversations**
   - ✅ Création conversation
   - ✅ Liste conversations
   - ✅ Renommer conversation
   - ✅ Supprimer conversation

4. **Admin**
   - ✅ Créer utilisateur
   - ✅ Modifier utilisateur
   - ✅ Supprimer utilisateur
   - ✅ Analytics (stats correctes)

---

## 🎯 Avantages de la migration

| Avant (n8n) | Après (FastAPI) |
|-------------|-----------------|
| 11 workflows JSON complexes | Code Python lisible |
| Debug difficile (logs n8n) | Debug facile (logs Python) |
| Forte dépendance n8n | Stack standard Python |
| ~400MB RAM (n8n) | ~100MB RAM (FastAPI) |
| Déploiement complexe | `docker-compose up` |
| Versionning difficile | Git standard |

---

## 🚨 Points d'attention

1. **Secrets :**
   - Ne jamais commit les clés API dans Git
   - Utiliser `.env` (ajouté au `.gitignore`)

2. **Password hashing :**
   - Utiliser `bcrypt` (pas de hash simple)
   - Exemple actuel : `test123` en clair → à changer

3. **CORS :**
   - Configurer correctement pour le frontend React

4. **Rate limiting :**
   - Ajouter protection contre abus (optionnel)

5. **Logs :**
   - Configurer logging Python (fichiers + console)

---

## 📚 Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Mistral AI API](https://docs.mistral.ai/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Pydantic Models](https://docs.pydantic.dev/)

---

## 🤝 Support

Pour toute question pendant la migration, consulter :
- Ce document
- Code source n8n workflows (référence logique)
- Schéma PostgreSQL (`init.sql`)

---

**Date :** 2026-01-01
**Version :** 1.0
**Auteur :** Documentation générée pour migration WIBOT
