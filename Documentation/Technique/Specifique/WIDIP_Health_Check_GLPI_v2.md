# WIDIP_Health_Check_GLPI_v2
## Surveillance Santé - Circuit Breaker GLPI

> **Version** : 2.0 | **Type** : Workflow Infrastructure | **Trigger** : Schedule 30s

---

## 🎯 Rôle

Workflow de surveillance qui vérifie la disponibilité de l'API GLPI toutes les 30 secondes. Implémente un circuit breaker : si GLPI est DOWN, met à jour Redis pour que les workflows principaux passent en mode dégradé automatiquement.

**Positionnement** : Infrastructure critique WIDIP, évite les timeouts et échecs en cascade.

---

## 📊 Architecture Workflow

### Vue d'ensemble

```
[Schedule 30s] → Trigger automatique
    ↓
[Ping GLPI API] (timeout 5s)
    ↓
[Analyze Health] (ok | degraded | down)
    ↓
[Redis: Update Status] (clé: glpi_health_status, TTL 60s)
    ↓
[GLPI Down ?]
    ├─ DOWN → Check Alert Sent ?
    │   ├─ Pas encore → Send Alert + Mark Sent (TTL 5min)
    │   └─ Déjà envoyée → Skip notification
    └─ OK → Check Was Down ?
        ├─ Oui → Send Recovery + Clear Flag
        └─ Non → Log silencieux
```

### Mécanisme Circuit Breaker

1. **Ping GLPI** : Tentative `initSession` (timeout 5s)
2. **Analyse statut** :
   - `ok` : Session token présent
   - `degraded` : HTTP 401/403 (auth)
   - `down` : Timeout, 5xx, erreur connexion
3. **Mise à jour Redis** : Clé `glpi_health_status` = statut
4. **Autres workflows** : Lisent cette clé avant d'utiliser GLPI

---

## 🔄 Exemple Concret

### Cas 1 : GLPI tombe en panne

**Contexte** :
```
18:32:00 - GLPI fonctionne normalement (status = ok)
18:32:15 - Serveur GLPI crash (base de données KO)
```

**Détection** :
```
1. [18:32:30] Trigger 30s → Ping GLPI
2. [18:32:35] Timeout 5s → Pas de réponse
3. [18:32:35] Analyze Health:
   {
     "status": "down",
     "checked_at": "2025-12-24T18:32:35.000Z",
     "error": "Connection timeout after 5000ms",
     "redis_value": "down"
   }

4. [18:32:36] Redis: Update Status
   SET glpi_health_status = "down" (TTL 60s)

5. [18:32:36] IF GLPI Down? → OUI
6. [18:32:37] Redis: Check Alert Sent
   GET glpi_down_alert_sent → null (pas encore envoyée)

7. [18:32:37] Should Send Alert? → OUI
8. [18:32:38] Prepare Down Alert:
   {
     "type": "glpi_down",
     "severity": "critical",
     "title": "🚨 GLPI DOWN - Circuit Breaker Activé",
     "message": "GLPI API ne répond plus.\n\nErreur: Connection timeout\nHeure: 18:32:35\n\nLes workflows Proactif et Assist passent en mode dégradé."
   }

9. [18:32:39] [NOTIFICATION TEAMS ENVOYÉE]
10. [18:32:40] Redis: Mark Alert Sent
    SET glpi_down_alert_sent = "sent" (TTL 300s = 5min)

11. [18:32:40] Log: "GLPI DOWN détecté"
```

**Pendant la panne** :
```
[18:33:00] Trigger 30s → Ping GLPI → DOWN
           Redis: Update Status → "down"
           Alert déjà envoyée → Skip notification

[18:33:30] Trigger 30s → Ping GLPI → DOWN
           Redis: Update Status → "down"
           Alert déjà envoyée → Skip notification

[... toutes les 30s, recheck silencieux ...]
```

**Impact sur autres workflows** :
```
[18:32:45] WIDIP_Proactif_Observium_v9 démarre:
   → Redis: Check GLPI Health
   → GET glpi_health_status → "down"
   → IF GLPI OK? → NON
   → Mode Dégradé activé (skip création ticket)

[18:33:12] WIDIP_Assist_ticket_v6.1 démarre:
   → Redis: Check GLPI Health
   → GET glpi_health_status → "down"
   → Alerte technicien "GLPI indisponible, intervention manuelle requise"
```

---

### Cas 2 : GLPI revient en ligne (Recovery)

**Contexte** :
```
18:47:00 - GLPI DOWN depuis 15 minutes
18:47:10 - Admin redémarre serveur GLPI
18:47:30 - GLPI accessible à nouveau
```

**Détection Recovery** :
```
1. [18:47:30] Trigger 30s → Ping GLPI
2. [18:47:31] Response 200 + session_token présent
3. [18:47:31] Analyze Health:
   {
     "status": "ok",
     "checked_at": "2025-12-24T18:47:31.000Z",
     "error": null
   }

4. [18:47:32] Redis: Update Status
   SET glpi_health_status = "ok" (TTL 60s)

5. [18:47:32] IF GLPI Down? → NON
6. [18:47:32] GLPI OK Handler
7. [18:47:33] Redis: Check Was Down
   GET glpi_down_alert_sent → "sent" (flag présent)

8. [18:47:33] Was Previously Down? → OUI
9. [18:47:34] Prepare Recovery Alert:
   {
     "type": "glpi_recovered",
     "severity": "info",
     "title": "✅ GLPI RECOVERED - Circuit Breaker Désactivé",
     "message": "GLPI API est de nouveau accessible.\n\nLes workflows reprennent le fonctionnement normal."
   }

10. [18:47:35] [NOTIFICATION TEAMS ENVOYÉE]
11. [18:47:36] Redis: Clear Down Flag
    DEL glpi_down_alert_sent

12. [18:47:36] Log: "GLPI recovered, circuit breaker cleared"
```

**Reprise workflows** :
```
[18:48:00] WIDIP_Assist_ticket_v6.1:
   → Redis: GET glpi_health_status → "ok"
   → Mode normal repris, tickets traités
```

---

## 🔗 Dépendances

### Workflows appelés

| Workflow | Usage |
|----------|-------|
| **WIDIP_Redis_Helper_v2.2** | GET/SET/DELETE clés Redis |

### Workflows dépendants (consommateurs)

| Workflow | Usage du health check |
|----------|----------------------|
| **WIDIP_Proactif_Observium_v9** | Skip création ticket si GLPI DOWN |
| **WIDIP_Assist_ticket_v6.1** | Mode dégradé si GLPI DOWN |

### Services externes

- **GLPI API** : Endpoint `/apirest.php/initSession` surveillé
- **Redis** : Stockage statut + flags alertes

---

## ⚙️ Configuration

### Variables d'environnement

```bash
GLPI_API_URL=http://localhost:8670
GLPI_APP_TOKEN=***
GLPI_USER_TOKEN=***
REDIS_HELPER_V2_WORKFLOW_ID=aCuwZ3jJb1c2dMVY
```

### Paramètres clés

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Check interval | 30s | Fréquence vérification |
| Ping timeout | 5s | Timeout requête GLPI |
| Redis TTL health | 60s | Expiration statut |
| Alert cooldown | 5min (300s) | Anti-spam notifications |

### Clés Redis utilisées

| Clé | Valeurs possibles | TTL | Usage |
|-----|-------------------|-----|-------|
| `glpi_health_status` | `ok` `degraded` `down` | 60s | Statut GLPI actuel |
| `glpi_down_alert_sent` | `sent` (ou absent) | 300s | Flag anti-spam alertes |

---

## 📊 Métriques

Le workflow ne persiste pas de métriques, mais log dans la console :
- Statut actuel (ok/degraded/down)
- Erreurs détectées (timeouts, HTTP codes)
- Transitions (ok → down, down → ok)

---

## 🚀 Points clés

### ✅ Ce qui fonctionne bien
- **Réactivité** : Détection panne en max 30s
- **Anti-spam** : Alerte unique toutes les 5min
- **Recovery auto** : Notification rétablissement
- **Circuit breaker efficace** : Évite timeouts en cascade
- **TTL court** : Si Health Check crash, Redis expire = workflows reprennent

### ⚠️ Points d'attention
- **Pas de persistance** : Pas d'historique pannes (seulement logs console)
- **Granularité 30s** : Micro-coupures < 30s peuvent être manquées
- **Single point** : Si Health Check workflow crash, pas de détection
- **Dépendance Redis** : Si Redis KO, circuit breaker inefficace

---

## 🔧 Nouveautés v2

### Changements vs v1
- ✅ **Execute Sub-Workflow** au lieu de HTTP Request direct vers Redis
- ✅ Cohérent avec architecture MCP centralisée
- ✅ Plus rapide (~10ms vs ~20ms)
- ✅ Réutilise WIDIP_Redis_Helper_v2.2

---

## 📚 Fichiers liés

- **Workflow** : `Workflow principaux/WIDIP_Health_Check_GLPI_v2.json`
- **Redis Helper** : `Workflow utilitaires/WIDIP_Redis_Helper_v2.2.json`
- **Architecture globale** : `Documentation/Technique/WIDIP_ARCHITECTURE_v15.md`

---

**Dernière mise à jour** : 24 Décembre 2025 | **Version** : 2.0
