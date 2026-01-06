# PROC-001 : Diagnostic Panne Internet Établissement

## Catégorie
Réseau / Connectivité / FAI

## Symptômes
- Aucun accès Internet sur l'ensemble de l'établissement
- Les postes affichent "Pas d'accès Internet"
- Le logiciel métier ne se connecte pas au serveur distant

## Prérequis
- Accès Phibee pour vérifier l'état du lien
- Accès Observium pour les métriques réseau
- Numéro de contrat FAI du client

## Procédure de Diagnostic

### Étape 1 : Vérification Phibee
1. Se connecter à Phibee (https://phibee.widip.local)
2. Rechercher l'établissement par nom ou code client
3. Vérifier le statut du lien :
   - **VERT** : Lien UP → Problème local
   - **ROUGE** : Lien DOWN → Problème FAI

### Étape 2 : Si Lien DOWN (FAI)
1. Noter l'heure de début de panne (timestamp Phibee)
2. Contacter le FAI avec :
   - Numéro de contrat : disponible dans GLPI fiche client
   - Adresse IP publique : visible dans Observium
   - Description : "Lien DOWN depuis [heure]"
3. Créer ticket GLPI catégorie "Réseau > FAI > Panne"
4. Informer le client par email (template MAIL_FAI_PANNE)

### Étape 3 : Si Lien UP (Local)
1. Vérifier dans Observium :
   - État du routeur/firewall
   - Saturation bande passante
   - Alertes actives
2. Demander au client de vérifier :
   - Câble réseau branché sur le routeur
   - Voyants du routeur (Power, Internet, LAN)
3. Si routeur KO → Planifier intervention sur site

## Temps de Résolution Moyen
- Panne FAI : 2-4h (dépend du FAI)
- Problème local : 30min-2h

## Escalade
Si non résolu après 4h → Escalade N2 (Responsable Réseau)

## Tags
`réseau` `internet` `fai` `phibee` `diagnostic` `panne`
