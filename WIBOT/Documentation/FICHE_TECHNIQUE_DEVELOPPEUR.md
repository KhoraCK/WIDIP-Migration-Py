# 📘 WIBOT - Fiche Technique Développeur

**Version :** 1.0
**Date :** Janvier 2026
**Entreprise :** WIDIP
**Type :** Chatbot IA Intelligent Interne

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture système](#architecture-système)
3. [Stack technique](#stack-technique)
4. [Base de données](#base-de-données)
5. [Ports et services](#ports-et-services)
6. [Authentification et sécurité](#authentification-et-sécurité)
7. [Fonctionnalités](#fonctionnalités)
8. [Limites et contraintes](#limites-et-contraintes)
9. [Migration prévue](#migration-prévue)
10. [Améliorations recommandées](#améliorations-recommandées)
11. [Guide d'utilisation](#guide-dutilisation)
12. [Maintenance et déploiement](#maintenance-et-déploiement)

---

## 🎯 Vue d'ensemble

### Description
WIBOT est un chatbot IA intelligent développé pour WIDIP, permettant aux employés d'interagir avec une IA avancée (Mistral AI) avec support RAG (Retrieval-Augmented Generation) pour l'analyse de documents.

### Objectifs
- ✅ Centraliser les interactions IA de l'entreprise
- ✅ Gérer les quotas de tokens par utilisateur
- ✅ Supporter plusieurs modes d'IA (flash, code, rédaction)
- ✅ Permettre l'analyse de documents (RAG)
- ✅ Interface moderne et intuitive

### Utilisateurs
- **Utilisateurs standards** : Employés WIDIP (chat, conversations)
- **Administrateurs** : Gestion utilisateurs, analytics, supervision

---

## 🏗️ Architecture système

### Architecture actuelle (Hybride)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│                      http://localhost:5173                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  - React 19 + Vite                                       │   │
│  │  - TailwindCSS                                           │   │
│  │  - Zustand (state management)                            │   │
│  │  - React Router                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                       │
│                      http://localhost:8080                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Route /webhook/* → n8n:5678                             │   │
│  │  CORS + Headers                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (n8n Workflows)                       │
│                      http://localhost:5678                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  11 Workflows JSON :                                     │   │
│  │  - auth_login.json                                       │   │
│  │  - chat_main.json                                        │   │
│  │  - get_conversations.json                                │   │
│  │  - create_conversation.json                              │   │
│  │  - rename_conversation.json                              │   │
│  │  - delete_conversation.json                              │   │
│  │  - get_messages.json                                     │   │
│  │  - get_user_tokens.json                                  │   │
│  │  - analytics.json                                        │   │
│  │  - admin_users.json                                      │   │
│  │  - rag_ingestion.json                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────┬───────────────┬───────────────┬────────────────────┘
             │               │               │
             ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌─────────────────────┐
│   PostgreSQL     │ │  Mistral AI  │ │  Qdrant (Vector DB) │
│   localhost:5432 │ │   API Cloud  │ │  localhost:6333     │
│                  │ │              │ │                     │
│  - users         │ │  - Flash     │ │  - Embeddings       │
│  - conversations │ │  - Code      │ │  - RAG Search       │
│  - messages      │ │  - Rédaction │ │                     │
│  - token_usage   │ │              │ │                     │
└──────────────────┘ └──────────────┘ └─────────────────────┘
```

### Flux de données principal

```
┌─────────┐      ┌─────────┐      ┌──────────┐      ┌──────────┐
│  User   │─────▶│ Frontend│─────▶│  Nginx   │─────▶│   n8n    │
│ Browser │◀─────│  React  │◀─────│  :8080   │◀─────│  :5678   │
└─────────┘      └─────────┘      └──────────┘      └────┬─────┘
                                                          │
                    ┌─────────────────────────────────────┤
                    │                                     │
                    ▼                                     ▼
            ┌───────────────┐                   ┌────────────────┐
            │  PostgreSQL   │                   │  Mistral API   │
            │   Database    │                   │  (Cloud)       │
            └───────────────┘                   └────────────────┘
                    ▲
                    │
                    ▼
            ┌───────────────┐
            │  Qdrant       │
            │  Vector DB    │
            └───────────────┘
```

---

## 🛠️ Stack technique

### Frontend

| Technologie | Version | Usage |
|-------------|---------|-------|
| **React** | 19.2.0 | Framework UI |
| **Vite** | 7.2.4 | Build tool & dev server |
| **TypeScript** | 5.9.3 | Langage typé |
| **TailwindCSS** | 3.4.19 | Styling |
| **Zustand** | 5.0.9 | State management |
| **React Router** | 7.11.0 | Routing |
| **Axios** | 1.13.2 | HTTP client |
| **React Markdown** | 10.1.0 | Rendu markdown |
| **Lucide React** | 0.562.0 | Icônes |

**Structure :**
```
wibot-frontend/
├── src/
│   ├── components/     # Composants réutilisables
│   │   ├── ui/        # Button, Input, Spinner, etc.
│   │   ├── Chat/      # ChatWindow, MessageBubble, etc.
│   │   └── Layout/    # Sidebar, Header
│   ├── pages/         # Pages principales
│   │   ├── Login.tsx
│   │   ├── Chat.tsx
│   │   ├── Supervision.tsx
│   │   └── AdminUsers.tsx
│   ├── services/      # API services
│   │   ├── api.ts     # Axios instance + endpoints
│   │   └── auth.ts    # JWT management
│   ├── store/         # Zustand stores
│   │   └── index.ts   # Auth, Chat, Conversations stores
│   ├── hooks/         # Custom hooks
│   │   └── useAuth.ts
│   ├── types/         # TypeScript types
│   └── App.tsx        # Root component
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

### Backend (Actuel : n8n)

| Technologie | Version | Usage |
|-------------|---------|-------|
| **n8n** | 1.122.4 | Workflow automation |
| **Node.js** | 20+ | Runtime n8n |
| **LangChain** | Intégré | RAG & IA orchestration |

**Workflows principaux :**
- 🔐 **auth_login** : Authentification JWT
- 💬 **chat_main** : Logique principale du chat
- 📁 **Conversations** : CRUD conversations
- 📊 **analytics** : Statistiques (admin)
- 👥 **admin_users** : Gestion utilisateurs
- 📄 **rag_ingestion** : Traitement documents

### Base de données

| Technologie | Version | Usage |
|-------------|---------|-------|
| **PostgreSQL** | 16+ | Base principale |
| **Qdrant** | Latest | Vector DB (embeddings) |

### IA & Embeddings

| Service | Modèle | Usage |
|---------|--------|-------|
| **Mistral AI** | mistral-small-latest | Mode Flash (rapide) |
| **Mistral AI** | codestral-latest | Mode Code |
| **Mistral AI** | mistral-large-latest | Mode Rédaction |
| **Mistral Embeddings** | mistral-embed | Embeddings pour RAG |

### Infrastructure

| Technologie | Version | Usage |
|-------------|---------|-------|
| **Docker** | 24+ | Containerisation |
| **Docker Compose** | 2.0+ | Orchestration |
| **Nginx** | 1.25+ | Reverse proxy |

---

## 🗄️ Base de données

### Schéma PostgreSQL

#### Table `users`
```sql
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,       -- ⚠️ Actuellement en clair (à changer)
    email           VARCHAR(255),
    role            VARCHAR(50) DEFAULT 'user',  -- 'user' ou 'admin'
    created_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT true
);

-- Index
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

**Exemple de données :**
| user_id | username | password_hash | role |
|---------|----------|---------------|------|
| 1 | khora | test123 | admin |
| 2 | test | test123 | user |

#### Table `conversations`
```sql
CREATE TABLE conversations (
    conversation_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    title            VARCHAR(255),
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_conversations_user ON conversations(user_id, updated_at DESC);
```

#### Table `messages`
```sql
CREATE TABLE messages (
    message_id       SERIAL PRIMARY KEY,
    conversation_id  UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    user_id          INTEGER REFERENCES users(user_id),
    role             VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT NOT NULL,
    tokens           INTEGER DEFAULT 0,
    attachments      JSONB,

    -- Colonnes analytics
    mode             VARCHAR(20) DEFAULT 'flash',    -- 'flash', 'code', 'redaction'
    rag_used         BOOLEAN DEFAULT false,
    files_count      INTEGER DEFAULT 0,

    created_at       TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at ASC);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_mode ON messages(mode);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_analytics ON messages(user_id, mode, created_at);
```

#### Table `user_token_usage`
```sql
CREATE TABLE user_token_usage (
    usage_id        SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    month           DATE NOT NULL,                    -- Premier jour du mois
    used_tokens     BIGINT DEFAULT 0,
    quota_tokens    BIGINT DEFAULT 50000,

    UNIQUE(user_id, month)
);

-- Index
CREATE INDEX idx_token_usage_user_month ON user_token_usage(user_id, month);
```

**Logique de quota :**
- Quota mensuel par défaut : **50 000 tokens**
- Reset automatique chaque 1er du mois
- Bloquage si `used_tokens >= quota_tokens`

### Diagramme entité-relation

```
┌──────────────────┐
│      users       │
│──────────────────│
│ PK user_id       │
│    username      │
│    password_hash │
│    role          │
│    email         │
└────────┬─────────┘
         │ 1
         │
         │ N
┌────────┴─────────────────┐
│    conversations         │
│──────────────────────────│
│ PK conversation_id (UUID)│
│ FK user_id               │
│    title                 │
│    created_at            │
│    updated_at            │
└────────┬─────────────────┘
         │ 1
         │
         │ N
┌────────┴─────────────┐         ┌───────────────────┐
│      messages        │         │ user_token_usage  │
│──────────────────────│         │───────────────────│
│ PK message_id        │         │ PK usage_id       │
│ FK conversation_id   │◀────────│ FK user_id        │
│ FK user_id           │    N:1  │    month          │
│    role              │         │    used_tokens    │
│    content           │         │    quota_tokens   │
│    tokens            │         └───────────────────┘
│    mode              │
│    rag_used          │
│    files_count       │
└──────────────────────┘
```

### Qdrant (Vector Database)

**Collections :**
- `wibot_documents` : Embeddings des documents uploadés

**Structure d'un point :**
```json
{
  "id": "uuid-v4",
  "vector": [0.123, -0.456, ...],  // 1024 dimensions (Mistral embeddings)
  "payload": {
    "text": "Contenu du chunk",
    "conversation_id": "uuid",
    "user_id": 123,
    "filename": "document.pdf",
    "page": 1,
    "chunk_index": 0,
    "created_at": "2026-01-01T12:00:00Z"
  }
}
```

---

## 🌐 Ports et services

### Tableau des ports

| Service | Port | Protocole | Accès | Description |
|---------|------|-----------|-------|-------------|
| **Frontend (Vite)** | 5173 | HTTP | Public | Interface React |
| **n8n** | 5678 | HTTP | Interne | Workflows (API) |
| **n8n Editor** | 5679 | HTTP | Admin | Interface n8n |
| **PostgreSQL** | 5432 | TCP | Interne | Base de données |
| **Qdrant** | 6333 | HTTP | Interne | Vector DB |
| **Nginx** | 8080 | HTTP | Public | Reverse proxy |

### Configuration Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: wibot-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: wibot
      POSTGRES_USER: widip
      POSTGRES_PASSWORD: widipbot2024
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  n8n:
    image: n8nio/n8n:latest
    container_name: wibot-n8n
    ports:
      - "5678:5678"   # API workflows
      - "5679:5679"   # Interface édition
    environment:
      - N8N_BASIC_AUTH_ACTIVE=false
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=wibot
      - DB_POSTGRESDB_USER=widip
      - DB_POSTGRESDB_PASSWORD=widipbot2024
      - WEBHOOK_URL=http://localhost:8080
    volumes:
      - n8n_data:/home/node/.n8n
      - ./rag-documents:/home/node/.n8n-files/rag-documents

  nginx:
    image: nginx:alpine
    container_name: wibot-nginx
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - n8n
```

### URLs d'accès

| Environnement | URL | Usage |
|---------------|-----|-------|
| **Frontend** | http://localhost:5173 | Interface utilisateur |
| **API Backend** | http://localhost:8080/webhook/* | Endpoints REST |
| **n8n Editor** | http://localhost:5679 | Edition workflows (dev) |
| **PostgreSQL** | localhost:5432 | Base de données |

---

## 🔐 Authentification et sécurité

### Système d'authentification

#### JWT (JSON Web Token)

**Génération :**
```javascript
// Dans n8n (node "Verify JWT" - auth_login.json)
const jwt = require('jsonwebtoken');

const payload = {
  userId: user.user_id,
  username: user.username,
  role: user.role,
  exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)  // 24h
};

const token = jwt.sign(payload, SECRET_KEY, { algorithm: 'HS256' });
```

**Structure du token :**
```json
{
  "userId": 1,
  "username": "khora",
  "role": "admin",
  "exp": 1735776000
}
```

**Validation :**
- Tous les endpoints (sauf `/auth/login`) requièrent un header :
  ```
  Authorization: Bearer <token>
  ```
- Validation dans chaque workflow via node "Verify JWT"
- Vérification de l'expiration
- Extraction de `userId` et `role`

#### Flux d'authentification

```
┌─────────┐                 ┌──────────┐                ┌──────────┐
│ Client  │                 │  Backend │                │   DB     │
└────┬────┘                 └─────┬────┘                └─────┬────┘
     │                            │                            │
     │  POST /auth/login          │                            │
     │  {username, password}      │                            │
     ├───────────────────────────>│                            │
     │                            │  SELECT * FROM users       │
     │                            │  WHERE username=?          │
     │                            ├──────────────────────────>│
     │                            │                            │
     │                            │  <user data>               │
     │                            │<───────────────────────────┤
     │                            │                            │
     │                            │  Compare passwords         │
     │                            │  (⚠️ plaintext actuellement)│
     │                            │                            │
     │  {success, token, user}    │                            │
     │<───────────────────────────┤                            │
     │                            │                            │
     │  POST /chat                │                            │
     │  Header: Bearer <token>    │                            │
     ├───────────────────────────>│                            │
     │                            │  Verify JWT                │
     │                            │  Decode payload            │
     │                            │                            │
     │  <response>                │                            │
     │<───────────────────────────┤                            │
```

### Points de sécurité actuels

| Aspect | État | Notes |
|--------|------|-------|
| **HTTPS** | ❌ Non | HTTP uniquement (développement) |
| **Password hashing** | ⚠️ **CRITIQUE** | Mots de passe en **clair** dans la DB |
| **JWT Secret** | ⚠️ Faible | Secret hardcodé dans workflows |
| **CORS** | ✅ Configuré | Nginx autorise localhost:5173 |
| **Rate limiting** | ❌ Non | Pas de protection brute-force |
| **SQL Injection** | ✅ Protégé | Requêtes paramétrées n8n |
| **XSS** | ✅ Protégé | React échappe automatiquement |
| **Session expiration** | ✅ Oui | JWT expire après 24h |
| **Role-based access** | ✅ Partiel | Admin vs User (non vérifié partout) |

### ⚠️ Vulnérabilités critiques identifiées

#### 1. **Mots de passe en clair**
```sql
-- ❌ ACTUEL (DANGEREUX)
INSERT INTO users (username, password_hash)
VALUES ('khora', 'test123');

-- ✅ À FAIRE
-- Utiliser bcrypt avec salt
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash('test123', 10);
INSERT INTO users (username, password_hash)
VALUES ('khora', '$2b$10$...');
```

#### 2. **JWT Secret hardcodé**
```javascript
// ❌ ACTUEL
const SECRET_KEY = 'wibot_secret_key_2024';

// ✅ À FAIRE
const SECRET_KEY = process.env.JWT_SECRET;  // 256 bits minimum
```

#### 3. **Pas de HTTPS**
- Tokens JWT exposés en clair sur le réseau
- Credentials exposés lors du login

---

## ⚡ Fonctionnalités

### 1. Chat IA (Multi-modes)

#### Modes disponibles

| Mode | Modèle Mistral | Usage | Vitesse | Coût tokens |
|------|----------------|-------|---------|-------------|
| **Flash** ⚡ | mistral-small-latest | Questions rapides, généraliste | Rapide | Faible |
| **Code** 💻 | codestral-latest | Programmation, debug, review | Moyenne | Moyen |
| **Rédaction** 📝 | mistral-large-latest | Textes longs, analyse approfondie | Lent | Élevé |

#### Workflow de chat (chat_main.json)

```
┌─────────────────┐
│ Webhook trigger │
│ POST /chat      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Verify JWT     │ ──────> ❌ Unauthorized
└────────┬────────┘
         │ ✅
         ▼
┌─────────────────┐
│ Process Files   │ (si fichiers joints)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Has Files?     │
└────┬────────┬───┘
     │ Oui    │ Non
     ▼        ▼
┌────────┐   └────────────┐
│  RAG   │                │
│Ingest  │                │
└───┬────┘                │
    │                     │
    └─────────┬───────────┘
              ▼
      ┌───────────────┐
      │ Check Quota   │ ──────> ❌ Quota dépassé
      └───────┬───────┘
              │ ✅
              ▼
      ┌───────────────┐
      │ Prepare Quota │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │  Mode Switch  │
      └───┬───┬───┬───┘
          │   │   │
    Flash │   │Code│ Rédaction
          ▼   ▼   ▼
      ┌───────────────┐
      │ Mistral AI    │ (avec RAG si activé)
      │ Chat Model    │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ Prepare Save  │ (calcul tokens, format)
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ UPSERT Conv   │ (créer/update conversation)
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ INSERT User   │ (message utilisateur)
      │    Message    │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ INSERT AI     │ (réponse IA)
      │   Message     │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ UPDATE Tokens │ (décompte quota)
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │  Response     │ ──────> ✅ {success, response, tokens}
      └───────────────┘
```

### 2. RAG (Retrieval-Augmented Generation)

#### Fonctionnement

**Ingestion de documents (rag_ingestion.json) :**
```
Fichier uploadé (PDF/DOCX/TXT)
         │
         ▼
    Extraction texte
         │
         ▼
    Chunking (1000 chars avec overlap)
         │
         ▼
    Embedding (Mistral API)
         │
         ▼
    Stockage Qdrant (conversation_id)
```

**Utilisation en chat :**
1. Utilisateur envoie message + fichier(s)
2. Fichiers ingérés dans Qdrant
3. À chaque message suivant :
   - Recherche de similarité dans Qdrant
   - Top 5 chunks pertinents récupérés
   - Contexte ajouté au prompt Mistral

**Exemple de prompt avec RAG :**
```
System: Tu es WIBOT, assistant IA de WIDIP.

Context (documents):
- Chunk 1: [contenu pertinent du PDF]
- Chunk 2: [autre chunk pertinent]

User: Que dit le document sur la sécurité ?
```

### 3. Gestion des conversations

**Endpoints :**
- `GET /conversations` : Liste des conversations de l'utilisateur
- `POST /conversations` : Créer une nouvelle conversation
- `PATCH /conversation/rename` : Renommer une conversation
- `DELETE /conversation/delete` : Supprimer une conversation + messages

**Logique :**
- Chaque utilisateur ne voit que **ses** conversations
- Conversations triées par `updated_at DESC`
- Titre auto-généré (50 premiers caractères du 1er message)

### 4. Gestion des quotas

**Système de quotas :**
- Quota mensuel : **50 000 tokens** par utilisateur
- Reset automatique le 1er de chaque mois
- Comptage :
  - Tokens input (message utilisateur)
  - Tokens output (réponse IA)
  - Tokens contexte (RAG)

**Vérification :**
```sql
SELECT
  COALESCE(t.used_tokens, 0) as used_tokens,
  COALESCE(t.quota_tokens, 50000) as quota_tokens
FROM users u
LEFT JOIN user_token_usage t ON (
  t.user_id = u.user_id
  AND t.month = DATE_TRUNC('month', CURRENT_DATE)
)
WHERE u.user_id = ?
```

**Blocage :**
- Si `used_tokens >= quota_tokens` → Erreur 403
- Message : "Quota mensuel de tokens dépassé"

### 5. Analytics (Admin uniquement)

**Endpoint :** `GET /analytics?period=7d`

**Métriques :**
```json
{
  "tokens": {
    "total_used": 125000,
    "total_quota": 500000,
    "percentage": 25
  },
  "messages_per_day": [
    {"date": "2026-01-01", "count": 45, "tokens": 12500}
  ],
  "modes": {
    "flash": 120,
    "code": 35,
    "redaction": 12
  },
  "global_stats": {
    "total_users": 10,
    "active_users": 7,
    "total_conversations": 45,
    "total_messages": 167
  },
  "files_rag": {
    "files_uploaded": 23,
    "messages_with_rag": 56
  },
  "top_users": [
    {"username": "khora", "messages": 78, "tokens": 45000}
  ]
}
```

**Périodes disponibles :**
- `24h` : Dernières 24 heures
- `7d` : 7 derniers jours (défaut)
- `30d` : 30 derniers jours

### 6. Administration utilisateurs

**Endpoints (Admin uniquement) :**
- `GET /admin/users` : Liste tous les utilisateurs
- `POST /admin/users` : Créer un utilisateur
- `PUT /admin/users` : Modifier un utilisateur
- `DELETE /admin/users` : Supprimer un utilisateur

**Permissions :**
```javascript
// Vérification rôle admin
if (decoded.role !== 'admin') {
  return { error: 'Admin access required' };
}
```

**Champs modifiables :**
- `username`
- `password`
- `email`
- `role` (user/admin)
- `is_active` (activation/désactivation compte)

---

## ⚠️ Limites et contraintes

### Limites techniques

| Aspect | Limite actuelle | Impact |
|--------|----------------|--------|
| **Quota tokens/mois** | 50 000 tokens/user | Bloque l'utilisateur si dépassé |
| **Taille fichiers** | 10 MB max | Fichiers plus gros rejetés |
| **Types de fichiers** | PDF, DOCX, TXT | Autres formats non supportés |
| **Contexte conversation** | 10 messages | LangChain Memory limite |
| **Timeout Mistral API** | 90 secondes | Requêtes longues peuvent échouer |
| **Concurrence** | Non testé | Risque de conflits DB |

### Limites de l'API Mistral

**Rate limits (selon plan) :**
- **Free tier** : Limité (non documenté précisément)
- **Pay-as-you-go** : ~500 requêtes/minute

**Modèles et contexte :**
| Modèle | Contexte max | Coût relatif |
|--------|--------------|--------------|
| mistral-small | 32k tokens | 1x |
| codestral | 32k tokens | 1.5x |
| mistral-large | 128k tokens | 3x |

**Quotas tokens recommandés :**
- Flash : ~100-500 tokens/requête
- Code : ~500-2000 tokens/requête
- Rédaction : ~2000-5000 tokens/requête

### Limites fonctionnelles

❌ **Non implémenté :**
- Partage de conversations entre utilisateurs
- Export de conversations (PDF, Markdown)
- Historique des modifications de messages
- Recherche dans les conversations
- Tags/catégories de conversations
- Notifications en temps réel
- Multi-langue (uniquement français)
- API publique (tout interne)

### Limites de sécurité

⚠️ **Points d'attention :**
- Pas de chiffrement des données sensibles en DB
- Pas d'audit logs (traçabilité actions admin)
- Pas de détection d'anomalies (usage suspect)
- Pas de backup automatique
- Pas de disaster recovery plan

---

## 🔄 Migration prévue (n8n → FastAPI)

### Motivations

| Problème actuel (n8n) | Solution FastAPI |
|----------------------|------------------|
| 11 workflows JSON complexes | Code Python structuré |
| Debug difficile | Logs Python + debugger |
| Dépendance forte n8n | Stack Python standard |
| ~400 MB RAM | ~100 MB RAM |
| Versionning difficile | Git natif |
| Tests compliqués | Pytest intégré |

### Architecture cible

```
wibot-backend/ (FastAPI)
├── main.py
├── requirements.txt
├── .env
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   ├── messages.py
│   │   ├── tokens.py
│   │   ├── analytics.py
│   │   └── admin_users.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── ai_service.py
│   │   ├── rag_service.py
│   │   ├── db_service.py
│   │   └── quota_service.py
│   ├── models/
│   ├── middleware/
│   └── utils/
└── tests/
```

### Plan de migration

**Phase 1 : Setup** (½ jour)
- ✅ Structure FastAPI
- ✅ Configuration .env
- ✅ Connexion PostgreSQL

**Phase 2 : Auth** (½ jour)
- ✅ Login endpoint
- ✅ JWT middleware
- ✅ Password hashing (bcrypt)

**Phase 3 : Chat** (1 jour)
- ✅ Chat endpoint
- ✅ Mistral AI service
- ✅ Quota management

**Phase 4 : RAG** (1 jour)
- ✅ Ingestion service
- ✅ Qdrant integration
- ✅ RAG dans chat

**Phase 5 : Admin** (½ jour)
- ✅ Users CRUD
- ✅ Analytics

**Phase 6 : Tests & Deploy** (½ jour)
- ✅ Tests unitaires
- ✅ Docker
- ✅ Migration données

**Total : 3-4 jours**

### Avantages post-migration

✅ **Performance** : 4x moins de RAM
✅ **Maintenabilité** : Code Python vs JSON
✅ **Scalabilité** : Facile à déployer (Kubernetes ready)
✅ **Sécurité** : Meilleur contrôle, audit logs
✅ **Tests** : Pytest + coverage
✅ **Documentation** : Auto-générée (OpenAPI/Swagger)

---

## 🔧 Améliorations recommandées

### Priorité 1 : Sécurité (CRITIQUE)

#### 1.1 Hash des mots de passe
```python
# Utiliser bcrypt
import bcrypt

# Création utilisateur
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Vérification login
if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
    # OK
```

#### 1.2 JWT Secret sécurisé
```python
# Générer un secret 256 bits
import secrets
JWT_SECRET = secrets.token_hex(32)  # À stocker dans .env
```

#### 1.3 HTTPS
```yaml
# nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/wibot.crt;
    ssl_certificate_key /etc/ssl/private/wibot.key;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

#### 1.4 Rate limiting
```python
# FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 tentatives/minute
async def login():
    ...
```

### Priorité 2 : Fonctionnalités

#### 2.1 Export de conversations
```python
@app.get("/conversations/{id}/export")
async def export_conversation(
    id: str,
    format: str = "pdf"  # pdf, md, json
):
    # Générer PDF avec messages + formatting
    ...
```

#### 2.2 Recherche dans conversations
```python
@app.get("/search")
async def search_messages(
    q: str,
    user_id: int
):
    # Full-text search PostgreSQL
    query = """
    SELECT * FROM messages
    WHERE user_id = %s
    AND to_tsvector('french', content) @@ plainto_tsquery('french', %s)
    """
```

#### 2.3 Partage de conversations
```sql
CREATE TABLE conversation_shares (
    share_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations,
    shared_by INTEGER REFERENCES users,
    shared_with INTEGER REFERENCES users,
    permission VARCHAR(20) DEFAULT 'read',  -- read, write
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Priorité 3 : Monitoring

#### 3.1 Logs structurés
```python
import logging
import json

logger = logging.getLogger("wibot")

logger.info("chat_request", extra={
    "user_id": user.id,
    "mode": "flash",
    "tokens": 150,
    "duration_ms": 1200
})
```

#### 3.2 Métriques Prometheus
```python
from prometheus_client import Counter, Histogram

chat_requests = Counter('wibot_chat_requests_total', 'Total chat requests')
chat_duration = Histogram('wibot_chat_duration_seconds', 'Chat request duration')

@chat_duration.time()
async def process_chat():
    chat_requests.inc()
    ...
```

#### 3.3 Health checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_postgres(),
        "qdrant": check_qdrant(),
        "mistral_api": check_mistral()
    }
```

### Priorité 4 : UX

#### 4.1 Websockets pour streaming
```python
# Réponse IA en temps réel
@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    async for chunk in mistral_stream():
        await websocket.send_text(chunk)
```

#### 4.2 Notifications
```python
# Système de notifications (quota proche, admin actions)
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    type VARCHAR(50),
    message TEXT,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📖 Guide d'utilisation

### Pour les utilisateurs

#### 1. Connexion
1. Ouvrir http://localhost:5173
2. Entrer identifiants
3. Cliquer "Se connecter"

**Identifiants par défaut :**
- Admin : `khora` / `test123`
- User : `test` / `test123`

#### 2. Créer une conversation
1. Cliquer sur "+ Nouvelle conversation"
2. Sélectionner le mode IA :
   - ⚡ **Flash** : Réponses rapides
   - 💻 **Code** : Programmation
   - 📝 **Rédaction** : Textes longs

#### 3. Envoyer un message
1. Taper le message dans la zone de texte
2. (Optionnel) Ajouter des fichiers (PDF, DOCX, TXT)
3. Appuyer sur Entrée ou cliquer "Envoyer"

#### 4. Utiliser le RAG
1. Joindre un fichier à un message
2. Le fichier est analysé automatiquement
3. Les messages suivants utilisent le contenu du fichier

#### 5. Gérer ses conversations
- **Renommer** : Cliquer sur le titre → Éditer
- **Supprimer** : Clic droit → Supprimer
- **Rechercher** : Barre de recherche (à venir)

#### 6. Vérifier son quota
- Indicateur dans la barre supérieure
- Affiche : `12 450 / 50 000 tokens`
- Reset le 1er de chaque mois

### Pour les administrateurs

#### 1. Accéder aux analytics
1. Menu latéral → "Supervision"
2. Voir :
   - Tokens utilisés globalement
   - Messages par jour
   - Modes utilisés
   - Top utilisateurs

#### 2. Gérer les utilisateurs
1. Menu → "Utilisateurs"
2. **Créer** : Cliquer "+ Nouvel utilisateur"
3. **Modifier** : Cliquer sur un utilisateur
4. **Supprimer** : Bouton "Supprimer"

#### 3. Éditer les workflows n8n
1. Accéder à http://localhost:5679
2. Modifier les workflows
3. Sauvegarder

⚠️ **Attention** : Modifications avancées, risque de casser le système

---

## 🔧 Maintenance et déploiement

### Démarrage

**Windows :**
```batch
start.bat
```

**Linux/Mac :**
```bash
chmod +x start.sh
./start.sh
```

**Manuel :**
```bash
# Backend
cd wibot-backend
docker-compose up -d

# Frontend
cd wibot-frontend
npm run dev
```

### Arrêt

```bash
cd wibot-backend
docker-compose down
```

### Backup PostgreSQL

```bash
# Backup complet
docker exec wibot-postgres pg_dump -U widip wibot > backup_$(date +%Y%m%d).sql

# Restauration
docker exec -i wibot-postgres psql -U widip wibot < backup_20260101.sql
```

### Logs

```bash
# Logs n8n
docker logs -f wibot-n8n

# Logs PostgreSQL
docker logs -f wibot-postgres

# Logs frontend
# Dans le terminal où tourne npm run dev
```

### Mise à jour

**Frontend :**
```bash
cd wibot-frontend
npm update
```

**Backend (n8n) :**
```bash
cd wibot-backend
docker-compose pull
docker-compose up -d
```

### Migration DB

```bash
# Appliquer une migration
docker exec -i wibot-postgres psql -U widip -d wibot < migrations/001_add_analytics_columns.sql
```

### Monitoring production

**Recommandations :**
- **Uptime monitoring** : UptimeRobot, Pingdom
- **Logs centralisés** : ELK Stack, Grafana Loki
- **Métriques** : Prometheus + Grafana
- **Alertes** : PagerDuty, Slack webhooks

### Checklist déploiement production

- [ ] HTTPS activé (certificat SSL)
- [ ] Mots de passe hashés (bcrypt)
- [ ] JWT secret généré (256 bits)
- [ ] Secrets dans .env (pas hardcodés)
- [ ] CORS restreint (pas `*`)
- [ ] Rate limiting activé
- [ ] Backups automatiques (quotidiens)
- [ ] Logs persistants
- [ ] Health checks configurés
- [ ] Monitoring actif
- [ ] Documentation à jour

---

## 📚 Ressources et contacts

### Documentation externe

- **FastAPI** : https://fastapi.tiangolo.com/
- **Mistral AI** : https://docs.mistral.ai/
- **Qdrant** : https://qdrant.tech/documentation/
- **n8n** : https://docs.n8n.io/
- **React** : https://react.dev/
- **PostgreSQL** : https://www.postgresql.org/docs/

### Fichiers clés du projet

| Fichier | Description |
|---------|-------------|
| `MIGRATION_N8N_TO_FASTAPI.md` | Doc migration vers FastAPI |
| `wibot-backend/init.sql` | Schéma DB initial |
| `wibot-backend/migrations/` | Migrations DB |
| `wibot-backend/workflows/` | Workflows n8n (JSON) |
| `wibot-frontend/src/` | Code source React |
| `docker-compose.yml` | Orchestration Docker |

### Commandes utiles

```bash
# Vérifier l'état des containers
docker ps

# Restart un service
docker restart wibot-n8n

# Accéder à PostgreSQL
docker exec -it wibot-postgres psql -U widip -d wibot

# Nettoyer les volumes Docker
docker-compose down -v

# Rebuild complet
docker-compose down
docker-compose up -d --build
```

---

## 📝 Changelog

### Version 1.0 (Janvier 2026)
- ✅ Authentification JWT
- ✅ Chat multi-modes (Flash, Code, Rédaction)
- ✅ RAG avec Qdrant
- ✅ Gestion conversations
- ✅ Quotas tokens mensuels
- ✅ Analytics admin
- ✅ CRUD utilisateurs admin
- ⚠️ **Sécurité** : Mots de passe en clair (à corriger)
- 🐛 **Fix** : Colonne `mode` ajoutée à `messages`
- 🐛 **Fix** : Requête Check Quota (LEFT JOIN)

---

## 🎯 Conclusion

WIBOT est un chatbot IA fonctionnel et modulaire, avec :
- ✅ Frontend React moderne
- ✅ Backend n8n (workflows) opérationnel
- ✅ Base PostgreSQL bien structurée
- ✅ RAG pour analyse de documents
- ✅ Gestion quotas et analytics

**Points d'attention :**
- ⚠️ Sécurité à renforcer (passwords, HTTPS)
- 🔄 Migration FastAPI recommandée (3-4 jours)
- 📈 Scalabilité limitée (n8n)

**Prochaines étapes :**
1. **Urgent** : Hash passwords (bcrypt)
2. **Court terme** : Migration FastAPI
3. **Moyen terme** : HTTPS, monitoring, backups
4. **Long terme** : Features avancées (export, partage, multi-langue)

---

**Document généré le :** 2 janvier 2026
**Par :** Claude Code
**Pour :** WIDIP - Projet WIBOT
