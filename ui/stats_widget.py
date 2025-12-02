"""Widget de statistiques et rapports."""
from datetime import datetime, timedelta
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QGridLayout, QMessageBox, QComboBox, QTextEdit, QScrollArea,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
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
        # Layout principal
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Créer un widget de contenu pour le scroll area
        content_widget = QWidget()
        layout = QVBoxLayout()
        content_widget.setLayout(layout)

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

        # Historique journalier des ventes
        daily_history_group = QGroupBox("📅 Historique Journalier des Ventes")
        daily_history_layout = QVBoxLayout()

        # Sélecteur de date avec navigation
        date_nav_layout = QHBoxLayout()

        # Bouton jour précédent
        self.prev_day_btn = QPushButton("◀ Jour précédent")
        self.prev_day_btn.clicked.connect(self._prev_day)
        date_nav_layout.addWidget(self.prev_day_btn)

        # Sélecteur de date
        date_nav_layout.addWidget(QLabel("Date:"))
        self.daily_date_picker = QDateEdit()
        self.daily_date_picker.setCalendarPopup(True)
        self.daily_date_picker.setDate(QDate.currentDate())
        self.daily_date_picker.setDisplayFormat("dd/MM/yyyy")
        self.daily_date_picker.dateChanged.connect(self._update_daily_sales)
        date_nav_layout.addWidget(self.daily_date_picker)

        # Bouton jour suivant
        self.next_day_btn = QPushButton("Jour suivant ▶")
        self.next_day_btn.clicked.connect(self._next_day)
        date_nav_layout.addWidget(self.next_day_btn)

        # Bouton aujourd'hui
        self.today_btn = QPushButton("📅 Aujourd'hui")
        self.today_btn.clicked.connect(self._go_to_today)
        date_nav_layout.addWidget(self.today_btn)

        date_nav_layout.addStretch()

        daily_history_layout.addLayout(date_nav_layout)

        # Résumé du jour
        self.daily_summary_label = QLabel()
        self.daily_summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2980b9; padding: 10px;")
        daily_history_layout.addWidget(self.daily_summary_label)

        # Tableau des ventes du jour
        self.daily_sales_table = QTableWidget()
        self.daily_sales_table.setColumnCount(5)
        self.daily_sales_table.setHorizontalHeaderLabels([
            "Heure", "Client", "Montant Total", "Statut", "N° Facture"
        ])
        self.daily_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.daily_sales_table.setAlternatingRowColors(True)
        self.daily_sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.daily_sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.daily_sales_table.setMinimumHeight(250)
        daily_history_layout.addWidget(self.daily_sales_table)

        daily_history_group.setLayout(daily_history_layout)
        layout.addWidget(daily_history_group)

        # Alertes critiques
        alerts_group = QGroupBox("⚠️ Alertes Critiques")
        alerts_layout = QVBoxLayout()
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMinimumHeight(150)
        alerts_layout.addWidget(self.alerts_text)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # Produits les plus vendus
        top_products_group = QGroupBox("🏆 Top 10 Produits les Plus Vendus")
        top_products_layout = QVBoxLayout()
        self.top_products_text = QTextEdit()
        self.top_products_text.setReadOnly(True)
        self.top_products_text.setMinimumHeight(150)
        top_products_layout.addWidget(self.top_products_text)
        top_products_group.setLayout(top_products_layout)
        layout.addWidget(top_products_group)

        # Meilleurs clients
        top_clients_group = QGroupBox("👑 Top 10 Meilleurs Clients")
        top_clients_layout = QVBoxLayout()
        self.top_clients_text = QTextEdit()
        self.top_clients_text.setReadOnly(True)
        self.top_clients_text.setMinimumHeight(150)
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
        self.sales_period_text.setMinimumHeight(120)
        sales_period_layout.addWidget(self.sales_period_text)

        sales_period_group.setLayout(sales_period_layout)
        layout.addWidget(sales_period_group)

        # Ajouter le widget de contenu dans un scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        main_layout.addWidget(scroll_area)

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
        self.total_sales_label.setText(f"{int(total_sales)} CFA")

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

        # Afficher l'historique journalier
        self._update_daily_sales()

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
                html += f"<li><b>{product_name}</b>: {int(quantity)} unités vendues</li>"
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
                html += f"<li><b>{client_name}</b>: {int(total_spent)} CFA</li>"
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
            html = f"<p><b>Total sur la période: {int(total)} CFA</b></p><ul>"

            for date_str, amount in sales_by_period:
                html += f"<li>{date_str}: {int(amount)} CFA</li>"

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

    def _prev_day(self):
        """Affiche le jour précédent."""
        current_date = self.daily_date_picker.date()
        self.daily_date_picker.setDate(current_date.addDays(-1))

    def _next_day(self):
        """Affiche le jour suivant."""
        current_date = self.daily_date_picker.date()
        self.daily_date_picker.setDate(current_date.addDays(1))

    def _go_to_today(self):
        """Retourne à la date du jour."""
        self.daily_date_picker.setDate(QDate.currentDate())

    def _update_daily_sales(self):
        """Met à jour l'affichage des ventes du jour sélectionné."""
        selected_date = self.daily_date_picker.date().toPyDate()

        # Récupérer toutes les ventes
        all_sales = self.db.get_all_sales(limit=10000)

        # Filtrer les ventes du jour sélectionné
        daily_sales = []
        for sale in all_sales:
            sale_date = sale.sale_date.date() if isinstance(sale.sale_date, datetime) else sale.sale_date
            if sale_date == selected_date:
                daily_sales.append(sale)

        # Vider le tableau
        self.daily_sales_table.setRowCount(0)

        # Calculer le résumé
        total_amount = sum(sale.total_amount for sale in daily_sales)
        paid_count = sum(1 for sale in daily_sales if sale.status == "PAID")
        pending_count = sum(1 for sale in daily_sales if sale.status == "PENDING")

        # Afficher le résumé
        date_str = selected_date.strftime("%d/%m/%Y")
        summary_text = f"📊 {date_str}: {len(daily_sales)} vente(s) - Total: {int(total_amount)} CFA"
        if paid_count > 0 or pending_count > 0:
            summary_text += f" (✅ {paid_count} payée(s), ⏳ {pending_count} en attente)"
        self.daily_summary_label.setText(summary_text)

        if not daily_sales:
            # Afficher un message si aucune vente
            self.daily_sales_table.setRowCount(1)
            no_sales_item = QTableWidgetItem("Aucune vente enregistrée pour cette date")
            no_sales_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.daily_sales_table.setSpan(0, 0, 1, 5)
            self.daily_sales_table.setItem(0, 0, no_sales_item)
            return

        # Trier les ventes par heure (plus récentes en premier)
        daily_sales.sort(key=lambda s: s.sale_date, reverse=True)

        # Remplir le tableau
        for sale in daily_sales:
            row = self.daily_sales_table.rowCount()
            self.daily_sales_table.insertRow(row)

            # Heure
            time_str = sale.sale_date.strftime("%H:%M") if isinstance(sale.sale_date, datetime) else "N/A"
            self.daily_sales_table.setItem(row, 0, QTableWidgetItem(time_str))

            # Client
            if sale.client_id:
                client = self.db.get_client(sale.client_id)
                client_name = client.name if client else "Client inconnu"
            else:
                client_name = "Client anonyme"
            self.daily_sales_table.setItem(row, 1, QTableWidgetItem(client_name))

            # Montant
            amount_item = QTableWidgetItem(f"{int(sale.total_amount)} CFA")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.daily_sales_table.setItem(row, 2, amount_item)

            # Statut
            status_text = "✅ Payée" if sale.status == "PAID" else "⏳ En attente"
            status_item = QTableWidgetItem(status_text)
            if sale.status == "PAID":
                status_item.setForeground(QFont().resolve(QFont()).defaultFamily())
            self.daily_sales_table.setItem(row, 3, status_item)

            # N° Facture
            invoice_number = f"#{sale.id:04d}"
            self.daily_sales_table.setItem(row, 4, QTableWidgetItem(invoice_number))
