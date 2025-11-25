#!/usr/bin/env python3
"""
Gestion-Frigo - Application de Gestion de Stock pour Produits Réfrigérés
Point d'entrée principal de l'application.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


def main():
    """Fonction principale de l'application."""
    # Créer l'application Qt
    app = QApplication(sys.argv)

    # Définir les propriétés de l'application
    app.setApplicationName("Gestion-Frigo")
    app.setOrganizationName("Gestion-Frigo")
    app.setApplicationVersion("1.0.0")

    # Initialiser la base de données
    db = DatabaseManager()

    # Afficher la page de connexion
    login_dialog = LoginDialog(db)
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        # L'utilisateur a annulé la connexion
        return 0

    # Récupérer l'utilisateur connecté
    current_user = login_dialog.get_current_user()

    if not current_user:
        QMessageBox.critical(None, "Erreur", "Erreur lors de la connexion")
        return 1

    # Créer et afficher la fenêtre principale
    window = MainWindow(current_user)
    window.show()

    # Lancer la boucle d'événements
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
