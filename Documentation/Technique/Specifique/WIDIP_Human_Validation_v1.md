# WIDIP_Human_Validation_v1
## Interface Web - Validation Humaine Actions Sensibles

> **Version** : 1.0 | **Type** : Interface Web + Notifications | **Trigger** : Webhooks HTTP

---

## 🎯 Rôle

Workflow fournissant une interface web moderne pour les validations humaines (actions L3 SAFEGUARD). Offre un dashboard avec liste des demandes, pages de détail, et notifications Teams enrichies avec boutons d'action.

**Positionnement** : Interface utilisateur du système SAFEGUARD, complète WIDIP_Safeguard_v2.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[3 Webhooks Endpoints]
    ├─ /human/dashboard → Dashboard principal
    ├─ /human/detail/:id → Page détail demande
    └─ /human/notify-teams → Notification Teams

[Dashboard]
Query PostgreSQL → Build HTML → Respond
    ↓
Affiche:
- Demandes en attente (avec actions)
- Historique 24h (approuvées/refusées)
- Stats temps réel

[Detail]
Query PostgreSQL → Build HTML → Respond
    ↓
Affiche:
- Contexte complet action
- Impact et réversibilité
- Boutons Approve/Reject

[Notify Teams]
Build Adaptive Card → POST Teams Webhook
    ↓
Carte Teams avec boutons:
- Voir détails
- Approuver
- Refuser
- Dashboard
```

---

## 🔄 Exemple Concret

### Cas 1 : Technicien consulte le dashboard

**Accès** :
```
1. [0s]    Technicien ouvre http://n8n.widip.local/webhook/human/dashboard
2. [500ms] Webhook trigger → Query PostgreSQL
3. [200ms] 3 demandes en attente retournées:
   - APR-2025-001: ad_reset_password (expire dans 45 min)
   - APR-2025-002: ad_disable_account (expire dans 22 min)
   - APR-2025-003: glpi_close_ticket (expire dans 58 min)

4. [300ms] Build HTML dashboard:
   ┌─────────────────────────────────────────────────────────┐
   │ WIDIP - Dashboard Validation Humaine                    │
   ├─────────────────────────────────────────────────────────┤
   │ [3] En attente  [12] Approuvées (24h)  [2] Refusées    │
   ├─────────────────────────────────────────────────────────┤
   │ Demandes en attente:                                    │
   │ ┌───────────────────────────────────────────────────┐  │
   │ │ ID: APR-2025-001                                  │  │
   │ │ Action: ad_reset_password                         │  │
   │ │ Params: username: jdupont                         │  │
   │ │ Créée: 24/12/2025 14:15                          │  │
   │ │ Expire: 45 min                                    │  │
   │ │ [Approuver] [Refuser]                             │  │
   │ └───────────────────────────────────────────────────┘  │
   │ ... 2 autres demandes ...                              │
   └─────────────────────────────────────────────────────────┘

5. [100ms] Respond HTML → Affichage navigateur
6. [30s]   Auto-refresh (meta http-equiv="refresh")
```

---

### Cas 2 : Notification Teams avec validation rapide

**Notification** :
```
1. [0s]    WIDIP_Safeguard_v2 détecte action L3 → ad_reset_password
2. [1s]    Demande créée en PostgreSQL (APR-2025-004)
3. [1.5s]  POST http://n8n.widip.local/webhook/human/notify-teams
   Body: {
     "approval_id": "APR-2025-004",
     "tool_name": "ad_reset_password",
     "security_level": "L3",
     "arguments": {"username": "mmartin", "temp_password": "***"},
     "description": "Utilisateur bloqué après 3 échecs MFA",
     "expires_at": "Dans 1 heure"
   }

4. [2s]    Build Teams Adaptive Card:
   ╔═══════════════════════════════════════════════════╗
   ║ ⚠️ SAFEGUARD - Validation Requise                ║
   ╠═══════════════════════════════════════════════════╣
   ║ Action: Réinitialisation mot de passe AD         ║
   ║ Niveau: L3 (Sensible)                            ║
   ║ ID: APR-2025-004                                  ║
   ║ Expire: Dans 1 heure                              ║
   ║                                                    ║
   ║ Paramètres:                                       ║
   ║ username: mmartin                                 ║
   ║ temp_password: ***                                ║
   ║                                                    ║
   ║ Utilisateur bloqué après 3 échecs MFA            ║
   ║                                                    ║
   ║ [Voir détails] [✅ Approuver] [❌ Refuser] [📊 Dashboard] ║
   ╚═══════════════════════════════════════════════════╝

5. [3s]    POST Teams Webhook → Notification envoyée
6. [10s]   Technicien voit notification Teams mobile
7. [12s]   Click [✅ Approuver] → Redirige vers WIDIP_Dashboard_Safeguard_v1
8. [15s]   Saisit email + commentaire → Action exécutée
```

---

## 🔗 Dépendances

### Base de données PostgreSQL

| Table | Usage |
|-------|-------|
| `safeguard_pending_approvals` | Source demandes validation |

### Workflows liés

| Workflow | Relation |
|----------|----------|
| **WIDIP_Safeguard_v2** | Crée les demandes, appelle notify-teams |
| **WIDIP_Dashboard_Safeguard_v1** | Exécute les approbations/rejets |

### Services externes

- **PostgreSQL** : Stockage demandes
- **Teams Webhook** : Notifications push
- **n8n Webhook** : Interface HTTP

---

## ⚙️ Configuration

### Variables d'environnement

```bash
N8N_WEBHOOK_URL=http://n8n.widip.local:5678
SAFEGUARD_DASHBOARD_URL=http://safeguard.widip.local/dashboard
TEAMS_WEBHOOK_URL=https://example.webhook.office.com/webhookb2/***
```

### Endpoints disponibles

| Endpoint | Méthode | Usage |
|----------|---------|-------|
| `/webhook/human/dashboard` | GET | Dashboard principal |
| `/webhook/human/detail/:id` | GET | Page détail demande |
| `/webhook/human/notify-teams` | POST | Envoyer notification Teams |

---

## 📊 Métriques

Le workflow ne track pas de métriques, mais affiche dans le dashboard :
- Nombre demandes en attente
- Nombre approuvées/refusées 24h
- Temps restant avant expiration (minutes)

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Interface moderne** : HTML5 + CSS responsive
- **Auto-refresh** : Dashboard se rafraîchit toutes les 30s
- **Adaptive Cards** : Notifications Teams riches avec boutons
- **Contexte complet** : Impact, réversibilité, paramètres
- **Historique** : Vue 24h des décisions passées

### ⚠️ Points d'attention
- **Pas d'authentification** : Endpoints publics (à sécuriser en prod)
- **Pas de pagination** : Limite 100 demandes
- **Pas de filtres** : Affiche toutes les demandes
- **Boutons Teams** : Redirection web (pas d'action inline)

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Human_Validation_v1.json`
- **SAFEGUARD** : `Workflow principaux/WIDIP_Safeguard_v2.json`
- **Dashboard** : `Workflow principaux/WIDIP_Dashboard_Safeguard_v1.json`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 1.0
