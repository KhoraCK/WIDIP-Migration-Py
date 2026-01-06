# WIDIP_Proactif_Observium_v9
## Agent Proactif - Surveillance Réseau et Diagnostic Automatisé

> **Version** : 9.1 | **Type** : Agent IA Principal | **Trigger** : Webhook (alertes Observium)

---

## 🎯 Rôle

Agent IA qui réagit aux alertes réseau Observium en temps réel. Il analyse automatiquement l'incident, détermine la responsabilité (WIDIP vs FAI vs Client), crée un ticket GLPI et notifie le client avec les actions appropriées.

**Positionnement** : Système proactif WIDIP, détecte et traite les pannes avant que le client n'appelle.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[Observium] → Webhook HTTP
    ↓
[Parse + Tracking ID]
    ↓
[Pre-Filter] (micro-coupures, maintenance)
    ↓ Valide
[Cache Redis] (diag < 20min ?)
    ├─ HIT → Réutilise diagnostic
    └─ MISS → Analyse complète
         ↓
    [GLPI Health Check]
         ↓
    [Agent SENTINEL v9] (Observium + RAG)
         ↓
    [Détermine responsabilité + confiance]
         ↓
    [Besoin outil client ?]
    ├─ OUI (confiance < 80%) → Email outil diagnostic
    └─ NON (confiance >= 80%) → Email standard
         ↓
    [Agent NOTIFICATEUR v9]
         ↓
    [Crée ticket + Envoie email]
         ↓
    [Log metrics PostgreSQL]
```

### Architecture bi-agent

Le workflow utilise **2 agents IA spécialisés** :

#### **AGENT SENTINEL v9** (Diagnostic réseau)
1. Recherche client dans GLPI
2. Interroge base RAG (cas similaires)
3. Analyse état Observium (device, ports, metrics)
4. Calcule **responsabilité + niveau de confiance** (0-100%)
5. Détermine si besoin outil diagnostic client

#### **AGENT NOTIFICATEUR v9** (Actions)
1. Crée ticket GLPI adapté
2. Envoie email client (outil ou standard)
3. Log toutes les actions
4. Track métriques de performance

---

## 🔄 Exemple Concret

### Cas 1 : Switch client DOWN - Confiance moyenne

**Entrée** : Alerte Observium
```
Device: SW-EHPAD-PARIS-12
IP: 10.50.12.1
Type: ping_down
Status: critical
Downtime: 15 minutes
```

**Traitement** :
```
1. [100ms] Webhook reçoit alerte → Tracking ID: ALT-2025-1735041234-A3F9X2
2. [50ms]  Pre-filter: downtime > 5min → PASS
3. [200ms] Redis cache check → MISS (première fois)
4. [100ms] GLPI Health → OK
5. [15s]   Agent SENTINEL v9:
   → glpi_search_client("EHPAD-PARIS-12") → Client trouvé
   → memory_search_similar_cases("switch down") → 2 cas passés
   → observium_get_device_status() → Device DOWN
   → observium_get_device_metrics() → Tous les ports DOWN

   ANALYSE: Tous ports down = probable coupure FAI ou alim locale

   OUTPUT:
   {
     "responsibility": "fai_probable",
     "confidence": 65,
     "besoin_diagnostic_client": true,
     "diagnosis": "Switch complètement injoignable, tous ports affectés",
     "reasoning": "Panne totale device suggère FAI ou électrique local"
   }

6. [2s]   Confiance 65% < 80% → Prépare email outil diagnostic
7. [10s]  Agent NOTIFICATEUR v9:
   → glpi_create_ticket(urgence: high, catégorie: réseau)
   → glpi_send_email(template: diagnostic_tool_request)

   Ticket #5432 créé, email envoyé avec instructions outil

8. [100ms] Redis: Cache diagnostic (TTL 20min)
9. [50ms]  Log PostgreSQL: Success, 28s total
```

**Résultat** : Client notifié en **<30s**, outil diagnostic demandé, ticket créé.

---

### Cas 2 : Équipement WIDIP DOWN - Haute confiance

**Entrée** : Alerte Observium
```
Device: RTR-WIDIP-CORE-01
IP: 192.168.1.1
Type: device_down
Status: critical
Downtime: 2 minutes
```

**Traitement** :
```
1. [100ms] Webhook + Tracking ID: ALT-2025-1735041456-B7K2P9
2. [50ms]  Pre-filter → PASS
3. [200ms] Redis cache → MISS
4. [12s]   Agent SENTINEL v9:
   → glpi_search_client("WIDIP-CORE") → Infrastructure WIDIP
   → observium_get_device_status() → Routeur principal DOWN

   ANALYSE: Équipement WIDIP managé = responsabilité WIDIP certaine

   OUTPUT:
   {
     "responsibility": "widip",
     "confidence": 95,
     "besoin_diagnostic_client": false,
     "diagnosis": "Routeur cœur WIDIP injoignable",
     "severity": "critical",
     "recommended_action": "Intervention immédiate équipe WIDIP"
   }

5. [8s]   Agent NOTIFICATEUR v9:
   → glpi_create_ticket(urgence: critical, assign: tech_senior)
   → glpi_send_email(template: widip_fault)

   Email: "Panne de notre infrastructure, notre équipe intervient"

6. [100ms] Log: Success, 21s total
```

**Résultat** : Client informé de l'intervention WIDIP, pas d'action demandée au client.

---

## 🔗 Dépendances

### MCP Tools (via widip-mcp-server)

| Tool | Niveau SAFEGUARD | Usage |
|------|------------------|-------|
| `observium_get_device_status` | L0 (Read) | État device |
| `observium_get_device_metrics` | L0 (Read) | Ports, trafic |
| `observium_get_device_history` | L0 (Read) | Historique 24h |
| `glpi_search_client` | L0 (Read) | Identifie client |
| `glpi_create_ticket` | L1 (Minor) | Crée ticket |
| `glpi_send_email` | L1 (Minor) | Email client |
| `memory_search_similar_cases` | L0 (Read) | Recherche RAG |

### Workflows appelés

- **WIDIP_Redis_Helper_v2.2** : Cache + Health checks

### Services externes

- **Observium** : Source alertes réseau (webhook push)
- **GLPI API** : Création tickets + emails
- **PostgreSQL + pgvector** : Base RAG + logs
- **Redis** : Cache diagnostics (TTL 20min)
- **Ollama (Q3C30b)** : LLM local agents IA

---

## ⚙️ Configuration

### Variables d'environnement

```bash
OBSERVIUM_URL=https://observium.example.com/api/v0
OBSERVIUM_USER=api_user
OBSERVIUM_PASS=***
GLPI_URL=https://glpi.example.com/apirest.php
REDIS_URL=redis://redis:6379/0
POSTGRES_DSN=postgresql://user:pass@host/widip_knowledge
```

### Paramètres clés

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Webhook path | `/widip-alertes` | URL endpoint Observium |
| Pre-filter downtime | 5 min | Ignore micro-coupures |
| Cache TTL | 20 min | Durée cache diagnostic |
| Sentinel timeout | 20s | Timeout agent analyse |
| Notificateur timeout | 15s | Timeout agent actions |
| Confidence seuil | 80% | Seuil outil client |

---

## 📊 Métriques

Le workflow track automatiquement :
- Durée SENTINEL (analyse réseau)
- Durée NOTIFICATEUR (actions)
- Durée totale workflow (cible < 60s)
- Cache hit rate (réutilisation diagnostics)
- Taux de confiance moyen
- Taux demande outil client

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Réactivité extrême** : <30s entre alerte et notification client
- **Analyse intelligente** : Confiance 0-100% honnête
- **Cache performant** : Évite re-diagnostics inutiles
- **Tri automatique** : Filtre micro-coupures et maintenance
- **Human-in-the-Loop** : Demande outil client si incertain

### ⚠️ Points d'attention
- **Pas d'API Phibee** : Analyse Observium seule (v9), confiance limitée
- **Qualité diagnostic** : Dépend richesse données Observium
- **Outil client** : Nécessite coopération utilisateur final
- **LLM local** : Performance dépend ressources serveur

---

## 🔄 Nouveautés v9

### Retraits vs v8
- ❌ MCP Phibee Telecom (pas d'API disponible)
- ❌ MCP SMTP (remplacé par GLPI send_email)

### Ajouts v9
- ✅ Système de confiance (0-100%)
- ✅ Détection besoin outil diagnostic client
- ✅ Email automatique avec instructions outil
- ✅ Routage intelligent selon confiance
- ✅ Analyse Observium seule

### Améliorations v9.1
- ✅ Suppression MUTEX (API gère concurrence)
- ✅ Parallélisme illimité
- ✅ Workflow 20% plus rapide

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Proactif_Observium_v9.json`
- **MCP Tools** : `widip-mcp-server/src/tools/observium_tools.py`
- **RAG** : `widip-mcp-server/src/tools/memory_tools.py`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 9.1
