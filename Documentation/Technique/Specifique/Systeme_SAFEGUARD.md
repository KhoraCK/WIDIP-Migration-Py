# Système SAFEGUARD v15.3
## Framework Sécurité Actions IA - Niveaux L0 à L4

> **Version** : 15.3 | **Type** : Système Transverse | **Scope** : Tous workflows WIDIP

---

## 🎯 Vision

Le système SAFEGUARD est un framework de sécurité qui protège contre les actions dangereuses de l'IA en implémentant 5 niveaux de sécurité (L0 à L4). Il garantit que les actions sensibles ne sont jamais exécutées sans validation humaine.

**Principe** : "Trust, but verify" - L'IA peut proposer, l'humain valide.

---

## 📊 Niveaux de Sécurité

### L0 - READ_ONLY (Auto, aucune restriction)
- **Actions** : Lecture seule (GLPI, Observium, RAG)
- **Exemples** : `glpi_search_client`, `observium_get_device_status`
- **Validation** : Aucune
- **Log** : Minimal

### L1 - MINOR (Auto avec log)
- **Actions** : Modifications mineures réversibles
- **Exemples** : `glpi_add_ticket_followup`, `memory_add_knowledge`
- **Validation** : Automatique
- **Log** : Standard (PostgreSQL)

### L2 - MODERATE (Auto avec log détaillé)
- **Actions** : Modifications importantes
- **Exemples** : `glpi_assign_ticket`, `ad_unlock_account`
- **Validation** : Automatique
- **Log** : Détaillé + métriques

### L3 - SENSITIVE ⚠️ (Validation humaine OBLIGATOIRE)
- **Actions** : Actions sensibles, impact significatif
- **Exemples** : `ad_reset_password`, `glpi_close_ticket`, `ad_disable_account`
- **Validation** : **Humaine via Dashboard + timeout 60min**
- **Log** : Audit trail complet + approbateur

### L4 - FORBIDDEN 🔴 (Bloqué pour l'IA)
- **Actions** : Interdites à l'IA, humain uniquement
- **Exemples** : `ad_create_user`, `ad_delete_user`
- **Validation** : **Blocage total**
- **Log** : Alerte sécurité

---

## 🏗️ Architecture Système

```
[Agent IA] → Appelle MCP Tool
    ↓
[MCP Server] → Vérifie TOOL_SECURITY_LEVELS (config.py)
    ↓
[Niveau détecté]
    ├─ L0/L1/L2 → EXECUTE + Log
    │   ↓
    │   [PostgreSQL] safeguard_actions_log
    │
    └─ L3 → DEMANDE VALIDATION
        ↓
        [WIDIP_Safeguard_v2]
        ↓
        [PostgreSQL] safeguard_approvals (status=pending)
        ↓
        [WIDIP_Human_Validation_v1] → Teams notification
        ↓
        [Technicien] → Dashboard
            ├─ Approve → EXECUTE + Log
            └─ Reject → ABORT + Log
        ↓
        [Timeout 60min] → AUTO-REJECT + Alert

    └─ L4 → BLOCK IMMÉDIAT
        ↓
        [Log] safeguard_blocks
        ↓
        [Alert] Teams sécurité
```

---

## 🔄 Exemple Flux Complet L3

### Reset Password AD

```
T+0s     Agent IA: "Utilisateur jdupont bloqué → Reset MDP"
T+0.1s   Call: ad_reset_password(username="jdupont")
T+0.2s   MCP Server: Check TOOL_SECURITY_LEVELS
         → ad_reset_password = L3_SENSITIVE
T+0.3s   WIDIP_Safeguard_v2: Demande validation
T+0.5s   PostgreSQL INSERT:
         safeguard_approvals (
           approval_id: APR-2025-001,
           tool_name: ad_reset_password,
           arguments: {"username": "jdupont"},
           status: pending,
           expires_at: NOW() + 60min
         )
T+1s     WIDIP_Human_Validation_v1: Notification Teams
         ╔══════════════════════════════════════╗
         ║ ⚠️ SAFEGUARD - Validation Requise   ║
         ║ Action: Reset MDP AD                ║
         ║ User: jdupont                        ║
         ║ [Approuver] [Refuser] [Détails]     ║
         ╚══════════════════════════════════════╝

T+1s-60min  Polling: Check status toutes les 10s

T+12min  Technicien clique [Approuver]
T+12.1s  Dashboard: POST /safeguard/approve/APR-2025-001
T+12.2s  PostgreSQL UPDATE: status=approved, approver=tech@widip.fr
T+12.3s  Safeguard détecte approved → EXECUTE ad_reset_password()
T+12.5s  MCP Tool exécute reset (LDAP)
T+12.8s  PostgreSQL INSERT safeguard_actions_log:
         {
           approval_id: APR-2025-001,
           action: approved_and_executed,
           executor: tech@widip.fr,
           result: success
         }
T+13s    RETURN au workflow initial: {success: true}
```

---

## 🗄️ Schéma Base de Données

### Table `safeguard_approvals`
```sql
CREATE TABLE safeguard_approvals (
    approval_id VARCHAR(255) PRIMARY KEY,
    tool_name VARCHAR(255) NOT NULL,
    security_level VARCHAR(10) NOT NULL,
    arguments JSONB NOT NULL,
    requester_workflow VARCHAR(255),
    requester_ip VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    approver VARCHAR(255),
    decided_at TIMESTAMP,
    approval_reason TEXT
);
```

### Table `safeguard_actions_log`
```sql
CREATE TABLE safeguard_actions_log (
    log_id SERIAL PRIMARY KEY,
    approval_id VARCHAR(255) REFERENCES safeguard_approvals(approval_id),
    tool_name VARCHAR(255) NOT NULL,
    security_level VARCHAR(10) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- executed | blocked | rejected
    executor VARCHAR(255),
    result VARCHAR(20),  -- success | failure
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔒 Sécurité v15.3

### Corrections Décembre 2025

1. **Dashboard authentifié** : Basic Auth obligatoire
2. **Endpoints POST** : CSRF-safe (plus de GET)
3. **Production enforcement** : Validation config au startup
4. **Audit trail complet** : Toutes actions tracées

---

## 🚀 Workflows Impliqués

| Workflow | Rôle SAFEGUARD |
|----------|----------------|
| **WIDIP_Safeguard_v2** | Orchestrateur central |
| **WIDIP_Dashboard_Safeguard_v1** | Interface approbation web |
| **WIDIP_Human_Validation_v1** | Notifications + Dashboard moderne |

---

## 📚 Configuration

Fichier : `widip-mcp-server/src/config.py`

```python
class SecurityLevel(str, Enum):
    L0_READ_ONLY = "L0"
    L1_MINOR = "L1"
    L2_MODERATE = "L2"
    L3_SENSITIVE = "L3"
    L4_FORBIDDEN = "L4"

TOOL_SECURITY_LEVELS = {
    "ad_reset_password": SecurityLevel.L3_SENSITIVE,
    "ad_create_user": SecurityLevel.L4_FORBIDDEN,
    # ... 40+ tools
}
```

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 15.3
