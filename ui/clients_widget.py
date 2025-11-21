"""Widget de gestion des clients."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMessageBox, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from database.models import Client


class ClientsWidget(QWidget):
    """Widget pour gérer les clients."""

    def __init__(self, db: DatabaseManager):
        """Initialise le widget de clients."""
        super().__init__()
        self.db = db
        self._create_ui()
        self.refresh_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("Gestion des Clients")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Boutons d'action
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Nouveau Client")
        self.add_btn.clicked.connect(self._add_client)

        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table des clients
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Entreprise", "Email", "Téléphone", "Ville", "Actions"
        ])
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.clients_table)

    def refresh_data(self):
        """Rafraîchit les données affichées."""
        clients = self.db.get_all_clients()
        self.clients_table.setRowCount(len(clients))

        for row, client in enumerate(clients):
            self.clients_table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            self.clients_table.setItem(row, 1, QTableWidgetItem(client.name))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client.company or "-"))
            self.clients_table.setItem(row, 3, QTableWidgetItem(client.email or "-"))
            self.clients_table.setItem(row, 4, QTableWidgetItem(client.phone or "-"))
            self.clients_table.setItem(row, 5, QTableWidgetItem(client.city or "-"))

            # Boutons d'action
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda checked, c=client: self._edit_client(c))

            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(40)
            delete_btn.clicked.connect(lambda checked, c=client: self._delete_client(c))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()

            self.clients_table.setCellWidget(row, 6, action_widget)

    def _add_client(self):
        """Ouvre le dialogue pour ajouter un client."""
        dialog = ClientDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client = dialog.get_client()
            self.db.add_client(client)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Client ajouté avec succès!")

    def _edit_client(self, client: Client):
        """Ouvre le dialogue pour modifier un client."""
        dialog = ClientDialog(client=client, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_client = dialog.get_client()
            self.db.update_client(updated_client)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Client modifié avec succès!")

    def _delete_client(self, client: Client):
        """Supprime un client après confirmation."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Êtes-vous sûr de vouloir supprimer le client "{client.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_client(client.id)
                self.refresh_data()
                QMessageBox.information(self, "Succès", "Client supprimé avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le client: {str(e)}")


class ClientDialog(QDialog):
    """Dialogue pour ajouter/modifier un client."""

    def __init__(self, client: Client = None, parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Nouveau Client" if client is None else "Modifier Client")
        self.setMinimumWidth(500)
        self._create_ui()

        if client:
            self._load_client_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QFormLayout()
        self.setLayout(layout)

        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.city_input = QLineEdit()
        self.postal_code_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        layout.addRow("Nom *:", self.name_input)
        layout.addRow("Entreprise:", self.company_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Téléphone:", self.phone_input)
        layout.addRow("Adresse:", self.address_input)
        layout.addRow("Ville:", self.city_input)
        layout.addRow("Code postal:", self.postal_code_input)
        layout.addRow("Notes:", self.notes_input)

        # Boutons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.clicked.connect(self._validate_and_accept)
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def _load_client_data(self):
        """Charge les données du client dans le formulaire."""
        self.name_input.setText(self.client.name)
        self.company_input.setText(self.client.company or "")
        self.email_input.setText(self.client.email or "")
        self.phone_input.setText(self.client.phone or "")
        self.address_input.setText(self.client.address or "")
        self.city_input.setText(self.client.city or "")
        self.postal_code_input.setText(self.client.postal_code or "")
        self.notes_input.setText(self.client.notes or "")

    def _validate_and_accept(self):
        """Valide les données avant d'accepter."""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire!")
            return
        self.accept()

    def get_client(self) -> Client:
        """Retourne le client avec les données du formulaire."""
        client = self.client if self.client else Client()

        client.name = self.name_input.text()
        client.company = self.company_input.text()
        client.email = self.email_input.text()
        client.phone = self.phone_input.text()
        client.address = self.address_input.text()
        client.city = self.city_input.text()
        client.postal_code = self.postal_code_input.text()
        client.notes = self.notes_input.toPlainText()

        return client
