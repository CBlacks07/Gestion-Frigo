# Gestion-Frigo - Application de Gestion de Stock pour Produits Réfrigérés

Application desktop professionnelle pour la gestion complète de stocks de produits réfrigérés et congelés.

## Fonctionnalités

### 📦 Gestion des Stocks
- Enregistrement des entrées et sorties de stock
- Alertes automatiques pour stocks bas
- Suivi en temps réel des quantités

### ⏰ Suivi des Dates
- Gestion des dates de péremption
- Suivi des dates de congélation
- Alertes pour produits bientôt périmés

### 💰 Ventes et Facturation
- Création et gestion des ventes
- Génération automatique de factures (PDF)
- Historique complet des transactions

### 👥 Gestion des Clients
- Base de données clients complète
- Historique des achats par client
- Coordonnées et informations détaillées

### 🏢 Gestion des Fournisseurs
- Répertoire des fournisseurs
- Suivi des commandes et livraisons
- Historique des achats

### 📊 Statistiques et Rapports
- Tableau de bord avec indicateurs clés
- Graphiques de ventes et stocks
- Rapports détaillés exportables

## Installation

### Prérequis
- Python 3.8 ou supérieur

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Lancement de l'application

```bash
python main.py
```

## Structure du Projet

```
Gestion-Frigo/
├── main.py                 # Point d'entrée de l'application
├── database/
│   ├── __init__.py
│   ├── db_manager.py      # Gestionnaire de base de données
│   └── models.py          # Modèles de données
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Fenêtre principale
│   ├── stock_widget.py    # Interface gestion stocks
│   ├── sales_widget.py    # Interface ventes
│   ├── clients_widget.py  # Interface clients
│   ├── suppliers_widget.py # Interface fournisseurs
│   └── stats_widget.py    # Interface statistiques
├── utils/
│   ├── __init__.py
│   ├── alerts.py          # Système d'alertes
│   └── reports.py         # Génération de rapports
└── requirements.txt
```

## Technologies Utilisées

- **Python 3.x** - Langage principal
- **PyQt6** - Interface graphique
- **SQLite** - Base de données embarquée
- **ReportLab** - Génération de PDF
- **Matplotlib** - Graphiques et visualisations

## Licence

Propriétaire - Tous droits réservés

## Auteur

Développé pour la gestion professionnelle de produits réfrigérés et congelés.
