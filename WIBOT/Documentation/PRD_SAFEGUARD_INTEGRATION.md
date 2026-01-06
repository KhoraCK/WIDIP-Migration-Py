# PRD - Intégration Safeguard dans WIBOT

> **Version** : 1.5 | **Date** : 5 Janvier 2026 | **Auteur** : Claude
> **Statut** : 🚧 En cours (Frontend complet + Backend Phases 1, 2, 3 complètes)

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Flux Métier](#flux-métier)
3. [Objectifs](#objectifs)
4. [Architecture cible](#architecture-cible)
5. [Roadmap Frontend](#roadmap-frontend)
6. [Roadmap Backend](#roadmap-backend)
7. [Spécifications détaillées](#spécifications-détaillées)
8. [Checklist de progression](#checklist-de-progression)

---

## Vue d'ensemble

### Contexte

WIBOT est l'assistant IA interne de WIDIP. Le système SAFEGUARD gère les validations humaines pour les actions sensibles (L3) des workflows IA (Assist Ticket, Proactif Observium).

### Problème actuel

- Les techniciens reçoivent les demandes Safeguard via **Teams** (notifications)
- Ils doivent aller sur un **Dashboard séparé** pour approuver/refuser
- Pas de centralisation : basculement entre plusieurs outils

### Solution proposée

Intégrer un **onglet Safeguard** directement dans WIBOT pour :
- Centraliser toutes les interactions technicien
- Afficher les demandes d'approbation L3 dans une interface familière
- Permettre l'approbation/refus directement depuis WIBOT
- Gérer les niveaux d'accréditation (N0-N4) des techniciens

---

## Flux Métier

### Chronologie complète : Du ticket client à la résolution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUX COMPLET SAFEGUARD                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. CLIENT                                                            │    │
│  │    └─→ Ouvre ticket GLPI                                            │    │
│  │        Ex: "MDP oublié pour l'utilisateur jdupont"                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 2. WORKFLOW ASSIST TICKET (polling toutes les 3 min)                │    │
│  │    └─→ Détecte nouveau ticket                                       │    │
│  │    └─→ Analyse le contenu (RAG + Claude)                            │    │
│  │    └─→ Détermine l'action nécessaire: ad_reset_password             │    │
│  │    └─→ Appelle MCP Server pour exécuter l'action                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 3. MCP SERVER                                                        │    │
│  │    └─→ Reçoit appel: ad_reset_password("jdupont")                   │    │
│  │    └─→ Vérifie niveau sécurité: L3 (SENSITIVE)                      │    │
│  │    └─→ ⚠️ SAFEGUARD BLOQUE L'EXÉCUTION                              │    │
│  │    └─→ Crée entrée dans table safeguard_approvals (status: pending) │    │
│  │    └─→ Retourne à Assist Ticket: "awaiting_human_approval"          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 4. WIBOT - ONGLET SAFEGUARD (nouvelle interface)                    │    │
│  │                                                                      │    │
│  │    Le technicien voit apparaître la demande avec:                   │    │
│  │    ┌────────────────────────────────────────────────────────────┐   │    │
│  │    │ 🛡️ Demande #APR-2026-001           ⏱️ Expire dans 58 min  │   │    │
│  │    │────────────────────────────────────────────────────────────│   │    │
│  │    │ Action: ad_reset_password                                   │   │    │
│  │    │ Niveau requis: L3                                           │   │    │
│  │    │ Utilisateur cible: jdupont                                  │   │    │
│  │    │                                                             │   │    │
│  │    │ 📋 Contexte:                                                │   │    │
│  │    │ • Ticket GLPI: #1234 - "MDP oublié"                        │   │    │
│  │    │ • Client: EHPAD Les Music Art                               │   │    │
│  │    │ • Demandeur: Mme Martin (secrétariat)                       │   │    │
│  │    │                                                             │   │    │
│  │    │ 💬 Commentaire: [____________________________]              │   │    │
│  │    │                                                             │   │    │
│  │    │        [✅ Approuver]        [❌ Refuser]                   │   │    │
│  │    └────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                      ┌─────────────┴─────────────┐                          │
│                      ▼                           ▼                          │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐    │
│  │ 5A. APPROUVÉ ✅              │  │ 5B. REFUSÉ ❌                     │    │
│  │                              │  │                                   │    │
│  │ → MCP exécute l'action       │  │ → Ticket reste ouvert            │    │
│  │ → Reset MDP effectué         │  │ → Notification au workflow       │    │
│  │ → Email MySecret envoyé      │  │ → Technicien gère manuellement   │    │
│  │ → Followup GLPI automatique  │  │ → Intervention humaine requise   │    │
│  │ → Ticket peut être fermé     │  │                                   │    │
│  └──────────────────────────────┘  └──────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cas d'usage principaux

| Scénario | Action IA | Niveau | Résultat si approuvé |
|----------|-----------|--------|----------------------|
| MDP oublié | `ad_reset_password` | L3 | Reset + lien MySecret |
| Compte bloqué | `ad_unlock_account` | L2 | Déverrouillage AD |
| Fermeture ticket | `glpi_close_ticket` | L3 | Ticket fermé + email client |
| Désactivation compte | `ad_disable_account` | L3 | Compte désactivé |

### Timeout et expiration

- **Délai par défaut** : 60 minutes
- **Si non traité** : Demande expire automatiquement → Ticket reste ouvert
- **Notification** : Le workflow est informé du timeout

---

## Objectifs

### Objectifs principaux

| # | Objectif | Priorité |
|---|----------|----------|
| 1 | Nouvel onglet "Safeguard" dans le menu utilisateur | 🔴 Haute |
| 2 | Interface liste des demandes (similaire aux conversations) | 🔴 Haute |
| 3 | Vue détail d'une demande avec actions Approuver/Refuser | 🔴 Haute |
| 4 | Niveaux d'accréditation N0-N4 pour les utilisateurs | 🟠 Moyenne |
| 5 | Filtrage des demandes par niveau d'accréditation | 🟠 Moyenne |

### Critères de succès

- [ ] Un technicien peut voir les demandes Safeguard depuis WIBOT
- [ ] Un technicien peut approuver/refuser une demande depuis WIBOT
- [ ] Les niveaux d'accréditation sont gérés à la création/modification d'utilisateur
- [ ] Seuls les techniciens avec le bon niveau voient les demandes correspondantes

---

## Architecture cible

### Vue globale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           WIBOT v2                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Menu utilisateur (dropdown)                                             │
│  ┌────────────────────────┐                                              │
│  │ 👤 khora (Admin)       │                                              │
│  │ ───────────────────────│                                              │
│  │ 📊 Supervision         │ ← Existant                                   │
│  │ 👥 Utilisateurs        │ ← Existant                                   │
│  │ 🛡️ Safeguard          │ ← NOUVEAU                                    │
│  │ ───────────────────────│                                              │
│  │ 🚪 Se déconnecter      │                                              │
│  └────────────────────────┘                                              │
│                                                                          │
│  Page Safeguard                                                          │
│  ┌──────────────────────┬───────────────────────────────────────────┐   │
│  │ DEMANDES EN ATTENTE  │  DÉTAIL DEMANDE                           │   │
│  │                      │                                            │   │
│  │ ┌──────────────────┐ │  ┌────────────────────────────────────┐   │   │
│  │ │ 🔴 APR-001       │ │  │ 🛡️ DEMANDE #APR-001                │   │   │
│  │ │ Reset MDP AD     │ │  │                                     │   │   │
│  │ │ jdupont          │ │  │ Action: ad_reset_password           │   │   │
│  │ │ ⏱️ 45 min        │ │  │ Niveau requis: L3                   │   │   │
│  │ └──────────────────┘ │  │ Utilisateur: jdupont                │   │   │
│  │                      │  │                                     │   │   │
│  │ ┌──────────────────┐ │  │ 📋 Contexte:                        │   │   │
│  │ │ 🟡 APR-002       │ │  │ • Ticket GLPI #1234                 │   │   │
│  │ │ Fermeture ticket │ │  │ • Client: EHPAD Music Art           │   │   │
│  │ │ #1234            │ │  │ • Motif: MDP oublié                 │   │   │
│  │ │ ⏱️ 32 min        │ │  │                                     │   │   │
│  │ └──────────────────┘ │  │ 💬 Commentaire: [_______________]   │   │   │
│  │                      │  │                                     │   │   │
│  │ (Pas de bouton       │  │  [✅ Approuver]  [❌ Refuser]       │   │   │
│  │  "Nouvelle demande") │  └────────────────────────────────────┘   │   │
│  └──────────────────────┴───────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Niveaux d'accréditation

| Niveau | Nom | Peut approuver | Exemples d'actions |
|--------|-----|----------------|-------------------|
| **N0** | Lecture seule | Aucune | Voir les demandes uniquement |
| **N1** | Technicien | L1 | Ajout followup, notifications |
| **N2** | Technicien senior | L1, L2 | Déverrouillage compte AD |
| **N3** | Admin | L1, L2, L3 | Reset MDP, fermeture ticket |
| **N4** | Super Admin | L1, L2, L3 | + Gestion utilisateurs |

---

## Roadmap Frontend

### Phase 1 : Onglet Safeguard (Base) ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| F1.1 | Ajouter lien "Safeguard" dans le menu dropdown | `src/components/layout/Header.tsx` | ✅ Fait |
| F1.2 | Créer la route `/safeguard` | `src/App.tsx` | ✅ Fait |
| F1.3 | Créer la page `Safeguard.tsx` | `src/pages/Safeguard.tsx` | ✅ Fait |
| F1.4 | Créer le composant liste des demandes | `src/components/safeguard/RequestList.tsx` | ✅ Fait |
| F1.5 | Créer le composant détail demande | `src/components/safeguard/RequestDetail.tsx` | ✅ Fait |
| F1.6 | Créer le composant carte demande (sidebar) | `src/components/safeguard/RequestCard.tsx` | ✅ Fait |

### Phase 2 : Types & Services ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| F2.1 | Ajouter types `SafeguardRequest`, `ApprovalStatus` | `src/components/safeguard/types.ts` | ✅ Fait |
| F2.2 | Ajouter type `AccreditationLevel` (N0-N4) | `src/types/index.ts` | ✅ Fait |
| F2.3 | Créer service API Safeguard | `src/services/safeguard.ts` | ✅ Fait |
| F2.4 | Créer hook `useSafeguard` | `src/hooks/useSafeguard.ts` | ✅ Fait |

### Phase 3 : Store & State ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| F3.1 | Créer store Zustand pour Safeguard | `src/store/safeguardStore.ts` | ✅ Fait |
| F3.2 | Polling auto avec intervalle configurable | `src/pages/Safeguard.tsx` | ✅ Fait |
| F3.3 | Badge notification en temps réel | `src/components/layout/Header.tsx` | ✅ Fait |

### Phase 4 : Gestion Utilisateurs (Niveaux) ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| F4.1 | Ajouter champ niveau dans formulaire création user | `src/pages/AdminUsers.tsx` | ✅ Fait |
| F4.2 | Ajouter sélecteur niveau (N0-N4) | `src/components/ui/LevelSelector.tsx` | ✅ Fait |
| F4.3 | Afficher niveau dans liste utilisateurs | `src/pages/AdminUsers.tsx` | ✅ Fait |
| F4.4 | Permettre modification niveau existant | `src/pages/AdminUsers.tsx` | ✅ Fait |

### Phase 5 : UX & Polish

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| F5.1 | Badge notification (nombre demandes pending) | `src/components/layout/Header.tsx` | ✅ Fait |
| F5.2 | Timer countdown (expire dans X min) | `src/components/safeguard/RequestCard.tsx` | ✅ Fait |
| F5.3 | Toast confirmation après action | `src/pages/Safeguard.tsx` | ✅ Fait |
| F5.4 | Animation transition liste → détail | `src/pages/Safeguard.tsx` | ⬜ À faire |
| F5.5 | Responsive mobile | `src/pages/Safeguard.tsx` | ⬜ À faire |

---

## Roadmap Backend

### Phase 1 : Base de données ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| B1.1 | Ajouter colonne `accreditation_level` à table `users` | `wibot-backend/init.sql` | ✅ Fait |
| B1.2 | Migration pour users existants (défaut N1) | `wibot-backend/migrations/002_add_accreditation_level.sql` | ✅ Fait |

### Phase 2 : Workflows n8n (Safeguard) ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| B2.1 | Créer workflow `safeguard_requests.json` (list + detail) | `wibot-backend/workflows/safeguard_requests.json` | ✅ Fait |
| B2.2 | Créer workflow `safeguard_actions.json` (approve + reject) | `wibot-backend/workflows/safeguard_actions.json` | ✅ Fait |

### Phase 3 : Workflows n8n (Utilisateurs) ✅ COMPLÈTE

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| B3.1 | Modifier `admin_users.json` - ajout niveau création | `wibot-backend/workflows/admin_users.json` | ✅ Fait |
| B3.2 | Ajouter endpoint modification niveau | `wibot-backend/workflows/admin_users.json` | ✅ Fait |
| B3.3 | Retourner niveau dans `auth_login.json` | `wibot-backend/workflows/auth_login.json` | ✅ Fait |

### Phase 4 : Intégration MCP Server

| # | Tâche | Fichier(s) | Statut |
|---|-------|-----------|--------|
| B4.1 | Configurer connexion Wibot → MCP Server | `wibot-backend/.env` | ⬜ À faire |
| B4.2 | Tester endpoint `/safeguard/pending` | - | ⬜ À faire |
| B4.3 | Tester endpoint `/safeguard/{id}/approve` | - | ⬜ À faire |
| B4.4 | Tester endpoint `/safeguard/{id}/reject` | - | ⬜ À faire |

---

## Spécifications détaillées

### Types TypeScript

```typescript
// src/types/index.ts

// Niveaux d'accréditation
export type AccreditationLevel = 'N0' | 'N1' | 'N2' | 'N3' | 'N4';

export const ACCREDITATION_LABELS: Record<AccreditationLevel, string> = {
  N0: 'Lecture seule',
  N1: 'Technicien',
  N2: 'Technicien Senior',
  N3: 'Admin',
  N4: 'Super Admin',
};

// Statut d'une demande Safeguard
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'executed';

// Demande Safeguard
export interface SafeguardRequest {
  approval_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  security_level: string;
  status: ApprovalStatus;
  created_at: string;
  expires_at: string;
  time_remaining_seconds: number;
  requester_ip?: string;
  context?: {
    ticket_id?: number;
    client_name?: string;
    description?: string;
  };
  approver?: string;
  approval_comment?: string;
}

// User avec niveau
export interface User {
  id: number;
  username: string;
  role: 'user' | 'admin';
  accreditation_level: AccreditationLevel;
  created_at: string;
}
```

### Endpoints API

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| `GET` | `/webhook/wibot/safeguard/pending` | Liste demandes en attente | JWT + N1+ |
| `GET` | `/webhook/wibot/safeguard/:id` | Détail d'une demande | JWT + N1+ |
| `POST` | `/webhook/wibot/safeguard/:id/approve` | Approuver une demande | JWT + niveau requis |
| `POST` | `/webhook/wibot/safeguard/:id/reject` | Refuser une demande | JWT + niveau requis |

### Structure des fichiers (à créer)

```
wibot-frontend/src/
├── pages/
│   └── Safeguard.tsx                 # NOUVEAU
├── components/
│   └── safeguard/                    # NOUVEAU dossier
│       ├── index.ts
│       ├── RequestList.tsx           # Liste sidebar
│       ├── RequestCard.tsx           # Carte dans la liste
│       ├── RequestDetail.tsx         # Vue détail
│       └── ApprovalActions.tsx       # Boutons Approuver/Refuser
│   └── ui/
│       └── LevelSelector.tsx         # NOUVEAU - Sélecteur N0-N4
├── hooks/
│   └── useSafeguard.ts               # NOUVEAU
├── services/
│   └── safeguard.ts                  # NOUVEAU
└── store/
    └── safeguardStore.ts             # NOUVEAU
```

---

## Checklist de progression

### 🎯 Milestone 1 : MVP Safeguard (Semaine 1)

- [x] **F1.1** Menu dropdown avec lien Safeguard ✅
- [x] **F1.2** Route `/safeguard` fonctionnelle ✅
- [x] **F1.3** Page Safeguard basique ✅ (inclut liste + détail avec mock data)
- [ ] **F2.1** Types SafeguardRequest (extraire dans types/index.ts)
- [ ] **F2.3** Service API (mock data) → intégré dans page pour l'instant
- [x] **F1.4** Liste des demandes (mock) ✅ (intégré dans Safeguard.tsx)
- [x] **F1.5** Détail demande (mock) ✅ (intégré dans Safeguard.tsx)

### 🎯 Milestone 2 : Intégration Backend (Semaine 2)

- [ ] **B2.1** Workflow list pending
- [ ] **B2.2** Workflow get detail
- [ ] **B2.3** Workflow approve
- [ ] **B2.4** Workflow reject
- [x] **F2.2** Type AccreditationLevel (N0-N4) ✅
- [x] **F2.3** Service API Safeguard ✅
- [x] **F2.4** Hook useSafeguard ✅
- [x] **F3.1** Store Zustand ✅
- [x] **F3.2** Polling auto (30s) ✅
- [x] **F3.3** Badge notification ✅

### 🎯 Milestone 3 : Niveaux d'accréditation (Semaine 3)

- [ ] **B1.1** Colonne accreditation_level
- [ ] **B1.2** Migration users existants
- [ ] **B3.1** Modification workflow admin_users
- [x] **F4.1** Formulaire création avec niveau ✅
- [x] **F4.2** Composant LevelSelector ✅
- [x] **F4.3** Affichage niveau dans liste ✅
- [x] **F4.4** Modification niveau ✅

### 🎯 Milestone 4 : Polish & Production (Semaine 4)

- [x] **F5.1** Badge notification ✅
- [x] **F5.2** Timer countdown ✅
- [x] **F5.3** Toast confirmations ✅
- [ ] **F5.4** Animations
- [ ] **F5.5** Responsive
- [ ] **B4.1-4** Tests intégration MCP

---

## Notes techniques

### Connexion MCP Server

Le MCP Server expose déjà les endpoints nécessaires dans `safeguard_queue.py` :
- `get_pending_approvals()` → Liste les demandes pending
- `approve()` → Approuve une demande
- `reject()` → Rejette une demande

Les workflows n8n feront le pont entre le frontend Wibot et le MCP Server.

### Sécurité

- Vérifier le niveau d'accréditation de l'utilisateur avant d'afficher/autoriser les actions
- Les demandes L3 ne peuvent être approuvées que par des utilisateurs N3+
- Audit trail : logger qui a approuvé/refusé quoi

### Performance

- Polling des demandes toutes les 30 secondes (configurable)
- Cache local des demandes déjà vues
- Optimistic UI pour les actions (feedback immédiat)

---

## Historique des modifications

| Date | Version | Auteur | Description |
|------|---------|--------|-------------|
| 2026-01-05 | 1.0 | Claude | Création initiale du PRD |
| 2026-01-05 | 1.1 | Claude | Ajout section Flux Métier avec chronologie complète |
| 2026-01-05 | 1.2 | Claude | Complétion Phases 1, 2, 3 et partie Phase 5 (F5.1-F5.3) |
| 2026-01-05 | 1.3 | Claude | Complétion Phase 4 - Gestion niveaux d'accréditation |
| 2026-01-05 | 1.4 | Claude | Backend: Phase 1 (BDD) et Phase 3 (Workflows users) complètes |
| 2026-01-05 | 1.5 | Claude | Backend: Phase 2 (Workflows Safeguard) complète |

---

**Prochaine étape** : Importer les workflows Safeguard dans n8n et tester l'intégration
