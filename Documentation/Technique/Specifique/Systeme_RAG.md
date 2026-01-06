# Système RAG v15.3
## Retrieval Augmented Generation - Base de Connaissances Vectorielle

> **Version** : 15.3 (Quality Score) | **Type** : PostgreSQL + pgvector | **Embeddings** : Ollama (768D)

---

## 🎯 Vision

Le système RAG (Retrieval Augmented Generation) est la mémoire collective de WIDIP. Il stocke tous les tickets résolus sous forme de vecteurs, permettant aux agents IA de retrouver des solutions similaires pour les nouveaux tickets.

**Principe** : "Apprendre du passé pour résoudre le futur"

---

## 📊 Architecture

```
[Nouveau Ticket GLPI]
    ↓
[Agent IA] → Cherche solution
    ↓
[memory_search_similar_cases("Imprimante bloquée")]
    ↓
[Ollama] → Génère embedding query (vector[768])
    ↓
[PostgreSQL + pgvector]
    SELECT *,
           embedding <-> query_embedding as similarity
    FROM knowledge_base
    WHERE quality_score >= 0.4
    ORDER BY similarity ASC
    LIMIT 3
    ↓
[Résultats] 3 cas similaires:
    1. Sim: 0.87 - "Imprimante HP bourrage capteur" → Reset
    2. Sim: 0.76 - "Erreur faux bourrage papier" → Nettoyage rouleaux
    3. Sim: 0.65 - "Imprimante bloquée en erreur" → Redémarrage
    ↓
[Claude] → Génère solution adaptée
    ↓
[Réponse au client]
```

---

## 🗄️ Schéma Base de Données

### Table `knowledge_base`

```sql
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    problem_summary TEXT NOT NULL,
    solution_summary TEXT NOT NULL,
    ticket_title TEXT,
    ticket_category VARCHAR(255),
    resolution_time_minutes INTEGER,
    quality_score FLOAT DEFAULT 0.5,  -- v15.2: Nouveau
    embedding vector(768) NOT NULL,    -- pgvector
    source VARCHAR(50) DEFAULT 'glpi',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index vectoriel (IVFFlat)
CREATE INDEX knowledge_embedding_idx
ON knowledge_base
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index quality score
CREATE INDEX knowledge_quality_idx
ON knowledge_base (quality_score DESC);
```

---

## 🔄 Flux Enrichissement (Cercle Vertueux)

### Quotidien 18h00 - WIDIP_Enrichisseur_v1

```
[18:00] Cron trigger
    ↓
[GLPI] glpi_get_resolved_tickets(hours_since=24)
    → Retourne 15 tickets résolus
    ↓
[Déduplication]
    FOR each ticket:
        memory_check_exists(ticket_id) ?
            → 7 déjà présents → SKIP
            → 8 nouveaux → PROCESS
    ↓
[Extraction] Pour chaque ticket nouveau:
    problem_summary = ticket.title + ticket.description
    solution_summary = ticket.solution
    ↓
[Quality Score v15.2] Calcul 0-1:
    - Longueur solution > 10 chars → +0.2
    - Contient pas "fait", "ok", "résolu" → +0.2
    - Contient mots techniques → +0.3
    - Description détaillée → +0.3

    Exemple:
    - "Fait" → 0.1 (filtré)
    - "Reset de l'imprimante" → 0.4 (limite)
    - "Reset capteur HP via menu maintenance" → 0.85 (excellent)
    ↓
[Filter] quality_score >= 0.4 ?
    → 6 tickets passent le filtre
    → 2 tickets rejetés (solutions vides)
    ↓
[Embeddings] Pour les 6 tickets:
    Ollama embedding(problem_summary)
    → vector[768] float32
    ↓
[INSERT PostgreSQL]
    INSERT INTO knowledge_base (
        ticket_id,
        problem_summary,
        solution_summary,
        quality_score,
        embedding
    ) VALUES (...);
    ↓
[Résultat] +6 nouvelles connaissances dans le RAG
```

---

## 🔍 Recherche Similarité

### Algorithme pgvector

```sql
-- Recherche par cosine similarity
SELECT
    ticket_id,
    problem_summary,
    solution_summary,
    quality_score,
    1 - (embedding <-> $query_embedding) as similarity
FROM knowledge_base
WHERE quality_score >= 0.4
ORDER BY embedding <-> $query_embedding ASC
LIMIT 3;
```

**Paramètres** :
- **Seuil similarité** : 0.6 (60%)
- **Max résultats** : 3
- **Quality threshold** : 0.4 (40%)

---

## 📊 Métriques Clés

### Stats Temps Réel

```python
enrichisseur_get_stats()
# {
#   "total_entries": 1247,
#   "added_last_24h": 6,
#   "added_last_7d": 42,
#   "avg_quality_score": 0.67,
#   "top_categories": [
#     {"category": "Matériel", "count": 324},
#     {"category": "Réseau", "count": 198},
#     {"category": "Comptes", "count": 156}
#   ]
# }
```

### Croissance Typique

```
Jour 1:   100 tickets → 50% autonomie IA
Jour 30:  250 tickets → 70% autonomie IA
Jour 90:  450 tickets → 85% autonomie IA
Jour 180: 800 tickets → 90% autonomie IA
```

---

## 🛠️ Configuration

### Ollama (Embeddings)

```bash
# Modèle recommandé v15.3
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_EMBED_DIMENSIONS=768

# Alternative (meilleure qualité, plus lent)
# OLLAMA_EMBED_MODEL=intfloat/multilingual-e5-large
# OLLAMA_EMBED_DIMENSIONS=1024
```

### PostgreSQL + pgvector

```bash
# Extension requise
CREATE EXTENSION vector;

# Configuration recommandée
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 1GB
```

### Paramètres RAG

```bash
RAG_MIN_SIMILARITY=0.6      # Seuil pertinence
RAG_MAX_RESULTS=3           # Nombre résultats
RAG_QUALITY_THRESHOLD=0.4   # Filtre quality score (v15.2)
```

---

## 🚀 Workflows Utilisant le RAG

| Workflow | Usage RAG |
|----------|-----------|
| **WIDIP_Assist_ticket_v6.1** | Recherche solutions pour tickets support |
| **WIDIP_Proactif_Observium_v9** | Recherche incidents réseau similaires |
| **WIDIP_Enrichisseur_v1** | Alimentation quotidienne base |

---

## 🔧 Maintenance

### Recalcul Quality Score (si migration v15.2)

```sql
-- Recalculer pour anciennes entrées (sans quality_score)
UPDATE knowledge_base
SET quality_score = calculate_quality_score(solution_summary)
WHERE quality_score IS NULL OR quality_score = 0.5;
```

### Vacuum Régulier

```sql
-- Toutes les semaines
VACUUM ANALYZE knowledge_base;

-- Mensuel (complet)
VACUUM FULL knowledge_base;
```

---

## 📚 Fichiers Liés

- **MCP Tools** : `widip-mcp-server/src/tools/memory_tools.py`
- **Enrichisseur Tools** : `widip-mcp-server/src/tools/enrichisseur_tools.py`
- **Migration SQL** : `widip-mcp-server/migrations/001_add_quality_score.sql`
- **Workflow Enrichissement** : `Workflow principaux/WIDIP_Enrichisseur_v1.json`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 15.3 (Quality Score)
