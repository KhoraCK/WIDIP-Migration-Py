# WIDIP_Assist_ticket_v6.1
## Agent Support Automatisé - Traitement Tickets GLPI

> **Version** : 6.1 | **Type** : Agent IA Principal | **Trigger** : Schedule 3 min

---

## 🎯 Rôle

Agent IA qui traite automatiquement les nouveaux tickets GLPI. Il recherche des solutions dans la base de connaissances (RAG), génère une réponse avec Claude, et propose une solution au technicien.

**Positionnement** : Cœur du système WIDIP, traite 70% des tickets en autonomie ou mode assisté.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[Schedule 3min]
    ↓
[MCP: Récup tickets GLPI] (20 max)
    ↓
[Détection #DIAG ?]
    ├─ OUI → BRANCHE DIAG (Validation Phibee)
    └─ NON → BRANCHE SUPPORT (Standard)
         ↓
    [RAG: Cherche cas similaires]
         ↓
    [Claude: Génère solution]
         ↓
    [GLPI: Ajoute followup]
         ↓
    [Redis: Marque traité]
```

### Architecture bi-branche

Le workflow se divise en **2 flux parallèles** selon le type de ticket :

#### **BRANCHE SUPPORT** (tickets standards)
1. Extraction info ticket
2. Recherche RAG (similarité vectorielle)
3. Construction prompt avec contexte
4. Génération solution Claude
5. Ajout followup GLPI
6. Déduplication Redis

#### **BRANCHE DIAG** (tickets réseau #DIAG) - NOUVEAU v6.1
1. Notification technicien → validation Phibee
2. Polling réponse technicien
3. Parse format `#DIAG gw=ok int=fail`
4. Analyse responsabilité (WIDIP vs Client)
5. Documentation ticket

---

## 🔄 Exemple Concret

### Cas 1 : Ticket standard "Imprimante bloquée"

**Entrée** : Ticket GLPI #1234
```
Titre: Imprimante HP bloquée en erreur
Description: Message "Bourrage papier" mais aucun papier coincé
Catégorie: Matériel
```

**Traitement** :
```
1. [3min] Polling détecte nouveau ticket #1234
2. [2s]   Pas de #DIAG → flux SUPPORT
3. [500ms] RAG trouve 2 cas similaires (sim: 0.82, 0.76)
   - Cas A: "Bourrage capteur HP" → Solution: Reset capteur
   - Cas B: "Erreur faux bourrage" → Solution: Nettoyage rouleaux
4. [3s]   Claude génère solution adaptée:
   "Bonjour,
   Ce message peut indiquer un problème de capteur.
   Actions à tester:
   1. Éteindre 30s puis rallumer
   2. Menu > Maintenance > Nettoyer capteurs
   3. Vérifier rouleaux encrassés
   Si persistant, prévoir intervention."
5. [200ms] Ajout followup GLPI (visible client)
6. [50ms]  Redis: ticket_processed:1234 = true (TTL 24h)
```

**Résultat** : Ticket résolu en **<10s**, client a solution immédiate.

---

### Cas 2 : Ticket #DIAG "Pas internet"

**Entrée** : Ticket GLPI #5678
```
Titre: #DIAG Plus d'accès internet établissement
Description: Coupure depuis 8h ce matin
```

**Traitement** :
```
1. [3min] Polling détecte ticket #5678
2. [100ms] Détection #DIAG → flux DIAG
3. [1s]   Notification Teams technicien:
   "⚠️ Ticket #5678 - Validation Phibee requise
   Vérifier lien sur https://phibee.widip.fr
   Répondre format: #DIAG gw=ok int=fail dns=ok ping=15ms"
4. [10min] Technicien vérifie Phibee → Passerelle OK, réseau interne KO
5. [3min] Polling détecte réponse technicien dans followups
6. [200ms] Parse: gw=ok, int=fail → PROBLÈME CLIENT
7. [1s]   Ajout followup GLPI:
   "Diagnostic réseau effectué:
   ✅ Infrastructure WIDIP: OK
   ❌ Réseau interne établissement: Défaillant

   Action client: Contacter prestataire informatique local
   WIDIP ne peut intervenir (hors périmètre)"
```

**Résultat** : Responsabilité clarifiée, pas d'intervention WIDIP inutile.

---

## 🔗 Dépendances

### MCP Tools (via widip-mcp-server)

| Tool | Niveau SAFEGUARD | Usage |
|------|------------------|-------|
| `glpi_search_new_tickets` | L0 (Read) | Récupération tickets |
| `glpi_add_ticket_followup` | L1 (Minor) | Ajout réponse |
| `memory_search_similar_cases` | L0 (Read) | Recherche RAG |
| `notify_technician` | L1 (Minor) | Alerte #DIAG |

### Workflows appelés

- **WIDIP_Redis_Helper_v2.2** : Déduplication (évite retraiter même ticket)

### Services externes

- **GLPI API** : Source tickets + ajout followups
- **Claude API (Sonnet 4.5)** : Génération solutions
- **PostgreSQL + pgvector** : Base connaissances RAG
- **Redis** : Cache déduplication
- **Phibee Telecom** : (référence manuelle, pas d'API)

---

## ⚙️ Configuration

### Variables d'environnement

```bash
MCP_SERVER_URL=http://mcp-server:3001
GLPI_URL=https://glpi.example.com/apirest.php
ANTHROPIC_API_KEY=sk-ant-...
POSTGRES_DSN=postgresql://user:pass@host/widip_knowledge
REDIS_URL=redis://redis:6379/0
```

### Paramètres clés

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Polling | 3 min | Fréquence check nouveaux tickets |
| Lookback | 24h | Fenêtre recherche tickets |
| Max tickets | 20/run | Limite traitement |
| RAG similarity | 0.6 (60%) | Seuil pertinence |
| RAG results | 3 max | Cas similaires retournés |

---

## 📊 Métriques

Le workflow track automatiquement :
- Nombre tickets traités (standard vs #DIAG)
- Hit rate RAG (% avec solutions trouvées)
- Durée traitement moyenne
- Tokens Claude consommés
- Taux d'erreurs

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Réactivité** : 3 min max entre création ticket et réponse
- **Pertinence RAG** : 80%+ des suggestions utiles
- **Déduplication** : Aucun ticket traité 2x
- **Human-in-the-Loop #DIAG** : 100% validés

### ⚠️ Points d'attention
- **Dépendance Claude API** : Rate limits possibles
- **Qualité RAG** : Dépend enrichissement quotidien
- **Parse #DIAG** : Format strict requis du technicien

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Assist_ticket_v6.1.json`
- **MCP Tools** : `widip-mcp-server/src/tools/glpi_tools.py`
- **RAG** : `widip-mcp-server/src/tools/memory_tools.py`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 6.1
