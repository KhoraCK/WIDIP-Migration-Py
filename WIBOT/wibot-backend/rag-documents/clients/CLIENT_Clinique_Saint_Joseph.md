# Fiche Client : Clinique Saint-Joseph

## Informations Générales
| Champ | Valeur |
|-------|--------|
| **Code Client** | CLI-2023-0089 |
| **Nom** | Clinique Saint-Joseph |
| **Type** | Clinique SSR |
| **Adresse** | 12 Rue de la Santé, 69003 Lyon |
| **Téléphone** | 04 72 33 44 55 |
| **Email** | dsi@clinique-stjoseph.fr |
| **Capacité** | 85 lits |
| **Groupe** | Groupe Santé Plus |

## Contacts
| Rôle | Nom | Téléphone | Email |
|------|-----|-----------|-------|
| Directeur | Jean-Pierre Lefebvre | 04 72 33 44 01 | jp.lefebvre@clinique-stjoseph.fr |
| DSI | Amélie Rousseau | 04 72 33 44 02 | a.rousseau@clinique-stjoseph.fr |
| Cadre Infirmier | Marc Dubois | 04 72 33 44 03 | m.dubois@clinique-stjoseph.fr |
| Référent RGPD | Claire Martin | 04 72 33 44 04 | c.martin@clinique-stjoseph.fr |

## Infrastructure Réseau

### Connexion Internet
| Paramètre | Valeur |
|-----------|--------|
| **FAI Principal** | SFR Business |
| **Contrat** | SFR-ENT-2024-12345 |
| **Débit** | 200 Mbps symétrique |
| **IP Publique** | 93.17.245.132 |
| **FAI Backup** | Bouygues 4G |
| **IP Routeur** | 10.0.0.1 |

### Serveurs
| Nom | IP | Rôle | OS |
|-----|-----|------|-----|
| SRV-CSJ-DC01 | 10.0.1.10 | Contrôleur de domaine principal | Windows Server 2022 |
| SRV-CSJ-DC02 | 10.0.1.11 | Contrôleur de domaine secondaire | Windows Server 2022 |
| SRV-CSJ-HOP01 | 10.0.1.20 | Serveur Hopital Manager | Windows Server 2019 |
| SRV-CSJ-IMG01 | 10.0.1.21 | Serveur imagerie PACS | Linux Ubuntu 22.04 |
| SRV-CSJ-MAIL01 | 10.0.1.30 | Serveur Exchange | Windows Server 2019 |
| SRV-CSJ-VDI01 | 10.0.1.40 | Serveur VDI Citrix | Windows Server 2022 |

### Équipements Réseau
| Équipement | IP | Modèle | Localisation |
|------------|-----|--------|--------------|
| Firewall | 10.0.0.1 | Fortinet FortiGate 60F | Salle serveurs |
| Switch Core | 10.0.0.2 | HPE Aruba 2930F-48G | Salle serveurs |
| Switch Bloc A | 10.0.0.3 | HPE Aruba 2530-24G | Bloc chirurgical |
| Switch Bloc B | 10.0.0.4 | HPE Aruba 2530-24G | Rééducation |
| Switch Bloc C | 10.0.0.5 | HPE Aruba 2530-24G | Administration |
| Contrôleur WiFi | 10.0.0.10 | Aruba Mobility Controller | Salle serveurs |

### Équipements Médicaux Connectés
| Équipement | IP | Type | Service |
|------------|-----|------|---------|
| Scanner CT | 10.0.2.100 | Siemens SOMATOM | Imagerie |
| IRM | 10.0.2.101 | GE Signa | Imagerie |
| Échographe 1 | 10.0.2.110 | Philips EPIQ | Consultation |
| Échographe 2 | 10.0.2.111 | Philips Affiniti | Rééducation |
| Moniteurs patients | 10.0.2.120-135 | Philips IntelliVue | Soins |

## Logiciels Métier
| Logiciel | Version | Serveur | Usage |
|----------|---------|---------|-------|
| Hopital Manager | 12.3 | SRV-CSJ-HOP01 | DPI (Dossier Patient Informatisé) |
| Easily RH | Cloud | SaaS | Gestion RH |
| PACS Carestream | 14.0 | SRV-CSJ-IMG01 | Imagerie médicale |
| Citrix Virtual Apps | 2203 | SRV-CSJ-VDI01 | Accès distant |

## Contrat WIDIP
| Paramètre | Valeur |
|-----------|--------|
| **Type** | Platinum HDS |
| **Début** | 15/03/2023 |
| **Renouvellement** | 15/03/2026 |
| **SLA** | 2h ouvrées (critique) / 4h (standard) |
| **Interventions/an** | Illimitées |
| **Astreinte** | Oui (24/7) |
| **Certification** | HDS (Hébergeur Données Santé) |

## Sécurité et Conformité

### Certifications
- ISO 27001 (en cours)
- HDS niveau 5
- RGPD conforme

### Politique de sécurité
- MFA obligatoire pour accès distant
- Rotation mots de passe : 90 jours
- Audit sécurité : trimestriel
- PRA/PCA : testé annuellement

## Historique Incidents Majeurs

### Décembre 2024
- **08/12/2024** - Alerte sécurité FortiGate : tentative intrusion bloquée (IP Russie)
- **15/12/2024** - Saturation stockage PACS → Extension NAS 20TB

### Novembre 2024
- **02/11/2024** - Panne serveur VDI 6h (crash disque) - Restauration Veeam OK
- **19/11/2024** - Mise à jour critique Exchange (CVE-2024-XXXX)

### Octobre 2024
- **07/10/2024** - Migration Hopital Manager 12.2 → 12.3
- **21/10/2024** - Remplacement 12 postes Windows 10 → 11
- **30/10/2024** - Exercice PRA réussi (RTO: 2h30)

## Particularités Techniques

### Réseau segmenté (VLAN)
| VLAN | Plage IP | Usage |
|------|----------|-------|
| 10 | 10.0.1.0/24 | Serveurs |
| 20 | 10.0.2.0/24 | Équipements médicaux |
| 30 | 10.0.3.0/24 | Postes administratifs |
| 40 | 10.0.4.0/24 | Postes soignants |
| 50 | 10.0.5.0/24 | WiFi Invités (isolé) |

### Sauvegarde
- **Solution** : Veeam Backup & Replication 12
- **Rétention** : 30 jours local, 90 jours cloud
- **RPO** : 4h (serveurs critiques), 24h (autres)
- **Cible cloud** : Azure Blob Storage (région France)

## Notes Importantes
- **CRITIQUE** : Le serveur PACS ne doit JAMAIS être redémarré sans coordination avec le service imagerie (risque perte examen en cours)
- **Contact urgence** : DSI Amélie Rousseau joignable 24/7 au 06 12 34 56 78
- **Maintenance** : Fenêtre autorisée uniquement dimanche 2h-6h

## Tags
`clinique` `lyon` `hds` `platinum` `ssr` `imagerie` `citrix` `critique`
