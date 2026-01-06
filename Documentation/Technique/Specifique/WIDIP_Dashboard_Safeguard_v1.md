# WIDIP_Dashboard_Safeguard_v1
## Dashboard Web - Validation Humaine Actions Sensibles

> **Version** : 1.1 (secured) | **Type** : Interface Web | **Trigger** : Accès HTTP (Basic Auth)

---

## 🎯 Rôle

Dashboard web permettant aux techniciens d'approuver ou refuser les actions sensibles (L3) nécessitant une validation humaine dans le système SAFEGUARD. Affiche les demandes en attente et leur contexte complet.

**Positionnement** : Interface Human-in-the-Loop du système SAFEGUARD, sécurise les actions critiques.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[Technicien] → Accès URL dashboard
    ↓
[Basic Auth] (credentials requises)
    ↓
[Query PostgreSQL] → safeguard_approvals
    ↓
[Génère HTML] (table interactive)
    ↓
[Boutons Approve/Reject]
    ↓ Click
[JavaScript POST] → MCP Server
    ↓
[Mise à jour statut] + Notification
    ↓
[Workflow déblocage] (WIDIP_Safeguard_v2)
```

### Flux de validation

1. **Affichage demandes** : Liste toutes les demandes `status = pending`
2. **Contexte enrichi** : Affiche tool, paramètres, workflow source, raison
3. **Approbation** : Bouton → POST `/safeguard/approve/{id}`
4. **Refus** : Bouton → POST `/safeguard/reject/{id}`
5. **Notification** : Email/Teams au requester du workflow

---

## 🔄 Exemple Concret

### Cas 1 : Reset password AD en attente

**Contexte** :
```
Un ticket GLPI demande un reset MDP pour utilisateur "jdupont".
Agent IA a détecté que ad_reset_password est L3 SENSITIVE.
Demande de validation créée en base PostgreSQL.
```

**Utilisation Dashboard** :
```
1. [0s]    Technicien accède à http://safeguard.widip.local/dashboard
2. [1s]    Prompt Basic Auth → Saisit user/pass
3. [2s]    Dashboard charge les demandes en attente

   TABLE AFFICHÉE:
   ┌────────────┬───────────────────┬─────────────────────┬──────────────┬─────────┐
   │ ID         │ Tool              │ Paramètres          │ Workflow     │ Actions │
   ├────────────┼───────────────────┼─────────────────────┼──────────────┼─────────┤
   │ APR-2025-1 │ ad_reset_password │ username: jdupont   │ Assist_v6.1  │ [✅][❌] │
   │            │                   │ temp_password: ***  │              │         │
   │            │ Raison: Utilisateur bloqué après 3 échecs connexion    │         │
   │            │ Créé: Il y a 5 min                                     │         │
   └────────────┴───────────────────┴─────────────────────┴──────────────┴─────────┘

4. [10s]   Technicien clique [✅ Approuver]
5. [0.5s]  Prompt: "Email approbateur ?" → tech@widip.fr
6. [0.5s]  Prompt: "Commentaire ?" → "Validé après vérif identité tél"
7. [1s]    POST → http://mcp-server:3001/safeguard/approve/APR-2025-1
           Body: {
             "approver": "tech@widip.fr",
             "comment": "Validé après vérif identité tél"
           }

8. [500ms] MCP Server:
   → UPDATE safeguard_approvals SET status='approved'
   → INSERT safeguard_actions_log
   → Notify workflow WIDIP_Safeguard_v2 → Exécute ad_reset_password

9. [1s]    Dashboard refresh → Demande disparue (status != pending)
```

**Résultat** : Action exécutée après validation humaine, tracée dans les logs.

---

### Cas 2 : Refus d'une action suspecte

**Contexte** :
```
Demande de création compte AD (ad_create_user) depuis workflow inconnu.
Paramètres suspects : username "admin2", groups "Domain Admins".
```

**Utilisation Dashboard** :
```
1. Dashboard affiche la demande avec flag "⚠️ Suspect"
2. Technicien analyse le contexte
3. Clique [❌ Refuser]
4. Saisit: "Création admin non autorisée, escalade sécurité"
5. POST → /safeguard/reject/APR-2025-2
6. MCP Server:
   → UPDATE status='rejected'
   → Alerte équipe sécurité (Teams webhook)
   → Workflow requester reçoit erreur "Action refusée par humain"
```

**Résultat** : Action bloquée, sécurité alertée, audit trail complet.

---

## 🔗 Dépendances

### Base de données PostgreSQL

| Table | Usage |
|-------|-------|
| `safeguard_approvals` | Demandes en attente/traitées |
| `safeguard_actions_log` | Historique toutes actions |

### MCP Server Endpoints

| Endpoint | Méthode | Usage |
|----------|---------|-------|
| `/safeguard/approve/{id}` | POST | Approuver action |
| `/safeguard/reject/{id}` | POST | Refuser action |

### Workflows liés

- **WIDIP_Safeguard_v2** : Système orchestration SAFEGUARD
- **WIDIP_Human_Validation_v1** : Gère les timeouts et relances

### Services externes

- **PostgreSQL** : Stockage demandes
- **MCP Server** : API approbation
- **Teams/Slack** : Notifications (via MCP)

---

## ⚙️ Configuration

### Variables d'environnement (n8n)

```bash
# Authentification dashboard
SAFEGUARD_DASHBOARD_USER=admin
SAFEGUARD_DASHBOARD_PASS=***

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_DB=widip_knowledge
POSTGRES_USER=widip
POSTGRES_PASS=***

# MCP Server
MCP_SERVER_URL=http://mcp-server:3001
MCP_API_KEY=***
```

### Paramètres clés

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Webhook path | `/safeguard/dashboard` | URL accès dashboard |
| Auth type | Basic Auth | Sécurité accès |
| Credentials ID | `safeguard-dashboard-auth` | n8n credentials |
| Refresh auto | Non | Manuel (F5) |
| Timeout validation | 60 min | Expire après 1h (géré par Human_Validation) |

---

## 📊 Métriques

Le dashboard ne track pas de métriques lui-même, mais permet de visualiser :
- Nombre de demandes en attente
- Temps écoulé depuis création
- Workflow source de chaque demande
- Historique approvals (via PostgreSQL)

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Sécurité renforcée** : Basic Auth obligatoire (v1.1)
- **Contexte complet** : Technicien voit tous les détails
- **Actions CSRF-safe** : POST avec API Key
- **Interface simple** : HTML pur, pas de framework complexe
- **Traçabilité** : Audit trail complet dans PostgreSQL

### ⚠️ Points d'attention
- **Pas de refresh auto** : Technicien doit actualiser manuellement
- **Une seule page** : Pas de pagination (OK si < 50 demandes)
- **UI basique** : HTML/CSS simple, pas de framework moderne
- **Pas de filtres** : Affiche toutes les demandes pending

---

## 🔒 Sécurité v1.1

### Corrections sécurité (24/12/2025)

1. **Basic Auth ajoutée** :
   - Credentials n8n obligatoires
   - Pas d'accès anonyme

2. **Actions POST sécurisées** :
   - Remplacé GET links → POST JavaScript fetch
   - API Key MCP Server requise
   - Protection CSRF

3. **Table PostgreSQL harmonisée** :
   - `safeguard_approvals` (pas `pending_approvals`)
   - Colonnes: `id as approval_id`, `request_context`

### Checklist déploiement

```bash
# 1. Créer credentials Basic Auth dans n8n
# 2. Configurer variables PostgreSQL
# 3. Vérifier endpoints MCP Server actifs
# 4. Tester accès: http://safeguard.widip.local/dashboard
# 5. Vérifier logs PostgreSQL après approbation
```

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Dashboard_Safeguard_v1.json`
- **Système SAFEGUARD** : `Documentation/Technique/Systeme_SAFEGUARD.md`
- **MCP Endpoints** : `widip-mcp-server/src/routes/safeguard.py`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 1.1-secured
