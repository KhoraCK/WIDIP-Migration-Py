# Documentation Technique WIDIP

## Architecture Réseau Standard Client

### Schéma Type EHPAD/Clinique

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Routeur   │  IP: x.x.x.1
                    │   /Firewall │  (souvent Cisco, Fortinet, ou Box FAI)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Switch Core │  IP: x.x.x.2
                    │  (managé)   │  (HPE, Cisco, ou Netgear Pro)
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌──────▼─────┐
    │ Serveurs  │   │  Postes   │   │   WiFi     │
    │ (VLAN 10) │   │ (VLAN 20) │   │ (VLAN 30)  │
    └───────────┘   └───────────┘   └────────────┘
```

### Plan d'Adressage Standard

| VLAN | Plage IP | Masque | Usage |
|------|----------|--------|-------|
| 1 | x.x.x.1-9 | /24 | Équipements réseau |
| 10 | x.x.x.10-49 | /24 | Serveurs |
| 20 | x.x.x.50-99 | /24 | Imprimantes |
| 30 | x.x.x.100-199 | /24 | Postes de travail |
| 40 | x.x.x.200-254 | /24 | WiFi / DHCP |

### Ports Standards à Connaître

| Service | Port | Protocole |
|---------|------|-----------|
| HTTP | 80 | TCP |
| HTTPS | 443 | TCP |
| RDP | 3389 | TCP |
| SSH | 22 | TCP |
| DNS | 53 | UDP/TCP |
| DHCP | 67-68 | UDP |
| LDAP | 389 | TCP |
| LDAPS | 636 | TCP |
| SMB | 445 | TCP |
| SQL Server | 1433 | TCP |
| MySQL | 3306 | TCP |
| PostgreSQL | 5432 | TCP |

---

## Logiciels Métier Courants

### Secteur EHPAD/Maison de Retraite

| Logiciel | Éditeur | Usage | Port Serveur |
|----------|---------|-------|--------------|
| NetSoins | Teranga | Dossier résident, soins | 8080 |
| Titan | Cegedim | Planning, RH | Cloud |
| Osiris | Evolucare | Dossier résident | 443 |
| BlueKanGo | BlueKanGo | Qualité, HACCP | Cloud |
| Medissimo | Medissimo | PDA (Préparation Doses) | Cloud |

### Secteur Clinique/Hôpital

| Logiciel | Éditeur | Usage | Port Serveur |
|----------|---------|-------|--------------|
| Hopital Manager | Softway | DPI complet | 8443 |
| Easily | Cegedim | Gestion administrative | Cloud |
| Xplore | Maincare | DPI | 443 |
| PACS Carestream | Carestream | Imagerie DICOM | 4242 (DICOM) |
| Citrix | Citrix | Accès distant | 443, 1494, 2598 |

---

## Commandes de Diagnostic Essentielles

### Windows

```powershell
# Test connectivité
ping 8.8.8.8                      # Test Internet
ping [IP_SERVEUR]                 # Test serveur local
tracert google.com                # Trace route

# Informations réseau
ipconfig /all                     # Configuration IP complète
nslookup [DOMAINE]               # Résolution DNS
netstat -an                       # Connexions actives

# Services
net start                         # Liste services démarrés
sc query [SERVICE]               # État d'un service
services.msc                      # Console services

# Active Directory
nltest /dsgetdc:[DOMAINE]        # Trouver contrôleur domaine
gpresult /r                       # Stratégies appliquées

# Spouleur impression
net stop spooler                  # Arrêter spouleur
net start spooler                 # Démarrer spouleur
```

### Linux

```bash
# Test connectivité
ping -c 4 8.8.8.8                 # Test Internet
traceroute google.com             # Trace route
curl -I https://google.com        # Test HTTP

# Informations réseau
ip addr show                      # Interfaces réseau
ip route                          # Table de routage
ss -tuln                          # Ports en écoute
dig [DOMAINE]                     # Résolution DNS

# Services
systemctl status [SERVICE]        # État service
systemctl restart [SERVICE]       # Redémarrer service
journalctl -u [SERVICE] -f        # Logs en temps réel

# Disques
df -h                             # Espace disque
lsblk                             # Liste disques
```

---

## Procédures d'Urgence

### Panne Internet Totale

1. **Vérifier Phibee** → État lien (UP/DOWN)
2. **Si DOWN** → Contacter FAI avec n° contrat
3. **Si UP** → Vérifier routeur local (ping, voyants)
4. **Solution temporaire** → Partage 4G

### Serveur Critique DOWN

1. **Vérifier Observium** → État serveur
2. **Console VMware/Hyper-V** → État VM
3. **Si VM OK mais service KO** → Redémarrer service
4. **Si VM KO** → Restauration Veeam
5. **Communiquer** → Informer client + ETA

### Ransomware Détecté

1. **ISOLER IMMÉDIATEMENT** → Débrancher réseau
2. **NE PAS ÉTEINDRE** → Préserver RAM pour forensic
3. **ALERTER** → DSI + Direction + WIDIP N2
4. **DOCUMENTER** → Screenshots, fichiers chiffrés
5. **RESTAURER** → Depuis sauvegardes APRÈS nettoyage

---

## Contacts Fournisseurs

### FAI

| FAI | Support Pro | Horaires |
|-----|-------------|----------|
| Orange Pro | 3901 | 24/7 |
| SFR Business | 1023 | 8h-20h |
| Bouygues Pro | 1064 | 8h-20h |
| Free Pro | 3244 | 8h-20h |

### Constructeurs

| Marque | Support | Horaires |
|--------|---------|----------|
| HP/HPE | 01 57 32 32 32 | 24/7 |
| Dell | 08 05 54 05 40 | 8h-18h |
| Cisco | TAC Web | 24/7 |
| Fortinet | support.fortinet.com | 24/7 |

### Éditeurs Métier

| Éditeur | Support | Horaires |
|---------|---------|----------|
| Teranga (NetSoins) | 01 46 12 34 56 | 8h-18h |
| Softway Medical | 04 67 91 22 22 | 8h-18h |
| Carestream | 01 53 80 80 80 | 8h-18h |

---

## Glossaire WIDIP

| Terme | Définition |
|-------|------------|
| **Phibee** | Outil de monitoring des liens Internet clients |
| **Observium** | Plateforme de supervision réseau (SNMP) |
| **SAFEGUARD** | Système de sécurité WIDIP (niveaux L0-L4) |
| **RAG** | Retrieval-Augmented Generation - Base de connaissances IA |
| **MCP** | Model Context Protocol - Interface outils IA |
| **PRA** | Plan de Reprise d'Activité |
| **PCA** | Plan de Continuité d'Activité |
| **RPO** | Recovery Point Objective - Perte de données max acceptable |
| **RTO** | Recovery Time Objective - Temps de reprise max acceptable |
| **HDS** | Hébergeur de Données de Santé (certification) |
| **DPI** | Dossier Patient Informatisé |
| **PACS** | Picture Archiving and Communication System (imagerie) |

## Tags
`documentation` `technique` `réseau` `commandes` `diagnostic` `urgence`
