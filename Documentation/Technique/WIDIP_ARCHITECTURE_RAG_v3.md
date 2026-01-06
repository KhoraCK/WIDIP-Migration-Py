# WIDIP RAG Architecture V3
## Système Intelligent Auto-Apprenant pour le Support IT Médico-Social

> **Version** : 3.0  
> **Date** : 18 Décembre 2025  
> **Évolution** : V1.1 (concept) → V3 (implémentation complète avec fichiers Word)  
> **Philosophie** : RAG auto-enrichissant qui rend les agents de plus en plus autonomes

---

## Table des matières

1. [Vision et Philosophie](#1-vision-et-philosophie)
2. [Architecture Globale](#2-architecture-globale)
3. [Sources de Données](#3-sources-de-données)
4. [Structure du RAG](#4-structure-du-rag)
5. [L'Agent ENRICHISSEUR](#5-lagent-enrichisseur)
6. [Le Cercle Vertueux](#6-le-cercle-vertueux)
7. [Intégration avec les Agents](#7-intégration-avec-les-agents)
8. [Complémentarité RAG + MCP GLPI](#8-complémentarité-rag--mcp-glpi)
9. [Outils MCP](#9-outils-mcp)
10. [Workflows n8n](#10-workflows-n8n)
11. [Métriques et Évolution](#11-métriques-et-évolution)
12. [Planning d'Implémentation](#12-planning-dimplémentation)

---

## 1. Vision et Philosophie

### 1.1 Le principe fondamental

\`\`\`
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   "Chaque ticket résolu enrichit le RAG,                                 ║
║    chaque procédure créée rend les agents plus autonomes,                ║
║    chaque jour le système devient plus intelligent."                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
\`\`\`

### 1.2 L'évolution visée

\`\`\`
┌─────────────────────────────────────────────────────────────────────────┐
│                    ÉVOLUTION DE L'AUTONOMIE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MOIS 1                    MOIS 3                    MOIS 6            │
│                                                                         │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐    │
│  │  RAG INIT   │          │  RAG ENRICHI│          │  RAG MATURE │    │
│  │ ~50k chunks │   ───►   │ ~80k chunks │   ───►   │ ~150k chunks│    │
│  │ Fichiers    │          │ + Procédures│          │ + Patterns  │    │
│  │ Word        │          │ auto-créées │          │ + Solutions │    │
│  └─────────────┘          └─────────────┘          └─────────────┘    │
│        │                        │                        │             │
│        ▼                        ▼                        ▼             │
│  Agents: 30% auto         Agents: 50% auto         Agents: 70%+ auto  │
│  Tech: 70% manuel         Tech: 50% manuel         Tech: 30% manuel   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
\`\`\`

### 1.3 Les trois piliers

| Pilier | Rôle | Composants |
|--------|------|------------|
| **RAG (Savoir)** | Base de connaissances | Infos clients, procédures, solutions, patterns |
| **AGENTS (Action)** | Exécution intelligente | SENTINEL, SUPPORT, Interface tech, SAFEGUARD |
| **ENRICHISSEUR (Évolution)** | Amélioration continue | Analyse tickets, extraction solutions, création procédures |

---

## 2. Architecture Globale

### 2.1 Vue d'ensemble

\`\`\`
╔═══════════════════════════════════════════════════════════════════════════╗
║                     ARCHITECTURE RAG V3 - VUE GLOBALE                     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║                          ┌─────────────────────┐                          ║
║                          │   SOURCES DONNÉES   │                          ║
║                          └──────────┬──────────┘                          ║
║                                     │                                     ║
║            ┌────────────────────────┼────────────────────────┐            ║
║            │                        │                        │            ║
║            ▼                        ▼                        ▼            ║
║   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      ║
║   │  FICHIERS WORD  │    │  GLPI (tickets  │    │  ENRICHISSEUR   │      ║
║   │  P:\CLIENTS     │    │   résolus)      │    │  (procédures    │      ║
║   │  P:\CONTRATS    │    │  Via workflow   │    │   générées)     │      ║
║   │  11 277 fichiers│    │  quotidien      │    │                 │      ║
║   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘      ║
║            │                      │                      │                ║
║            └──────────────────────┼──────────────────────┘                ║
║                                   │                                       ║
║                                   ▼                                       ║
║   ┌───────────────────────────────────────────────────────────────────┐   ║
║   │                    POSTGRESQL + PGVECTOR (RAG)                    │   ║
║   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   ║
║   │  │   CLIENTS   │ │ PROCÉDURES  │ │  SOLUTIONS  │ │  PATTERNS   │ │   ║
║   │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   ║
║   └───────────────────────────────┬───────────────────────────────────┘   ║
║                                   │                                       ║
║                                   ▼                                       ║
║   ┌───────────────────────────────────────────────────────────────────┐   ║
║   │                       SERVEUR MCP PYTHON                          │   ║
║   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐      │   ║
║   │  │  MCP-RAG  │  │ MCP-GLPI  │  │  MCP-AD   │  │ MCP-SMTP  │      │   ║
║   │  └───────────┘  └───────────┘  └───────────┘  └───────────┘      │   ║
║   └───────────────────────────────┬───────────────────────────────────┘   ║
║                                   │                                       ║
║                                   ▼                                       ║
║   ┌───────────────────────────────────────────────────────────────────┐   ║
║   │                          AGENTS IA                                │   ║
║   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐      │   ║
║   │  │ SENTINEL  │  │  SUPPORT  │  │ENRICHISSEUR│  │ SAFEGUARD │      │   ║
║   │  └───────────┘  └───────────┘  └───────────┘  └───────────┘      │   ║
║   │                         ┌───────────┐                            │   ║
║   │                         │ DEVSTRAL  │                            │   ║
║   │                         └───────────┘                            │   ║
║   └───────────────────────────────────────────────────────────────────┘   ║
╚═══════════════════════════════════════════════════════════════════════════╝
\`\`\`

### 2.2 Flux de données quotidien

| Heure | Workflow | Action |
|-------|----------|--------|
| **3h00** | RAG-SYNC-FILES | Sync fichiers Word modifiés → RAG |
| **8h-18h** | SENTINEL + SUPPORT | Agents consultent RAG + GLPI |
| **8h-18h** | Interface Chat | Techniciens interrogent RAG |
| **18h00** | RAG-ENRICH | Tickets résolus → Nouvelles procédures → RAG |

---

## 3. Sources de Données

### 3.1 Sources initiales (Fichiers Word)

| Dossier | Taille | Fichiers | Contenu |
|---------|--------|----------|---------|
| **P:\CLIENTS** | 8,72 Go | 11 277 | Fiches établissements, contacts, infrastructure, historique |
| **P:\CONTRATS** | 368 Mo | 552 | Contrats, SLA, engagements, conditions |

**Estimation après import : ~50 000 chunks dans le RAG**

### 3.2 Sources dynamiques (Auto-enrichissement)

| Source | Déclencheur | Résultat |
|--------|-------------|----------|
| **Tickets résolus GLPI** | Quotidien 18h | Nouvelles solutions/procédures |
| **Patterns récurrents** | Hebdomadaire | Diagnostics type documentés |
| **Lacunes détectées** | Continu | Priorité enrichissement |

### 3.3 Ce qui reste dans GLPI (temps réel)

- Tickets en cours (statut, assignation)
- Historique récent
- Créer/modifier tickets
- Recherche "Ce client a-t-il déjà eu ce problème ?"

---

## 4. Structure du RAG

### 4.1 Organisation des données

\`\`\`
📁 RAG WIDIP V3
│
├── 📂 CLIENTS (doc_type: client_*)
│   ├── client_fiche      → Informations établissement
│   ├── client_contact    → Contacts avec coordonnées
│   ├── client_infra      → Serveurs, IPs, configurations
│   ├── client_reseau     → FAI, liaisons, VPN
│   └── client_contrat    → SLA, engagements
│
├── 📂 PROCÉDURES (doc_type: procedure_*)
│   ├── procedure_diagnostic  → Comment diagnostiquer
│   ├── procedure_resolution  → Comment résoudre
│   └── procedure_config      → Comment configurer
│   └── [AUTO-GÉNÉRÉES PAR ENRICHISSEUR] ⭐
│
├── 📂 SOLUTIONS (doc_type: solution)
│   └── Solutions extraites des tickets résolus ⭐
│
└── 📂 PATTERNS (doc_type: pattern)
    └── Patterns récurrents détectés ⭐
\`\`\`

### 4.2 Schéma PostgreSQL principal

\`\`\`sql
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Contenu
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_embedding vector(1024),
    
    -- Classification
    doc_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    
    -- Hiérarchie client
    groupe_client VARCHAR(200),
    etablissement VARCHAR(200),
    
    -- Source
    source_type VARCHAR(50) NOT NULL, -- 'word_import', 'auto_enrichment', 'manual'
    source_path TEXT,
    source_hash VARCHAR(32),
    
    -- Qualité
    quality_score FLOAT,
    auto_generated BOOLEAN DEFAULT FALSE,
    
    -- Métriques
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index vectoriel
CREATE INDEX idx_rag_embedding 
ON rag_documents USING ivfflat (content_embedding vector_cosine_ops);
\`\`\`

---

## 5. L'Agent ENRICHISSEUR

### 5.1 Mission

> **Combler les lacunes des autres agents** en enrichissant continuellement le RAG avec de nouvelles procédures extraites des tickets résolus.

### 5.2 Responsabilités

1. **ANALYSER** les tickets résolus du jour
2. **EXTRAIRE** les solutions documentées
3. **CRÉER** des procédures formalisées
4. **DÉTECTER** les patterns récurrents
5. **VALIDER** la qualité avant injection

### 5.3 Pipeline d'enrichissement (18h00)

\`\`\`
┌─────────────────────────────────────────────────────────────────────────┐
│                  PIPELINE ENRICHISSEMENT QUOTIDIEN                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. COLLECTER                                                          │
│     glpi_get_resolved_tickets(today)                                   │
│     → Liste tickets fermés avec solution                               │
│                                                                         │
│  2. FILTRER                                                            │
│     rag_search(ticket.description)                                     │
│     → Si score < 0.85 : Candidat enrichissement                        │
│                                                                         │
│  3. EXTRAIRE (via Devstral)                                            │
│     Prompt → JSON structuré :                                          │
│     {titre, probleme, diagnostic[], solution[], verification...}       │
│                                                                         │
│  4. VALIDER                                                            │
│     Score qualité auto (complétude, clarté, applicabilité)            │
│     → Si >= 0.7 : Insertion directe                                    │
│     → Si < 0.7 : Staging pour validation humaine                       │
│                                                                         │
│  5. INJECTER                                                           │
│     rag_add_document(procedure)                                        │
│     → Nouvelle procédure disponible pour les agents                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
\`\`\`

### 5.4 Format procédure auto-générée

\`\`\`markdown
# [TITRE DE LA PROCÉDURE]

**Catégorie** : Réseau / VPN / AD / Imprimante
**Niveau** : Facile / Moyen / Avancé
**Temps estimé** : XX minutes
**Équipements** : Routeur Orange, Switch Cisco...
**Tags** : #vpn #orange #ipsec

## Problème
Description du problème rencontré.

## Diagnostic
1. Première étape de vérification
2. Deuxième étape...

## Solution
1. Première action
2. Deuxième action...

## Vérification
Comment vérifier que c'est résolu.

---
*Source : Ticket GLPI #XXXX - Généré le DD/MM/YYYY*
\`\`\`

---

## 6. Le Cercle Vertueux

### 6.1 Principe

\`\`\`
                    ┌─────────────────────────┐
                    │    TICKET ENTRANT       │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  AGENT CONSULTE RAG     │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        ┌───────────┐    ┌───────────┐    ┌───────────┐
        │  TROUVÉ   │    │ PARTIEL   │    │ PAS       │
        │    ✓      │    │    ~      │    │ TROUVÉ ✗  │
        └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
              │                │                │
              ▼                ▼                ▼
        Résolution       Résolution       Log unresolved
        AUTO             ASSISTÉE         → Technicien
                                          → Résolution
                                                │
              └────────────────┴────────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │    TICKET RÉSOLU        │
                    │  (solution documentée)  │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │    ENRICHISSEUR (18h)   │
                    │                         │
                    │  • Analyse solution     │
                    │  • Crée procédure       │
                    │  • Injecte dans RAG     │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      RAG ENRICHI        │◄── Le RAG grandit !
                    └───────────┬─────────────┘
                                │
                                ▼
               PROCHAIN TICKET SIMILAIRE → Résolution AUTO ✓
\`\`\`

### 6.2 Projection d'évolution

| Période | Documents RAG | Procédures auto | Autonomie agents |
|---------|---------------|-----------------|------------------|
| **Semaine 1** | ~50 000 | 0 | 30% |
| **Mois 1** | ~50 500 | ~160 | 40% |
| **Mois 3** | ~52 000 | ~480 | 55% |
| **Mois 6** | ~55 000 | ~1000 | **70%** |

---

## 7. Intégration avec les Agents

### 7.1 Agent SENTINEL (Proactif)

\`\`\`
TRIGGER : Alerte Observium

1. RÉCEPTION ALERTE
   device: "RTR-EHPAD-SOLEIL", alert: "BGP Peer Down"

2. ENRICHISSEMENT CONTEXTE (RAG)
   rag_search("RTR-EHPAD-SOLEIL")
   → Établissement: EHPAD Soleil, FAI: Orange, Contact: Marie

   rag_search("BGP Peer Down Orange", type="procedure")
   → Procédure: "Diagnostic BGP Orange" (score: 0.89)

3. VÉRIFICATION HISTORIQUE (GLPI)
   glpi_search_tickets(entity="EHPAD Soleil", keyword="BGP")
   → Historique incidents similaires

4. ANALYSE + ACTION (Devstral)
   → Diagnostic + Création ticket + Actions
\`\`\`

### 7.2 Agent SUPPORT (Assist-Ticket)

\`\`\`
TRIGGER : Nouveau ticket GLPI #DIAG

1. RÉCEPTION TICKET
   #4550: "VPN site EHPAD Bellevue ne fonctionne plus"

2. ENRICHISSEMENT CONTEXTE (RAG)
   rag_get_client("EHPAD Bellevue")
   → Groupe, FAI, Config VPN, Routeur, Contacts

   rag_search("VPN down", type="procedure")
   → Procédure applicable (score: 0.91)

3. VÉRIFICATION HISTORIQUE (GLPI)
   glpi_search_tickets(entity="EHPAD Bellevue", keyword="VPN")
   → "Ce client a déjà eu ce problème 2 fois"

4. GÉNÉRATION DIAGNOSTIC
   → Diagnostic structuré + Étapes suggérées + Confiance 87%

5. ACTION
   Si confiance >= 80% → Followup auto + Résolution proposée
   Si confiance < 80% → Log unresolved + Escalade technicien
\`\`\`

### 7.3 Interface Technicien (Chat)

\`\`\`
👤 Tech : "IP serveur principal EHPAD Soleil ?"

🤖 Bot : [rag_get_infrastructure("EHPAD Soleil")]
   "Le serveur principal de l'EHPAD Soleil :
    📦 SRV-SOLEIL-DC01
    • IP : 192.168.10.1
    • Rôle : Contrôleur de domaine
    Contact sur site : Marie Dupont (06.xx.xx.xx)"

👤 Tech : "Comment résoudre un VPN SFR qui ne monte pas ?"

🤖 Bot : [rag_search("VPN SFR ne monte pas", type="procedure")]
   "Procédure 'Résolution VPN SFR - IPSec' :
    📋 Diagnostic : [étapes...]
    🔧 Résolution : [actions...]
    Source : Auto-généré depuis ticket #4320"
\`\`\`

---

## 8. Complémentarité RAG + MCP GLPI

### 8.1 Répartition des responsabilités

| Besoin | RAG | GLPI |
|--------|-----|------|
| "Comment faire ?" | ✅ | |
| Procédures diagnostic/résolution | ✅ | |
| Infos clients (contacts, infra) | ✅ | |
| Configurations type | ✅ | |
| "Que se passe-t-il ?" | | ✅ |
| Tickets en cours | | ✅ |
| Historique récent | | ✅ |
| Créer/modifier tickets | | ✅ |

### 8.2 Règle d'or

\`\`\`
• RAG  = Ce qui ne change pas souvent (infos, procédures, solutions)
• GLPI = Ce qui change tout le temps (tickets, statuts, assignations)

Les deux sont COMPLÉMENTAIRES, pas concurrents.
Un agent performant utilise les DEUX systématiquement.
\`\`\`

---

## 9. Outils MCP

### 9.1 MCP-RAG (nouveau)

| Outil | Description |
|-------|-------------|
| `rag_search(query, doc_types?, category?, limit?)` | Recherche sémantique générale |
| `rag_get_client(etablissement)` | Fiche client complète |
| `rag_get_infrastructure(etablissement)` | Serveurs, IPs, réseau |
| `rag_get_contacts(etablissement)` | Contacts avec coordonnées |
| `rag_get_procedure(problem_type)` | Meilleure procédure |
| `rag_add_document(...)` | Ajouter document (enrichisseur) |
| `rag_log_unresolved(...)` | Log cas non résolu |

### 9.2 MCP-GLPI (existant)

| Outil | Description |
|-------|-------------|
| `glpi_search_tickets(...)` | Rechercher tickets |
| `glpi_get_ticket_details(id)` | Détails ticket |
| `glpi_get_resolved_tickets(date)` | Tickets résolus (pour enrichisseur) |
| `glpi_create_ticket(...)` | Créer ticket |
| `glpi_add_followup(...)` | Ajouter suivi |

---

## 10. Workflows n8n

### 10.1 Liste des workflows

| Workflow | Trigger | Fonction | RAG |
|----------|---------|----------|-----|
| **RAG-SYNC-FILES** | Cron 3h00 | Sync fichiers Word | Write |
| **RAG-ENRICH** | Cron 18h00 | Enrichissement auto | Write |
| **RAG-CHAT** | Webhook Teams | Interface technicien | Read |
| **SENTINEL** | Observium | Alertes réseau | Read |
| **SUPPORT** | GLPI webhook | Traitement tickets | Read |

---

## 11. Métriques et Évolution

### 11.1 KPIs à suivre

**Utilisation :**
- Requêtes RAG / jour
- Taux de hit (score >= 0.8)
- Documents les plus consultés

**Enrichissement :**
- Procédures créées / jour
- Taux de validation
- Lacunes comblées

**Efficacité :**
- Taux de résolution automatique
- Temps moyen résolution
- Réduction escalades

---

## 12. Planning d'Implémentation

### 12.1 Vue d'ensemble (5 semaines)

| Semaine | Focus | Livrable |
|---------|-------|----------|
| **S1-2** | Fondations | DB + Scripts extraction |
| **S3** | Ingestion | RAG peuplé (~50k chunks) |
| **S4** | Intégration | Agents utilisent RAG |
| **S5** | Enrichissement | Cercle vertueux actif |

### 12.2 Critères de succès

- ✅ 100% fichiers Word importés
- ✅ Temps recherche < 500ms
- ✅ Taux de hit > 70%
- ✅ Enrichissement quotidien actif
- ✅ Agents utilisent RAG systématiquement

---

## Conclusion

### Ce que RAG V3 apporte

| Aspect | Bénéfice |
|--------|----------|
| **Base initiale riche** | 50 000 chunks depuis fichiers Word |
| **Auto-enrichissement** | Procédures créées automatiquement |
| **Cercle vertueux** | Système qui s'améliore chaque jour |
| **Complémentarité** | RAG (savoir) + GLPI (temps réel) |
| **Objectif** | **70% autonomie en 6 mois** |

### Architecture finale

\`\`\`
           FICHIERS WORD + ENRICHISSEMENT AUTO
                          │
                          ▼
                 ┌─────────────────┐
                 │   RAG CENTRAL   │
                 └────────┬────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
  ┌─────────┐       ┌─────────┐       ┌───────────┐
  │ SENTINEL│       │ SUPPORT │       │ENRICHISSEUR│
  └────┬────┘       └────┬────┘       └─────┬─────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   MCP GLPI      │
                │  (temps réel)   │
                └─────────────────┘
\`\`\`

---

> **Document créé le** : 18 Décembre 2025  
> **Version** : 3.0  
> **Statut** : Validé - Prêt pour implémentation
