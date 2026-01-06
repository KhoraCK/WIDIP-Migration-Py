# WIDIP_Safeguard_v2
## Orchestrateur Système SAFEGUARD L0-L4

> **Version** : 2.0 | **Type** : Workflow Core | **Trigger** : Execute Workflow (appels MCP Tools)

---

## 🎯 Rôle

Workflow orchestrateur central du système SAFEGUARD. Intercepte tous les appels MCP Tools, vérifie le niveau de sécurité (L0-L4), et décide si l'action peut être auto-exécutée ou nécessite une validation humaine.

**Positionnement** : Cœur du système de sécurité WIDIP, protège toutes les actions sensibles.

---

## 📊 Architecture

```
[MCP Tool appelé]
    ↓
[Check Security Level] (config.py)
    ├─ L0 (Read) → EXECUTE directement
    ├─ L1 (Minor) → LOG + EXECUTE
    ├─ L2 (Moderate) → LOG détaillé + EXECUTE
    ├─ L3 (Sensitive) → DEMANDE VALIDATION HUMAINE
    └─ L4 (Forbidden) → BLOCK total
    ↓
[Si L3] → PostgreSQL: Insert safeguard_approvals
    ↓
[Notify Teams] → WIDIP_Human_Validation_v1
    ↓
[Polling Approval] (check toutes les 10s)
    ├─ Approved → EXECUTE + Log
    ├─ Rejected → ABORT + Log
    └─ Timeout 60min → ABORT + Alert
```

---

## 🔄 Exemple Concret

### L3: Reset password AD avec validation

```
1. [0s]    Agent IA appelle ad_reset_password(username="jdupont")
2. [100ms] Safeguard détecte L3 SENSITIVE
3. [500ms] INSERT PostgreSQL safeguard_approvals (APR-2025-001)
4. [1s]    POST /webhook/human/notify-teams → Notification Teams
5. [1s-60min] Polling approval status toutes les 10s

   [12min] Technicien approve via Dashboard

6. [12min] Status=approved détecté
7. [12min] EXECUTE ad_reset_password() réel
8. [13min] INSERT safeguard_actions_log (success)
9. [13min] RETURN success au workflow initial
```

### L4: Création compte AD bloquée

```
1. [0s]    Agent IA appelle ad_create_user()
2. [100ms] Safeguard détecte L4 FORBIDDEN
3. [100ms] Log alerte sécurité
4. [100ms] RETURN error "Action L4 interdite à l'IA"
5. [200ms] Notification Teams équipe sécurité
```

---

## 🔗 Dépendances

### Workflows appelés

- **WIDIP_Human_Validation_v1** : Notifications Teams
- **WIDIP_Dashboard_Safeguard_v1** : Interface validation

### Base PostgreSQL

| Table | Usage |
|-------|-------|
| `safeguard_approvals` | Demandes validation |
| `safeguard_actions_log` | Audit trail |

### Configuration

Fichier `widip-mcp-server/src/config.py`:
```python
TOOL_SECURITY_LEVELS = {
    "ad_reset_password": SecurityLevel.L3_SENSITIVE,
    "ad_create_user": SecurityLevel.L4_FORBIDDEN,
    # ... 40+ tools mappés
}
```

---

## ⚙️ Paramètres

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Polling interval | 10s | Check approval status |
| Timeout validation | 60min | Expiration demande |
| Notification channel | Teams | Alertes techniciens |

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Safeguard_v2.json`
- **Config** : `widip-mcp-server/src/config.py`
- **Documentation** : `Documentation/Technique/Systeme_SAFEGUARD.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 2.0
