# PROC-002 : Réinitialisation Mot de Passe Active Directory

## Catégorie
Utilisateur / Active Directory / Authentification

## Symptômes
- L'utilisateur ne peut plus se connecter à son poste
- Message "Mot de passe incorrect" ou "Compte verrouillé"
- L'utilisateur a oublié son mot de passe

## Prérequis
- Vérifier l'identité de l'utilisateur (procédure IDENT-001)
- Accès au MCP Server (tool ad_reset_password - SAFEGUARD L3)

## Procédure

### Étape 1 : Identification Utilisateur
1. Demander à l'utilisateur :
   - Son nom complet
   - Son établissement
   - Son login Windows (si connu)
2. Vérifier dans GLPI que l'utilisateur existe
3. **IMPORTANT** : Valider l'identité par question secrète ou rappel manager

### Étape 2 : Vérification État Compte
1. Utiliser `ad_check_user` pour vérifier si le compte existe
2. Utiliser `ad_get_user_info` pour voir :
   - État du compte (actif/désactivé)
   - Dernière connexion
   - Verrouillage éventuel

### Étape 3 : Déverrouillage si Nécessaire
Si le compte est verrouillé (trop de tentatives) :
1. Utiliser `ad_unlock_account` (SAFEGUARD L1)
2. Informer l'utilisateur qu'il peut réessayer avec son ancien mot de passe

### Étape 4 : Reset Mot de Passe
Si l'utilisateur a oublié son mot de passe :
1. Générer un mot de passe temporaire sécurisé :
   - Minimum 12 caractères
   - Majuscules + minuscules + chiffres + spéciaux
   - Exemple format : `Widip-[Mois][Année]!` → `Widip-Dec2025!`
2. Utiliser `ad_reset_password` (SAFEGUARD L3 - nécessite approbation)
3. Transmettre le mot de passe via MySecret :
   - Utiliser `mysecret_create_secret`
   - Envoyer le lien par email à l'utilisateur
   - Le lien expire après 1 visualisation

### Étape 5 : Finalisation
1. Demander à l'utilisateur de changer son mot de passe à la première connexion
2. Documenter l'action dans le ticket GLPI
3. Clôturer le ticket

## Sécurité
- **JAMAIS** transmettre le mot de passe par téléphone
- **JAMAIS** envoyer le mot de passe en clair par email
- **TOUJOURS** utiliser MySecret pour les mots de passe temporaires

## Temps de Résolution
- Déverrouillage simple : 5 minutes
- Reset complet : 15-30 minutes (inclut approbation L3)

## Tags
`active-directory` `mot-de-passe` `reset` `utilisateur` `sécurité`
