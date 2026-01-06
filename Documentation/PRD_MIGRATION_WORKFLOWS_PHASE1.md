# PRD - Migration Workflows n8n vers Python
## Phase 1 : SENTINEL, SUPPORT, ENRICHISSEUR, SAFEGUARD, Health Check

**Version:** 1.0
**Date:** 2026-01-06
**Auteur:** Migration Team
**Statut:** Draft - En attente validation

---

## Table des matières

1. [Vision & Objectifs](#1-vision--objectifs)
2. [Périmètre Phase 1](#2-périmètre-phase-1)
3. [Architecture Cible](#3-architecture-cible)
4. [Structure du Projet](#4-structure-du-projet)
5. [Spécifications par Workflow](#5-spécifications-par-workflow)
6. [Plan de Migration](#6-plan-de-migration)
7. [Stratégie de Tests](#7-stratégie-de-tests)
8. [Risques & Mitigations](#8-risques--mitigations)
9. [Critères de Succès](#9-critères-de-succès)
10. [Roadmap Détaillée](#10-roadmap-détaillée)

---

## 1. Vision & Objectifs

### 1.1 Contexte

WIDIP gère actuellement ~20,000 tickets/an pour 600+ établissements de santé. Le système repose sur :
- **6 workflows n8n** (~4,558 lignes JSON) pour l'orchestration
- **1 MCP Server Python** (déjà migré) avec 36+ outils
- **PostgreSQL + pgvector** pour le RAG
- **Redis** pour le cache et l'état partagé

### 1.2 Pourquoi migrer ?

| Problème n8n | Solution Python |
|--------------|-----------------|
| JSON difficile à versionner/diff | Code Python lisible, Git-friendly |
| Debugging visuel mais limité | Breakpoints, logs structurés, stack traces |
| Tests manuels uniquement | pytest, mocking, CI/CD |
| Dépendance à un outil tiers | Code 100% maîtrisé |
| Scalabilité limitée | Async natif, workers parallèles |
| Logs dispersés | Logs centralisés structurés |

### 1.3 Objectifs Phase 1

1. **Migrer 5 workflows** vers Python pur (SENTINEL, SUPPORT, ENRICHISSEUR, SAFEGUARD, Health Check)
2. **Conserver 100% des fonctionnalités** actuelles
3. **Améliorer l'observabilité** (logs structurés, métriques)
4. **Préparer l'intégration WIBOT** (Phase 2)
5. **Maintenir la compatibilité MCP** existante

### 1.4 Ce qui NE change PAS

- ❌ Le MCP Server (déjà en Python, reste inchangé)
- ❌ Le RAG workflow n8n (conservé par choix personnel)
- ❌ Le WIBOT (migration Phase 2 séparée)
- ❌ Les schémas de base de données
- ❌ Les APIs externes (GLPI, Observium, AD)

---

## 2. Périmètre Phase 1

### 2.1 Workflows à migrer

| Workflow | Complexité | Priorité | Dépendances |
|----------|------------|----------|-------------|
| **Health Check** | ⭐ Simple | P0 (premier) | Redis |
| **Redis Helper** | ⭐ Simple | P0 (premier) | Redis |
| **SAFEGUARD** | ⭐⭐⭐ Moyenne | P1 | PostgreSQL, Redis |
| **ENRICHISSEUR** | ⭐⭐ Simple | P2 | MCP, PostgreSQL |
| **SENTINEL** | ⭐⭐⭐⭐⭐ Complexe | P3 | MCP, Redis, GLPI |
| **SUPPORT** | ⭐⭐⭐⭐ Complexe | P4 | MCP, Redis, SAFEGUARD |

### 2.2 Ordre de migration recommandé

```
Phase 1.0 : Infrastructure
├── Health Check (circuit breaker)
├── Redis Helper (cache layer)
└── Tests d'intégration infra

Phase 1.1 : Sécurité
├── SAFEGUARD (approbations L3)
└── Tests validation humaine

Phase 1.2 : Enrichissement
├── ENRICHISSEUR (RAG auto)
└── Tests batch processing

Phase 1.3 : Agents IA
├── SENTINEL (détection incidents)
├── SUPPORT (traitement tickets)
└── Tests end-to-end
```

### 2.3 Hors périmètre Phase 1

- WIBOT (frontend React + backend n8n) → Phase 2
- RAG Ingestion workflow → conservé en n8n
- Migration des données existantes (non nécessaire)
- Changement d'infrastructure (Docker, PostgreSQL, Redis)

---

## 3. Architecture Cible

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      WIDIP PYTHON WORKFLOWS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Application                          │   │
│  │                        (Port 3002)                               │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  Endpoints:                      Scheduler (APScheduler):        │   │
│  │  ├─ POST /webhook/observium      ├─ SUPPORT: every 3min         │   │
│  │  ├─ POST /safeguard/request      ├─ ENRICHISSEUR: daily 18h     │   │
│  │  ├─ GET  /safeguard/approve/:id  └─ Health Check: every 30s     │   │
│  │  ├─ GET  /safeguard/pending                                      │   │
│  │  └─ GET  /health                                                 │   │
│  │                                                                  │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                           │
│  ┌──────────────────────────▼──────────────────────────────────────┐   │
│  │                    Workflow Engine                               │   │
│  │                                                                  │   │
│  │  workflows/                                                      │   │
│  │  ├── core/                    # Framework commun                 │   │
│  │  │   ├── base.py             # WorkflowBase class               │   │
│  │  │   ├── scheduler.py        # APScheduler wrapper              │   │
│  │  │   ├── context.py          # Execution context                │   │
│  │  │   └── events.py           # Event bus (pub/sub)              │   │
│  │  │                                                               │   │
│  │  ├── sentinel/               # Agent SENTINEL                   │   │
│  │  ├── support/                # Agent SUPPORT                    │   │
│  │  ├── enrichisseur/           # Batch ENRICHISSEUR               │   │
│  │  ├── safeguard/              # Validations L3                   │   │
│  │  └── health_check/           # Monitoring GLPI                  │   │
│  │                                                                  │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                           │
│  ┌──────────────────────────▼──────────────────────────────────────┐   │
│  │                    MCP Client Layer                              │   │
│  │                                                                  │   │
│  │  Appels HTTP vers MCP Server existant (port 3001)               │   │
│  │  ├─ glpi_* tools                                                 │   │
│  │  ├─ observium_* tools                                            │   │
│  │  ├─ ad_* tools                                                   │   │
│  │  ├─ memory_* tools                                               │   │
│  │  └─ notification_* tools                                         │   │
│  │                                                                  │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                           │
│  ┌──────────────────────────▼──────────────────────────────────────┐   │
│  │                    Data Layer                                    │   │
│  │                                                                  │   │
│  │  ├─ PostgreSQL (audit, approvals, incident_logs)                │   │
│  │  ├─ Redis (cache, state, health status)                         │   │
│  │  └─ Structured Logging (JSON → stdout)                          │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Communication avec le MCP Server existant

```python
# Le MCP Server reste sur le port 3001 (inchangé)
# Les workflows Python appellent le MCP via HTTP

class MCPClient:
    """Client pour appeler les outils MCP existants"""

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.api_key = settings.mcp_api_key

    async def call(self, tool_name: str, arguments: dict) -> dict:
        """Appelle un outil MCP"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/call",
                json={
                    "jsonrpc": "2.0",
                    "id": str(uuid4()),
                    "method": tool_name,
                    "params": {"name": tool_name, "arguments": arguments}
                },
                headers={"X-API-Key": self.api_key}
            )
            return response.json()["result"]
```

### 3.3 Cohabitation n8n / Python

Pendant la migration, les deux systèmes coexistent :

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (reverse   │
                    │   proxy)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   n8n       │ │   Python    │ │    MCP      │
    │  (legacy)   │ │  Workflows  │ │   Server    │
    │  Port 5678  │ │  Port 3002  │ │  Port 3001  │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    │   + Redis   │
                    └─────────────┘

Stratégie de bascule :
1. Déployer workflow Python en parallèle
2. Tester en shadow mode (logs only)
3. Basculer le trigger (désactiver n8n, activer Python)
4. Monitorer 24-48h
5. Supprimer workflow n8n si OK
```

---

## 4. Structure du Projet

### 4.1 Arborescence proposée

```
widip-mcp-server/                    # Projet existant
├── src/                             # MCP Server (INCHANGÉ)
│   ├── main.py
│   ├── config.py
│   ├── clients/
│   ├── tools/
│   ├── mcp/
│   └── utils/
│
├── workflows/                       # 🆕 NOUVEAU - Workflows Python
│   ├── __init__.py
│   │
│   ├── core/                        # Framework commun
│   │   ├── __init__.py
│   │   ├── base.py                  # WorkflowBase (classe abstraite)
│   │   ├── context.py               # WorkflowContext (état d'exécution)
│   │   ├── scheduler.py             # Wrapper APScheduler
│   │   ├── mcp_client.py            # Client HTTP vers MCP Server
│   │   ├── redis_client.py          # Client Redis async
│   │   ├── db.py                    # Client PostgreSQL async
│   │   ├── events.py                # Event bus interne
│   │   └── exceptions.py            # Exceptions personnalisées
│   │
│   ├── health_check/                # Workflow Health Check
│   │   ├── __init__.py
│   │   ├── workflow.py              # HealthCheckWorkflow
│   │   └── config.py                # Configuration spécifique
│   │
│   ├── safeguard/                   # Workflow SAFEGUARD
│   │   ├── __init__.py
│   │   ├── workflow.py              # SafeguardWorkflow
│   │   ├── handlers.py              # Approve/Reject handlers
│   │   ├── notifier.py              # Slack/Email notifications
│   │   └── config.py
│   │
│   ├── enrichisseur/                # Workflow ENRICHISSEUR
│   │   ├── __init__.py
│   │   ├── workflow.py              # EnrichisseurWorkflow
│   │   ├── extractor.py             # Knowledge extraction
│   │   └── config.py
│   │
│   ├── sentinel/                    # Workflow SENTINEL
│   │   ├── __init__.py
│   │   ├── workflow.py              # SentinelWorkflow
│   │   ├── agent.py                 # Agent IA (LangChain)
│   │   ├── analyzer.py              # Responsibility analyzer
│   │   ├── notifier.py              # Client notifications
│   │   └── config.py
│   │
│   └── support/                     # Workflow SUPPORT
│       ├── __init__.py
│       ├── workflow.py              # SupportWorkflow
│       ├── agent.py                 # Agent IA (LangChain)
│       ├── diag_parser.py           # Parser #DIAG codes
│       ├── ticket_processor.py      # Ticket actions
│       └── config.py
│
├── runner.py                        # 🆕 Point d'entrée workflows
├── tests/                           # 🆕 Tests
│   ├── conftest.py
│   ├── test_health_check.py
│   ├── test_safeguard.py
│   ├── test_enrichisseur.py
│   ├── test_sentinel.py
│   └── test_support.py
│
├── docker-compose.yml               # Mise à jour avec nouveau service
├── pyproject.toml                   # Dépendances mises à jour
└── README.md
```

### 4.2 Nouvelles dépendances

```toml
# pyproject.toml - Ajouts pour workflows

[project]
dependencies = [
    # Existant (MCP Server)
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "structlog>=24.1.0",

    # 🆕 Nouveau pour Workflows
    "apscheduler>=3.10.0",          # Scheduler (cron, interval)
    "langchain>=0.1.0",              # Agent IA orchestration
    "langchain-community>=0.0.10",   # Ollama integration
    "tenacity>=8.2.0",               # Retry logic
    "aiosmtplib>=3.0.0",             # Async SMTP
    "python-json-logger>=2.0.0",     # JSON logging
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "respx>=0.20.0",                 # Mock httpx requests
    "fakeredis>=2.20.0",             # Mock Redis
]
```

---

## 5. Spécifications par Workflow

### 5.1 Health Check

**Objectif :** Surveiller la disponibilité de GLPI et activer le circuit breaker

**Trigger :** Toutes les 30 secondes

**Flux :**
```
┌─────────────────────────────────────────────────────────────────┐
│                      HEALTH CHECK                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Every 30s                                                      │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Ping GLPI API                                           │   │
│  │ POST /apirest.php/initSession                           │   │
│  │ Timeout: 5000ms                                         │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │                         │                        │
│              ▼                         ▼                        │
│         SUCCESS                      FAILURE                    │
│              │                         │                        │
│              ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────────┐           │
│  │ Redis SET        │      │ Redis SET            │           │
│  │ glpi_health=ok   │      │ glpi_health=down     │           │
│  │ TTL: 60s         │      │ TTL: 60s             │           │
│  └────────┬─────────┘      └────────┬─────────────┘           │
│           │                         │                          │
│           ▼                         ▼                          │
│  ┌──────────────────┐      ┌──────────────────────┐           │
│  │ Was down before? │      │ Alert already sent?  │           │
│  │ (check flag)     │      │ (check flag)         │           │
│  └────────┬─────────┘      └────────┬─────────────┘           │
│           │                         │                          │
│      YES  │  NO                YES  │  NO                      │
│           ▼                         ▼                          │
│  ┌──────────────────┐      ┌──────────────────────┐           │
│  │ Send recovery    │      │ Send DOWN alert      │           │
│  │ alert to Slack   │      │ Set flag (TTL 5min)  │           │
│  └──────────────────┘      └──────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Code Python :**
```python
# workflows/health_check/workflow.py

class HealthCheckWorkflow(WorkflowBase):
    name = "health_check"
    interval_seconds = 30

    async def execute(self, ctx: WorkflowContext) -> dict:
        # 1. Ping GLPI
        try:
            status = await self._ping_glpi()
        except Exception:
            status = "down"

        # 2. Update Redis
        await self.redis.set("glpi_health_status", status, ex=60)

        # 3. Handle state transitions
        if status == "down":
            await self._handle_down()
        else:
            await self._handle_up()

        return {"status": status}
```

---

### 5.2 SAFEGUARD

**Objectif :** Gérer les demandes d'approbation humaine pour les actions L3

**Triggers :**
- `POST /safeguard/request` : Créer une demande
- `GET /safeguard/approve/:id` : Approuver
- `GET /safeguard/reject/:id` : Rejeter
- Cron toutes les heures : Cleanup expired

**Flux principal :**
```
┌─────────────────────────────────────────────────────────────────┐
│                      SAFEGUARD                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Agent requests L3 action (e.g., ad_reset_password)            │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ POST /safeguard/request                                 │   │
│  │ Body: { tool_name, arguments, context }                 │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Redact sensitive fields (password → [REDACTED])     │   │
│  │ 2. Encrypt secrets → Redis (TTL 1h)                    │   │
│  │ 3. Save request → PostgreSQL (status=pending)          │   │
│  │ 4. Generate approval_id                                 │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Notify technicians                                      │   │
│  │ • Slack: Rich message with [APPROVE] [REJECT] buttons  │   │
│  │ • Email: HTML with action links                        │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │                         │                        │
│              ▼                         ▼                        │
│     Tech clicks APPROVE       Tech clicks REJECT               │
│              │                         │                        │
│              ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────────┐           │
│  │ 1. Verify status │      │ 1. Update status     │           │
│  │ 2. Retrieve      │      │    = rejected        │           │
│  │    secrets       │      │ 2. Log rejection     │           │
│  │ 3. Execute tool  │      │ 3. Return HTML       │           │
│  │ 4. Log result    │      └──────────────────────┘           │
│  │ 5. Cleanup Redis │                                         │
│  └──────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tables PostgreSQL utilisées :**
```sql
-- Déjà existantes dans le MCP Server
safeguard_approvals (
    id UUID,
    tool_name VARCHAR(100),
    arguments JSONB,          -- REDACTED
    security_level VARCHAR(10),
    status VARCHAR(20),       -- pending/approved/rejected/expired
    expires_at TIMESTAMP,
    approver VARCHAR(100),
    ...
)

safeguard_audit_log (
    tool_name, action, approval_id, details, created_at
)
```

---

### 5.3 ENRICHISSEUR

**Objectif :** Extraire les connaissances des tickets résolus et enrichir le RAG

**Trigger :** Cron quotidien à 18h00

**Flux :**
```
┌─────────────────────────────────────────────────────────────────┐
│                      ENRICHISSEUR                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Daily 18h00                                                    │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MCP: glpi_get_resolved_tickets(hours=24, limit=50)     │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ For each ticket:                                        │   │
│  │                                                         │   │
│  │   1. Check if already in RAG (memory_check_exists)     │   │
│  │      └─ Skip if exists                                 │   │
│  │                                                         │   │
│  │   2. Calculate quality_score:                          │   │
│  │      • title_length: 15%                               │   │
│  │      • description_length: 20%                         │   │
│  │      • solution_length: 40%                            │   │
│  │      • has_category: 10%                               │   │
│  │      • has_tags: 15%                                   │   │
│  │      └─ Skip if score < 0.4                           │   │
│  │                                                         │   │
│  │   3. Extract knowledge:                                │   │
│  │      • problem_summary (from title + description)      │   │
│  │      • solution_summary (from resolution)              │   │
│  │      • category, tags                                  │   │
│  │                                                         │   │
│  │   4. Inject into RAG (memory_add_knowledge)            │   │
│  │      └─ Generates embedding via Ollama                 │   │
│  │                                                         │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Summary notification:                                   │   │
│  │ "✅ RAG enrichi: 12 nouvelles entrées, 38 déjà présentes"│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Calcul du quality_score :**
```python
def calculate_quality_score(ticket: dict) -> float:
    score = 0.0

    # Title (15%)
    title_len = len(ticket.get("title", ""))
    score += min(title_len / 50, 1.0) * 0.15

    # Description (20%)
    desc_len = len(ticket.get("description", ""))
    score += min(desc_len / 200, 1.0) * 0.20

    # Solution (40%) - le plus important
    solution = ticket.get("solution", "").lower()
    if solution in ["fait", "ok", "ras", "résolu", ""]:
        score += 0.0  # Pénalité pour solutions vides
    else:
        score += min(len(solution) / 300, 1.0) * 0.40

    # Category (10%)
    if ticket.get("category"):
        score += 0.10

    # Tags (15%)
    if ticket.get("tags"):
        score += 0.15

    return round(score, 2)
```

---

### 5.4 SENTINEL

**Objectif :** Détecter et analyser les incidents réseau depuis Observium

**Trigger :** Webhook `POST /webhook/observium`

**Flux complet :**
```
┌─────────────────────────────────────────────────────────────────┐
│                         SENTINEL                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /webhook/observium                                        │
│  Body: { device_name, ip_address, alert_type, message, ... }   │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Parse alert + Generate tracking_id                   │   │
│  │    ALT-{YEAR}-{TIMESTAMP}-{RANDOM}                      │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2. Pre-filters:                                         │   │
│  │    • Alert < 5 min old? (ignore stale)                 │   │
│  │    • Device in maintenance window?                      │   │
│  │    • Duplicate alert in last 20 min? (check Redis)     │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │                         │                        │
│           PASS                       SKIP                       │
│              │                         │                        │
│              ▼                         ▼                        │
│  ┌──────────────────┐          Log & Exit                      │
│  │ 3. Check Redis   │                                          │
│  │    cache for     │                                          │
│  │    diagnostic    │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│      ┌────┴────┐                                               │
│      │         │                                                │
│   CACHE HIT  MISS                                              │
│      │         │                                                │
│      ▼         ▼                                                │
│  ┌──────┐  ┌──────────────────────────────────────────────┐   │
│  │Reuse │  │ 4. Check GLPI health (Redis)                 │   │
│  │diag  │  │    └─ If DOWN → Degraded mode               │   │
│  └──┬───┘  └────────────────────┬─────────────────────────┘   │
│     │                           │                              │
│     │                           ▼                              │
│     │      ┌─────────────────────────────────────────────┐    │
│     │      │ 5. Run Agent_Sentinel (LangChain)           │    │
│     │      │    Timeout: 20 seconds                      │    │
│     │      │                                             │    │
│     │      │    Tools available:                         │    │
│     │      │    • observium_get_device_status            │    │
│     │      │    • observium_get_device_metrics           │    │
│     │      │    • observium_get_device_history           │    │
│     │      │    • memory_search_similar_cases            │    │
│     │      │    • glpi_search_client                     │    │
│     │      │                                             │    │
│     │      │    Output: {                                │    │
│     │      │      responsibility: widip|fai|local|?,     │    │
│     │      │      confidence: 0-100,                     │    │
│     │      │      diagnosis: "...",                      │    │
│     │      │      besoin_diagnostic_client: bool         │    │
│     │      │    }                                        │    │
│     │      └────────────────────┬────────────────────────┘    │
│     │                           │                              │
│     └───────────────────────────┤                              │
│                                 ▼                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 6. Cache diagnostic in Redis (TTL 20min)               │   │
│  │    Key: observium_diag_{device}_{date}                 │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 7. Run Agent_Notificateur                               │   │
│  │    • glpi_create_ticket (#DIAG if confidence < 80%)    │   │
│  │    • notify_client (if besoin_diagnostic_client)       │   │
│  │    • notify_technician                                  │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 8. Log to PostgreSQL (incident_logs)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Règles de responsabilité :**
```python
def determine_responsibility(diagnosis: dict) -> tuple[str, int]:
    """
    Retourne (responsibility, confidence)
    """
    # Équipement WIDIP (switch, serveur interne)
    if diagnosis.get("is_widip_equipment"):
        return "widip", 95

    # Tests client
    gw = diagnosis.get("gateway_status")
    internet = diagnosis.get("internet_status")
    dns = diagnosis.get("dns_status")

    if gw == "fail":
        return "local", 90  # Problème local chez le client

    if gw == "ok" and internet == "fail":
        return "fai", 85  # FAI responsable

    if gw == "ok" and internet == "ok" and dns == "fail":
        return "fai_dns", 75  # DNS FAI

    if gw == "ok" and internet == "ok" and dns == "ok":
        return "resolved", 80  # Plus de problème

    return "indetermine", 40  # Besoin diagnostic client
```

---

### 5.5 SUPPORT

**Objectif :** Traiter automatiquement les tickets à faible valeur ajoutée

**Trigger :** Cron toutes les 3 minutes

**Dual-branch architecture :**
```
┌─────────────────────────────────────────────────────────────────┐
│                         SUPPORT                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Every 3 minutes                                                │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Check GLPI health (Redis: glpi_health_status)          │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │                         │                        │
│           GLPI OK                   GLPI DOWN                   │
│              │                         │                        │
│              ▼                         ▼                        │
│  ┌──────────────────┐          Skip cycle                      │
│  │ Execute BOTH     │          Log "GLPI down"                 │
│  │ branches in      │          Retry in 3 min                  │
│  │ parallel         │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│     ┌─────┴─────┐                                              │
│     │           │                                               │
│     ▼           ▼                                               │
│ ┌───────────────────────────┐  ┌───────────────────────────┐   │
│ │   BRANCH A: Agent         │  │   BRANCH B: DIAG Parser   │   │
│ │                           │  │                           │   │
│ │ 1. Search new tickets     │  │ 1. Search followups with  │   │
│ │    (glpi_search_new)      │  │    #DIAG codes            │   │
│ │                           │  │                           │   │
│ │ 2. For each ticket:       │  │ 2. For each #DIAG:        │   │
│ │    • Categorize           │  │    • Parse gw/int/dns     │   │
│ │    • Run appropriate      │  │    • Apply rules          │   │
│ │      action               │  │    • Determine resp.      │   │
│ │                           │  │    • Add followup         │   │
│ │ Categories:               │  │                           │   │
│ │ • RESET_MDP               │  │ Output:                   │   │
│ │ • DEBLOCAGE_COMPTE        │  │ { ticket_id,              │   │
│ │ • #DIAG (wait human)      │  │   responsibility,         │   │
│ │ • AUTRE (escalate)        │  │   confidence,             │   │
│ │                           │  │   followup_sent }         │   │
│ └───────────┬───────────────┘  └───────────┬───────────────┘   │
│             │                              │                    │
│             └──────────────┬───────────────┘                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Aggregate results + Log to PostgreSQL                   │   │
│  │ (widip_agent_logs)                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Actions par catégorie :**

| Catégorie | Actions | SAFEGUARD |
|-----------|---------|-----------|
| RESET_MDP | ad_check_user → ad_reset_password → mysecret_create_secret → glpi_send_email → glpi_close_ticket | L3 (reset_password, close_ticket) |
| DEBLOCAGE_COMPTE | ad_check_user → ad_unlock_account → glpi_add_followup → glpi_close_ticket | L2 (unlock), L3 (close) |
| #DIAG | glpi_add_followup (privé) → notify_technician → WAIT | L1 |
| AUTRE | glpi_add_followup (privé) → escalate | L1 |

**Parser #DIAG :**
```python
import re

def parse_diag_code(followup_content: str) -> dict | None:
    """
    Parse: #DIAG gw=ok int=fail dns=ok ping=45ms
    """
    match = re.search(r'#DIAG\s+(.+)', followup_content)
    if not match:
        return None

    parts = match.group(1).split()
    result = {}

    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key.lower()] = value.lower()

    return result

# Exemple
parse_diag_code("#DIAG gw=ok int=fail dns=ok ping=45ms")
# → {'gw': 'ok', 'int': 'fail', 'dns': 'ok', 'ping': '45ms'}
```

---

## 6. Plan de Migration

### 6.1 Stratégie globale

```
┌─────────────────────────────────────────────────────────────────┐
│                   STRATÉGIE DE MIGRATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Phase 1.0: Infrastructure (1 semaine)                        │
│   ════════════════════════════════════                         │
│   □ Créer structure workflows/                                  │
│   □ Implémenter WorkflowBase + Context                         │
│   □ Configurer APScheduler                                      │
│   □ Créer MCPClient (appels HTTP)                              │
│   □ Migrer Health Check                                         │
│   □ Migrer Redis Helper (intégré dans core)                    │
│   □ Tests unitaires infra                                       │
│   □ Déploiement shadow mode                                     │
│                                                                 │
│   Phase 1.1: Sécurité (1 semaine)                              │
│   ════════════════════════════════                             │
│   □ Migrer SAFEGUARD workflow                                   │
│   □ Endpoints approve/reject                                    │
│   □ Notifications Slack/Email                                   │
│   □ Tests validation humaine                                    │
│   □ Déploiement + bascule                                       │
│                                                                 │
│   Phase 1.2: Enrichissement (1 semaine)                        │
│   ══════════════════════════════════                           │
│   □ Migrer ENRICHISSEUR                                         │
│   □ Quality score calculator                                    │
│   □ Batch processing optimisé                                   │
│   □ Tests + validation RAG                                      │
│   □ Déploiement + bascule                                       │
│                                                                 │
│   Phase 1.3: Agents IA (2 semaines)                            │
│   ══════════════════════════════                               │
│   □ Setup LangChain + Ollama                                    │
│   □ Migrer SENTINEL                                             │
│   │   □ Agent_Sentinel                                          │
│   │   □ Agent_Notificateur                                      │
│   │   □ Responsibility analyzer                                 │
│   □ Tests SENTINEL end-to-end                                   │
│   □ Migrer SUPPORT                                              │
│   │   □ Agent Support                                           │
│   │   □ DIAG Parser                                             │
│   │   □ Ticket processor                                        │
│   □ Tests SUPPORT end-to-end                                    │
│   □ Déploiement progressif                                      │
│   □ Monitoring 48h                                              │
│   □ Bascule définitive                                          │
│                                                                 │
│   Phase 1.4: Cleanup (1 semaine)                               │
│   ═════════════════════════════                                │
│   □ Supprimer workflows n8n migrés                              │
│   □ Documentation mise à jour                                   │
│   □ Optimisations performances                                  │
│   □ Monitoring long terme                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Procédure de bascule par workflow

```
Pour chaque workflow:

1. DÉVELOPPEMENT
   └─ Implémenter en Python
   └─ Tests unitaires (>80% coverage)
   └─ Tests d'intégration

2. SHADOW MODE (24-48h)
   └─ Déployer Python workflow
   └─ Garder n8n actif
   └─ Python log-only (pas d'actions réelles)
   └─ Comparer outputs n8n vs Python

3. VALIDATION
   └─ Vérifier 100% compatibilité
   └─ Corriger divergences
   └─ Re-test si corrections

4. BASCULE
   └─ Désactiver trigger n8n
   └─ Activer trigger Python
   └─ Monitoring intensif 24h

5. ROLLBACK (si problème)
   └─ Réactiver n8n
   └─ Désactiver Python
   └─ Analyser et corriger

6. CLEANUP (après 1 semaine stable)
   └─ Supprimer workflow n8n
   └─ Documenter changements
```

---

## 7. Stratégie de Tests

### 7.1 Niveaux de tests

```
┌─────────────────────────────────────────────────────────────────┐
│                    PYRAMIDE DE TESTS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                        ┌─────────┐                              │
│                        │   E2E   │  10%                         │
│                        │  Tests  │  (Selenium/Playwright)       │
│                       ─┴─────────┴─                             │
│                      ┌─────────────┐                            │
│                      │ Integration │  30%                       │
│                      │    Tests    │  (Docker, real services)   │
│                     ─┴─────────────┴─                           │
│                    ┌─────────────────┐                          │
│                    │   Unit Tests    │  60%                     │
│                    │ (pytest, mocks) │  (fast, isolated)        │
│                   ─┴─────────────────┴─                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Structure des tests

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_mcp_client():
    """Mock du client MCP"""
    client = AsyncMock()
    client.call.return_value = {"success": True}
    return client

@pytest.fixture
def mock_redis():
    """Mock Redis avec fakeredis"""
    import fakeredis.aioredis
    return fakeredis.aioredis.FakeRedis()

@pytest.fixture
async def test_db():
    """Base de test PostgreSQL"""
    # Setup test database
    yield db
    # Cleanup

# tests/test_health_check.py
@pytest.mark.asyncio
async def test_health_check_glpi_up(mock_redis, mock_mcp_client):
    """Test Health Check quand GLPI est UP"""
    mock_mcp_client.call.return_value = {"status": "ok"}

    workflow = HealthCheckWorkflow(mock_mcp_client, mock_redis)
    result = await workflow.execute(WorkflowContext())

    assert result["status"] == "ok"
    assert await mock_redis.get("glpi_health_status") == b"ok"

@pytest.mark.asyncio
async def test_health_check_glpi_down_sends_alert(mock_redis, mock_mcp_client):
    """Test Health Check envoie alerte quand GLPI DOWN"""
    mock_mcp_client.call.side_effect = TimeoutError()

    workflow = HealthCheckWorkflow(mock_mcp_client, mock_redis)
    result = await workflow.execute(WorkflowContext())

    assert result["status"] == "down"
    # Vérifier que l'alerte Slack a été envoyée
    mock_mcp_client.call.assert_any_call("notify_slack", {...})
```

### 7.3 Tests d'intégration

```python
# tests/integration/test_sentinel_integration.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_sentinel_full_flow():
    """Test complet SENTINEL avec vrais services (Docker)"""

    # 1. Simuler alerte Observium
    alert = {
        "device_name": "SWITCH-TEST-001",
        "ip_address": "10.0.0.1",
        "alert_type": "ping_down",
        "message": "Device unreachable"
    }

    # 2. Appeler le workflow
    workflow = SentinelWorkflow()
    result = await workflow.run(alert)

    # 3. Vérifier les résultats
    assert result["success"] is True
    assert result["ticket_id"] is not None
    assert result["responsibility"] in ["widip", "fai", "local", "indetermine"]

    # 4. Vérifier le cache Redis
    cached = await redis.get(f"observium_diag_switch-test-001_{today}")
    assert cached is not None

    # 5. Vérifier les logs PostgreSQL
    log = await db.fetch_one(
        "SELECT * FROM incident_logs WHERE tracking_id = $1",
        result["tracking_id"]
    )
    assert log is not None
```

---

## 8. Risques & Mitigations

### 8.1 Matrice des risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Régression fonctionnelle** | Moyenne | Élevé | Shadow mode + comparaison outputs |
| **Performance dégradée** | Faible | Moyen | Benchmarks avant/après |
| **Perte de données** | Faible | Critique | Backups, transactions ACID |
| **Downtime migration** | Moyenne | Élevé | Bascule progressive, rollback ready |
| **Incompatibilité MCP** | Faible | Moyen | Tests intégration continus |
| **Agent IA divergent** | Moyenne | Moyen | Prompts identiques, tests outputs |
| **Redis/PostgreSQL indispo** | Faible | Critique | Circuit breakers, retries |

### 8.2 Plan de rollback

```
SI problème critique détecté:

1. IMMÉDIAT (< 5 min)
   └─ Activer flag: WORKFLOW_LEGACY_MODE=true
   └─ Rediriger trafic vers n8n
   └─ Désactiver schedulers Python

2. ANALYSE (< 1h)
   └─ Collecter logs erreur
   └─ Identifier root cause
   └─ Documenter incident

3. CORRECTION (variable)
   └─ Fix en développement
   └─ Tests
   └─ Re-déploiement shadow mode

4. RE-BASCULE
   └─ Validation étendue
   └─ Bascule progressive
   └─ Monitoring renforcé
```

---

## 9. Critères de Succès

### 9.1 Critères fonctionnels

| Critère | Mesure | Cible |
|---------|--------|-------|
| Parité fonctionnelle | % features migrées | 100% |
| Tickets traités | Volume comparable | ±5% |
| Temps de réponse SENTINEL | p95 latency | < 25s |
| Temps de réponse SUPPORT | p95 latency | < 60s |
| Taux de succès | % exécutions OK | > 99% |
| Faux positifs SAFEGUARD | % blocages incorrects | < 1% |

### 9.2 Critères techniques

| Critère | Mesure | Cible |
|---------|--------|-------|
| Couverture tests | % code coverage | > 80% |
| Temps de déploiement | Minutes | < 5 |
| Temps de rollback | Minutes | < 2 |
| Logs structurés | % logs JSON | 100% |
| Métriques exposées | Prometheus endpoints | Oui |

### 9.3 Critères opérationnels

| Critère | Mesure | Cible |
|---------|--------|-------|
| Documentation | Pages à jour | 100% |
| Formation équipe | Personnes formées | 100% |
| Alerting configuré | Dashboards Grafana | Oui |
| Procédures incident | Runbooks | Oui |

---

## 10. Roadmap Détaillée

### 10.1 Vue calendaire

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP PHASE 1                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Semaine 1: Infrastructure                                              │
│  ─────────────────────────                                              │
│  Jour 1-2: Setup projet                                                 │
│    □ Créer structure workflows/                                         │
│    □ WorkflowBase, WorkflowContext                                      │
│    □ Configuration pyproject.toml                                       │
│                                                                         │
│  Jour 3-4: Core components                                              │
│    □ MCPClient (HTTP vers MCP Server)                                   │
│    □ RedisClient async                                                  │
│    □ DatabaseClient async                                               │
│    □ APScheduler setup                                                  │
│                                                                         │
│  Jour 5: Health Check + Redis                                           │
│    □ HealthCheckWorkflow                                                │
│    □ Tests unitaires                                                    │
│    □ Déploiement shadow mode                                            │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Semaine 2: SAFEGUARD                                                   │
│  ────────────────────                                                   │
│  Jour 1-2: Workflow core                                                │
│    □ SafeguardWorkflow                                                  │
│    □ Approval handlers                                                  │
│    □ Endpoints FastAPI                                                  │
│                                                                         │
│  Jour 3-4: Notifications                                                │
│    □ Slack notifier                                                     │
│    □ Email notifier                                                     │
│    □ Tests intégration                                                  │
│                                                                         │
│  Jour 5: Bascule                                                        │
│    □ Shadow mode validation                                             │
│    □ Bascule production                                                 │
│    □ Monitoring                                                         │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Semaine 3: ENRICHISSEUR                                                │
│  ───────────────────────                                                │
│  Jour 1-2: Workflow core                                                │
│    □ EnrichisseurWorkflow                                               │
│    □ Quality score calculator                                           │
│    □ Knowledge extractor                                                │
│                                                                         │
│  Jour 3-4: Tests & optimisation                                         │
│    □ Tests unitaires                                                    │
│    □ Tests batch processing                                             │
│    □ Optimisation performances                                          │
│                                                                         │
│  Jour 5: Bascule                                                        │
│    □ Shadow mode                                                        │
│    □ Bascule production                                                 │
│    □ Validation RAG                                                     │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Semaine 4-5: SENTINEL & SUPPORT                                        │
│  ───────────────────────────────                                        │
│  Jour 1-3: SENTINEL                                                     │
│    □ SentinelWorkflow                                                   │
│    □ Agent_Sentinel (LangChain)                                         │
│    □ Responsibility analyzer                                            │
│    □ Agent_Notificateur                                                 │
│                                                                         │
│  Jour 4-5: Tests SENTINEL                                               │
│    □ Tests unitaires                                                    │
│    □ Tests intégration                                                  │
│    □ Shadow mode                                                        │
│                                                                         │
│  Jour 6-8: SUPPORT                                                      │
│    □ SupportWorkflow                                                    │
│    □ Agent Support (LangChain)                                          │
│    □ DIAG Parser                                                        │
│    □ Ticket processor                                                   │
│                                                                         │
│  Jour 9-10: Tests SUPPORT                                               │
│    □ Tests unitaires                                                    │
│    □ Tests intégration                                                  │
│    □ Tests end-to-end                                                   │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Semaine 6: Stabilisation & Cleanup                                     │
│  ──────────────────────────────────                                     │
│  Jour 1-2: Bascule progressive                                          │
│    □ SENTINEL production                                                │
│    □ SUPPORT production                                                 │
│    □ Monitoring intensif                                                │
│                                                                         │
│  Jour 3-4: Stabilisation                                                │
│    □ Corrections bugs                                                   │
│    □ Optimisations                                                      │
│    □ Documentation                                                      │
│                                                                         │
│  Jour 5: Cleanup                                                        │
│    □ Suppression workflows n8n                                          │
│    □ Documentation finale                                               │
│    □ Formation équipe                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Livrables par phase

| Phase | Livrables |
|-------|-----------|
| 1.0 Infrastructure | `workflows/core/*`, Health Check fonctionnel |
| 1.1 Sécurité | SAFEGUARD Python, endpoints approval |
| 1.2 Enrichissement | ENRICHISSEUR Python, batch optimisé |
| 1.3 Agents IA | SENTINEL + SUPPORT Python, agents LangChain |
| 1.4 Cleanup | n8n supprimé, documentation, formation |

---

## Annexes

### A. Mapping n8n → Python

| Concept n8n | Équivalent Python |
|-------------|-------------------|
| Webhook Trigger | FastAPI route handler |
| Cron Trigger | APScheduler job |
| Execute Workflow | Function call |
| Switch Node | if/elif/else ou match/case |
| IF Node | Conditional |
| Code Node (JS) | Python function |
| Redis Node | redis-py async |
| HTTP Request | httpx async |
| Agent Node | LangChain ReAct agent |
| PostgreSQL Node | asyncpg |

### B. Variables d'environnement

```bash
# Workflows Python
WORKFLOWS_ENABLED=true
WORKFLOWS_PORT=3002
WORKFLOWS_LOG_LEVEL=INFO
WORKFLOWS_LOG_FORMAT=json

# Scheduler
SCHEDULER_HEALTH_CHECK_INTERVAL=30
SCHEDULER_SUPPORT_INTERVAL=180
SCHEDULER_ENRICHISSEUR_HOUR=18

# MCP Client
MCP_SERVER_URL=http://localhost:3001
MCP_API_KEY=your-api-key

# Redis
REDIS_URL=redis://localhost:6379

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/widip

# LangChain / Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.example.com
```

### C. Commandes utiles

```bash
# Démarrer les workflows
python -m workflows.runner

# Tests
pytest tests/ -v --cov=workflows

# Linting
ruff check workflows/
mypy workflows/

# Logs
tail -f /var/log/widip-workflows/app.log | jq .

# Shadow mode
WORKFLOWS_SHADOW_MODE=true python -m workflows.runner
```

---

**Document rédigé le 2026-01-06**
**Version 1.0 - En attente validation**
