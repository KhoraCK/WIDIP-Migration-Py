# Ticket Résolu : TKT-2024-15847

## Informations Ticket
| Champ | Valeur |
|-------|--------|
| **ID** | TKT-2024-15847 |
| **Client** | EHPAD Les Music Art |
| **Date Création** | 12/12/2024 09:15 |
| **Date Résolution** | 12/12/2024 12:30 |
| **Catégorie** | Réseau > Internet > Panne |
| **Priorité** | Urgente |
| **Technicien** | Alexandre Dupont |
| **Temps Résolution** | 3h15 |

## Description du Problème
L'établissement n'a plus d'accès Internet depuis 9h00 ce matin. Tous les postes affichent "Pas de connexion Internet". Le logiciel NetSoins ne peut plus se synchroniser avec le cloud. Les soignants ne peuvent plus accéder aux dossiers patients.

## Diagnostic Réalisé

### Étape 1 : Vérification Phibee
- Connexion à Phibee : https://phibee.widip.local
- Recherche client "EHPAD Les Music Art"
- **Résultat** : Lien affiché en ROUGE - DOWN depuis 08:47

### Étape 2 : Vérification Observium
- État routeur 192.168.1.1 : UP (accessible en local)
- Bande passante WAN : 0 Mbps (confirme panne FAI)
- Aucune alerte locale

### Étape 3 : Contact FAI
- Appel Orange Pro : 3901
- Référence contrat : PRO-2023-78456
- **Diagnostic FAI** : Coupure fibre dans le quartier suite travaux voirie
- **ETA réparation** : 12h00

## Actions Réalisées

1. **09:30** - Ouverture incident chez Orange (Réf: INC-ORA-789456)
2. **09:45** - Information client par email (template MAIL_FAI_PANNE)
3. **10:00** - Mise en place solution de contournement :
   - Activation partage de connexion 4G sur smartphone direction
   - Configuration poste accueil en WiFi sur 4G
   - Priorité : accès NetSoins pour médicaments
4. **12:15** - Orange confirme réparation effectuée
5. **12:20** - Vérification Phibee : lien repassé en VERT
6. **12:25** - Test connectivité OK sur tous les postes
7. **12:30** - Clôture ticket après confirmation client

## Solution Appliquée
Panne FAI (Orange) suite à coupure fibre lors de travaux de voirie. Résolution par l'opérateur. Solution de contournement 4G mise en place pendant l'incident pour maintenir l'accès aux applications critiques.

## Recommandations Post-Incident
- Proposer au client une ligne de backup 4G/5G permanente
- Mettre à jour le PRA avec cette solution de contournement
- Durée panne : 3h27 (08:47 → 12:14)

## Tags
`réseau` `internet` `fai` `orange` `panne` `fibre` `4g` `contournement`

---

# Ticket Résolu : TKT-2024-15923

## Informations Ticket
| Champ | Valeur |
|-------|--------|
| **ID** | TKT-2024-15923 |
| **Client** | Clinique Saint-Joseph |
| **Date Création** | 02/11/2024 14:22 |
| **Date Résolution** | 02/11/2024 20:45 |
| **Catégorie** | Serveur > Windows > Crash |
| **Priorité** | Critique |
| **Technicien** | Marie Lecomte |
| **Temps Résolution** | 6h23 |

## Description du Problème
Le serveur VDI SRV-CSJ-VDI01 ne répond plus. Les utilisateurs en télétravail ne peuvent plus se connecter via Citrix. Environ 25 utilisateurs impactés.

## Diagnostic Réalisé

### Étape 1 : Vérification Observium
- Serveur SRV-CSJ-VDI01 (10.0.1.40) : DOWN
- Dernière métrique : 14:18
- Alertes : "Host unreachable"

### Étape 2 : Vérification Console VMware
- VM SRV-CSJ-VDI01 : État "Not responding"
- Logs ESXi : Erreurs I/O disque multiples
- Diagnostic : Défaillance disque VMFS

### Étape 3 : Analyse Stockage
- Datastore VMFS-SRV01 : Erreurs lecture
- RAID Controller : 1 disque en état "Failed"
- Impact : VM corrompue

## Actions Réalisées

1. **14:45** - Escalade N2 (problème matériel identifié)
2. **15:00** - Contact DSI client (Amélie Rousseau) - Validation intervention
3. **15:30** - Démarrage restauration Veeam :
   - Point de restauration : 02/11/2024 06:00 (RPO 8h)
   - Cible : Datastore VMFS-SRV02 (sain)
4. **17:00** - Restauration VM terminée
5. **17:15** - Démarrage VM - Services Citrix en cours de démarrage
6. **17:45** - Tests accès Citrix :
   - StoreFront : OK
   - Delivery Controller : OK
   - VDA : 3/4 OK, 1 en erreur
7. **18:30** - Réparation VDA défaillant (réinstallation agent)
8. **19:00** - Tests utilisateurs pilotes (3 personnes) : OK
9. **20:00** - Communication aux utilisateurs : service rétabli
10. **20:45** - Clôture après monitoring 45min sans incident

## Solution Appliquée
Restauration complète de la VM depuis sauvegarde Veeam suite à corruption causée par défaillance disque physique. Remplacement disque prévu en maintenance dimanche.

## Données Perdues
- Fichiers temporaires Citrix (non critiques)
- Sessions utilisateurs en cours au moment du crash (reconnexion nécessaire)
- Données perdues estimées : ~8h de travail non sauvegardé sur serveur VDI

## Actions Préventives
1. Remplacement disque défaillant programmé (dimanche 03/11)
2. Revue politique RPO : proposer 4h au lieu de 8h pour serveurs critiques
3. Ajout monitoring prédictif disques (SMART)

## Tags
`serveur` `vdi` `citrix` `crash` `veeam` `restauration` `disque` `vmware`

---

# Ticket Résolu : TKT-2024-16102

## Informations Ticket
| Champ | Valeur |
|-------|--------|
| **ID** | TKT-2024-16102 |
| **Client** | EHPAD Les Music Art |
| **Date Création** | 22/11/2024 10:05 |
| **Date Résolution** | 22/11/2024 10:35 |
| **Catégorie** | Utilisateur > Active Directory > Mot de passe |
| **Priorité** | Normale |
| **Technicien** | Alexandre Dupont |
| **Temps Résolution** | 30min |

## Description du Problème
L'infirmière Caroline Mercier ne peut plus se connecter à son poste. Message "Le mot de passe est incorrect". Elle affirme ne pas avoir changé son mot de passe.

## Diagnostic Réalisé

### Étape 1 : Identification Utilisateur
- Nom : Caroline Mercier
- Login : c.mercier
- Service : Infirmerie
- Établissement : EHPAD Les Music Art

### Étape 2 : Vérification AD
- `ad_check_user("c.mercier")` : Utilisateur existe
- `ad_get_user_info("c.mercier")` :
  - Compte : Actif
  - Dernière connexion : 21/11/2024 18:32
  - **Compte verrouillé** : OUI (5 tentatives échouées à 09:58)
  - Mot de passe expiré : NON

### Étape 3 : Analyse
- L'utilisatrice a probablement fait une faute de frappe répétée
- Le compte s'est verrouillé automatiquement (politique : 5 tentatives)

## Actions Réalisées

1. **10:15** - Validation identité utilisateur par question secrète
2. **10:18** - Déverrouillage compte : `ad_unlock_account("c.mercier")`
3. **10:20** - Demande à l'utilisatrice de réessayer avec son mot de passe habituel
4. **10:22** - **Échec** - L'utilisatrice ne se souvient plus du mot de passe
5. **10:25** - Reset mot de passe : `ad_reset_password("c.mercier", "Widip-Nov2024!")` 
   - Approbation SAFEGUARD L3 obtenue
6. **10:28** - Création lien MySecret avec nouveau mot de passe
7. **10:30** - Envoi lien par email à c.mercier@music-art-ehpad.fr
8. **10:32** - Utilisatrice connectée avec succès
9. **10:35** - Confirmation changement mot de passe personnel effectué

## Solution Appliquée
Compte verrouillé après 5 tentatives de connexion échouées. Déverrouillage du compte puis reset du mot de passe (l'utilisatrice avait oublié son mot de passe). Nouveau mot de passe transmis via MySecret.

## Tags
`utilisateur` `active-directory` `mot-de-passe` `verrouillage` `reset` `mysecret`
