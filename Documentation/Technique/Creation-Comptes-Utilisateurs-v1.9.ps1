<###############################################################################################################

SCRIPT : Création automatique de comptes utilisateurs
AUTEUR : Alexis MACAIRE (amacaire@widip.fr)

VERSION : 1.9

----------------------------------------------------------------------------------------------------------------
DESCRIPTION
----------------------------------------------------------------------------------------------------------------
Ce script permet d’automatiser la création de comptes utilisateurs, soit :
- à partir d’un fichier Excel (converti automatiquement en CSV par le script),
- soit via une saisie manuelle pour la création d’un seul compte.

Il prend en charge l’ensemble du processus de création, incluant :
- la création du compte Active Directory,
- l’attribution des attributs AD,
- la création et la configuration des dossiers USERS et PROFILES,
- la désactivation de l’héritage des droits,
- la création de la boîte mail,
- l’attribution de la licence Office 365 ou la création du compte Exchange selon le client,
- la création du compte GLPI.

En l’absence d’un compte référent, le script proposera de définir manuellement l’OU de l’utilisateur.

----------------------------------------------------------------------------------------------------------------
FONCTIONNEMENT
----------------------------------------------------------------------------------------------------------------
• Création de plusieurs comptes :
  - Placer le fichier Excel dans le dossier :
    C:\Users\adminwidip\Desktop\CSV_Création\
  - Exécuter le script.

• Création d’un seul compte :
  - Exécuter directement le script et suivre les instructions.

Lors de l’exécution, les identifiants du tenant Office 365 sont requis.
Le mot de passe est stocké dans RDM.

----------------------------------------------------------------------------------------------------------------
SORTIE
----------------------------------------------------------------------------------------------------------------
À la fin de l’exécution, le fichier "identifiant.txt" est automatiquement ouvert.
Il contient les identifiants de connexion générés pour chaque utilisateur, à transmettre au client
pour la clôture du ticket.

----------------------------------------------------------------------------------------------------------------
HISTORIQUE DES RÉVISIONS
----------------------------------------------------------------------------------------------------------------
v0.1 - 15/12/2025 : Création initiale du script
v1.1 - 16/12/2025 : Ajout de la compatibilité avec le client ADAPEI01
v1.2 - 17/12/2025 : Ajout de la compatibilité avec le client PRADO
v1.3 - 18/12/2025 : Ajout de la compatibilité avec le client PEP01
v1.4 - 19/12/2025 : Ajout de la compatibilité avec le client WITKOWSKA
v1.5 - 22/12/2025 : Ajout de la compatibilité avec le client ODYNEO
v1.6 - 24/12/2025 : Ajout de la compatibilité avec le client MFI/MFRPDS
v1.7 - 29/12/2025 : Ajout de la compatibilité avec le client SAUVEGARDE69
v1.8 - 29/12/2025 : Ajout de la compatibilité avec le client ALR
v1.9 - 30/12/2025 : Ajout de la compatibilité avec le client ADPA

################################################################################################################>


Import-Module ActiveDirectory
try { Import-Module ADSync -ErrorAction SilentlyContinue } catch {}
Import-Module ImportExcel
Import-Module Microsoft.Graph.Users
Import-Module Microsoft.Graph.Identity.DirectoryManagement


<#####################################################################################      
#                                                                                    #           
#                                                                                    #        
#                                                                                    #
#                                Configuration Clients                               #
#                                                                                    #
#                                                                                    #
#                                                                                    #
#####################################################################################>

$ClientConfigs = @{
    "ADAPEI01.LOCAL" = @{
        Name = "ADAPEI01"
        DossierUsers = "\\fichier02\Data\USERS"
        DossierProfils = "\\fichier02\Data\PROFILS"
        RootOU = "OU=ADAPEI01,DC=ADAPEI01,DC=LOCAL"
        EmailDomain = "adapei01.fr"
        EmailFormat = "{firstname}.{lastname}" #john.doe@domaine
        UPNSuffix = "adapei01.fr"
        UsernameFormat = "{initial}.{lastname}" # j.doe
        AzureDisplayName = "{lastname} {firstname}" # NOM Prenom
        DisplayNameFormat = "{lastname} {firstname}" # NOM Prenom
        DefaultGroup = "ADAPEI_USERS"
        HasAzureAD = $true
        HasExchange = $false
        HasOffice365 = $true
        PasswordLength = 12
        DefaultGLPIEntity = "150"
        LicenseSKU = @{
            Default = "STANDARDPACK"    # E1
            Premium = "ENTERPRISEPACK"  # E3
        }
        ADAttributes = @{
            extensionAttribute4 = "arrivalDate"
            department = "company"
            Title = "poste_employe"
            description = "company"
            company = "company"
        }
    }
    "PEP01.LOCAL" = @{
        Name = "PEP01"
        DossierUsers = "\\fichier01\Data\USERS"
        DossierProfils = "\\fichier01\Data\PROFILES"
        RootOU = "OU=PEP01,DC=PEP01,DC=LOCAL"
        EmailDomain = "lespep01.org"
        UPNSuffix = "lespep01.org"
        EmailFormat = "{firstname}.{lastname}" #john.doe@domaine
        UsernameFormat = "{lastname}.{firstname}" # doe.john
        AzureDisplayName = "{lastname} {firstname}" # NOM Prenom
        DisplayNameFormat = "{lastname} {firstname}" # NOM Prenom
        DefaultGroup = $null
        HasAzureAD = $true
        HasExchange = $false
        HasOffice365 = $true
        AzureAccountId = "adminwidip@lespep01.org"
        PasswordLength = 10
        DefaultGLPIEntity = "350"
        LicenseSKU = @{
            Default = "ENTERPRISEPACK"
        }
        ADAttributes = @{
            company = "company"
        }
    }
    "PRADO.LAN" = @{
        Name = "PRADO"
        DossierUsers = "\\fichier\DATA\USERS"
        DossierProfils = "\\fichier\DATA\PROFILES"
        RootOU = "OU=Etablissements,DC=prado,DC=lan"
        EmailDomain = "le-prado.fr"
        UPNSuffix = "prado.lan"
        EmailFormat = "{initial}{lastname}" #jdoe@domaine
        UsernameFormat = "{initial}{lastname}" # jdoe
        DisplayNameFormat = "{firstname} {lastname}" # Prenom NOM
        DefaultGroup = "Cloud_PRADO"
        HasAzureAD = $false
        HasExchange = $true
        HasOffice365 = $false
        ExchangeServer = "EXCH01.PRADO.LAN"
        PasswordLength = 10
        DefaultGLPIEntity = "159"
        ADAttributes = @{
            extensionAttribute4 = "arrivalDate"
            company = "company"
            personalTitle = "personalTitle"
        }
    }
    "WITKOWSKA.LOCAL" = @{
        Name = "WITKOWSKA"
        DossierUsers = "\\fichier01\DATA\USERS"
        DossierProfils = "\\fichier01\DATA\PROFILES"
        RootOU = "OU=WITKOWSKA_67,DC=WITKOWSKA,DC=LOCAL"
        EmailDomain = "centre-witkowska.org"
        UPNSuffix = "WITKOWSKA.LOCAL"
        EmailFormat = "{firstname}.{lastname}" #john.doe@domaine
        UsernameFormat = "{initial}.{lastname}" # j.doe
        DisplayNameFormat = "{lastname} {firstname}" # NOM Prenom
        DefaultGroup = "Bureau_WITKOWSKA"
        HasAzureAD = $false
        HasExchange = $true
        HasOffice365 = $false
        ExchangeServer = "EXCH01.WITKOWSKA.LOCAL"
        PasswordLength = 12
        DefaultGLPIEntity = "67"
        ADAttributes = @{
            extensionAttribute4 = "arrivalDate"
            company = "company"
        }
    }

   "adsea69s.local" = @{
        Name = "SAUV69"
        DossierUsers = "\\fichier01\DATA\USERS" # Si l'utilisateur n'est pas en UPD
        DossierProfils = "\\fichier01\DATA\PROFILES" # Si l'utilisateur n'est pas en UPD
        RootOU = "OU=ETABLISSEMENTS,DC=adsea69s,DC=local"
        EmailDomain = "sauvegarde69.fr"
        UPNSuffix = "sauvegarde69.fr"
        EmailFormat = "{firstname}.{lastname}" #john.doe@domaine
        UsernameFormat = "{firstname}.{lastname}" # john.doe
        DisplayNameFormat = "{lastname} {firstname} ({ou})" # NOM Prenom (OU)
        AzureDisplayName = "{lastname} {firstname}" # NOM Prenom
        DefaultGroup = $null
        HasAzureAD = $true
        HasExchange = $false
        HasOffice365 = $true
        PasswordLength = 12
        DefaultGLPIEntity = "341"
        UDPCheckGroup = "GG_Bureau_Sauv69"  # Groupe pour déterminer si profil itinérant ou UPD
        LicenseSKU = @{
            Default = "STANDARDPACK"    # E1
            Premium = "ENTERPRISEPACK"  # E3
        }
        ADAttributes = @{
            extensionAttribute1 = "extensionAttribute1"
            extensionAttribute2 = "extensionAttribute2"
            extensionAttribute4 = "arrivalDate"
            company = "company"
            title = "poste_employe"
            postalCode = "postalCode"
            l = "l"
            streetAddress = "streetAddress"
        }
    }

    "mfi.local" = @{
        Name = "MFI/MFRPDS"
        DossierUsers = $null # UPD
        DossierProfils = $null # UPD
        RootOU = "OU=MFI,DC=mfi,DC=local"
        EmailDomain = "mutualiteisere.org"
        EmailFormat = "{initial}{lastname}" #jdoe@domaine
        UPNSuffix = "mfi.local"
        UsernameFormat = "{initial}{lastname}" # jdoe
        DisplayNameFormat = "{firstname} {lastname}" # Prenom NOM
        DefaultGroup = $null
        HasAzureAD = $false
        HasExchange = $true
        HasOffice365 = $false
        ExchangeServer = "EXCH02.mfi.local"
        PasswordLength = 16
        DefaultGLPIEntity = "4"
        ADAttributes = @{
            extensionAttribute4 = "arrivalDate"
            company = "company"
        }
    }

     "arimc.ra.siege.int" = @{
        Name = "Odyneo"
        DossierUsers = $null
        DossierProfils = $null
        RootOU = "OU=ETABLISSEMENTS,DC=arimc,DC=ra,DC=siege,DC=int"
        EmailDomain = "odyneo.fr"
        EmailFormat = "{firstname}.{lastname}" #john.doe@domaine
        UPNSuffix = "odyneo.fr"
        UsernameFormat = "{initial}{lastname}" # jdoe
        DisplayNameFormat = "{firstname} {lastname}" # Prenom NOM
        AzureDisplayName = "{firstname} {lastname} " # Prenom NOM
        DefaultGroup = $null
        HasAzureAD = $true
        HasExchange = $false
        HasOffice365 = $true
        PasswordLength = 12
        DefaultGLPIEntity = "1"
        LicenseSKU = @{
            Default = "STANDARDPACK"    # E1
            Premium = "ENTERPRISEPACK"  # E3
        }
        ADAttributes = @{
            company = "company"
        }
    }

    "alr.local" = @{
        Name = "ALR"
        DossierUsers = "\\fichier001\USERS_DATA"
        DossierProfils = $null
        RootOU = "OU=ETABLISSEMENTS ALR,DC=alr,DC=local"
        EmailDomain = "laroche.asso.fr"
        EmailFormat = "{initial}.{lastname}" #j.doe@domaine
        UPNSuffix = "alr.local"
        UsernameFormat = "{initial}{lastname}" # jdoe
        DisplayNameFormat = "{lastname} {firstname}" # NOM Prenom
        DefaultGroup = $null
        HasAzureAD = $false
        HasExchange = $true
        HasOffice365 = $false
        PasswordLength = 12
        DefaultGLPIEntity = "13"
        ExchangeServer = "EXCH001.ALR.LOCAL"
        SecondaryEmailDomain = "alr.asso.fr"  # Email secondaire
        CloudGroups = @("ALR_Data", "Bureau_ALR")  # Groupes pour comptes Cloud (BV)
        ADAttributes = @{
            extensionAttribute1 = "extensionAttribute1"
            company = "company"
        }
    }

    "adpa-ni.local" = @{
        Name = "ADPA"
        DossierUsers = "\\fichier01\Users"
        DossierProfils = $null
        RootOU = "OU=UTILISATEURS,DC=adpa-ni,DC=local"
        EmailDomain = "adpa-nordisere.org"
        EmailFormat = "{initial}{lastname}" #jdoe@domaine
        UPNSuffix = "adpabj.local"
        UsernameFormat = "{initial}{lastname}" # jdoe
        AzureDisplayName = "{firstname} {lastname} " # Prenom NOM
        DisplayNameFormat = "{firstname} {lastname}" # Prenom NOM
        DefaultGroup = $null
        HasAzureAD = $true
        HasExchange = $false
        HasOffice365 = $true
        PasswordLength = 12
        DefaultGLPIEntity = "7"
        LicenseSKU = @{
            Default = "STANDARDPACK"    # E1
            Premium = "ENTERPRISEPACK"  # E3
        }
        CloudGroups = $null  # Groupes ajoutés uniquement si BV
        ADAttributes = @{
            extensionAttribute1 = "extensionAttribute1"
            company = "company"
        }
    }


}

# Configuration GLPI
$GLPIConfig = @{
    URL_API = "https://support.widip.fr/apirest.php/"
    USER_TOKEN = "FSVQHS32dtXt83OyQiw06JVtjmA2YJFQ6dK078AP"
    Headers = @{ "Content-Type" = "application/json" }
}

# Chemins CSV
$CSVPaths = @{
    Creation = "C:\Sources\Alexis\Creation de compte\CSV_Creation\compte.csv"
    Source = "C:\Sources\Alexis\Creation de compte\CSV_Creation\"
    Origin = "C:\Sources\Alexis\CSV\CSV_Creation.csv"
}


<#####################################################################################      
#                                                                                    #           
#                                                                                    #        
#                                                                                    #
#                               Fonctions Utilitaires                                #
#                                                                                    #
#                                                                                    #
#                                                                                    #
#####################################################################################>
function Remove-Accents {
    param([string]$text)
    $accents = @{
        'à'='a'; 'â'='a'; 'ä'='a'; 'á'='a'; 'é'='e'; 'è'='e'; 'ê'='e'; 'ë'='e'
        'î'='i'; 'ï'='i'; 'ô'='o'; 'ö'='o'; 'û'='u'; 'ü'='u'; 'ù'='u'; 'ç'='c'
    }
    foreach ($char in $accents.Keys) { $text = $text -replace $char, $accents[$char] }
    return $text
}

function Format-Name {
    param(
        [string]$firstname, 
        [string]$lastname,
        [string]$format = "{lastname} {firstname}",
        [string]$ouName = ""
    )
    $formattedPrenom = $firstname.Substring(0,1).ToUpper() + $firstname.Substring(1).ToLower()
    $formattedNom = $lastname.ToUpper()
    
    switch ($format) {
        "{firstname} {lastname}" { return "$formattedPrenom $formattedNom" }
        "{lastname} {firstname}" { return "$formattedNom $formattedPrenom" }
        "{lastname} {firstname} ({ou})" { 
            if ($ouName) {
                return "$formattedNom $formattedPrenom ($ouName)"
            } else {
                return "$formattedNom $formattedPrenom"
            }
        }
        default { return "$formattedNom $formattedPrenom" }
    }
}


function Format-CompositeName {
    param([string]$firstname, [string]$lastname)
    if (($firstname -split '\s+').Length -ge 2 -or ($lastname -split '\s+').Length -ge 2) {
        $formattedFirstname = ($firstname -split '\s+')[0]
        $formattedLastname = $lastname -replace '\s+', ''
        return @{
            UserId = "$($formattedFirstname.Substring(0,1).ToLower()).$($formattedLastname.ToLower())"
            Email = "$($formattedFirstname.ToLower()).$($formattedLastname.ToLower())"
        }
    }
    return $null
}

function Generate-Password {
    param([int]$length = 16)
    $chars = @{
        Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        Lower = "abcdefghijklmnopqrstuvwxyz"
        Digit = "0123456789"
        Special = "!@$*"
    }
    $password = @(
        $chars.Upper[(Get-Random -Maximum $chars.Upper.Length)]
        $chars.Lower[(Get-Random -Maximum $chars.Lower.Length)]
        $chars.Digit[(Get-Random -Maximum $chars.Digit.Length)]
        $chars.Special[(Get-Random -Maximum $chars.Special.Length)]
    )
    $allChars = $chars.Upper + $chars.Lower + $chars.Digit + $chars.Special
    for ($i = $password.Count; $i -lt $length; $i++) {
        $password += $allChars[(Get-Random -Maximum $allChars.Length)]
    }
    return -join ($password | Get-Random -Count $password.Count)
}

function Convert-SemicolonToComma {
    param([string]$filePath)
    if (Test-Path $filePath) {
        $content = Get-Content -Path $filePath -Raw -Encoding UTF8
        $content = $content -replace ';', ','
        Set-Content -Path $filePath -Value $content -Encoding UTF8
    }
}

function Wait-ADSyncCompletion {
    try {
        $syncStatus = Get-ADSyncScheduler
        while ($syncStatus.SyncCycleInProgress -eq $true) {
            Start-Sleep -Seconds 5
            $syncStatus = Get-ADSyncScheduler
        }
    } catch {}
}


function Convert-ExcelToCsv {
    param([string]$sourceFolder = $CSVPaths.Source)
    $excelFiles = Get-ChildItem -Path $sourceFolder -Filter *.xlsx -ErrorAction SilentlyContinue
    if ($excelFiles.Count -eq 0) { return }
    
    foreach ($file in $excelFiles) {
        try {
            $excelData = Import-Excel -Path $file.FullName
            $csvFileName = [System.IO.Path]::ChangeExtension($file.FullName, ".csv")
            $csvContent = $excelData | ConvertTo-Csv -NoTypeInformation
            $cleanCsvContent = $csvContent | ForEach-Object { $_ -replace '"', '' }
            $cleanCsvContent | Out-File -FilePath $csvFileName -Encoding utf8
            Remove-Item -Path $file.FullName -ErrorAction Stop
        } catch {
            Write-Host -ForegroundColor Red "    Échec de conversion : $($file.FullName)"
        }
    }
}

function Get-UserInput {
    param([hashtable]$config)
    
    $user = [ordered]@{}
    do {
        $user.prenom = Read-Host "    Entrez le prénom de l'utilisateur"
        $user.prenom = $user.prenom.Substring(0,1).ToUpper() + $user.prenom.Substring(1).ToLower()
    } while ([string]::IsNullOrWhiteSpace($user.prenom) -or $user.prenom.Length -eq 1)
    
    do {
        $user.nom = Read-Host "    Entrez le nom de l'utilisateur"
        $user.nom = $user.nom.ToUpper()
    } while ([string]::IsNullOrWhiteSpace($user.nom) -or $user.nom.Length -eq 1)
    
    # Demander le genre uniquement pour PRADO
    if ($config.Name -eq "PRADO") {
        Write-Host ""
        Write-Host -ForegroundColor Yellow "    Sélectionnez la civilité :"
        Write-Host -ForegroundColor Cyan "    1. M."
        Write-Host -ForegroundColor Cyan "    2. Mme"
        
        do {
            $genreChoice = Read-Host "`n    Entrez 1 ou 2"
        } while ($genreChoice -ne '1' -and $genreChoice -ne '2')
        
        $user.personalTitle = if ($genreChoice -eq '1') { "M." } else { "Mme" }
    }
    
    $user.poste = (Read-Host "    Entrez la fonction de l'utilisateur").ToUpper()
    if ([string]::IsNullOrWhiteSpace($user.poste)) { $user.poste = "N/A" }
    
    $user.etablissement = (Read-Host "    Entrez l'établissement de l'utilisateur").ToUpper()
    if ([string]::IsNullOrWhiteSpace($user.etablissement)) { $user.etablissement = "N/A" }
    
    $user.nom_compte_referent = (Read-Host "    Entrez le nom du compte référent").ToUpper()
    return $user
}

function Add-UserToCSV {
    param([string]$csvPath, [hashtable]$user, [hashtable]$config)
    if (-not $csvPath) { return }
    
    # Ajouter personalTitle uniquement pour PRADO
    if ($config.Name -eq "PRADO") {
        $fieldsOrder = @("prenom", "nom", "personalTitle", "poste", "etablissement", "nom_compte_referent")
    } else {
        $fieldsOrder = @("prenom", "nom", "poste", "etablissement", "nom_compte_referent")
    }
    
    $userLine = @()
    foreach ($field in $fieldsOrder) {
        if ($user.ContainsKey($field)) {
            $userLine += $user[$field]
        } else {
            $userLine += ""
        }
    }
    $userLine = $userLine -join ","
    
    if (-Not (Test-Path $csvPath)) {
        $header = $fieldsOrder -join ","
        Set-Content -Path $csvPath -Value $header -Encoding UTF8
        Add-Content -Path $csvPath -Value $userLine -Encoding UTF8
    } else {
        Add-Content -Path $csvPath -Value $userLine -Encoding UTF8
    }
}


function Try-ConnectMgGraph {
    param([string]$accountId)
    try {
        Connect-MgGraph -Scopes "User.ReadWrite.All","Group.ReadWrite.All","Organization.Read.All" -NoWelcome -ErrorAction Stop
        Write-Host -ForegroundColor Green "   Connexion réussie à Microsoft Graph."
        return $true
    } catch {
        Write-Host -ForegroundColor Red "   Échec de la connexion à Microsoft Graph."
        return $false
    }
}

function Connect-ExchangeServer {
    param([string]$exchangeServer)
    try {
        $session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri "http://$exchangeServer/PowerShell/" -Authentication Kerberos
        Import-PSSession $session -DisableNameChecking -AllowClobber | Out-Null
        return $session
    } catch {
        Write-Host -ForegroundColor Red "    Erreur lors de la connexion à Exchange : $_"
        return $null
    }
}


function Init-GLPISession {
    try {
        # Authentification via header Authorization (PAS de body avec GET)
        $auth = "user_token $($GLPIConfig.USER_TOKEN)"
        $headers = @{
            "Content-Type"  = "application/json"
            "Authorization" = $auth
        }
        $url = "$($GLPIConfig.URL_API)initSession"
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers
        $script:GLPIHeaders = @{
            "Content-Type"  = "application/json"
            "Session-Token" = $response.session_token
        }
        return $true
    } catch {
        Write-Host -ForegroundColor Red "    Erreur GLPI : $_"
        return $false
    }
}

function Close-GLPISession {
    try {
        Invoke-RestMethod -Uri "$($GLPIConfig.URL_API)killSession" -Method Get -Headers $script:GLPIHeaders | Out-Null
    } catch {}
}

function Create-GLPIUserFull {
    param(
        [string]$upn,
        [string]$firstname,
        [string]$lastname,
        [string]$password,
        [string]$referentUPN
    )
    $URL_API = $GLPIConfig.URL_API
    $GLPIuserId = $null
    $EtabId = $config.DefaultGLPIEntity
    
    try {
        Init-GLPISession | Out-Null
        
        $HEADERS = $script:GLPIHeaders
        
        Write-Host -ForegroundColor Green "    ✔ Connexion à la base de données GLPI réussi ! Création du compte en cours... Merci de patienter."

        # Récupération de l'entité cible via le référent si fourni
        if ($referentUPN) {
            $apiUrl = "$URL_API" + "User?range=0-50000"
            $initialResponse = Invoke-RestMethod -Uri $apiUrl -Method Get -Headers $HEADERS
            $AlluserGLPI = $initialResponse | Select-Object id, name, entities_id
            $Gooduser = $AlluserGLPI | Where-Object { $_.name -eq $referentUPN }
            $good_glpireferentid = $Gooduser.id
            
            if (-not $good_glpireferentid) {
                # Aucun compte référent trouvé → utiliser l'entité par défaut
                $EtabId = $config.DefaultGLPIEntity
            } else {
                # Récupérer l'entité du référent
                $url = "$URL_API" + "User/$good_glpireferentid/Profile_User"
                try {
                    $response = Invoke-RestMethod -Uri $url -Method Get -Headers $HEADERS
                    $EtabId = $response.entities_id
                } catch {
                    Write-Host -ForegroundColor Red "    Erreur: $($_.Exception.Message)"
                }
                if (-not $EtabId) {
                    Write-Host -ForegroundColor Red "    Erreur: Entité invalide. Impossible d'assigner l'entité sur le compte GLPI."
                    $EtabId = $config.DefaultGLPIEntity
                }
            }
        }
        #Création du compte GLPI
        $url = "$URL_API" + "User/"
        $payload = @{
            input = @{
                name      = $email
                email     = $email
                firstname = $firstname
                realname  = $lastname
                entities_id = 0
                active    = 1
                password    = $password
            }
        } | ConvertTo-Json -Depth 10
        
        try {
            $response = Invoke-RestMethod -Uri $url -Method Post -Headers $HEADERS -Body $payload -ContentType "application/json"
            Write-Host -ForegroundColor Green "    ✔ Compte GLPI créé avec succès."
            $GLPIuserId = $response.id

            #Assignation de l'adresse mail
            $urlEmail = "$URL_API" + "UserEmail/"
            $payloadEmail = @{
                input = @{
                    users_id   = $GLPIuserId
                    email      = $email
                    is_default = 1
                    is_dynamic = 0
                }
            } | ConvertTo-Json -Depth 10
            
            try {
                $response = Invoke-RestMethod -Uri $urlEmail -Method Post -Headers $HEADERS -Body $payloadEmail -ContentType "application/json"
            } catch {
                Write-Host -ForegroundColor Red "    Impossible d'assigner l'email sur le compte GLPI: $($_.Exception.Message)"
            }

            #Assignation de l'entité cible sur le compte GLPI
            $urlEntity = "$URL_API" + "User/$GLPIuserId/Profile_User"
            
            if (-not $GLPIuserId) {
                Write-Host -ForegroundColor Red "    Erreur : ID du compte GLPI Invalide."
            }
            
            if (-not $EtabId) {
                Write-Host -ForegroundColor Red "    Erreur : ID de l'entitée GLPI Invalide."
            }
            
            foreach ($entity in @($EtabId)) {
                $payloadEntity = @{
                    input = @{
                        users_id     = $GLPIuserId
                        profiles_id  = 1
                        entities_id  = [int]$entity
                        is_recursive = 0
                    }
                } | ConvertTo-Json -Depth 10
                
                try {
                    $response = Invoke-RestMethod -Uri $urlEntity -Method Post -Headers $HEADERS -Body $payloadEntity -ContentType "application/json"
                } catch {
                    Write-Host -ForegroundColor Red "Erreur assignation entité : $($_.Exception.Message)"
                }
            }
            
        } catch {
            Write-Host -ForegroundColor Red "    Erreur création GLPI : $($_.Exception.Message)"
            Close-GLPISession
            return $null

        }

        # Suppression de la relation avec l'entité racine (entities_id=0)
        $urlDeleteRoot = "$URL_API" + "User/$GLPIuserId/Profile_User"
        try {
            $response = Invoke-RestMethod -Uri $urlDeleteRoot -Method Get -Headers $HEADERS
            $profileId = 0
            
            # Recherche du profil associé à l'entité racine (entities_id=0)
            foreach ($profile in $response) {
                if ($profile.entities_id -eq 0) {
                    $profileId = $profile.id
                    break
                }
            }
            
            # Si un profil racine existe, le supprimer
            if ($profileId -and $profileId -ne 0) {
                $urlDelete = "$URL_API" + "User/$GLPIuserId/Profile_User/$profileId"
                try {
                    $response = Invoke-RestMethod -Uri $urlDelete -Method Delete -Headers $HEADERS
                } catch {
                    Write-Host -ForegroundColor red "    Erreur suppression profil racine: $($_.Exception.Message)"
                }
            }
        } catch {
            Write-Host -ForegroundColor red "    Erreur récupération profils: $($_.Exception.Message)"
        }

        Close-GLPISession
        return $GLPIuserId
        
    } catch {
        Write-Host -ForegroundColor Red "Erreur globale: $($_.Exception.Message)"
        Close-GLPISession
        return $null
    }
}


function Get-OUsWithDescription {
    param([string]$description, [string]$rootOU)
    if ([string]::IsNullOrEmpty($description)) { return @() }
    $filter = "c -eq '$description'"
    return Get-ADOrganizationalUnit -Filter $filter -SearchBase $rootOU -Properties Description, Name | Sort-Object -Property Name
}

function Select-OU {
    param([string]$rootOU, [string]$username)
    
    $selectedOUDN = $rootOU
    
    while ($true) {
        $ouObjects = @(Get-OUsWithDescription '1' -rootOU $rootOU)
        
        if ($ouObjects.Count -eq 0) {
            Write-Host -ForegroundColor Red "    Aucune OU trouvée"
            break
        } elseif ($ouObjects.Count -eq 1) {
            $selectedOU = $ouObjects[0]
            $selectedOUDN = $selectedOU.DistinguishedName
        } else {
            Write-Host -ForegroundColor Yellow "    Sélectionnez l'OU pour le compte $username :"
            for ($i = 0; $i -lt $ouObjects.Count; $i++) {
                Write-Host -ForegroundColor Cyan "     [$($i+1)] $($ouObjects[$i].Name)"
            }
            $ouChoice = Read-Host "    Entrez le numéro (1 à $($ouObjects.Count))"
            $ouChoiceInt = 0
            [void][int]::TryParse($ouChoice, [ref]$ouChoiceInt)
            if ($ouChoiceInt -ge 1 -and $ouChoiceInt -le $ouObjects.Count) {
                $selectedOU = $ouObjects[$ouChoiceInt - 1]
                $selectedOUDN = $selectedOU.DistinguishedName
            } else {
                Write-Host -ForegroundColor Red "    Sélection invalide."
                continue
            }
        }
        
        # Sous-OUs
        $currentDescription = 1
        while ($true) {
            $currentDescription++
            $subOUs = @(Get-OUsWithDescription "$currentDescription" -rootOU $rootOU | Where-Object { $_.DistinguishedName -like "*,$($selectedOU.DistinguishedName)" })
            
            if ($subOUs.Count -eq 0) { break }
            elseif ($subOUs.Count -eq 1) {
                $selectedOU = $subOUs[0]
                $selectedOUDN = $selectedOU.DistinguishedName
            } else {
                Write-Host -ForegroundColor Yellow "    Sélectionnez la sous-OU :"
                for ($i = 0; $i -lt $subOUs.Count; $i++) {
                    Write-Host -ForegroundColor Cyan "     [$($i+1)] $($subOUs[$i].Name)"
                }
                $subChoice = Read-Host "    Entrez le numéro (1 à $($subOUs.Count))"
                $subChoiceInt = 0
                [void][int]::TryParse($subChoice, [ref]$subChoiceInt)
                if ($subChoiceInt -ge 1 -and $subChoiceInt -le $subOUs.Count) {
                    $selectedOU = $subOUs[$subChoiceInt - 1]
                    $selectedOUDN = $selectedOU.DistinguishedName
                } else {
                    Write-Host -ForegroundColor Red "    Sélection invalide."
                    continue
                }
            }
        }
        break
    }
    
    return $selectedOUDN
}

function Get-OUNameFromDN {
    param([string]$distinguishedName)
    
    if ([string]::IsNullOrWhiteSpace($distinguishedName)) {
        return ""
    }
    
    # Pour SAUV69 : Extraire l'OU juste après OU=ETABLISSEMENTS
    
    if ($distinguishedName -match ',OU=([^,]+),OU=ETABLISSEMENTS,') {
        return $matches[1]
    }
    
    # Fallback : extraire le premier CN ou OU du DN
    if ($distinguishedName -match '^(?:CN|OU)=([^,]+)') {
        return $matches[1]
    }
    
    return ""
}


function Get-Username {
    param(
        [Parameter(Mandatory)]
        [string]$firstname,

        [Parameter(Mandatory)]
        [string]$lastname,

        [Parameter(Mandatory)]
        [string]$UsernameFormat,

        [Parameter(Mandatory)]
        [string]$EmailFormat,

        [Parameter(Mandatory)]
        [string]$EmailDomain,

        [hashtable]$compositeAttributes
    )

    # Normalisation
    $firstname = $firstname.ToLower()
    $lastname  = $lastname.ToLower()
    $initial   = $firstname.Substring(0,1)

    # ----- CAS COMPOSITE -----
    if ($compositeAttributes) {
        return @{
            Username = $compositeAttributes.UserId
            Email    = "$($compositeAttributes.Email)@$EmailDomain"
        }
    }

    # ----- USERNAME VIA TEMPLATE -----
    $username = $UsernameFormat `
        -replace "\{firstname\}", $firstname `
        -replace "\{lastname\}",  $lastname `
        -replace "\{initial\}",   $initial

    # ----- EMAIL VIA TEMPLATE -----
    $emailPrefix = $EmailFormat `
        -replace "\{firstname\}", $firstname `
        -replace "\{lastname\}",  $lastname `
        -replace "\{initial\}",   $initial `
        -replace "\{username\}",  $username

    $email = "$emailPrefix@$EmailDomain"

    return @{
        Username = $username
        Email    = $email
    }
}


function Get-UniqueUsername {
    param(
        [string]$firstname,
        [string]$lastname,
        [string]$baseUsername,
        [string]$baseEmail,
        [string]$format,
        [string]$emailDomain,
        [hashtable]$compositeAttributes
    )
    
    $username = $baseUsername
    $email = $baseEmail
    $initial = $firstname.Substring(0,1).ToLower()
    $initialLength = 1
    $maxInitialLength = [math]::Min($firstname.Length, 4)
    
    # Incrémenter les initiales
    while (($initialLength -le $maxInitialLength) -and (Get-ADUser -Filter { SamAccountName -eq $username } -ErrorAction SilentlyContinue)) {
        $initialLength++
        if ($initialLength -le $maxInitialLength) {
            $initial = $firstname.Substring(0, $initialLength).ToLower()
            
            if ($compositeAttributes) {
                $username = "$initial.$($lastname.Replace(' ','').ToLower())"
                $email = "$($firstname.Replace(' ','').ToLower()).$($lastname.Replace(' ','').ToLower())@$emailDomain"
            } else {
                switch ($format) {
                    "{initial}.{lastname}" { 
                        $username = "$initial.$($lastname.ToLower())"
                        $email = "$($firstname.ToLower()).$($lastname.ToLower())@$emailDomain"
                    }
                    "{lastname}.{firstname}" { 
                        $username = "$($lastname.ToLower()).$($firstname.ToLower())"
                        $email = "$($firstname.ToLower()).$($lastname.ToLower())@$emailDomain"
                    }
                    "{initial}{lastname}" { 
                        $username = "$initial$($lastname.ToLower())"
                        $email = "$username@$emailDomain"
                    }
                }
            }
        }
    }
    
    # Ajouter un compteur si nécessaire
    $counter = 1
    while (Get-ADUser -Filter { SamAccountName -eq $username } -ErrorAction SilentlyContinue) {
        if ($compositeAttributes) {
            $username = "$initial.$($lastname.Replace(' ','').ToLower())$counter"
        } else {
            switch ($format) {
                "{initial}.{lastname}" { $username = "$initial.$($lastname.ToLower())$counter" }
                "{lastname}.{firstname}" { $username = "$($lastname.ToLower()).$($firstname.ToLower())$counter" }
                "{initial}{lastname}" { $username = "$initial$($lastname.ToLower())$counter" }
            }
        }
        $counter++
    }
    
    return @{ Username = $username; Email = $email }
}

function Get-MFIConfiguration {
    param(
        [string]$referentID,
        [hashtable]$baseConfig
    )
    
    # Configuration par défaut (MFI)
    $mfiConfig = $baseConfig.Clone()
    
    if ([string]::IsNullOrWhiteSpace($referentID)) {
        return $mfiConfig
    }
    
    try {
        # Récupérer l'extensionAttribute2 du référent
        $referent = Get-ADUser -Identity $referentID -Properties extensionAttribute2 -ErrorAction Stop
        $extAttr2 = $referent.extensionAttribute2
        
        # Si c'est MFRPDS, adapter la configuration
        if ($extAttr2 -eq "MFRPDS") {
            $mfiConfig.RootOU = "OU=MFRPDS,DC=mfi,DC=local"
            $mfiConfig.EmailDomain = "mfrpds.fr"
            $mfiConfig.EmailFormat = "{initial}.{lastname}"
            $mfiConfig.UPNSuffix = "mfi.local"
            $mfiConfig.UsernameFormat = "{initial}.{lastname}"          
        }
        
        return $mfiConfig
    } catch {
        Write-Host -ForegroundColor Yellow "    ⚠️ Impossible de détecter le type MFI/MFRPDS, utilisation de la config MFI par défaut"
        return $mfiConfig
    }
}


function New-ADUserAccount {
    param(
        [hashtable]$userParams,
        [string]$ouPath,
        [hashtable]$config
    )
    
    try {
        $adParams = @{
            Name = $userParams.DisplayName
            GivenName = $userParams.FirstName
            Surname = $userParams.LastName
            UserPrincipalName = $userParams.UPN
            SamAccountName = $userParams.Username
            EmailAddress = $userParams.Email
            AccountPassword = (ConvertTo-SecureString $userParams.Password -AsPlainText -Force)
            Enabled = $true
            Path = $ouPath
            DisplayName = $userParams.DisplayName
            PassThru = $true
        }
        
        $newUser = New-ADUser @adParams
        
        # Attributs personnalisés
        $replaceAttrs = @{}

        foreach ($attr in $config.ADAttributes.Keys) {

            # Si l’attribut existe directement dans userParams
            if ($userParams.ContainsKey($attr) -and $null -ne $userParams[$attr]) {
                $replaceAttrs[$attr] = $userParams[$attr]
                continue
            }

            # Sinon, mapping via config (arrivalDate, company, etc.)
            $valueKey = $config.ADAttributes[$attr]

            if ([string]::IsNullOrWhiteSpace($valueKey)) {
                continue
            }

            if ($userParams.ContainsKey($valueKey) -and $null -ne $userParams[$valueKey]) {
                $replaceAttrs[$attr] = $userParams[$valueKey]
            }
        }

        
        # Attributs spéciaux pour MFI (extensionAttribute1/2/3)
        $clearAttrs = @()
        foreach ($extAttr in @("extensionAttribute1", "extensionAttribute2", "extensionAttribute3")) {
            if ($userParams.ContainsKey($extAttr)) {
                if ([string]::IsNullOrWhiteSpace($userParams[$extAttr])) {
                    # Si vide, on doit utiliser -Clear
                    $clearAttrs += $extAttr
                } else {
                    # Si non vide, on utilise -Replace
                    $replaceAttrs[$extAttr] = $userParams[$extAttr]
                }
            }
        }
        
        if ($replaceAttrs.Count -gt 0) {
            Set-ADUser -Identity $newUser -Replace $replaceAttrs
        }
        
        if ($clearAttrs.Count -gt 0) {
            Set-ADUser -Identity $newUser -Clear $clearAttrs
        }
        
        # Groupe par défaut
        if ($config.DefaultGroup) {
            Add-ADGroupMember -Identity $config.DefaultGroup -Members $newUser -ErrorAction SilentlyContinue
        }
        
        return $newUser
    } catch {
        Write-Host -ForegroundColor Red "    Erreur création AD : $_"
        return $null
    }
}

function Set-UserFolders {
    param(
        [string]$username,
        [string]$usersPath,
        [string]$profilesPath,
        [hashtable]$config = $null
    )
    
    try {
        # Pour SAUV69 : vérifier si l'utilisateur doit avoir des dossiers (profil itinérant vs UPD)
        if ($config -and $config.Name -eq "SAUV69" -and $config.UDPCheckGroup) {
            $groupMembers = Get-ADGroupMember -Identity $config.UDPCheckGroup -ErrorAction SilentlyContinue | Select-Object -ExpandProperty SamAccountName
            
            if ($groupMembers -notcontains $username) {
                Write-Host -ForegroundColor Cyan "    ℹ Utilisateur en UPD, pas de création de dossiers."
                return $true
            }
        }
        
        # Traitement spécifique pour ALR : un seul dossier utilisateur avec permissions spécifiques
        if ($config -and $config.Name -eq "ALR") {
            $userFolder = Join-Path -Path $usersPath -ChildPath $username
            
            if (-not (Test-Path $userFolder)) {
                New-Item -ItemType Directory -Path $userFolder -ErrorAction Stop | Out-Null
            }
            
            if (Test-Path $userFolder) {
                $acl = Get-Acl -Path $userFolder
                # Désactiver l'héritage et supprimer les ACE héritées
                $acl.SetAccessRuleProtection($true, $false)
                
                # Permissions ALR : Utilisateur = Modify (sans FullControl), Admins du domaine = FullControl
                $rules = @(
                    (New-Object System.Security.AccessControl.FileSystemAccessRule($username, "Modify", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule("Admins du domaine", "FullControl", "ContainerInherit, ObjectInherit", "None", "Allow"))
                )
                foreach ($rule in $rules) { $acl.AddAccessRule($rule) }
                Set-Acl -Path $userFolder -AclObject $acl
                Write-Host -ForegroundColor Green "    ✔ Dossier utilisateur ALR créé avec permissions spécifiques."
            }
            return $true
        }
        
        # Traitement spécifique pour ADPA : dossiers USERS et PROFILES avec permissions héritées du parent
        if ($config -and $config.Name -eq "ADPA") {
            $userFolder = Join-Path -Path $usersPath -ChildPath $username
            $profileFolder = Join-Path -Path $profilesPath -ChildPath $username
            
            foreach ($folder in @($userFolder, $profileFolder)) {
                if (-not (Test-Path $folder)) {
                    New-Item -ItemType Directory -Path $folder -ErrorAction Stop | Out-Null
                }
                
                if (Test-Path $folder) {
                    # Récupérer l'ACL du dossier parent
                    $parentPath = Split-Path -Path $folder -Parent
                    $parentAcl = Get-Acl -Path $parentPath
                    
                    $acl = Get-Acl -Path $folder
                    # Désactiver l'héritage mais copier les ACE du parent
                    $acl.SetAccessRuleProtection($true, $false)
                    
                    # Copier les règles d'accès du parent
                    foreach ($access in $parentAcl.Access) {
                        $acl.AddAccessRule($access)
                    }
                    
                    Set-Acl -Path $folder -AclObject $acl
                }
            }
            Write-Host -ForegroundColor Green "    ✔ Dossiers ADPA créés avec permissions héritées du parent."
            return $true
        }
        
        # Traitement standard pour les autres clients
        $userFolder = Join-Path -Path $usersPath -ChildPath $username
        $profileFolder = Join-Path -Path $profilesPath -ChildPath $username
        
        
        foreach ($folder in @($userFolder, $profileFolder)) {
            if (-not (Test-Path $folder)) {
                New-Item -ItemType Directory -Path $folder -ErrorAction SilentlyContinue | Out-Null
            }
            
            if (Test-Path $folder) {
                $acl = Get-Acl -Path $folder
                $acl.SetAccessRuleProtection($true, $false)
                
                $rules = @(
                    (New-Object System.Security.AccessControl.FileSystemAccessRule($username, "Modify", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule($username, "ReadAndExecute", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule($username, "ListDirectory", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule($username, "Write", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule("Admins du domaine", "FullControl", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule("adminwidip", "FullControl", "ContainerInherit, ObjectInherit", "None", "Allow"))
                    (New-Object System.Security.AccessControl.FileSystemAccessRule("Administrateurs", "FullControl", "ContainerInherit, ObjectInherit", "None", "Allow"))
                )
                foreach ($rule in $rules) { $acl.AddAccessRule($rule) }
                Set-Acl -Path $folder -AclObject $acl
            }
        }
        return $true
       

    } catch {
        Write-Host -ForegroundColor Red "    ❌ Erreur création dossiers : $_"
        return $false
    }
}


function New-MgUserAccount {
    param(
        [hashtable]$userParams,
        [hashtable]$config
    )
    
    try {
        $mgUserExists = Get-MgUser -UserId $userParams.UPN -ErrorAction SilentlyContinue
        
        if (-not $mgUserExists) {
            # Déterminer le mailNickname
            $compositeAttributes = Format-CompositeName -firstname $userParams.FirstName -lastname $userParams.LastName
            if ($compositeAttributes) {
                $mailNick = ($userParams.FirstName + $userParams.LastName).Replace(' ', '')
            } else {
                $mailNick = $userParams.LastName.Replace(' ', '')
            }
            
            $bodyParams = @{
                displayName = $AzuredisplayName
                userPrincipalName = $userParams.UPN
                mailNickname = $mailNick
                accountEnabled = $true
                givenName = $userParams.FirstName
                surname = $userParams.LastName
                passwordProfile = @{
                    password = $userParams.Password
                    forceChangePasswordNextSignIn = $false
                }
            }
            
            $newUser = New-MgUser -BodyParameter $bodyParams -ErrorAction Stop
            Write-Host -ForegroundColor Green "    ✔ Compte Azure créé."
            return $newUser
        } else {
            # Mise à jour du mot de passe
            $passwordProfile = @{
                password = $userParams.Password
                forceChangePasswordNextSignIn = $false
            }
            Update-MgUser -UserId $mgUserExists.Id -PasswordProfile $passwordProfile -ErrorAction SilentlyContinue
            Write-Host -ForegroundColor Yellow "    ⚠ Compte Azure existe déjà, mot de passe mis à jour."
            return $mgUserExists
        }
    } catch {
        Write-Host -ForegroundColor Red "    ❌ Erreur Azure : $_"
        return $null
    }
}

  function Get-MgUserIdByEmail {
        param([string]$email)
        (Get-MgUser -UserId $email).Id
    }

function Set-Office365License {
    param(
        [string]$upn,
        [string]$email,
        [string]$username,
        [string]$referentUPN,
        [hashtable]$config
    )
    
    try {
        # Définir l'emplacement d'utilisation
        Update-MgUser -UserId $upn -UsageLocation "FR" -ErrorAction SilentlyContinue | Out-Null
        
        # Récupérer l'ObjectId via Microsoft Graph
        $userId = Get-MgUserIdByEmail -email $email
        if (-not $userId) {
            Write-Host -ForegroundColor Red "    ❌ Impossible de récupérer l'ID utilisateur."
            return $false
        }
        
       # ============================================================
        # DÉTERMINATION DE LA LICENCE
        # ============================================================

        $skuPartNumber = $null

        # ----- 1️⃣ Tentative via compte référent -----
        if ($referentUPN) {

            $referent = Get-MgUser -UserId $referentUPN -ErrorAction SilentlyContinue
            if ($referent) {
                $refLicenses = Get-MgUserLicenseDetail -UserId $referent.Id -ErrorAction SilentlyContinue

                $allowedSkus = $config.LicenseSKU.Values
                $matchedSku = $refLicenses |
                              Where-Object { $allowedSkus -contains $_.SkuPartNumber } |
                              Select-Object -First 1

                if ($matchedSku) {
                    $skuPartNumber = $matchedSku.SkuPartNumber
                }
            }
        }

        # ----- 2️⃣ Choix manuel si nécessaire -----
        if (-not $skuPartNumber) {

            Write-Host -ForegroundColor Yellow "    ⚠ Aucune licence référente trouvée."
            Write-Host "    👉 Sélection manuelle requise :"

             $LicenseNames = @{
                "STANDARDPACK"    = "E1"
                "ENTERPRISEPACK"  = "E3"
            }

            $licenseList = $config.LicenseSKU.GetEnumerator() | Sort-Object Name

            $menu = @{}
            $i = 1

            foreach ($lic in $licenseList) {
                $displayName = $LicenseNames[$lic.Value]   # récupère E1/E3
                Write-Host "      [$i] $($lic.Key) ($displayName)"
                $menu[$i] = $lic.Value
                $i++
            }

            do {
                $choice = Read-Host "    Choisissez une licence (1-$($menu.Count))"
            } until ($menu.ContainsKey([int]$choice))

            $skuPartNumber = $menu[[int]$choice]
        }

        # ============================================================
        # ATTRIBUTION DE LA LICENCE
        # ============================================================

        $sku = Get-MgSubscribedSku -All | Where-Object {
            $_.SkuPartNumber -eq $skuPartNumber
        }

        if (-not $sku) {
            Write-Host -ForegroundColor Red "    ❌ SKU $skuPartNumber introuvable."
            return $false
        }

        $availableLicenses = $sku.PrepaidUnits.Enabled - $sku.ConsumedUnits
        if ($availableLicenses -le 0) {
            Write-Host -ForegroundColor Red "    ❌ Plus de licences disponibles pour $skuPartNumber."
            return $false
        }

        $currentLicenses = Get-MgUserLicenseDetail -UserId $userId -ErrorAction SilentlyContinue
        if ($currentLicenses.SkuPartNumber -contains $skuPartNumber) {
            Write-Host -ForegroundColor Yellow "    ⚠ Licence déjà attribuée."
            return $true
        }

        Set-MgUserLicense -UserId $userId -BodyParameter @{
            addLicenses    = @(@{ skuId = $sku.SkuId })
            removeLicenses = @()
        } | Out-Null

        Write-Host -ForegroundColor Green "    ✔ Licence $skuPartNumber attribuée."

    } catch {
        Write-Host -ForegroundColor Red "    ❌ Erreur licence : $_"
    }
}


function New-ExchangeMailbox {
    param(
        [string]$username,
        [string]$displayName,
        [string]$email,
        [string]$extensionAttribute2 = $null,
        [string]$secondaryEmail = $null
    )
    
    try {
        $mailbox = Get-Mailbox -Identity $username -ErrorAction SilentlyContinue
        
        if (-not $mailbox) {
            Enable-Mailbox -Identity $username -Alias $username -PrimarySmtpAddress $email -ErrorAction Stop
            Write-Host -ForegroundColor Green "    ✔ Boîte aux lettres Exchange créée."
            
            # Si c'est MFI ou MFRPDS, appliquer la Address Book Policy
            if ($extensionAttribute2 -eq "MFI") {
                Set-Mailbox -Identity $username -AddressBookPolicy "MFI Policy" -ErrorAction SilentlyContinue
                Write-Host -ForegroundColor Green "    ✔ Address Book Policy 'MFI Policy' appliquée."
            } elseif ($extensionAttribute2 -eq "MFRPDS") {
                Set-Mailbox -Identity $username -AddressBookPolicy "MFRPDS Policy" -ErrorAction SilentlyContinue
                Write-Host -ForegroundColor Green "    ✔ Address Book Policy 'MFRPDS Policy' appliquée."
            }
            
            # Ajouter l'email secondaire pour ALR
            if ($secondaryEmail) {
                Start-Sleep -Seconds 2
                Set-Mailbox -Identity $username -EmailAddresses @{Add=$secondaryEmail} -ErrorAction SilentlyContinue
                Write-Host -ForegroundColor Green "    ✔ Email secondaire ajouté : $secondaryEmail"
            }
            
            return $true
        } else {
            Write-Host -ForegroundColor Yellow "    Boîte aux lettres existe déjà."
            return $true
        }
    } catch {
        Write-Host -ForegroundColor Red "    Erreur Exchange : $_"
        return $false
    }
}


function Get-ReferentData {
    param(
        [string]$referentName,
        [string]$rootOU
    )
    
    if ([string]::IsNullOrWhiteSpace($referentName) -or $referentName -eq "aucun") {
        return @{ Count = 0; Referent = $null; ID = $null; Valid = $false }
    }
    
    $referents = Get-ADUser -Filter { Surname -eq $referentName } -SearchBase $rootOU -ErrorAction SilentlyContinue
    $count = ($referents | Measure-Object).Count
    
    if ($count -eq 1) {
        return @{
            Count = 1
            Referent = $referents
            ID = $referents.SamAccountName
            Valid = $true
            OU = ($referents.DistinguishedName -split ',', 2)[1]
        }
    } elseif ($count -gt 1) {
        Write-Host -ForegroundColor Yellow "    Plusieurs comptes trouvés pour '$referentName' :"
        for ($i = 0; $i -lt $referents.Count; $i++) {
            Write-Host -ForegroundColor Cyan "     [$($i+1)] $($referents[$i].GivenName) $($referents[$i].Surname)"
        }
        $choice = Read-Host "    Sélectionnez le référent (1 à $count)"
        if ($choice -ge 1 -and $choice -le $count) {
            $selected = $referents[$choice - 1]
            return @{
                Count = 1
                Referent = $selected
                ID = $selected.SamAccountName
                Valid = $true
                OU = ($selected.DistinguishedName -split ',', 2)[1]
            }
        }
    }
    
    return @{ Count = 0; Referent = $null; ID = $null; Valid = $false }
}

function Copy-ReferentGroups {
    param(
        [string]$referentID,
        [string]$username
    )
    
    try {
        if ([string]::IsNullOrWhiteSpace($referentID)) { return }
        Get-ADUser -Identity $referentID -Properties memberof | 
            Select-Object -ExpandProperty memberof | 
            Add-ADGroupMember -Members $username -ErrorAction SilentlyContinue
    } catch {}
}


function Show-Banner {
    Clear-Host
    Write-Host -ForegroundColor Yellow @"


    +════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════+
    |                                                                                                                                            |
    |                      _____                _   _                     _                                    _                                 |
    |                     / ____|              | | (_)                   | |                                  | |                                |
    |                    | |     _ __ ___  __ _| |_ _  ___  _ __       __| | ___      ___ ___  _ __ ___  _ __ | |_ ___                           |
    |                    | |    | '__/ _ \/  _` | __| |/ _ \| '_ \     /  _` |/ _ \    / __/ _ \| '_ ` _  \| '_ \| __/ _ \                          |
    |                    | |____| | |  __/ (_| | |_| | (_) | | | |   | (_| |  __/   | (_| (_) | | | | | | |_) | ||  __/                          |
    |                     \_____|_|  \___|\__,_|\__|_|\___/|_| |_|    \__,_|\___|    \___\___/|_| |_| |_| .__/ \__\___|                          |
    |                                                                                                   | |                                      |
    |                                                                                                   |_|                                      |
    |                                                     _                        _                                                             |
    |                                          /\        | |                      | | (_)                                                        |
    |                                         /  \  _   _| |_ ___  _ __ ___   __ _| |_ _  __ _ _   _  ___                                        |
    |                                        / /\ \| | | | __/ _ \| '_ ` _  \ /  _` | __| |/ _ ` | | | |/ _ \                                       |
    |                                       / ____ \ |_| | || (_) | | | | | | (_| | |_| | (_| | |_| |  __/                                       |
    |                                      /_/    \_\__,_|\__\___/|_| |_| |_|\__,_|\__|_|\__, |\__,_|\___|                                       |
    |                                                                                       | |                                                  |
    |                                                                                       |_|                                                  |
    |                                                                                                                                            |
    +════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════+

"@
}

function Show-Summary {
    param([array]$users)
    
    Write-Host ""
    Write-Host -ForegroundColor Yellow "    Récapitulatif : Les comptes suivants seront créés."
    Write-Host ""
    
    foreach ($user in $users) {
        # Remplacer les valeurs null/vides par des chaînes vides
        if ([string]::IsNullOrWhiteSpace($user.prenom)) { $user.prenom = "" }
        if ([string]::IsNullOrWhiteSpace($user.nom)) { $user.nom = "" }
        if ([string]::IsNullOrWhiteSpace($user.poste)) { $user.poste = "" }
        if ([string]::IsNullOrWhiteSpace($user.etablissement)) { $user.etablissement = "" }
        if ([string]::IsNullOrWhiteSpace($user.nom_compte_referent)) { $user.nom_compte_referent = "" }
    }
    
    $maxPrenom = ($users.prenom | Where-Object { $_ -ne $null } | Measure-Object -Maximum Length).Maximum
    $maxNom = ($users.nom | Where-Object { $_ -ne $null } | Measure-Object -Maximum Length).Maximum
    $maxPoste = ($users.poste | Where-Object { $_ -ne $null } | Measure-Object -Maximum Length).Maximum
    $maxEtab = ($users.etablissement | Where-Object { $_ -ne $null } | Measure-Object -Maximum Length).Maximum
    

    if ($null -eq $maxPrenom) { $maxPrenom = 0 }
    if ($null -eq $maxNom) { $maxNom = 0 }
    if ($null -eq $maxPoste) { $maxPoste = 0 }
    if ($null -eq $maxEtab) { $maxEtab = 0 }
    
    $maxRef = 0
    $referentLabels = @()
    
    foreach ($user in $users) {

        if ($user.PSObject.Properties.Name -contains 'ReferentName' -and -not [string]::IsNullOrWhiteSpace($user.ReferentName)) {
            $label = $user.ReferentName
        } else {
            $referent = $null
            if (![string]::IsNullOrWhiteSpace($nomRef)) {
                $referent = Get-ADUser -Filter { Surname -eq $nomRef } -ErrorAction SilentlyContinue | Select-Object -First 1
            }
            if ($referent) {
                $label = "$($referent.GivenName) $($referent.Surname)"
            } elseif (![string]::IsNullOrWhiteSpace($nomRef)) {
                $label = "aucun compte référent trouvé"
            } else {
                $label = ""
            }
        }
        $referentLabels += $label
        if ($label.Length -gt $maxRef) { $maxRef = $label.Length }
    }
   
    #  Garantir des largeurs minimales pour l'affichage
    $maxPrenom = [Math]::Max($maxPrenom, 7)
    $maxNom = [Math]::Max($maxNom, 3)
    $maxPoste = [Math]::Max($maxPoste, 8)
    $maxEtab = [Math]::Max($maxEtab, 13)
    $maxRef = [Math]::Max($maxRef, 15)
    
    $header = "| " + "Prénom".PadRight($maxPrenom) + " | " + "Nom".PadRight($maxNom) +
              " | " + "Fonction".PadRight($maxPoste) + " | " + "Etablissement".PadRight($maxEtab) +
              " | " + "Référent".PadRight($maxRef) + " |"
    $separator = "|" + ("-" * ($maxPrenom + 2)) + "|" + ("-" * ($maxNom + 2)) +
                 "|" + ("-" * ($maxPoste + 2)) + "|" + ("-" * ($maxEtab + 2)) +
                 "|" + ("-" * ($maxRef + 2)) + "|"
    Write-Host -ForegroundColor Cyan "    $separator"
    Write-Host -ForegroundColor Cyan "    $header"
    Write-Host -ForegroundColor Cyan "    $separator"
    
    for ($i = 0; $i -lt $users.Count; $i++) {
        $user = $users[$i]
        #  Protection contre les valeurs null lors de l'affichage
        $prenom = if ($user.prenom) { $user.prenom } else { "" }
        $nom = if ($user.nom) { $user.nom } else { "" }
        $poste = if ($user.poste) { $user.poste } else { "" }
        $etab = if ($user.etablissement) { $user.etablissement } else { "" }
        $ref = if ($referentLabels[$i]) { $referentLabels[$i] } else { "" }
        
        $line = "| " + $prenom.PadRight($maxPrenom) + " | " + $nom.PadRight($maxNom) +
                " | " + $poste.PadRight($maxPoste) + " | " + $etab.PadRight($maxEtab) +
                " | " + $ref.PadRight($maxRef) + " |"
        Write-Host -ForegroundColor White "    $line"
    }
    Write-Host -ForegroundColor Cyan "    $separator"
}

function New-MySecretLink {
    param(
        [string]$samAccountName,
        [string]$email,
        [string]$password
    )
    try {
        $combinedSecret = "Identifiant : $samAccountName`nEmail : $email`nMot de passe : $password"
        $body = @{
            "password[payload]" = $combinedSecret
            "password[expire_after_days]" = 10
            "password[expire_after_views]" = 10
        }
        $apiUrl = "https://mysecret.widip.fr/p.json"
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body
        if ($response -and $response.url_token) {
            return "https://mysecret.widip.fr/p/$($response.url_token)"
        } else {
            return "Erreur: L'URL secrète n'a pas été trouvée."
        }
    } catch {
        return "Erreur lors de l'appel à l'API POST: $_"
    }
}


<#####################################################################################      
#                                                                                    #           
#                                                                                    #        
#                                                                                    #
#                                 Début du script                                    #
#                                                                                    #
#                                                                                    #
#                                                                                    #
#####################################################################################>

Show-Banner

# Détection du client en amont
$domain = Get-ADDomain -Current LocalComputer
$client = $domain.Forest

if (-not $ClientConfigs.ContainsKey($client)) {
    Write-Host -ForegroundColor Red "    Client non reconnu : $client"
    exit
}

$config = $ClientConfigs[$client]

Write-Host -ForegroundColor Yellow "    Choisissez une action à effectuer :"
Write-Host -ForegroundColor Yellow -NoNewline "    1. Créer des comptes à partir d'un fichier CSV "
Write-Host -ForegroundColor White "(Plusieurs utilisateurs)"
Write-Host -ForegroundColor Yellow -NoNewline "    2. Créer un compte en rentrant manuellement les informations "
Write-Host -ForegroundColor White "(Un seul utilisateur)"

do {
    $choiceMode = Read-Host "`n    Entrez 1 ou 2"
} while ($choiceMode -ne '1' -and $choiceMode -ne '2')

Clear-Host

# Conversion Excel -> CSV
Convert-ExcelToCsv

# Récupération des utilisateurs
$users = @()
$referentsTable = @()

if ($choiceMode -eq '2') {
    # Mode manuel
    do {
        Clear-Host
        Write-Host -ForegroundColor Magenta @"
 
    +═════════════════════════════════════════════════════════════════════════════════════════════════════+
    |                                                                                                     |
    |                                                                                                     |
    |       _____       __       _   _                                                   _ _              |
    |      / ____|     /_/      | | (_)                                                 | | |             |
    |     | |     _ __ ___  __ _| |_ _  ___  _ __       _ __ ___   __ _ _ __  _   _  ___| | | ___         |
    |     | |    | '__/ _ \/  _` | __| |/ _ \| '_ \     | '_  ` _ \ / _`  | '_ \| | | |/ _ \ | |/ _ \        |
    |     | |____| | |  __/ (_| | |_| | (_) | | | |    | | | | | | (_| | | | | |_| |  __/ | |  __/        |
    |      \_____|_|  \___|\__,_|\__|_|\___/|_| |_|    |_| |_| |_|\__,_|_| |_|\__,_|\___|_|_|\___|        |
    |                                                                                                     |
    |                                                                                                     |
    |                                                                                                     |
    +═════════════════════════════════════════════════════════════════════════════════════════════════════+

"@
        $user = Get-UserInput -config $config
   
        $nom_referent = if (![string]::IsNullOrWhiteSpace($user.nom_compte_referent)) { $user.nom_compte_referent.Trim() } else { "" }
        $compte_referent = if (![string]::IsNullOrWhiteSpace($nom_referent)) { Get-ADUser -Filter { Surname -eq $nom_referent } -Properties GivenName, Surname, SamAccountName, UserPrincipalName } else { $null }
        $compte_referent_count = ($compte_referent | Measure-Object).Count
        $id_referent = $null
        $referentName = ""
        $referentUPN = ""
        $valid_referent = $false
    
        if ($compte_referent_count -eq 1) {
            # Un seul compte trouvé
            $compte_ref = $compte_referent | Select-Object -First 1
            $referentName = "$($compte_ref.GivenName) $($compte_ref.Surname)"
            $id_referent = $compte_ref.SamAccountName
            $referentUPN = $compte_ref.UserPrincipalName
            $valid_referent = $true
        
        } elseif ($compte_referent_count -gt 1) {
            # Plusieurs comptes trouvés - demander à l'utilisateur de choisir
            Write-Host -ForegroundColor Yellow "`n    Plusieurs comptes trouvés pour le nom '$nom_referent' :`n"
            for ($i = 0; $i -lt $compte_referent.Count; $i++) {
                $compte = $compte_referent[$i]
                Write-Host -ForegroundColor Yellow "    [$i] $($compte.GivenName) $($compte.Surname) - $($compte.SamAccountName)"
            }
        
            $validChoice = $false
            while (-not $validChoice) {
                Write-Host ""
                $choice = Read-Host "    Entrez le numéro du compte référent à copier (0 à $($compte_referent.Count - 1))"
            
                # Conversion explicite en int
                $choiceInt = 0
                if ([int]::TryParse($choice, [ref]$choiceInt) -and $choiceInt -ge 0 -and $choiceInt -lt $compte_referent.Count) {
                    $compte_ref = $compte_referent[$choiceInt]
                    $referentName = "$($compte_ref.GivenName) $($compte_ref.Surname)"
                    $id_referent = $compte_ref.SamAccountName
                    $referentUPN = $compte_ref.UserPrincipalName
                    $validChoice = $true
                    $valid_referent = $true
                    Write-Host -ForegroundColor Green "    ✔ Référent sélectionné : $referentName"
                } else {
                    Write-Host -ForegroundColor Red "    Choix invalide. Sélectionnez un numéro valide."
                }
            }
        
        } else {
            # Aucun compte trouvé
            if (![string]::IsNullOrWhiteSpace($nom_referent)) {
                Write-Host -ForegroundColor Red "    ❌ Aucun compte trouvé pour le nom '$nom_referent'."
            }
            $referentName = ""
            $id_referent = ""
            $referentUPN = ""
            $valid_referent = $false
        }

            # Ajout des infos référent dans l'objet utilisateur pour le tableau récap
            $user | Add-Member -NotePropertyName ReferentName -NotePropertyValue $referentName -Force
            $user | Add-Member -NotePropertyName ReferentID -NotePropertyValue $id_referent -Force
            $user | Add-Member -NotePropertyName ReferentUPN -NotePropertyValue $referentUPN -Force
    
        Show-Summary -users @($user)
        $confirm = Read-Host "`n    Validez-vous ces informations ? (O/N)"
        if ($confirm -eq 'O' -or $confirm -eq 'o') {
            Add-UserToCSV -csvPath $CSVPaths.Creation -user $user -config $config
            $users = @($user)
            break
        } else {
            $users = @() # Reset la liste si annulé
        }
    } while ($true)
} else {
    # Mode CSV
    Clear-Host
    Write-Host -ForegroundColor Magenta @"
 
    +══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════+
    |                                                                                                                          |
    |                                                                                                                          |
    |           _____       __       _   _                             _                        _   _                          |
    |          / ____|     /_/      | | (_)                           | |                      | | (_)                         |
    |         | |     _ __ ___  __ _| |_ _  ___  _ __       __ _ _   _| |_ ___  _ __ ___   __ _| |_ _  __ _ _   _  ___         |
    |         | |    | '__/ _ \/ _`  | __| |/ _ \| '_ \     / _`  | | | | __/ _ \| '_ ` _  \ / _`  | __| |/  _` | | | |/ _ \        |
    |         | |____| | |  __/ (_| | |_| | (_) | | | |   | (_| | |_| | || (_) | | | | | | (_| | |_| | (_| | |_| |  __/        |
    |          \_____|_|  \___|\__,_|\__|_|\___/|_| |_|    \__,_|\__,_|\__\___/|_| |_| |_|\__,_|\__|_|\__, |\__,_|\___|        |
    |                                                                                                    | |                   |
    |                                                                                                    |_|                   |
    |                                                                                                                          |
    |                                                                                                                          |
    |                            _                          __ _      _     _               _____  _______      __             |
    |                           (_)                        / _(_)    | |   (_)             / ____|/ ____\ \    / /             |
    |                     __   ___  __ _    _   _ _ __    | |_ _  ___| |__  _  ___ _ __   | |    | (___  \ \  / /              |
    |                     \ \ / / |/ _`  |  | | | | '_ \   |  _| |/ __| '_ \| |/ _ \ '__|  | |     \___ \  \ \/ /               |
    |                      \ V /| | (_| |  | |_| | | | |  | | | | (__| | | | |  __/ |     | |____ ____) |  \  /                |
    |                       \_/ |_|\__,_|   \__,_|_| |_|  |_| |_|\___|_| |_|_|\___|_|      \_____|_____/    \/                 |
    |                                                                                                                          |
    +══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════+


"@
    
    # Renommer le dernier CSV
    $CSVfiles = Get-ChildItem -Path $CSVPaths.Source -File -Filter *.csv
    $latestFile = $CSVfiles | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestFile) {
        if ($latestFile.Name -ne "compte.csv") {
            Rename-Item -Path $latestFile.FullName -NewName "compte.csv" -Force
        }
    }
    
    Convert-SemicolonToComma -filePath $CSVPaths.Creation
    
    # Nettoyage du CSV
    $lines = Get-Content -Path $CSVPaths.Creation -Encoding UTF8
    $headerLine = $lines | Where-Object { -not $_.StartsWith("#") } | Select-Object -First 1
    $dataLines = $lines | Where-Object { -not $_.StartsWith("#") -and $_ -ne $headerLine }
    $validLines = @($headerLine)
    
    foreach ($line in $dataLines) {
        $fields = $line -split ','
        if ($fields.Count -eq ($headerLine -split ',').Count) {
            $allEmpty = $true
            foreach ($field in $fields) {
                if (-not [string]::IsNullOrWhiteSpace($field)) {
                    $allEmpty = $false
                    break
                }
            }
            if (-not $allEmpty) { $validLines += $line }
        }
    }
    
    $validLines | Set-Content -Path $CSVPaths.Creation -Encoding UTF8
    $users = Import-Csv -Path $CSVPaths.Creation -Delimiter "," -Encoding UTF8
    
    #  Filtrer les utilisateurs avec au moins un prénom ET un nom valides
    $users = $users | Where-Object { 
        ![string]::IsNullOrWhiteSpace($_.prenom) -and 
        ![string]::IsNullOrWhiteSpace($_.nom) 
    }
    
    #  Vérifier qu'il reste des utilisateurs à traiter
    if ($users.Count -eq 0) {
        Write-Host -ForegroundColor Red "    Aucun utilisateur valide trouvé dans le fichier CSV."
        exit
    }
    
    # Validation du champ personalTitle pour PRADO
    if ($config.Name -eq "PRADO") {
        foreach ($user in $users) {
            if ([string]::IsNullOrWhiteSpace($user.personalTitle)) {
                Write-Host -ForegroundColor Red "    Erreur : Le champ 'personalTitle' est obligatoire pour PRADO (utilisateur: $($user.prenom) $($user.nom))"
                exit
            }
            if ($user.personalTitle -ne "M." -and $user.personalTitle -ne "Mme") {
                Write-Host -ForegroundColor Red "    Erreur : Le champ 'personalTitle' doit être 'M.' ou 'Mme' (utilisateur: $($user.prenom) $($user.nom))"
                exit
            }
        }
    }
    
    # Traitement des référents AVANT l'affichage du tableau récapitulatif
    Write-Host ""
    Write-Host -ForegroundColor Cyan "    ════════════════════════════════════════════════════════════"
    Write-Host -ForegroundColor Cyan "              Vérification des comptes référents"
    Write-Host -ForegroundColor Cyan "    ════════════════════════════════════════════════════════════"
    Write-Host ""
    
    foreach ($user in $users) {
        $nom_referent = if (![string]::IsNullOrWhiteSpace($user.nom_compte_referent)) { $user.nom_compte_referent.Trim() } else { "" }
        
        if ([string]::IsNullOrWhiteSpace($nom_referent)) {
            # Pas de référent spécifié
            $user | Add-Member -NotePropertyName ReferentName -NotePropertyValue "" -Force
            $user | Add-Member -NotePropertyName ReferentID -NotePropertyValue "" -Force
            $user | Add-Member -NotePropertyName ReferentUPN -NotePropertyValue "" -Force
            continue
        }
        
        $compte_referent = Get-ADUser -Filter { Surname -eq $nom_referent } -Properties GivenName, Surname, SamAccountName, UserPrincipalName -ErrorAction SilentlyContinue
        $compte_referent_count = ($compte_referent | Measure-Object).Count
        
        if ($compte_referent_count -eq 1) {
            # Un seul compte trouvé
            $compte_ref = $compte_referent | Select-Object -First 1
            $referentName = "$($compte_ref.GivenName) $($compte_ref.Surname)"
            $id_referent = $compte_ref.SamAccountName
            $referentUPN = $compte_ref.UserPrincipalName
            Write-Host -ForegroundColor Green "    ✔ Référent '$nom_referent' pour $($user.prenom) $($user.nom) : $referentName"
            
            $user | Add-Member -NotePropertyName ReferentName -NotePropertyValue $referentName -Force
            $user | Add-Member -NotePropertyName ReferentID -NotePropertyValue $id_referent -Force
            $user | Add-Member -NotePropertyName ReferentUPN -NotePropertyValue $referentUPN -Force
            
        } elseif ($compte_referent_count -gt 1) {
            # Plusieurs comptes trouvés - demander à l'utilisateur de choisir
            Write-Host -ForegroundColor Yellow "`n    ⚠ Plusieurs comptes trouvés pour le référent '$nom_referent' (utilisateur: $($user.prenom) $($user.nom)) :`n"
            for ($i = 0; $i -lt $compte_referent.Count; $i++) {
                $compte = $compte_referent[$i]
                Write-Host -ForegroundColor Cyan "       [$i] $($compte.GivenName) $($compte.Surname) - $($compte.SamAccountName)"
            }
            
            $validChoice = $false
            while (-not $validChoice) {
                Write-Host ""
                $choice = Read-Host "    Entrez le numéro du compte référent à utiliser (0 à $($compte_referent.Count - 1))"
                
                # Conversion explicite en int
                $choiceInt = 0
                if ([int]::TryParse($choice, [ref]$choiceInt) -and $choiceInt -ge 0 -and $choiceInt -lt $compte_referent.Count) {
                    $compte_ref = $compte_referent[$choiceInt]
                    $referentName = "$($compte_ref.GivenName) $($compte_ref.Surname)"
                    $id_referent = $compte_ref.SamAccountName
                    $referentUPN = $compte_ref.UserPrincipalName
                    $validChoice = $true
                    Write-Host -ForegroundColor Green "    ✔ Référent sélectionné : $referentName"
                    
                    $user | Add-Member -NotePropertyName ReferentName -NotePropertyValue $referentName -Force
                    $user | Add-Member -NotePropertyName ReferentID -NotePropertyValue $id_referent -Force
                    $user | Add-Member -NotePropertyName ReferentUPN -NotePropertyValue $referentUPN -Force
                } else {
                    Write-Host -ForegroundColor Red "    ❌ Choix invalide. Veuillez sélectionner un numéro valide."
                }
            }
            Write-Host ""
            
        } else {
            # Aucun compte trouvé
            Write-Host -ForegroundColor Red "    ❌ Aucun compte trouvé pour le référent '$nom_referent' (utilisateur: $($user.prenom) $($user.nom))"
            $user | Add-Member -NotePropertyName ReferentName -NotePropertyValue "" -Force
            $user | Add-Member -NotePropertyName ReferentID -NotePropertyValue "" -Force
            $user | Add-Member -NotePropertyName ReferentUPN -NotePropertyValue "" -Force
        }
    }
    
    Write-Host ""
    Write-Host -ForegroundColor Cyan "    ════════════════════════════════════════════════════════════"
    Write-Host ""
    
    Show-Summary -users $users
    
    $confirm = Read-Host "`n    Validez-vous ces informations ? (O/N)"
    if ($confirm -ne 'O' -and $confirm -ne 'o') {
        Write-Host -ForegroundColor Red "    Opération annulée."
        exit
    }
}

# Connexions spécifiques
$exchangeSession = $null
if ($config.HasExchange) {
    $exchangeSession = Connect-ExchangeServer -exchangeServer $config.ExchangeServer
}

if ($config.HasAzureAD -and $config.AzureAccountId) {
    $connected = $false
    while (-not $connected) {
        $connected = Try-ConnectMgGraph -accountId $config.AzureAccountId
        if (-not $connected) {
            $retry = Read-Host "   Réessayer la connexion Azure AD ? (O/N)"
            if ($retry -ne 'O' -and $retry -ne 'o') { exit }
        }
    }
}

# Synchronisation AD
Wait-ADSyncCompletion

# Date
$date = Get-Date -Format "dd/MM/yyyy"

# Traitement des utilisateurs
$userInfos = @()

foreach ($user in $users) {
    

    # Nettoyage des noms
    $firstname = Remove-Accents $user.prenom
    $lastname = Remove-Accents $user.nom
    $formattedPrenom = $firstname.Substring(0,1).ToUpper() + $firstname.Substring(1).ToLower()
    $formattedNom = $lastname.ToUpper()

    Write-Host ""
    Write-Host -ForegroundColor White "  ----------------------------------------------------"
    Write-Host -ForegroundColor Yellow "    Création de l'utilisateur : $formattedPrenom $formattedNom"
    Write-Host -ForegroundColor White "  ----------------------------------------------------"

    # Attributs composites
    $compositeAttributes = Format-CompositeName -firstname $firstname -lastname $lastname

    #  Récupération des infos référent déjà sélectionnées (avant le tableau récap)
    $referentName = if ($user.PSObject.Properties.Name -contains 'ReferentName') { $user.ReferentName } else { "" }
    $id_referent = if ($user.PSObject.Properties.Name -contains 'ReferentID') { $user.ReferentID } else { "" }
    $referentUPN = if ($user.PSObject.Properties.Name -contains 'ReferentUPN') { $user.ReferentUPN } else { "" }
    $valid_referent = ![string]::IsNullOrWhiteSpace($id_referent)
    
    if ($valid_referent) {
        Write-Host -ForegroundColor Green "    ✔ Utilisation du référent : $referentName"
    }

    # Pour MFI/MFRPDS : Adapter la configuration selon l'extensionAttribute2 du référent
    if ($config.Name -eq "MFI/MFRPDS" -and $valid_referent) {
        $config = Get-MFIConfiguration -referentID $id_referent -baseConfig $config
    }

    # Génération username/email avec la config adaptée
    $credentials = Get-Username -firstname $firstname -lastname $lastname -UsernameFormat $config.UsernameFormat -EmailFormat $config.EmailFormat -emailDomain $config.EmailDomain -compositeAttributes $compositeAttributes
    $username = $credentials.Username
    $email = $credentials.Email
    $upn = "$($email.Split('@')[0])@$($config.UPNSuffix)"
    $password = Generate-Password -length $config.PasswordLength
    $displayName = Format-Name -firstname $firstname -lastname $lastname -format $config.DisplayNameFormat
    $AzuredisplayName = Format-Name -firstname $firstname -lastname $lastname -format $config.AzureDisplayName

    # Vérification si l'utilisateur existe
    $adUserExists = Get-ADUser -Filter { GivenName -eq $firstname -and Surname -eq $lastname -and userPrincipalName -eq $upn } -Properties * -ErrorAction SilentlyContinue

    if ($adUserExists) {
        Write-Host -ForegroundColor Yellow "    L'utilisateur existe déjà, mise à jour du mot de passe."
        $password = Generate-Password -length $config.PasswordLength
        Set-ADAccountPassword -Identity $adUserExists -NewPassword (ConvertTo-SecureString $password -AsPlainText -Force)

        # Réinitialisation des groupes
        $groups = Get-ADUser -Identity $adUserExists.SamAccountName -Properties memberof
        foreach ($group in $groups.memberof) {
            Remove-ADGroupMember -Identity $group -Members $adUserExists.SamAccountName -Confirm:$false -ErrorAction SilentlyContinue
        }

        # Récupération du référent
        if ($valid_referent) {
            Copy-ReferentGroups -referentID $id_referent -username $adUserExists.SamAccountName
        }

        $username = $adUserExists.SamAccountName
        # Correction: fallback if EmailAddress or UserPrincipalName are null
        if (![string]::IsNullOrWhiteSpace($adUserExists.EmailAddress)) {
            $email = $adUserExists.EmailAddress
        } else {
            # Recalcule l'email si absent
            $email = "$username@$($config.EmailDomain)"
        }
        if (![string]::IsNullOrWhiteSpace($adUserExists.UserPrincipalName)) {
            $upn = $adUserExists.UserPrincipalName
        } else {
            # Recalcule le UPN si absent
            $upn = "$($email.Split('@')[0])@$($config.UPNSuffix)"
        }
    } else {
        # Génération d'un username unique
        $uniqueCreds = Get-UniqueUsername -firstname $firstname -lastname $lastname -baseUsername $username -baseEmail $email -format $config.UsernameFormat -emailDomain $config.EmailDomain -compositeAttributes $compositeAttributes
        $username = $uniqueCreds.Username
        $email = $uniqueCreds.Email
        $upn = "$($email.Split('@')[0])@$($config.UPNSuffix)"

        # Détermination de l'OU
        if ($valid_referent) {
            $ouPath = (Get-ADUser -Identity $id_referent).DistinguishedName -replace '^CN=[^,]+,', ''
        } else {
            $ouPath = Select-OU -rootOU $config.RootOU -username $username
        }
        
        # Pour SAUV69 : Extraire le nom de l'OU pour le DisplayName
        $ouName = ""
        if ($config.Name -eq "SAUV69") {
            $ouName = Get-OUNameFromDN -distinguishedName $ouPath
        }
        
        # Regénérer le DisplayName avec l'OU si nécessaire
        if ($ouName) {
            $displayName = Format-Name -firstname $firstname -lastname $lastname -format $config.DisplayNameFormat -ouName $ouName
        }

        # Paramètres utilisateur
        $userParams = @{
            Username = $username
            Email = $email
            UPN = $upn
            FirstName = $formattedPrenom
            LastName = $formattedNom
            DisplayName = $displayName
            Password = $password
            arrivalDate = $date
            company = $user.etablissement
            title = $user.poste
        }
        
        # Ajouter personalTitle uniquement pour PRADO
        if ($config.Name -eq "PRADO" -and ![string]::IsNullOrWhiteSpace($user.personalTitle)) {
            $userParams.personalTitle = $user.personalTitle
        }

        # Pour SAUV69 : Copier les attributs spécifiques du référent
        if ($config.Name -eq "SAUV69" -and $id_referent) {
            try {
                $referent = Get-ADUser $id_referent -Properties extensionAttribute1, extensionAttribute2, company, title, postalCode, l, streetAddress -ErrorAction Stop
        
                # Copier les attributs seulement s'ils ont une valeur
                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute1)) {
                    $userParams["extensionAttribute1"] = $referent.extensionAttribute1
                }

                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute2)) {
                    $userParams["extensionAttribute2"] = $referent.extensionAttribute2
                }

                if (![string]::IsNullOrWhiteSpace($referent.company)) {
                    $userParams["company"] = $referent.company
                }

                if (![string]::IsNullOrWhiteSpace($referent.title)) {
                    $userParams["title"] = $referent.title
                }

                if (![string]::IsNullOrWhiteSpace($referent.postalCode)) {
                    $userParams["postalCode"] = $referent.postalCode
                }

                if (![string]::IsNullOrWhiteSpace($referent.l)) {
                    $userParams["l"] = $referent.l
                }

                if (![string]::IsNullOrWhiteSpace($referent.streetAddress)) {
                    $userParams["streetAddress"] = $referent.streetAddress
                }
                

            } catch {
                Write-Host -ForegroundColor Yellow "    ⚠️ Impossible de récupérer les attributs SAUV69 du référent"
            }
        }

        if ($config.Name -eq "MFI/MFRPDS" -and $id_referent) {
            try {
                $referent = Get-ADUser $id_referent -Properties extensionAttribute1, extensionAttribute2, extensionAttribute3 -ErrorAction Stop
        
                # Copier les attributs seulement s'ils ont une valeur
                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute1)) {
                    $userParams["extensionAttribute1"] = $referent.extensionAttribute1
                }

                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute2)) {
                    $userParams["extensionAttribute2"] = $referent.extensionAttribute2
                }

                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute3)) {
                    $userParams["extensionAttribute3"] = $referent.extensionAttribute3
                }
                
                Write-Host -ForegroundColor Cyan "    ℹ Attributs MFI copiés depuis le référent"

            } catch {
                Write-Host -ForegroundColor Yellow "    ⚠️ Impossible de récupérer les attributs MFI du référent"
            }
        }

        # Pour ALR : Copier les attributs spécifiques du référent
        if ($config.Name -eq "ALR" -and $id_referent) {
            try {
                $referent = Get-ADUser $id_referent -Properties extensionAttribute1, company -ErrorAction Stop
        
                # Copier extensionAttribute1 (BV pour les comptes Cloud)
                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute1)) {
                    $userParams["extensionAttribute1"] = $referent.extensionAttribute1
                }

                # Copier company
                if (![string]::IsNullOrWhiteSpace($referent.company)) {
                    $userParams["company"] = $referent.company
                }
                
                Write-Host -ForegroundColor Cyan "    ℹ Attributs ALR copiés depuis le référent"

            } catch {
                Write-Host -ForegroundColor Yellow "    ⚠️ Impossible de récupérer les attributs ALR du référent"
            }
        }

        # Pour ADPA : Copier les attributs spécifiques du référent
        if ($config.Name -eq "ADPA" -and $id_referent) {
            try {
                $referent = Get-ADUser $id_referent -Properties extensionAttribute1, company -ErrorAction Stop
        
                # Copier extensionAttribute1 (BV pour les comptes Cloud)
                if (![string]::IsNullOrWhiteSpace($referent.extensionAttribute1)) {
                    $userParams["extensionAttribute1"] = $referent.extensionAttribute1
                }

                # Copier company
                if (![string]::IsNullOrWhiteSpace($referent.company)) {
                    $userParams["company"] = $referent.company
                }
                
                Write-Host -ForegroundColor Cyan "    ℹ Attributs ADPA copiés depuis le référent"

            } catch {
                Write-Host -ForegroundColor Yellow "    ⚠️ Impossible de récupérer les attributs ADPA du référent"
            }
        }


        # Création du compte AD
        $newADUser = New-ADUserAccount -userParams $userParams -ouPath $ouPath -config $config

        if ($newADUser) {
            Write-Host -ForegroundColor Green "    ✔ Compte AD créé : $username"

            # Copie des groupes du référent
            if ($valid_referent) {
                Copy-ReferentGroups -referentID $id_referent -username $username
            }
            
            # Pour MFI avec BV : ajouter au groupe IS_RO
            if ($config.Name -eq "MFI/MFRPDS" -and $userParams.ContainsKey("extensionAttribute1")) {
                if ($userParams["extensionAttribute1"] -eq "BV") {
                    try {
                        Add-ADGroupMember -Identity "IS_RO" -Members $username -ErrorAction Stop
                        Write-Host -ForegroundColor Green "    ✔ Ajouté au groupe IS_RO (compte BV)"
                    } catch {
                        Write-Host -ForegroundColor Yellow "    ⚠️ Impossible d'ajouter au groupe IS_RO"
                    }
                }
            }
            
            # Pour ALR avec BV : ajouter aux groupes Cloud (ALR_Data et Bureau_ALR)
            if ($config.Name -eq "ALR" -and $userParams.ContainsKey("extensionAttribute1")) {
                if ($userParams["extensionAttribute1"] -eq "BV") {
                    foreach ($groupName in $config.CloudGroups) {
                        try {
                            Add-ADGroupMember -Identity $groupName -Members $username -ErrorAction Stop
                            Write-Host -ForegroundColor Green "    ✔ Ajouté au groupe $groupName (compte Cloud BV)"
                        } catch {
                            Write-Host -ForegroundColor Yellow "    ⚠️ Impossible d'ajouter au groupe $groupName"
                        }
                    }
                }
            }
        }
    }
    
    # Création des dossiers 
    # Pour ALR et ADPA : créer les dossiers SEULEMENT si l'utilisateur a l'attribut BV (compte Cloud)
    if ($config.DossierProfils -or $config.DossierUsers) {
        $shouldCreateFolders = $true
        
        # Vérification spécifique pour ALR
        if ($config.Name -eq "ALR") {
            if (-not ($userParams.ContainsKey("extensionAttribute1") -and $userParams["extensionAttribute1"] -eq "BV")) {
                $shouldCreateFolders = $false
                Write-Host -ForegroundColor Cyan "    ℹ Compte ALR sans BV, pas de création de dossiers (profil itinérant)."
            }
        }
        
        # Vérification spécifique pour ADPA
        if ($config.Name -eq "ADPA") {
            if (-not ($userParams.ContainsKey("extensionAttribute1") -and $userParams["extensionAttribute1"] -eq "BV")) {
                $shouldCreateFolders = $false
                Write-Host -ForegroundColor Cyan "    ℹ Compte ADPA sans BV, pas de création de dossiers (profil itinérant)."
            }
        }
        
        if ($shouldCreateFolders) {
            $foldersCreated = Set-UserFolders -username $username -usersPath $config.DossierUsers -profilesPath $config.DossierProfils -config $config
            if ($foldersCreated) {
                Write-Host -ForegroundColor Green "    ✔ Dossiers utilisateur créés."
            }
        }
    }

    # Azure AD / Office 365
    if ($config.HasAzureAD -and $config.HasOffice365) {
        $azureParams = @{
            Username = $username
            Email = $email
            UPN = $upn
            FirstName = $formattedPrenom
            LastName = $formattedNom
            Password = $password
        }

        Connect-MgGraph -NoWelcome

        $azureUser = New-MgUserAccount -userParams $azureParams -config $config
        
        if ($azureUser) {
            Start-Sleep -Seconds 3
            $licenseAssigned = Set-Office365License -upn $upn -email $email -username $username -referentUPN $referentUPN -config $config
        }
    }
    
    # Exchange On-Prem
    if ($config.HasExchange -and $exchangeSession) {
        Start-Sleep -Seconds 5
        
        # Récupérer extensionAttribute2 pour MFI/MFRPDS
        $extAttr2 = $null
        if ($config.Name -eq "MFI/MFRPDS" -and $userParams.ContainsKey("extensionAttribute2")) {
            $extAttr2 = $userParams["extensionAttribute2"]
        }
        
        # Préparer l'email secondaire pour ALR
        $secondaryEmail = $null
        if ($config.Name -eq "ALR" -and $config.SecondaryEmailDomain) {
            $emailPrefix = $email.Split('@')[0]
            $secondaryEmail = "$emailPrefix@$($config.SecondaryEmailDomain)"
        }
        
        $mailboxCreated = New-ExchangeMailbox -username $username -displayName $displayName -email $email -extensionAttribute2 $extAttr2 -secondaryEmail $secondaryEmail
    }
    
    # Stockage des informations
    $mySecretLink = New-MySecretLink -samAccountName $username -email $email -password $password

    # Création du compte GLPI
    $glpiUserId = Create-GLPIUserFull -upn $upn -firstname $formattedPrenom -lastname $formattedNom -password $password -referentUPN $referentUPN

    $userInfos += [PSCustomObject]@{
        Prenom = $formattedPrenom
        Nom = $formattedNom
        Username = $username
        Email = $email
        Password = $password
        MySecretLink = $mySecretLink
        GLPIUserId = $glpiUserId
    }
}

# Affichage final
Write-Host -ForegroundColor Green "`n    =========================================="
Write-Host -ForegroundColor Green "                CRÉATION TERMINÉE"
Write-Host -ForegroundColor Green "    =========================================="
Write-Host ""


# Création du texte final pour le bloc-notes
$userSpecificOutput = @()
foreach ($userInfo in $userInfos) {
    $formattedPrenom = $userInfo.Prenom
    $formattedNom = $userInfo.Nom
    $secretUrl = $userInfo.MySecretLink
    $userInfoOutput = @()
    $userInfoOutput += "Le compte utilisateur de $formattedPrenom $formattedNom a bien été créé."
    $userInfoOutput += ""
    $userInfoOutput += "Vous trouverez ci-dessous le lien avec ses identifiants de connexion valable pendant 10 jours, passé ce délai, il sera supprimé."
    $userInfoOutput += ""
    $userInfoOutput += "$secretUrl"
    $userInfoOutput += ""
    if ($userInfos.Count -gt 1) {
        $userInfoOutput += "_____________________________________________"
        $userInfoOutput += ""
    }
    $userSpecificOutput += $userInfoOutput
}
$commonOutput = @()
$commonOutput += "Bonjour,"
$commonOutput += ""
$commonOutput += $userSpecificOutput -join "`n"
$commonOutput += ""
$commonOutput += "Cordialement,"
$commonOutput += ""
$commonOutput += "Support WIDIP"
$tempFile = [System.IO.Path]::GetTempFileName() + ".txt"
$commonOutput | Out-File -FilePath $tempFile -Encoding UTF8
Start-Process notepad.exe -ArgumentList $tempFile

# Nettoyage
if ($exchangeSession) {
    Remove-PSSession $exchangeSession -ErrorAction SilentlyContinue
}

Remove-Item -Path "C:\Sources\Alexis\Creation de compte\CSV_Creation\*"  -Force
Copy-Item -Path $CSVPaths.Origin -Destination $CSVPaths.Source -Force

Write-Host ""
Read-Host "    Appuyez sur Entrée pour terminer"