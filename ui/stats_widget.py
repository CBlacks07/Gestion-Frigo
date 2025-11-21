"""Widget de statistiques et rapports."""
from datetime import datetime, timedelta
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QGridLayout, QMessageBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.db_manager import DatabaseManager
from utils.alerts import AlertManager
from utils.reports import ReportGenerator


class StatsWidget(QWidget):
    """Widget pour afficher les statistiques et générer des rapports."""

    def __init__(self, db: DatabaseManager, alert_manager: AlertManager, report_generator: ReportGenerator):
        """Initialise le widget de statistiques."""
        super().__init__()
        self.db = db
        self.alert_manager = alert_manager
        self.report_generator = report_generator
        self._create_ui()
        self.refresh_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("📊 Tableau de Bord et Statistiques")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Bouton actualiser
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_report_btn = QPushButton("📄 Exporter Rapport Stock")
        self.export_report_btn.clicked.connect(self._export_stock_report)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.export_report_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Indicateurs clés
        kpi_group = QGroupBox("Indicateurs Clés de Performance")
        kpi_layout = QGridLayout()

        # Labels pour les KPI
        self.total_products_label = self._create_kpi_label("0")
        self.low_stock_label = self._create_kpi_label("0")
        self.total_sales_label = self._create_kpi_label("0.00 €")
        self.pending_sales_label = self._create_kpi_label("0")
        self.total_clients_label = self._create_kpi_label("0")
        self.total_suppliers_label = self._create_kpi_label("0")

        # Ajouter les KPI au grid
        kpi_layout.addWidget(QLabel("📦 Produits en stock:"), 0, 0)
        kpi_layout.addWidget(self.total_products_label, 0, 1)

        kpi_layout.addWidget(QLabel("⚠️ Stocks bas:"), 0, 2)
        kpi_layout.addWidget(self.low_stock_label, 0, 3)

        kpi_layout.addWidget(QLabel("💰 Ventes totales:"), 1, 0)
        kpi_layout.addWidget(self.total_sales_label, 1, 1)

        kpi_layout.addWidget(QLabel("⏳ Ventes en attente:"), 1, 2)
        kpi_layout.addWidget(self.pending_sales_label, 1, 3)

        kpi_layout.addWidget(QLabel("👥 Clients:"), 2, 0)
        kpi_layout.addWidget(self.total_clients_label, 2, 1)

        kpi_layout.addWidget(QLabel("🏢 Fournisseurs:"), 2, 2)
        kpi_layout.addWidget(self.total_suppliers_label, 2, 3)

        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)

        # Alertes critiques
        alerts_group = QGroupBox("⚠️ Alertes Critiques")
        alerts_layout = QVBoxLayout()
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(200)
        alerts_layout.addWidget(self.alerts_text)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # Produits les plus vendus
        top_products_group = QGroupBox("🏆 Top 10 Produits les Plus Vendus")
        top_products_layout = QVBoxLayout()
        self.top_products_text = QTextEdit()
        self.top_products_text.setReadOnly(True)
        self.top_products_text.setMaximumHeight(200)
        top_products_layout.addWidget(self.top_products_text)
        top_products_group.setLayout(top_products_layout)
        layout.addWidget(top_products_group)

        # Meilleurs clients
        top_clients_group = QGroupBox("👑 Top 10 Meilleurs Clients")
        top_clients_layout = QVBoxLayout()
        self.top_clients_text = QTextEdit()
        self.top_clients_text.setReadOnly(True)
        self.top_clients_text.setMaximumHeight(200)
        top_clients_layout.addWidget(self.top_clients_text)
        top_clients_group.setLayout(top_clients_layout)
        layout.addWidget(top_clients_group)

        # Ventes par période
        sales_period_group = QGroupBox("📈 Ventes Récentes")
        sales_period_layout = QVBoxLayout()

        period_select_layout = QHBoxLayout()
        period_select_layout.addWidget(QLabel("Période:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("7 derniers jours", 7)
        self.period_combo.addItem("30 derniers jours", 30)
        self.period_combo.addItem("90 derniers jours", 90)
        self.period_combo.currentIndexChanged.connect(self._update_sales_period)
        period_select_layout.addWidget(self.period_combo)
        period_select_layout.addStretch()

        sales_period_layout.addLayout(period_select_layout)

        self.sales_period_text = QTextEdit()
        self.sales_period_text.setReadOnly(True)
        self.sales_period_text.setMaximumHeight(150)
        sales_period_layout.addWidget(self.sales_period_text)

        sales_period_group.setLayout(sales_period_layout)
        layout.addWidget(sales_period_group)

        layout.addStretch()

    def _create_kpi_label(self, text: str) -> QLabel:
        """Crée un label stylisé pour les KPI."""
        label = QLabel(text)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet("color: #2980b9; padding: 5px;")
        return label

    def refresh_data(self):
        """Rafraîchit les données affichées."""
        # Compter les produits
        products = self.db.get_all_products()
        self.total_products_label.setText(str(len(products)))

        # Compter les stocks bas
        low_stock = self.db.get_low_stock_products()
        self.low_stock_label.setText(str(len(low_stock)))
        if len(low_stock) > 0:
            self.low_stock_label.setStyleSheet("color: #e74c3c; padding: 5px; font-weight: bold;")
        else:
            self.low_stock_label.setStyleSheet("color: #27ae60; padding: 5px; font-weight: bold;")

        # Calculer le total des ventes
        total_sales = self.db.get_total_sales()
        self.total_sales_label.setText(f"{total_sales:.2f} €")

        # Compter les ventes en attente
        all_sales = self.db.get_all_sales(limit=1000)
        pending_sales = sum(1 for s in all_sales if s.status == "PENDING")
        self.pending_sales_label.setText(str(pending_sales))

        # Compter les clients
        clients = self.db.get_all_clients()
        self.total_clients_label.setText(str(len(clients)))

        # Compter les fournisseurs
        suppliers = self.db.get_all_suppliers()
        self.total_suppliers_label.setText(str(len(suppliers)))

        # Afficher les alertes
        self._update_alerts()

        # Afficher les top produits
        self._update_top_products()

        # Afficher les top clients
        self._update_top_clients()

        # Afficher les ventes par période
        self._update_sales_period()

    def _update_alerts(self):
        """Met à jour l'affichage des alertes."""
        alerts = self.alert_manager.get_all_alerts()

        if not alerts:
            self.alerts_text.setHtml("<p style='color: green; font-weight: bold;'>✓ Aucune alerte active</p>")
        else:
            html = "<ul>"
            for alert in alerts:
                color = "red" if alert['severity'] in ['CRITICAL', 'HIGH'] else "orange"
                html += f"<li style='color: {color};'><b>[{alert['severity']}]</b> {alert['message']}</li>"
            html += "</ul>"
            self.alerts_text.setHtml(html)

    def _update_top_products(self):
        """Met à jour l'affichage des produits les plus vendus."""
        top_products = self.db.get_top_products(limit=10)

        if not top_products:
            self.top_products_text.setText("Aucune vente enregistrée.")
        else:
            html = "<ol>"
            for product_name, quantity in top_products:
                html += f"<li><b>{product_name}</b>: {quantity:.2f} unités vendues</li>"
            html += "</ol>"
            self.top_products_text.setHtml(html)

    def _update_top_clients(self):
        """Met à jour l'affichage des meilleurs clients."""
        top_clients = self.db.get_top_clients(limit=10)

        if not top_clients:
            self.top_clients_text.setText("Aucun client enregistré.")
        else:
            html = "<ol>"
            for client_name, total_spent in top_clients:
                html += f"<li><b>{client_name}</b>: {total_spent:.2f} €</li>"
            html += "</ol>"
            self.top_clients_text.setHtml(html)

    def _update_sales_period(self):
        """Met à jour l'affichage des ventes par période."""
        days = self.period_combo.currentData()
        sales_by_period = self.db.get_sales_by_period(days=days)

        if not sales_by_period:
            self.sales_period_text.setText(f"Aucune vente sur les {days} derniers jours.")
        else:
            total = sum(amount for _, amount in sales_by_period)
            html = f"<p><b>Total sur la période: {total:.2f} €</b></p><ul>"

            for date_str, amount in sales_by_period:
                html += f"<li>{date_str}: {amount:.2f} €</li>"

            html += "</ul>"
            self.sales_period_text.setHtml(html)

    def _export_stock_report(self):
        """Exporte un rapport de stock en PDF."""
        try:
            pdf_path = self.report_generator.generate_stock_report()
            QMessageBox.information(
                self,
                "Succès",
                f"Rapport de stock généré avec succès!\n\nEmplacement: {pdf_path}"
            )

            # Ouvrir le fichier PDF si possible
            if os.path.exists(pdf_path):
                os.system(f'xdg-open "{pdf_path}" 2>/dev/null || open "{pdf_path}" 2>/dev/null || start "{pdf_path}" 2>/dev/null')

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport: {str(e)}")
