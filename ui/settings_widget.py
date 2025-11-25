"""Widget de gestion des paramètres de l'application (Admin seulement)."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QDialog, QComboBox,
    QColorDialog, QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from database.models import User, AppSettings


class SettingsWidget(QWidget):
    """Widget pour gérer les paramètres de l'application."""

    def __init__(self, db: DatabaseManager, current_user: User):
        """Initialise le widget de paramètres."""
        super().__init__()
        self.db = db
        self.current_user = current_user
        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("⚙️ Paramètres de l'Application")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Onglets
        self.tabs = QTabWidget()

        # Onglet Informations entreprise
        self.company_tab = self._create_company_tab()
        self.tabs.addTab(self.company_tab, "🏢 Entreprise")

        # Onglet Tickets de caisse
        self.receipt_tab = self._create_receipt_tab()
        self.tabs.addTab(self.receipt_tab, "🧾 Tickets")

        # Onglet Apparence
        self.appearance_tab = self._create_appearance_tab()
        self.tabs.addTab(self.appearance_tab, "🎨 Apparence")

        # Onglet Utilisateurs (seulement pour admin)
        if self.current_user.role == "ADMIN":
            self.users_tab = self._create_users_tab()
            self.tabs.addTab(self.users_tab, "👥 Utilisateurs")

        layout.addWidget(self.tabs)

        # Boutons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Enregistrer")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)

        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self._load_settings)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _create_company_tab(self) -> QWidget:
        """Crée l'onglet des informations entreprise."""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)

        self.company_name_input = QLineEdit()
        self.company_address_input = QLineEdit()
        self.company_phone_input = QLineEdit()
        self.company_email_input = QLineEdit()

        layout.addRow("Nom de l'entreprise:", self.company_name_input)
        layout.addRow("Adresse:", self.company_address_input)
        layout.addRow("Téléphone:", self.company_phone_input)
        layout.addRow("Email:", self.company_email_input)

        return widget

    def _create_receipt_tab(self) -> QWidget:
        """Crée l'onglet des paramètres de tickets."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        group = QGroupBox("Affichage sur le ticket")
        group_layout = QVBoxLayout()

        self.show_address_check = QCheckBox("Afficher l'adresse")
        self.show_phone_check = QCheckBox("Afficher le téléphone")
        self.show_email_check = QCheckBox("Afficher l'email")

        group_layout.addWidget(self.show_address_check)
        group_layout.addWidget(self.show_phone_check)
        group_layout.addWidget(self.show_email_check)

        group.setLayout(group_layout)
        layout.addWidget(group)

        # Message de pied de page
        footer_group = QGroupBox("Message de pied de page")
        footer_layout = QFormLayout()

        self.footer_text_input = QLineEdit()
        footer_layout.addRow("Texte:", self.footer_text_input)

        footer_group.setLayout(footer_layout)
        layout.addWidget(footer_group)

        layout.addStretch()

        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Crée l'onglet de l'apparence."""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)

        # Couleur principale
        color_layout = QHBoxLayout()
        self.primary_color_input = QLineEdit()
        self.primary_color_input.setReadOnly(True)

        color_btn = QPushButton("Choisir")
        color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.primary_color_input, 3)
        color_layout.addWidget(color_btn, 1)

        layout.addRow("Couleur principale:", color_layout)

        # Logo (futur)
        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setReadOnly(True)

        logo_btn = QPushButton("Parcourir")
        logo_btn.clicked.connect(self._choose_logo)
        logo_layout.addWidget(self.logo_path_input, 3)
        logo_layout.addWidget(logo_btn, 1)

        layout.addRow("Logo:", logo_layout)

        return widget

    def _create_users_tab(self) -> QWidget:
        """Crée l'onglet de gestion des utilisateurs."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Boutons d'action
        button_layout = QHBoxLayout()

        add_user_btn = QPushButton("➕ Nouvel utilisateur")
        add_user_btn.clicked.connect(self._add_user)

        edit_user_btn = QPushButton("✏️ Modifier")
        edit_user_btn.clicked.connect(self._edit_user)

        delete_user_btn = QPushButton("🗑️ Supprimer")
        delete_user_btn.clicked.connect(self._delete_user)

        button_layout.addWidget(add_user_btn)
        button_layout.addWidget(edit_user_btn)
        button_layout.addWidget(delete_user_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table des utilisateurs
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Nom d'utilisateur", "Nom complet", "Rôle", "Actif"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.users_table)

        # Charger les utilisateurs
        self._load_users()

        return widget

    def _load_settings(self):
        """Charge les paramètres depuis la base de données."""
        settings = self.db.get_app_settings()

        # Entreprise
        self.company_name_input.setText(settings.company_name)
        self.company_address_input.setText(settings.company_address)
        self.company_phone_input.setText(settings.company_phone)
        self.company_email_input.setText(settings.company_email)

        # Tickets
        self.show_address_check.setChecked(settings.show_address_on_receipt)
        self.show_phone_check.setChecked(settings.show_phone_on_receipt)
        self.show_email_check.setChecked(settings.show_email_on_receipt)
        self.footer_text_input.setText(settings.receipt_footer_text)

        # Apparence
        self.primary_color_input.setText(settings.primary_color)
        self.primary_color_input.setStyleSheet(f"background-color: {settings.primary_color};")
        self.logo_path_input.setText(settings.logo_path)

    def _save_settings(self):
        """Enregistre les paramètres."""
        settings = AppSettings()
        settings.id = 1

        # Entreprise
        settings.company_name = self.company_name_input.text()
        settings.company_address = self.company_address_input.text()
        settings.company_phone = self.company_phone_input.text()
        settings.company_email = self.company_email_input.text()

        # Tickets
        settings.show_address_on_receipt = self.show_address_check.isChecked()
        settings.show_phone_on_receipt = self.show_phone_check.isChecked()
        settings.show_email_on_receipt = self.show_email_check.isChecked()
        settings.receipt_footer_text = self.footer_text_input.text()

        # Apparence
        settings.primary_color = self.primary_color_input.text()
        settings.logo_path = self.logo_path_input.text()

        # Sauvegarder
        self.db.update_app_settings(settings)

        QMessageBox.information(
            self,
            "Succès",
            "Les paramètres ont été enregistrés avec succès!"
        )

    def _choose_color(self):
        """Ouvre le sélecteur de couleur."""
        current_color = QColor(self.primary_color_input.text())
        color = QColorDialog.getColor(current_color, self, "Choisir une couleur")

        if color.isValid():
            self.primary_color_input.setText(color.name())
            self.primary_color_input.setStyleSheet(f"background-color: {color.name()};")

    def _choose_logo(self):
        """Ouvre le sélecteur de fichier pour le logo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.logo_path_input.setText(file_path)

    def _load_users(self):
        """Charge les utilisateurs dans la table."""
        users = self.db.get_all_users()
        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.full_name))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.role))
            self.users_table.setItem(row, 4, QTableWidgetItem("Oui" if user.is_active else "Non"))

    def _add_user(self):
        """Ouvre le dialogue pour ajouter un utilisateur."""
        dialog = UserDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user, password = dialog.get_user_data()
            try:
                self.db.add_user(user, password)
                self._load_users()
                QMessageBox.information(self, "Succès", "Utilisateur créé avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {str(e)}")

    def _edit_user(self):
        """Ouvre le dialogue pour modifier un utilisateur."""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un utilisateur.")
            return

        user_id = int(self.users_table.item(current_row, 0).text())
        users = self.db.get_all_users()
        user = next((u for u in users if u.id == user_id), None)

        if user:
            dialog = UserDialog(self.db, user=user, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_user, password = dialog.get_user_data()
                try:
                    self.db.update_user(updated_user)
                    if password:
                        self.db.change_user_password(updated_user.id, password)
                    self._load_users()
                    QMessageBox.information(self, "Succès", "Utilisateur modifié avec succès!")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification: {str(e)}")

    def _delete_user(self):
        """Supprime l'utilisateur sélectionné."""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un utilisateur.")
            return

        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()

        # Ne pas permettre de supprimer le compte admin
        if username == "admin":
            QMessageBox.warning(self, "Interdiction", "Impossible de supprimer le compte admin.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_user(user_id)
                self._load_users()
                QMessageBox.information(self, "Succès", "Utilisateur supprimé avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")


class UserDialog(QDialog):
    """Dialogue pour créer/modifier un utilisateur."""

    def __init__(self, db: DatabaseManager, user: User = None, parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Nouvel utilisateur" if user is None else "Modifier utilisateur")
        self.setMinimumWidth(400)
        self._create_ui()

        if user:
            self._load_user_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QFormLayout()
        self.setLayout(layout)

        self.username_input = QLineEdit()
        self.full_name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Laisser vide pour ne pas changer")

        self.role_combo = QComboBox()
        self.role_combo.addItem("Utilisateur", "USER")
        self.role_combo.addItem("Administrateur", "ADMIN")

        self.is_active_check = QCheckBox("Compte actif")
        self.is_active_check.setChecked(True)

        layout.addRow("Nom d'utilisateur:", self.username_input)
        layout.addRow("Nom complet:", self.full_name_input)
        layout.addRow("Mot de passe:", self.password_input)
        layout.addRow("Rôle:", self.role_combo)
        layout.addRow("", self.is_active_check)

        # Boutons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Enregistrer")
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addRow(button_layout)

    def _load_user_data(self):
        """Charge les données de l'utilisateur."""
        self.username_input.setText(self.user.username)
        self.username_input.setReadOnly(True)  # Ne pas permettre de changer le username
        self.full_name_input.setText(self.user.full_name)

        index = self.role_combo.findData(self.user.role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        self.is_active_check.setChecked(self.user.is_active)

    def get_user_data(self):
        """Retourne les données de l'utilisateur."""
        if self.user:
            user = self.user
        else:
            user = User()

        user.username = self.username_input.text()
        user.full_name = self.full_name_input.text()
        user.role = self.role_combo.currentData()
        user.is_active = self.is_active_check.isChecked()

        password = self.password_input.text()

        return user, password
