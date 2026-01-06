# WIBOT - Guide d'Installation

Ce guide explique comment installer et lancer WIBOT sur un nouveau poste de travail.

---

## Table des matieres

1. [Prerequis](#prerequis)
2. [Installation Windows](#installation-windows)
3. [Installation Linux](#installation-linux)
4. [Configuration n8n (premiere fois)](#configuration-n8n-premiere-fois)
5. [Lancement quotidien](#lancement-quotidien)
6. [URLs et Acces](#urls-et-acces)
7. [Troubleshooting](#troubleshooting)

---

## Prerequis

### Logiciels requis

| Logiciel | Windows | Linux |
|----------|---------|-------|
| Docker Desktop | v4.x+ | Docker Engine + Docker Compose |
| Node.js | v18+ | v18+ |
| Navigateur moderne | Chrome, Firefox, Edge | Chrome, Firefox |

### Ressources minimales
- RAM : 4 Go minimum (8 Go recommande)
- Disque : 2 Go d'espace libre
- CPU : 2 coeurs minimum

---

# Installation Windows

## Etape 1 : Installer Docker Desktop

1. Telecharger Docker Desktop : https://www.docker.com/products/docker-desktop/
2. Executer l'installateur
3. **Activer WSL 2** si demande (recommande)
4. Redemarrer Windows si necessaire
5. Lancer Docker Desktop et attendre qu'il soit "Running"

## Etape 2 : Installer Node.js

1. Telecharger Node.js LTS : https://nodejs.org/
2. Executer l'installateur
3. Verifier l'installation :
```cmd
node --version
npm --version
```

## Etape 3 : Copier le projet

1. Copier le dossier `WIBOT` depuis la cle USB vers votre poste
2. Exemple : `C:\Projets\WIBOT\`

## Etape 4 : Lancer le Backend

Ouvrir un terminal (CMD ou PowerShell) :

```cmd
:: Aller dans le dossier backend
cd C:\Projets\WIBOT\wibot-backend

:: Lancer les conteneurs Docker
docker-compose up -d

:: Verifier que les 3 conteneurs tournent
docker ps
```

Vous devez voir :
- `wibot-postgres` (healthy)
- `wibot-n8n` (running)
- `wibot-nginx` (running)

**Attendre 30 secondes** que PostgreSQL soit pret.

## Etape 5 : Lancer le Frontend (mode developpement)

Ouvrir un **nouveau terminal** :

```cmd
:: Aller dans le dossier frontend
cd C:\Projets\WIBOT\wibot-frontend

:: Installer les dependances (premiere fois uniquement)
npm install

:: Lancer le serveur de developpement
npm run dev
```

## Etape 6 : Acceder a WIBOT

- **Mode production** (via Nginx) : http://localhost:8080
- **Mode developpement** (Vite) : http://localhost:5173
- **n8n Admin** : http://localhost:5679

---

# Installation Linux

## Etape 1 : Installer Docker

### Ubuntu / Debian

```bash
# Mettre a jour les paquets
sudo apt update

# Installer Docker
sudo apt install -y docker.io docker-compose

# Ajouter l'utilisateur au groupe docker (evite sudo)
sudo usermod -aG docker $USER

# IMPORTANT : Se deconnecter et se reconnecter pour appliquer
logout
```

### Fedora / RHEL

```bash
sudo dnf install -y docker docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
logout
```

### Arch Linux

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
logout
```

## Etape 2 : Installer Node.js

### Via NodeSource (recommande)

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verifier
node --version
npm --version
```

### Via NVM (alternative)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

## Etape 3 : Copier le projet

```bash
# Monter la cle USB (si pas auto-monte)
sudo mount /dev/sdb1 /mnt/usb

# Copier le projet
cp -r /mnt/usb/WIBOT ~/Projets/WIBOT

# Donner les permissions
chmod -R 755 ~/Projets/WIBOT
```

## Etape 4 : Lancer le Backend

```bash
# Aller dans le dossier backend
cd ~/Projets/WIBOT/wibot-backend

# Lancer les conteneurs Docker
docker-compose up -d

# Verifier les conteneurs
docker ps
```

## Etape 5 : Lancer le Frontend

```bash
# Nouveau terminal
cd ~/Projets/WIBOT/wibot-frontend

# Installer les dependances
npm install

# Lancer le serveur dev
npm run dev
```

## Etape 6 : Acceder a WIBOT

- http://localhost:8080 (production)
- http://localhost:5173 (developpement)
- http://localhost:5679 (n8n admin)

---

# Configuration n8n (premiere fois)

Lors de la premiere installation, vous devez configurer n8n manuellement.

## 1. Acceder a n8n

- URL : http://localhost:5679
- Login : `admin`
- Password : `wibot_admin_2024`

## 2. Creer les Credentials

### PostgreSQL

1. Aller dans **Settings** > **Credentials**
2. Cliquer **Add Credential** > **Postgres**
3. Nom : `WIBOT PostgreSQL`
4. Parametres :
   ```
   Host: postgres
   Database: wibot
   User: widip
   Password: widip_secure_password_2024
   Port: 5432
   SSL: Disable
   ```
5. Cliquer **Save**

### Mistral API

1. **Add Credential** > **Mistral Cloud API**
2. Nom : `Mistral API`
3. API Key : `LH0hs7MxTDGx6z2ioHC8oyrFnGHcbywL`
4. Cliquer **Save**

## 3. Importer les Workflows

1. Aller dans **Workflows**
2. Cliquer **Import from File**
3. Importer chaque fichier depuis `wibot-backend/workflows/` :
   - `auth_login.json`
   - `chat_main.json`
   - `get_conversations.json`
   - `get_messages.json`
   - `create_conversation.json`

## 4. Configurer les Credentials dans chaque Workflow

Pour chaque workflow importe :

1. Ouvrir le workflow
2. Cliquer sur chaque node **Postgres** ou **Mistral**
3. Selectionner le credential correspondant
4. Sauvegarder le workflow

## 5. Activer les Workflows

Pour chaque workflow :
1. Ouvrir le workflow
2. Cliquer sur le toggle **Active** (en haut a droite)

---

# Lancement quotidien

## Windows

```cmd
:: 1. S'assurer que Docker Desktop est lance

:: 2. Lancer le backend
cd C:\Projets\WIBOT\wibot-backend
docker-compose up -d

:: 3. Lancer le frontend (optionnel en mode dev)
cd C:\Projets\WIBOT\wibot-frontend
npm run dev
```

## Linux

```bash
# 1. S'assurer que Docker tourne
sudo systemctl start docker

# 2. Lancer le backend
cd ~/Projets/WIBOT/wibot-backend
docker-compose up -d

# 3. Lancer le frontend (optionnel en mode dev)
cd ~/Projets/WIBOT/wibot-frontend
npm run dev
```

## Arreter WIBOT

```bash
# Arreter le backend
cd wibot-backend
docker-compose down

# Le frontend : Ctrl+C dans le terminal
```

---

# URLs et Acces

| Service | URL | Identifiants |
|---------|-----|--------------|
| WIBOT (production) | http://localhost:8080 | khora / test123 |
| WIBOT (dev) | http://localhost:5173 | khora / test123 |
| n8n Admin | http://localhost:5679 | admin / wibot_admin_2024 |

### Utilisateurs de test

| Username | Password | Role |
|----------|----------|------|
| khora | test123 | admin |
| test | test123 | user |

---

# Troubleshooting

## Docker ne demarre pas

### Windows
- Verifier que la virtualisation est activee dans le BIOS
- S'assurer que WSL 2 est installe : `wsl --install`
- Redemarrer Docker Desktop

### Linux
```bash
# Verifier le status
sudo systemctl status docker

# Demarrer Docker
sudo systemctl start docker
```

## Port deja utilise

Erreur : `port is already allocated`

### Solution 1 : Trouver et arreter le processus

Windows :
```cmd
netstat -ano | findstr :5432
taskkill /PID <PID> /F
```

Linux :
```bash
sudo lsof -i :5432
sudo kill <PID>
```

### Solution 2 : Changer les ports

Editer `wibot-backend/docker-compose.yml` :
```yaml
ports:
  - "5433:5432"   # PostgreSQL
  - "5679:5678"   # n8n
  - "8081:80"     # Nginx
```

Et mettre a jour `wibot-frontend/.env` :
```env
VITE_API_URL=http://localhost:8081
```

## n8n : Workflows inactifs apres import

1. Ouvrir chaque workflow dans n8n
2. Verifier que les credentials sont configures
3. Activer le workflow (toggle Active)

## Erreur "Cannot connect to PostgreSQL"

1. Verifier que le conteneur postgres est lance :
   ```bash
   docker ps | grep postgres
   ```
2. Attendre 30 secondes apres le demarrage
3. Dans n8n, utiliser `postgres` comme host (pas `localhost`)

## Frontend : "Network Error"

1. Verifier que le backend est lance (`docker ps`)
2. Verifier que l'URL dans `.env` est correcte
3. Verifier les logs Nginx :
   ```bash
   docker-compose logs nginx
   ```

## Reset complet (supprimer toutes les donnees)

```bash
cd wibot-backend

# Arreter et supprimer les volumes
docker-compose down -v

# Relancer (repart de zero)
docker-compose up -d
```

**Attention :** Cela supprime toutes les conversations et l'historique !

---

# Scripts de lancement automatique

## Windows (start-wibot.bat)

Creer un fichier `start-wibot.bat` a la racine :

```batch
@echo off
echo === Demarrage WIBOT ===

cd /d %~dp0wibot-backend
echo Lancement du backend...
docker-compose up -d

echo Attente de PostgreSQL...
timeout /t 10

cd /d %~dp0wibot-frontend
echo Lancement du frontend...
start npm run dev

echo.
echo WIBOT est pret !
echo - Frontend : http://localhost:5173
echo - Backend : http://localhost:8080
echo - n8n : http://localhost:5679
pause
```

## Linux (start-wibot.sh)

Creer un fichier `start-wibot.sh` a la racine :

```bash
#!/bin/bash
echo "=== Demarrage WIBOT ==="

# Aller dans le dossier du script
cd "$(dirname "$0")"

# Backend
echo "Lancement du backend..."
cd wibot-backend
docker-compose up -d

echo "Attente de PostgreSQL..."
sleep 10

# Frontend
echo "Lancement du frontend..."
cd ../wibot-frontend
npm run dev &

echo ""
echo "WIBOT est pret !"
echo "- Frontend : http://localhost:5173"
echo "- Backend : http://localhost:8080"
echo "- n8n : http://localhost:5679"
```

Rendre executable :
```bash
chmod +x start-wibot.sh
```
