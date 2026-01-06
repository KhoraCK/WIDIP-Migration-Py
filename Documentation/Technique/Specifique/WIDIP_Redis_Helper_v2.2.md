# WIDIP_Redis_Helper_v2.2
## Utilitaire Redis - Cache et Déduplication

> **Version** : 2.2 | **Type** : Workflow Utilitaire | **Trigger** : Execute Workflow (appels internes)

---

## 🎯 Rôle

Workflow utilitaire centralisé pour toutes les opérations Redis (GET, SET, DELETE, EXISTS). Utilisé par tous les autres workflows pour le caching, la déduplication, et les health checks. Évite la duplication de code Redis.

**Positionnement** : Brique infrastructure WIDIP, appelée par 6+ workflows.

---

## 📊 Architecture

```
[Workflow appelant] → Execute Workflow
    ↓
[WIDIP_Redis_Helper_v2.2]
    ├─ GET key → Retourne value
    ├─ SET key value ttl → Stocke
    ├─ DELETE key → Supprime
    ├─ EXISTS key → Vérifie présence
    └─ INCR key → Incrémente compteur
    ↓
[Redis Server] (ioredis client)
    ↓
[Retour JSON] {success, value, error}
```

---

## 🔄 Exemples

### GET (Cache)
```javascript
Input: {action: "get", key: "glpi_health_status"}
Output: {success: true, key: "glpi_health_status", value: "ok"}
```

###SET (Déduplication)
```javascript
Input: {action: "set", key: "ticket_processed:1234", value: "true", ttl: 86400}
Output: {success: true, key: "ticket_processed:1234"}
```

### DELETE (Clear flag)
```javascript
Input: {action: "delete", key: "glpi_down_alert_sent"}
Output: {success: true, deleted: true}
```

---

## 🔗 Workflows dépendants

- WIDIP_Assist_ticket_v6.1 (déduplication tickets)
- WIDIP_Proactif_Observium_v9 (cache diagnostics)
- WIDIP_Health_Check_GLPI_v2 (health status)
- WIDIP_Enrichisseur_v1 (stats RAG)

---

## ⚙️ Configuration

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=***
REDIS_DB=0
```

### Paramètres

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| action | string | required | get\|set\|delete\|exists\|incr |
| key | string | required | Clé Redis |
| value | string | optional | Valeur (pour SET) |
| ttl | number | optional | TTL secondes (pour SET) |

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Redis_Helper_v2.2.json`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 2.2
