# Fiche Client : EHPAD Les Music Art

## Informations Générales
| Champ | Valeur |
|-------|--------|
| **Code Client** | CLI-2024-0142 |
| **Nom** | EHPAD Les Music Art |
| **Type** | EHPAD |
| **Adresse** | 45 Avenue des Music Art, 75012 Paris |
| **Téléphone** | 01 45 67 89 00 |
| **Email** | direction@music-art-ehpad.fr |
| **Capacité** | 120 lits |
| **Groupe** | Indépendant |

## Contacts
| Rôle | Nom | Téléphone | Email |
|------|-----|-----------|-------|
| Directrice | Marie Durand | 01 45 67 89 01 | m.durand@music-art-ehpad.fr |
| Responsable IT | Thomas Martin | 01 45 67 89 02 | t.martin@music-art-ehpad.fr |
| Cadre de Santé | Sophie Petit | 01 45 67 89 03 | s.petit@music-art-ehpad.fr |

## Infrastructure Réseau

### Connexion Internet
| Paramètre | Valeur |
|-----------|--------|
| **FAI** | Orange Pro |
| **Contrat** | PRO-2023-78456 |
| **Débit** | 100 Mbps symétrique |
| **IP Publique** | 86.234.156.78 |
| **IP Routeur** | 192.168.1.1 |

### Serveurs
| Nom | IP | Rôle | OS |
|-----|-----|------|-----|
| SRV-MDA-DC01 | 192.168.1.10 | Contrôleur de domaine AD | Windows Server 2019 |
| SRV-MDA-APP01 | 192.168.1.11 | Serveur applicatif (NetSoins) | Windows Server 2019 |
| SRV-MDA-FILE01 | 192.168.1.12 | Serveur de fichiers | Windows Server 2019 |
| SRV-MDA-BKP01 | 192.168.1.13 | Serveur de sauvegarde | Windows Server 2019 |

### Équipements Réseau
| Équipement | IP | Modèle | Localisation |
|------------|-----|--------|--------------|
| Routeur Principal | 192.168.1.1 | Cisco RV345 | Local technique RDC |
| Switch Core | 192.168.1.2 | Cisco SG350-28 | Local technique RDC |
| Switch Étage 1 | 192.168.1.3 | Cisco SG250-26 | Placard étage 1 |
| Switch Étage 2 | 192.168.1.4 | Cisco SG250-26 | Placard étage 2 |
| Borne WiFi 1 | 192.168.1.20 | Ubiquiti UAP-AC-PRO | Hall d'accueil |
| Borne WiFi 2 | 192.168.1.21 | Ubiquiti UAP-AC-PRO | Salle commune |

### Imprimantes
| Nom | IP | Modèle | Localisation |
|-----|-----|--------|--------------|
| IMP-MDA-ACC01 | 192.168.1.50 | HP LaserJet Pro M404 | Accueil |
| IMP-MDA-INF01 | 192.168.1.51 | Xerox VersaLink C405 | Infirmerie |
| IMP-MDA-ADM01 | 192.168.1.52 | HP LaserJet Pro M428 | Administration |

## Logiciels Métier
| Logiciel | Version | Serveur | Usage |
|----------|---------|---------|-------|
| NetSoins | 8.5.2 | SRV-MDA-APP01 | Dossier résident |
| Titan | 4.1 | Cloud | Planning personnel |
| Sage Compta | 2024 | SRV-MDA-APP01 | Comptabilité |

## Contrat WIDIP
| Paramètre | Valeur |
|-----------|--------|
| **Type** | Premium |
| **Début** | 01/01/2022 |
| **Renouvellement** | 01/01/2025 |
| **SLA** | 4h ouvrées |
| **Interventions/an** | Illimitées |
| **Astreinte** | Oui (24/7) |

## Historique Incidents Majeurs

### Décembre 2024
- **12/12/2024** - Panne Internet 3h (FAI Orange - coupure fibre quartier)
- **18/12/2024** - Serveur SRV-MDA-APP01 redémarré suite mise à jour Windows

### Novembre 2024
- **05/11/2024** - Remplacement switch étage 2 (défaillant)
- **22/11/2024** - Reset mot de passe x15 utilisateurs (campagne sécurité)

### Octobre 2024
- **10/10/2024** - Migration NetSoins 8.4 → 8.5.2
- **28/10/2024** - Intervention sur site : nettoyage serveurs

## Notes Importantes
- **Attention** : Le responsable IT (Thomas Martin) est souvent en déplacement. Privilégier le contact par email.
- **Particularité** : L'EHPAD a des résidents musiciens, événements fréquents avec besoins WiFi invités.
- **Sauvegarde** : Veeam vers NAS Synology local + réplication cloud OVH.

## Tags
`ehpad` `paris` `netsoins` `orange` `premium` `120-lits`
