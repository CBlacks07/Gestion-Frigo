"""Widget de gestion des ventes et factures."""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QMessageBox, QHeaderView, QLabel, QGroupBox,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem
from utils.reports import ReportGenerator
from utils.html_printer import HTMLPrinter


class SalesWidget(QWidget):
    """Widget pour gérer les ventes et factures."""

    def __init__(self, db: DatabaseManager, report_generator: ReportGenerator):
        """Initialise le widget de ventes."""
        super().__init__()
        self.db = db
        self.report_generator = report_generator
        self.html_printer = HTMLPrinter(db, self)
        self._create_ui()
        self.refresh_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("Gestion des Ventes et Factures")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Boutons d'action
        button_layout = QHBoxLayout()

        self.new_sale_btn = QPushButton("➕ Nouvelle Vente")
        self.new_sale_btn.clicked.connect(self._new_sale)

        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)

        button_layout.addWidget(self.new_sale_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table des ventes
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "ID", "Client", "Date", "Montant", "Statut", "Paiement", "Actions"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.sales_table)

    def refresh_data(self):
        """Rafraîchit les données affichées."""
        sales = self.db.get_all_sales(limit=100)
        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            # Récupérer le client
            client = self.db.get_client(sale.client_id)
            client_name = client.name if client else "Client inconnu"

            self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale.id)))
            self.sales_table.setItem(row, 1, QTableWidgetItem(client_name))

            date_str = sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else "-"
            self.sales_table.setItem(row, 2, QTableWidgetItem(date_str))

            self.sales_table.setItem(row, 3, QTableWidgetItem(f"{int(sale.total_amount)} CFA"))

            # Statut avec couleur
            status_item = QTableWidgetItem(self._get_status_label(sale.status))
            if sale.status == "COMPLETED":
                status_item.setBackground(QColor("#2ecc71"))
            elif sale.status == "CANCELLED":
                status_item.setBackground(QColor("#e74c3c"))
                status_item.setForeground(QColor("white"))
            else:
                status_item.setBackground(QColor("#f39c12"))

            self.sales_table.setItem(row, 4, status_item)
            self.sales_table.setItem(row, 5, QTableWidgetItem(self._get_payment_label(sale.payment_method)))

            # Boutons d'action
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            invoice_btn = QPushButton("🧾")
            invoice_btn.setToolTip("Imprimer ticket")
            invoice_btn.setMaximumWidth(40)
            invoice_btn.clicked.connect(lambda checked, s=sale: self._generate_invoice(s))

            view_btn = QPushButton("👁️")
            view_btn.setToolTip("Voir détails")
            view_btn.setMaximumWidth(40)
            view_btn.clicked.connect(lambda checked, s=sale: self._view_sale(s))

            action_layout.addWidget(view_btn)
            action_layout.addWidget(invoice_btn)
            action_layout.addStretch()

            self.sales_table.setCellWidget(row, 6, action_widget)

    def _get_status_label(self, status: str) -> str:
        """Retourne le label du statut."""
        labels = {
            'PENDING': 'En attente',
            'COMPLETED': 'Terminé',
            'CANCELLED': 'Annulé'
        }
        return labels.get(status, status)

    def _get_payment_label(self, payment: str) -> str:
        """Retourne le label du mode de paiement."""
        labels = {
            'CASH': 'Espèces',
            'CARD': 'Carte',
            'TRANSFER': 'Virement',
            'CHECK': 'Chèque'
        }
        return labels.get(payment, payment)

    def _new_sale(self):
        """Ouvre le dialogue pour créer une nouvelle vente."""
        dialog = SaleDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sale, items = dialog.get_sale_data()
            try:
                sale_id = self.db.add_sale(sale, items)
                self.refresh_data()
                QMessageBox.information(self, "Succès", f"Vente #{sale_id} créée avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de la vente: {str(e)}")

    def _view_sale(self, sale: Sale):
        """Affiche les détails d'une vente."""
        items = self.db.get_sale_items(sale.id)
        client = self.db.get_client(sale.client_id)

        details = f"Vente #{sale.id}\n\n"
        details += f"Client: {client.name if client else 'Inconnu'}\n"
        details += f"Date: {sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else '-'}\n"
        details += f"Statut: {self._get_status_label(sale.status)}\n"
        details += f"Paiement: {self._get_payment_label(sale.payment_method)}\n\n"
        details += "Articles:\n"

        for item in items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Produit #{item.product_id}"
            details += f"  • {product_name}: {int(item.quantity)} x {int(item.unit_price)} CFA = {int(item.subtotal)} CFA\n"

        details += f"\nTotal: {int(sale.total_amount)} CFA"

        if sale.notes:
            details += f"\n\nNotes: {sale.notes}"

        QMessageBox.information(self, f"Détails de la vente #{sale.id}", details)

    def _generate_invoice(self, sale: Sale):
        """Affiche l'aperçu d'impression du ticket de caisse."""
        try:
            self.html_printer.print_receipt(sale.id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression du ticket: {str(e)}")


class SaleDialog(QDialog):
    """Dialogue pour créer une nouvelle vente."""

    def __init__(self, db: DatabaseManager, parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Nouvelle Vente")
        self.setMinimumSize(700, 600)
        self.sale_items = []
        self._create_ui()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Informations de base
        form_layout = QFormLayout()

        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        self.client_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        clients = self.db.get_all_clients()
        for client in clients:
            self.client_combo.addItem(f"{client.name} ({client.company or 'Particulier'})", client.id)

        self.sale_date = QDateEdit()
        self.sale_date.setDate(QDate.currentDate())
        self.sale_date.setCalendarPopup(True)

        self.payment_combo = QComboBox()
        self.payment_combo.addItem("Espèces", "CASH")
        self.payment_combo.addItem("Carte bancaire", "CARD")
        self.payment_combo.addItem("Virement", "TRANSFER")
        self.payment_combo.addItem("Chèque", "CHECK")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)

        form_layout.addRow("Client *:", self.client_combo)
        form_layout.addRow("Date:", self.sale_date)
        form_layout.addRow("Mode de paiement:", self.payment_combo)
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Section articles
        items_group = QGroupBox("Articles de la vente")
        items_layout = QVBoxLayout()

        # Formulaire pour ajouter un article
        add_item_layout = QHBoxLayout()

        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        products = self.db.get_all_products()
        for product in products:
            self.product_combo.addItem(
                f"{product.name} (Stock: {int(product.current_stock)} {product.unit}) - {int(product.unit_price)} CFA",
                product.id
            )

        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(1)
        self.quantity_input.setPrefix("Qté: ")

        add_item_btn = QPushButton("➕ Ajouter")
        add_item_btn.clicked.connect(self._add_item)

        add_item_layout.addWidget(QLabel("Produit:"))
        add_item_layout.addWidget(self.product_combo, 3)
        add_item_layout.addWidget(self.quantity_input, 1)
        add_item_layout.addWidget(add_item_btn)

        items_layout.addLayout(add_item_layout)

        # Liste des articles
        self.items_list = QListWidget()
        self.items_list.setMaximumHeight(200)
        items_layout.addWidget(self.items_list)

        # Bouton supprimer article
        remove_item_btn = QPushButton("🗑️ Supprimer l'article sélectionné")
        remove_item_btn.clicked.connect(self._remove_item)
        items_layout.addWidget(remove_item_btn)

        items_group.setLayout(items_layout)
        layout.addWidget(items_group)

        # Total
        self.total_label = QLabel("Total: 0 CFA")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.total_label)

        # Boutons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer la vente")
        save_btn.clicked.connect(self._validate_and_accept)
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def _add_item(self):
        """Ajoute un article à la vente."""
        product_id = self.product_combo.currentData()
        if not product_id:
            return

        product = self.db.get_product(product_id)
        if not product:
            return

        quantity = self.quantity_input.value()

        # Vérifier le stock
        if quantity > product.current_stock:
            reply = QMessageBox.question(
                self,
                'Stock insuffisant',
                f'Stock disponible: {int(product.current_stock)} {product.unit}\n'
                f'Quantité demandée: {quantity} {product.unit}\n\n'
                'Voulez-vous continuer quand même?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Créer l'article
        item = SaleItem(
            product_id=product.id,
            quantity=quantity,
            unit_price=product.unit_price,
            subtotal=quantity * product.unit_price,
            discount=0.0
        )

        self.sale_items.append(item)

        # Ajouter à la liste
        item_text = f"{product.name} - {quantity} {product.unit} x {int(product.unit_price)} CFA = {int(item.subtotal)} CFA"
        self.items_list.addItem(item_text)

        # Mettre à jour le total
        self._update_total()

    def _remove_item(self):
        """Supprime l'article sélectionné."""
        current_row = self.items_list.currentRow()
        if current_row >= 0:
            self.items_list.takeItem(current_row)
            self.sale_items.pop(current_row)
            self._update_total()

    def _update_total(self):
        """Met à jour l'affichage du total."""
        total = sum(item.subtotal for item in self.sale_items)
        self.total_label.setText(f"Total: {int(total)} CFA")

    def _validate_and_accept(self):
        """Valide les données avant d'accepter."""
        if not self.client_combo.currentData():
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un client!")
            return

        if not self.sale_items:
            QMessageBox.warning(self, "Validation", "Veuillez ajouter au moins un article!")
            return

        self.accept()

    def get_sale_data(self):
        """Retourne les données de la vente."""
        sale = Sale()

        sale.client_id = self.client_combo.currentData()

        sale_date = self.sale_date.date().toPyDate()
        sale.sale_date = datetime.combine(sale_date, datetime.now().time())

        sale.total_amount = sum(item.subtotal for item in self.sale_items)
        sale.status = "COMPLETED"
        sale.payment_method = self.payment_combo.currentData()
        sale.notes = self.notes_input.toPlainText()

        return sale, self.sale_items
