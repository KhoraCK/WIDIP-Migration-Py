# Guide d'Installation WIBOT

## Table des matieres

1. [Prerequis](#1-prerequis)
2. [Installation sur Windows](#2-installation-sur-windows)
3. [Installation sur Linux](#3-installation-sur-linux)
4. [Demarrage de l'application](#4-demarrage-de-lapplication)
5. [Verification](#5-verification)
6. [Arret de l'application](#6-arret-de-lapplication)
7. [Depannage](#7-depannage)

---

## 1. Prerequis

Avant de commencer, vous devez installer les logiciels suivants sur votre machine :

| Logiciel | Version minimale | Pourquoi ? |
|----------|------------------|------------|
| **Docker Desktop** | 4.0+ | Fait tourner la base de donnees et n8n |
| **Node.js** | 18+ | Fait tourner le frontend React |
| **Git** (optionnel) | 2.0+ | Pour cloner le projet |

---

## 2. Installation sur Windows

### Etape 2.1 : Installer Docker Desktop

1. Telecharger Docker Desktop : https://www.docker.com/products/docker-desktop/
2. Lancer l'installateur et suivre les instructions
3. **Redemarrer l'ordinateur** apres l'installation
4. Lancer Docker Desktop (icone dans la barre des taches)
5. Attendre que Docker demarre (icone verte = pret)

**Verification :**
Ouvrir PowerShell et taper :
```powershell
docker --version
```
Vous devez voir quelque chose comme : `Docker version 24.x.x`

### Etape 2.2 : Installer Node.js

1. Telecharger Node.js LTS : https://nodejs.org/
2. Lancer l'installateur et suivre les instructions (garder les options par defaut)

**Verification :**
Ouvrir PowerShell et taper :
```powershell
node --version
npm --version
```
Vous devez voir : `v18.x.x` ou plus recent

### Etape 2.3 : Copier le projet WIBOT

Copier le dossier `WIBOT` a l'emplacement de votre choix.

Par exemple : `C:\Projets\WIBOT`

---

## 3. Installation sur Linux

### Etape 3.1 : Installer Docker

**Ubuntu/Debian :**
```bash
# Mettre a jour les paquets
sudo apt update

# Installer les dependances
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Ajouter la cle GPG Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le depot Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Ajouter votre utilisateur au groupe docker (pour eviter sudo)
sudo usermod -aG docker $USER

# IMPORTANT : Deconnectez-vous et reconnectez-vous pour appliquer
```

**Verification :**
```bash
docker --version
docker compose version
```

### Etape 3.2 : Installer Node.js

```bash
# Installer Node.js 20 LTS via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verification
node --version
npm --version
```

### Etape 3.3 : Copier le projet WIBOT

Copier le dossier `WIBOT` a l'emplacement de votre choix.

Par exemple : `/home/votre_user/WIBOT`

---

## 4. Demarrage de l'application

### Etape 4.1 : Demarrer le Backend (Docker)

**Windows (PowerShell) :**
```powershell
# Aller dans le dossier backend
cd C:\Projets\WIBOT\wibot-backend

# Demarrer les containers Docker
docker-compose up -d
```

**Linux (Terminal) :**
```bash
# Aller dans le dossier backend
cd ~/WIBOT/wibot-backend

# Demarrer les containers Docker
docker compose up -d
```

**Attendre 30 secondes** que les services demarrent.

### Etape 4.2 : Restaurer la base de donnees

Cette etape importe toutes les donnees (utilisateurs, conversations, workflows n8n).

**Windows (PowerShell) :**
```powershell
# Toujours dans wibot-backend
Get-Content backup\wibot_db_backup_final.sql | docker exec -i wibot-postgres psql -U widip -d wibot
```

**Linux (Terminal) :**
```bash
# Toujours dans wibot-backend
docker exec -i wibot-postgres psql -U widip -d wibot < backup/wibot_db_backup_final.sql
```

### Etape 4.3 : Redemarrer n8n

Apres la restauration, redemarrer n8n pour charger les workflows :

**Windows & Linux :**
```bash
docker-compose restart n8n
```

Attendre 10 secondes.

### Etape 4.4 : Installer et demarrer le Frontend

**Windows (PowerShell) :**
```powershell
# Aller dans le dossier frontend
cd C:\Projets\WIBOT\wibot-frontend

# Installer les dependances (premiere fois uniquement)
npm install

# Demarrer le serveur de developpement
npm run dev
```

**Linux (Terminal) :**
```bash
# Aller dans le dossier frontend
cd ~/WIBOT/wibot-frontend

# Installer les dependances (premiere fois uniquement)
npm install

# Demarrer le serveur de developpement
npm run dev
```

Le terminal affichera :
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

---

## 5. Verification

### 5.1 Ouvrir l'application

Ouvrir un navigateur et aller sur : **http://localhost:5173**

### 5.2 Se connecter

Utiliser les identifiants :
- **Nom d'utilisateur :** `khora`
- **Mot de passe :** `test123`

### 5.3 Tester les fonctionnalites

1. **Envoyer un message** : Taper un message et appuyer sur Entree
2. **Creer une conversation** : Cliquer sur "Nouvelle conversation"
3. **Renommer** : Survoler une conversation, cliquer sur l'icone crayon
4. **Supprimer** : Survoler une conversation, cliquer sur l'icone poubelle

### 5.4 Verifier les services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Interface utilisateur |
| n8n (API) | http://localhost:8080 | Proxy nginx vers n8n |
| n8n Editor | http://localhost:5679 | Interface d'administration n8n |

**Identifiants n8n Editor :** `admin` / `wibot_admin_2024`

---

## 6. Arret de l'application

### Arreter le Frontend

Dans le terminal ou PowerShell ou le frontend tourne, appuyer sur `Ctrl + C`

### Arreter le Backend (Docker)

**Windows (PowerShell) :**
```powershell
cd C:\Projets\WIBOT\wibot-backend
docker-compose down
```

**Linux (Terminal) :**
```bash
cd ~/WIBOT/wibot-backend
docker compose down
```

### Arreter completement (avec suppression des donnees)

**ATTENTION : Ceci supprime toutes les donnees !**
```bash
docker-compose down -v
```

---

## 7. Depannage

### Probleme : "docker: command not found"

**Cause :** Docker n'est pas installe ou pas dans le PATH.

**Solution :**
- Windows : Relancer Docker Desktop
- Linux : Verifier l'installation avec `which docker`

### Probleme : "Cannot connect to the Docker daemon"

**Cause :** Docker n'est pas demarre.

**Solution :**
- Windows : Lancer Docker Desktop depuis le menu Demarrer
- Linux : `sudo systemctl start docker`

### Probleme : "EACCES permission denied" (npm)

**Cause :** Probleme de permissions npm.

**Solution Linux :**
```bash
sudo chown -R $USER:$USER ~/.npm
```

### Probleme : "Port 5173 already in use"

**Cause :** Un autre processus utilise le port.

**Solution :**
```bash
# Trouver le processus
# Windows :
netstat -ano | findstr :5173

# Linux :
lsof -i :5173

# Tuer le processus (remplacer PID par le numero)
# Windows :
taskkill /PID <PID> /F

# Linux :
kill -9 <PID>
```

### Probleme : "wibot-postgres container not running"

**Solution :**
```bash
# Verifier les containers
docker ps -a

# Voir les logs du container
docker logs wibot-postgres

# Redemarrer
docker-compose restart postgres
```

### Probleme : Ecran blanc apres connexion

**Cause :** Les workflows n8n ne sont pas charges.

**Solution :**
1. Verifier que n8n tourne : `docker ps | grep n8n`
2. Redemarrer n8n : `docker-compose restart n8n`
3. Attendre 15 secondes et rafraichir la page

---

## Resume des commandes

### Demarrage rapide (apres premiere installation)

**Windows :**
```powershell
# Terminal 1 : Backend
cd C:\Projets\WIBOT\wibot-backend
docker-compose up -d

# Terminal 2 : Frontend
cd C:\Projets\WIBOT\wibot-frontend
npm run dev
```

**Linux :**
```bash
# Terminal 1 : Backend
cd ~/WIBOT/wibot-backend
docker compose up -d

# Terminal 2 : Frontend
cd ~/WIBOT/wibot-frontend
npm run dev
```

Puis ouvrir : **http://localhost:5173**

---

## Support

En cas de probleme, verifier :
1. Docker Desktop est lance (Windows)
2. Les containers tournent : `docker ps`
3. Les logs : `docker logs wibot-n8n` ou `docker logs wibot-postgres`

---

*Guide genere le 26/12/2025 - WIBOT v1.0*
