# WIDIP_Enrichisseur_v1
## Cercle Vertueux - Enrichissement Automatique Base RAG

> **Version** : 1.0 | **Type** : Workflow Automatisé | **Trigger** : Cron quotidien 18h00

---

## 🎯 Rôle

Workflow automatisé qui enrichit quotidiennement la base de connaissances RAG en extrayant les solutions des tickets GLPI résolus. Il crée un cercle vertueux d'apprentissage : plus il y a de tickets résolus, meilleure devient l'IA.

**Positionnement** : Moteur d'amélioration continue du système WIDIP, augmente l'autonomie des agents.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[Cron 18h00] → Trigger quotidien
    ↓
[MCP: enrichisseur_run_batch]
    ├→ Récupère tickets résolus 24h (GLPI)
    ├→ Filtre déjà présents (PostgreSQL)
    ├→ Extrait problème/solution
    ├→ Génère embeddings (Ollama)
    └→ Insère dans pgvector
    ↓
[Analyze Results]
    ├→ Calcul taux succès
    └→ Détecte anomalies
    ↓
[Should Notify ?]
    ├─ OUI → Notification Teams (résumé)
    └─ NON → Silent (rien à signaler)
    ↓
[Get RAG Stats] (métriques globales)
    ↓
[Final Log] (traçabilité)
```

### Flux d'enrichissement (MCP Tool)

Le MCP Tool `enrichisseur_run_batch` effectue :

1. **Récupération** : `glpi_get_resolved_tickets(hours_since=24)`
2. **Déduplication** : `memory_check_exists(ticket_id)` pour chaque ticket
3. **Extraction** : Analyse titre + description + solution
4. **Quality Score** : Calcule score 0-1 (filtre solutions vides)
5. **Embeddings** : Génère vecteur 768D avec Ollama
6. **Insertion** : INSERT dans `knowledge_base` avec quality_score

---

## 🔄 Exemple Concret

### Cas standard : Enrichissement de 8 nouveaux tickets

**Contexte** :
```
Date: 24/12/2025 18:00
Tickets résolus hier: 15 tickets
Déjà dans RAG: 7 tickets (déjà traités auparavant)
Nouveaux à traiter: 8 tickets
```

**Exécution** :
```
1. [18:00:00] Cron trigger → Lance workflow
2. [18:00:01] POST MCP Server:
   {
     "tool": "enrichisseur_run_batch",
     "arguments": {
       "hours_since": 24,
       "max_tickets": 50,
       "dry_run": false
     }
   }

3. [18:00:02] MCP Tool commence:
   → glpi_get_resolved_tickets(24h) → 15 tickets trouvés

4. [18:00:05] Déduplication:
   → memory_check_exists() pour chaque ticket
   → 7 déjà présents, 8 nouveaux

5. [18:00:06-18:01:30] Traitement des 8 tickets:

   Ticket #1234 "Imprimante bloquée":
   → Extraction: problème="Imprimante HP bourrage papier"
                 solution="Reset capteur + nettoyage rouleaux"
   → Quality score: 0.85 (solution complète)
   → Ollama embedding: vector[768] généré
   → INSERT knowledge_base

   Ticket #1235 "Mot de passe oublié":
   → Extraction: problème="Utilisateur bloqué après 3 tentatives"
                 solution="Fait"
   → Quality score: 0.25 (solution vide)
   → SKIPPED (< threshold 0.4)

   [... 6 autres tickets ...]

   Résultat final:
   - 8 traités
   - 6 injectés (quality_score >= 0.4)
   - 2 filtrés (solutions vides)

6. [18:01:31] MCP retourne:
   {
     "success": true,
     "tickets_found": 15,
     "tickets_already_in_rag": 7,
     "tickets_processed": 8,
     "tickets_injected": 6,
     "tickets_failed": 0
   }

7. [18:01:32] Analyze Results:
   → Success rate: 75% (6/8)
   → should_notify: true (nouveaux ajoutés)

8. [18:01:33] Notification Teams:
   "✅ Enrichissement RAG terminé
   📊 15 tickets trouvés
   🔄 7 déjà dans le RAG
   ✨ 6 nouveaux ajoutés
   ❌ 0 échecs"

9. [18:01:34] Get RAG Stats:
   {
     "total_entries": 1247,
     "added_last_24h": 6,
     "added_last_7d": 42,
     "top_categories": ["Matériel", "Réseau", "Comptes"]
   }

10. [18:01:35] Final Log → Console
```

**Résultat** : 6 nouveaux cas ajoutés au RAG, disponibles pour les agents dès maintenant.

---

### Cas exceptionnel : Journée sans résolution

**Contexte** :
```
Week-end, aucun technicien, tickets en attente.
Tickets résolus 24h: 0
```

**Exécution** :
```
1. [18:00:00] Cron trigger
2. [18:00:02] MCP Tool:
   → glpi_get_resolved_tickets(24h) → 0 tickets
   → Retourne immédiatement

3. [18:00:03] Analyze Results:
   → should_notify: false (rien à signaler)

4. [18:00:04] No Notification Needed
5. [18:00:05] Get RAG Stats (statistiques globales)
6. [18:00:06] Final Log
```

**Résultat** : Workflow terminé silencieusement, pas de notification inutile.

---

## 🔗 Dépendances

### MCP Tools (via widip-mcp-server)

| Tool | Niveau SAFEGUARD | Usage |
|------|------------------|-------|
| `enrichisseur_run_batch` | L1 (Minor) | Batch enrichissement |
| `glpi_get_resolved_tickets` | L0 (Read) | Source tickets résolus |
| `memory_check_exists` | L0 (Read) | Déduplication |
| `memory_add_knowledge` | L1 (Minor) | Insertion RAG |
| `enrichisseur_get_stats` | L0 (Read) | Statistiques RAG |
| `notify_technician` | L1 (Minor) | Notification Teams |

### Workflows liés

- **WIDIP_Assist_ticket_v6.1** : Consomme les données RAG enrichies
- **WIDIP_Proactif_Observium_v9** : Consomme les données RAG enrichies

### Services externes

- **GLPI API** : Source tickets résolus
- **PostgreSQL + pgvector** : Base RAG (table `knowledge_base`)
- **Ollama (nomic-embed-text)** : Génération embeddings 768D
- **Teams Webhook** : Notifications quotidiennes

---

## ⚙️ Configuration

### Variables d'environnement

```bash
MCP_SERVER_URL=http://mcp-server:3001
MCP_API_KEY=***
GLPI_URL=https://glpi.example.com/apirest.php
POSTGRES_DSN=postgresql://widip:***@postgres:5432/widip_knowledge
OLLAMA_URL=http://ollama:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
RAG_QUALITY_THRESHOLD=0.4
```

### Paramètres clés

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Schedule | `0 18 * * *` | Tous les jours 18h00 UTC |
| Lookback | 24h | Fenêtre tickets résolus |
| Max batch | 50 | Limite par exécution |
| Quality threshold | 0.4 | Seuil quality_score (40%) |
| Dry run | false | Mode test (sans insertion) |
| Timeout | 120s | Timeout MCP Tool |

---

## 📊 Métriques

Le workflow track automatiquement :
- Nombre tickets trouvés vs déjà présents
- Taux d'injection (tickets_injected / tickets_processed)
- Tickets filtrés (quality_score < 0.4)
- Durée exécution totale
- Croissance RAG (entries 24h, 7d, total)

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Automatisation totale** : Aucune intervention manuelle
- **Quality Score v15.2** : Filtre solutions vides ("Fait", "OK")
- **Déduplication** : Évite doublons dans RAG
- **Notifications intelligentes** : Alerte uniquement si utile
- **Traçabilité** : Logs détaillés dans console n8n

### ⚠️ Points d'attention
- **Dépendance Ollama** : Si Ollama down, enrichissement échoue
- **Qualité tickets GLPI** : Solutions mal renseignées = peu d'enrichissement
- **Seuil quality_score** : Peut nécessiter ajustement selon usage
- **Catégories exclues** : Tickets "test", "demo" ignorés

---

## 💡 Cercle Vertueux

Le workflow crée un cercle d'amélioration continue :

```
Jour 1:  100 tickets dans RAG → IA répond à 50% des demandes
         ↓ Enrichissement quotidien
Jour 30: 250 tickets dans RAG → IA répond à 70% des demandes
         ↓ Enrichissement quotidien
Jour 90: 450 tickets dans RAG → IA répond à 85% des demandes
```

**Résultat** : Plus le système est utilisé, plus il devient autonome.

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Enrichisseur_v1.json`
- **MCP Tool** : `widip-mcp-server/src/tools/enrichisseur_tools.py`
- **RAG Tools** : `widip-mcp-server/src/tools/memory_tools.py`
- **Migration SQL** : `widip-mcp-server/migrations/001_add_quality_score.sql`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 1.0
