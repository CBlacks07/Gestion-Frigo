"""Dialogue de connexion."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from database.db_manager import DatabaseManager
from database.models import User


class LoginDialog(QDialog):
    """Dialogue de connexion à l'application."""

    def __init__(self, db: DatabaseManager):
        """Initialise le dialogue de connexion."""
        super().__init__()
        self.db = db
        self.current_user = None
        self.setWindowTitle("Connexion - Gestion-Frigo")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._create_ui()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("🔐 Connexion")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Espacement
        layout.addSpacing(20)

        # Groupe de connexion
        login_group = QGroupBox()
        login_layout = QFormLayout()

        # Champ nom d'utilisateur
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.username_input.returnPressed.connect(self._on_login)

        # Champ mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.returnPressed.connect(self._on_login)

        login_layout.addRow("Nom d'utilisateur:", self.username_input)
        login_layout.addRow("Mot de passe:", self.password_input)

        login_group.setLayout(login_layout)
        layout.addWidget(login_group)

        # Message d'information
        info_label = QLabel("ℹ️ Compte par défaut: admin / admin")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addSpacing(20)

        # Boutons
        button_layout = QHBoxLayout()

        self.login_btn = QPushButton("🔓 Se connecter")
        self.login_btn.setMinimumHeight(35)
        self.login_btn.clicked.connect(self._on_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.login_btn)

        layout.addLayout(button_layout)

        # Focus sur le champ nom d'utilisateur
        self.username_input.setFocus()

    def _on_login(self):
        """Tente de se connecter."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Champs vides",
                "Veuillez remplir tous les champs."
            )
            return

        # Authentifier l'utilisateur
        user = self.db.authenticate_user(username, password)

        if user:
            self.current_user = user
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Échec de connexion",
                "Nom d'utilisateur ou mot de passe incorrect."
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def get_current_user(self) -> User:
        """Retourne l'utilisateur connecté."""
        return self.current_user
