"""
Assistant d'installation pour la première utilisation de l'application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTabWidget,
    QWidget, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from database.db_manager import DatabaseManager


class SetupWizard(QDialog):
    """Assistant d'installation pour configurer l'application."""

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setWindowTitle("Installation - Gestion-Frigo")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self._init_ui()

    def _init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout()

        # Titre de bienvenue
        title = QLabel("🎉 Bienvenue dans Gestion-Frigo!")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Configurons votre application en quelques étapes simples.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Onglets pour les différentes sections
        self.tabs = QTabWidget()

        # Onglet 1: Compte administrateur
        admin_tab = self._create_admin_tab()
        self.tabs.addTab(admin_tab, "👤 Compte Administrateur")

        # Onglet 2: Informations entreprise
        company_tab = self._create_company_tab()
        self.tabs.addTab(company_tab, "🏢 Entreprise")

        # Onglet 3: Apparence
        appearance_tab = self._create_appearance_tab()
        self.tabs.addTab(appearance_tab, "🎨 Apparence")

        layout.addWidget(self.tabs)

        # Boutons de navigation
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.finish_btn = QPushButton("✅ Terminer l'installation")
        self.finish_btn.clicked.connect(self._finish_setup)
        self.finish_btn.setDefault(True)  # Bouton par défaut pour la touche Entrée
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.finish_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_admin_tab(self) -> QWidget:
        """Crée l'onglet de création du compte administrateur."""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Créez le compte administrateur qui aura accès à tous les paramètres.\n"
            "⚠️ Ce compte sera nécessaire pour gérer l'application."
        )
        info_label.setStyleSheet("background-color: #e8f5e9; padding: 10px; border-radius: 4px; margin-bottom: 15px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Nom d'utilisateur
        layout.addWidget(QLabel("Nom d'utilisateur:*"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ex: admin")
        layout.addWidget(self.username_input)

        # Nom complet
        layout.addWidget(QLabel("Nom complet:*"))
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Ex: Administrateur Principal")
        layout.addWidget(self.fullname_input)

        # Mot de passe
        layout.addWidget(QLabel("Mot de passe:*"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Entrez un mot de passe sécurisé")
        layout.addWidget(self.password_input)

        # Confirmation mot de passe
        layout.addWidget(QLabel("Confirmer le mot de passe:*"))
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setPlaceholderText("Confirmez le mot de passe")
        layout.addWidget(self.password_confirm_input)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_company_tab(self) -> QWidget:
        """Crée l'onglet d'informations sur l'entreprise."""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Configurez les informations de votre entreprise.\n"
            "Ces informations apparaîtront sur les tickets de caisse."
        )
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 4px; margin-bottom: 15px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Nom de l'entreprise
        layout.addWidget(QLabel("Nom de l'entreprise:"))
        self.company_name_input = QLineEdit()
        self.company_name_input.setPlaceholderText("Ex: Frigo Shop")
        self.company_name_input.setText("Gestion-Frigo")
        layout.addWidget(self.company_name_input)

        # Adresse
        layout.addWidget(QLabel("Adresse:"))
        self.company_address_input = QLineEdit()
        self.company_address_input.setPlaceholderText("Ex: 123 Rue du Commerce, Lomé")
        layout.addWidget(self.company_address_input)

        # Téléphone
        layout.addWidget(QLabel("Téléphone:"))
        self.company_phone_input = QLineEdit()
        self.company_phone_input.setPlaceholderText("Ex: +228 90 00 00 00")
        layout.addWidget(self.company_phone_input)

        # Email
        layout.addWidget(QLabel("Email:"))
        self.company_email_input = QLineEdit()
        self.company_email_input.setPlaceholderText("Ex: contact@frigoshop.tg")
        layout.addWidget(self.company_email_input)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Crée l'onglet d'apparence."""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Personnalisez l'apparence de votre application.\n"
            "Vous pourrez modifier ces paramètres plus tard dans les réglages."
        )
        info_label.setStyleSheet("background-color: #fce4ec; padding: 10px; border-radius: 4px; margin-bottom: 15px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Couleur principale
        layout.addWidget(QLabel("Couleur principale:"))
        color_layout = QHBoxLayout()
        self.color_input = QLineEdit("#2980b9")
        self.color_input.setMaximumWidth(120)
        color_layout.addWidget(self.color_input)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #2980b9; border: 1px solid #ccc; border-radius: 4px;")
        color_layout.addWidget(self.color_preview)

        color_btn = QPushButton("Choisir...")
        color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Logo
        layout.addWidget(QLabel("Logo (optionnel):"))
        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setReadOnly(True)
        self.logo_path_input.setPlaceholderText("Aucun logo sélectionné")
        logo_layout.addWidget(self.logo_path_input)

        logo_btn = QPushButton("📁 Parcourir...")
        logo_btn.clicked.connect(self._choose_logo)
        logo_layout.addWidget(logo_btn)
        layout.addLayout(logo_layout)

        # Aperçu du logo
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(100, 100)
        self.logo_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 4px;")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_preview)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _choose_color(self):
        """Permet de choisir une couleur."""
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor

        current_color = QColor(self.color_input.text())
        color = QColorDialog.getColor(current_color, self, "Choisir une couleur")

        if color.isValid():
            color_hex = color.name()
            self.color_input.setText(color_hex)
            self.color_preview.setStyleSheet(
                f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 4px;"
            )

    def _choose_logo(self):
        """Permet de choisir un logo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.logo_path_input.setText(file_path)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_preview.setPixmap(scaled_pixmap)

    def _finish_setup(self):
        """Termine l'installation et crée les données initiales."""
        # Validation du compte admin
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        if not username or not fullname or not password:
            QMessageBox.warning(
                self,
                "Champs requis",
                "Veuillez remplir tous les champs obligatoires du compte administrateur."
            )
            self.tabs.setCurrentIndex(0)
            return

        if password != password_confirm:
            QMessageBox.warning(
                self,
                "Mots de passe différents",
                "Les mots de passe ne correspondent pas."
            )
            self.tabs.setCurrentIndex(0)
            return

        if len(password) < 4:
            QMessageBox.warning(
                self,
                "Mot de passe trop court",
                "Le mot de passe doit contenir au moins 4 caractères."
            )
            self.tabs.setCurrentIndex(0)
            return

        try:
            # Créer le compte administrateur
            self.db.add_user(
                username,      # user_or_username (positionnel)
                password,      # password
                fullname,      # full_name
                "ADMIN"        # role
            )

            # Mettre à jour les paramètres de l'entreprise
            settings = self.db.get_app_settings()
            settings.company_name = self.company_name_input.text().strip() or "Gestion-Frigo"
            settings.company_address = self.company_address_input.text().strip()
            settings.company_phone = self.company_phone_input.text().strip()
            settings.company_email = self.company_email_input.text().strip()
            settings.primary_color = self.color_input.text().strip() or "#2980b9"
            settings.logo_path = self.logo_path_input.text().strip()

            self.db.update_app_settings(settings)

            QMessageBox.information(
                self,
                "Installation terminée",
                f"L'application est maintenant configurée!\n\n"
                f"Utilisez vos identifiants pour vous connecter:\n"
                f"• Nom d'utilisateur: {username}\n"
                f"• Mot de passe: (celui que vous avez défini)"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors de l'installation:\n{str(e)}"
            )
