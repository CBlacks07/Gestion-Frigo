#!/usr/bin/env python3
"""
Gestion-Frigo - Application de Gestion de Stock pour Produits Réfrigérés
Point d'entrée principal de l'application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def main():
    """Fonction principale de l'application."""
    # Créer l'application Qt
    app = QApplication(sys.argv)

    # Définir les propriétés de l'application
    app.setApplicationName("Gestion-Frigo")
    app.setOrganizationName("Gestion-Frigo")
    app.setApplicationVersion("1.0.0")

    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()

    # Lancer la boucle d'événements
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
