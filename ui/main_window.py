"""Fenêtre principale de l'application."""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox, QLabel, QMenuBar, QMenu, QPushButton, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QPixmap

from database.db_manager import DatabaseManager
from database.models import User
from utils.alerts import AlertManager
from utils.reports import ReportGenerator

from .stock_widget import StockWidget
from .clients_widget import ClientsWidget
from .suppliers_widget import SuppliersWidget
from .sales_widget import SalesWidget
from .stats_widget import StatsWidget
from .settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    # Signal pour demander la déconnexion
    logout_requested = pyqtSignal()

    def __init__(self, current_user: User):
        """Initialise la fenêtre principale."""
        super().__init__()

        # Utilisateur connecté
        self.current_user = current_user

        # Initialiser les gestionnaires
        self.db = DatabaseManager()
        self.alert_manager = AlertManager(self.db)
        self.report_generator = ReportGenerator(self.db)

        # Récupérer les paramètres
        self.app_settings = self.db.get_app_settings()

        # Configuration de la fenêtre
        self.setWindowTitle(f"{self.app_settings.company_name} - Gestion de Stock")
        self.setMinimumSize(1200, 800)

        # Appliquer le logo si configuré
        if self.app_settings.logo_path:
            self.setWindowIcon(QIcon(self.app_settings.logo_path))

        # Créer la barre de menu
        self._create_menu()

        # Créer l'interface
        self._create_ui()

        # Appliquer le style personnalisé
        self._apply_custom_style()

        # Configurer la barre de statut
        self._setup_statusbar()

        # Timer pour rafraîchir les alertes
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self._update_alerts)
        self.alert_timer.start(60000)  # Rafraîchir toutes les minutes

        # Afficher les alertes au démarrage
        self._update_alerts()

    def _create_menu(self):
        """Crée la barre de menu."""
        menubar = self.menuBar()

        # Menu Fichier
        file_menu = menubar.addMenu("📁 Fichier")

        # Action déconnexion
        logout_action = QAction("🚪 Déconnexion", self)
        logout_action.setShortcut("Ctrl+Q")
        logout_action.triggered.connect(self._logout)
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        # Action quitter
        exit_action = QAction("❌ Quitter", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Aide (si admin)
        if self.current_user.role == "ADMIN":
            help_menu = menubar.addMenu("❓ Aide")

            about_action = QAction("ℹ️ À propos", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)

    def _logout(self):
        """Déconnecte l'utilisateur."""
        reply = QMessageBox.question(
            self,
            'Confirmation de déconnexion',
            'Êtes-vous sûr de vouloir vous déconnecter?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Fermer la fenêtre actuelle
            self.close()
            # Émettre le signal de déconnexion
            self.logout_requested.emit()

    def _show_about(self):
        """Affiche la fenêtre À propos."""
        QMessageBox.about(
            self,
            "À propos",
            f"<h2>{self.app_settings.company_name}</h2>"
            f"<p><b>Gestion de Stock Professionnel</b></p>"
            f"<p>Version 1.0.0</p>"
            f"<p>Utilisateur connecté: {self.current_user.full_name}</p>"
            f"<p>Rôle: {self.current_user.role}</p>"
        )

    def _apply_custom_style(self):
        """Applique le style personnalisé avec la couleur principale."""
        color = self.app_settings.primary_color

        # Style CSS personnalisé
        style = f"""
        QTabWidget::pane {{
            border: 1px solid #ddd;
        }}
        QTabBar::tab {{
            background: #f0f0f0;
            padding: 8px 15px;
            margin: 2px;
            border-radius: 5px 5px 0 0;
        }}
        QTabBar::tab:selected {{
            background: {color};
            color: white;
            font-weight: bold;
        }}
        QTabBar::tab:hover {{
            background: {color};
            color: white;
        }}
        QPushButton {{
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QGroupBox {{
            font-weight: bold;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            color: {color};
        }}
        """

        self.setStyleSheet(style)

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        # Widget central avec tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Créer les widgets pour chaque onglet
        self.stats_widget = StatsWidget(self.db, self.alert_manager, self.report_generator)
        self.stock_widget = StockWidget(self.db, self.alert_manager)
        self.sales_widget = SalesWidget(self.db, self.report_generator)
        self.clients_widget = ClientsWidget(self.db)
        self.suppliers_widget = SuppliersWidget(self.db)

        # Ajouter les onglets
        self.tabs.addTab(self.stats_widget, "📊 Tableau de Bord")
        self.tabs.addTab(self.stock_widget, "📦 Gestion des Stocks")
        self.tabs.addTab(self.sales_widget, "💰 Ventes & Factures")
        self.tabs.addTab(self.clients_widget, "👥 Clients")
        self.tabs.addTab(self.suppliers_widget, "🏢 Fournisseurs")

        # Onglet Paramètres (seulement pour admin)
        if self.current_user.role == "ADMIN":
            self.settings_widget = SettingsWidget(self.db, self.current_user)
            self.tabs.addTab(self.settings_widget, "⚙️ Paramètres")

        # Connecter les signaux
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _setup_statusbar(self):
        """Configure la barre de statut."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Label pour les alertes
        self.alert_label = QLabel()
        self.statusbar.addPermanentWidget(self.alert_label)

        # Label pour les informations
        self.info_label = QLabel(f"Connecté: {self.current_user.full_name} ({self.current_user.role})")
        self.statusbar.addWidget(self.info_label)

    def _on_tab_changed(self, index):
        """Appelé quand l'onglet change."""
        tab_names = [
            "Tableau de Bord",
            "Gestion des Stocks",
            "Ventes & Factures",
            "Clients",
            "Fournisseurs"
        ]
        if 0 <= index < len(tab_names):
            self.info_label.setText(f"Section active: {tab_names[index]}")

        # Rafraîchir les données du widget actif
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()

    def _update_alerts(self):
        """Met à jour l'affichage des alertes."""
        try:
            alert_count = self.alert_manager.get_alert_count()
            total = alert_count['total']

            if total > 0:
                critical = alert_count['CRITICAL']
                high = alert_count['HIGH']

                alert_text = f"⚠️ {total} alerte(s)"
                if critical > 0:
                    alert_text += f" | {critical} critique(s)"
                if high > 0:
                    alert_text += f" | {high} haute(s)"

                self.alert_label.setText(alert_text)
                self.alert_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.alert_label.setText("✓ Aucune alerte")
                self.alert_label.setStyleSheet("color: green;")

        except Exception as e:
            self.alert_label.setText(f"Erreur alertes: {str(e)}")
            self.alert_label.setStyleSheet("color: orange;")

    def closeEvent(self, event):
        """Appelé lors de la fermeture de la fenêtre."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            'Êtes-vous sûr de vouloir quitter l\'application?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Fermer la base de données
            self.db.close()
            event.accept()
        else:
            event.ignore()

    def show_message(self, title: str, message: str, message_type: str = "info"):
        """Affiche un message à l'utilisateur."""
        if message_type == "info":
            QMessageBox.information(self, title, message)
        elif message_type == "warning":
            QMessageBox.warning(self, title, message)
        elif message_type == "error":
            QMessageBox.critical(self, title, message)
        elif message_type == "success":
            QMessageBox.information(self, title, message)

    def update_statusbar(self, message: str):
        """Met à jour la barre de statut."""
        self.info_label.setText(message)
