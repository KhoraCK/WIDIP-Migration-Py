# PROC-003 : Dépannage Imprimante Réseau

## Catégorie
Matériel / Impression / Réseau

## Symptômes
- L'imprimante n'imprime plus
- Les documents restent bloqués dans la file d'attente
- Message "Imprimante hors ligne" sur les postes
- Erreur "Impossible de se connecter à l'imprimante"

## Prérequis
- Adresse IP de l'imprimante (disponible dans GLPI - fiche équipement)
- Accès physique ou contact sur site

## Procédure de Diagnostic

### Étape 1 : Vérification État Imprimante
1. Rechercher l'imprimante dans GLPI (`glpi_search_client` puis équipements)
2. Noter l'adresse IP configurée
3. Tester la connectivité : `ping [IP_IMPRIMANTE]`
   - **Répond** → Problème logiciel/driver
   - **Ne répond pas** → Problème réseau/matériel

### Étape 2 : Si Ping KO
1. Demander au client de vérifier physiquement :
   - L'imprimante est allumée ?
   - Le câble réseau est branché ?
   - Des voyants d'erreur sont affichés ?
2. Si imprimante en WiFi :
   - Vérifier que le WiFi est activé sur l'imprimante
   - L'imprimante est sur le bon réseau ?
3. Redémarrer l'imprimante (éteindre, attendre 30s, rallumer)

### Étape 3 : Si Ping OK mais N'imprime Pas
1. Sur le poste utilisateur :
   - Ouvrir "Périphériques et imprimantes"
   - Clic droit sur l'imprimante → "Voir les travaux d'impression"
   - Supprimer tous les documents bloqués
2. Redémarrer le service spouleur :
   ```
   net stop spooler
   net start spooler
   ```
3. Réessayer l'impression

### Étape 4 : Problème Driver
Si l'imprimante répond mais les impressions sont corrompues :
1. Supprimer l'imprimante du poste
2. Réinstaller avec le driver à jour
3. Source drivers : https://support.widip.local/drivers

### Étape 5 : Problème Matériel
Si rien ne fonctionne :
1. Vérifier les niveaux d'encre/toner (panneau imprimante)
2. Vérifier les bourrages papier
3. Si problème matériel confirmé → Créer ticket SAV constructeur

## Cas Particuliers

### Imprimante partagée sur serveur
1. Vérifier que le serveur d'impression est UP
2. Redémarrer le service "Spouleur d'impression" sur le serveur
3. Vérifier les permissions de partage

### Imprimante Xerox/Ricoh avec compteur
1. Vérifier que le compteur n'est pas bloqué
2. Contact : support@xerox.com ou support@ricoh.fr

## Temps de Résolution
- Problème simple (spouleur) : 10 minutes
- Problème driver : 30 minutes
- Problème matériel : Variable (SAV)

## Tags
`imprimante` `réseau` `impression` `spouleur` `driver` `matériel`
