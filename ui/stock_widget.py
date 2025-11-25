"""Widget de gestion des stocks."""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QLabel, QMessageBox, QHeaderView, QGroupBox,
    QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from database.models import Product, StockMovement
from utils.alerts import AlertManager


class StockWidget(QWidget):
    """Widget pour gérer les stocks."""

    def __init__(self, db: DatabaseManager, alert_manager: AlertManager):
        """Initialise le widget de stock."""
        super().__init__()
        self.db = db
        self.alert_manager = alert_manager
        self._create_ui()
        self.refresh_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Section alertes
        alerts_group = QGroupBox("⚠️ Alertes")
        alerts_layout = QVBoxLayout()
        self.alerts_label = QLabel("Chargement des alertes...")
        alerts_layout.addWidget(self.alerts_label)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # Boutons d'action
        button_layout = QHBoxLayout()

        self.add_product_btn = QPushButton("➕ Nouveau Produit")
        self.add_product_btn.clicked.connect(self._add_product)

        self.add_stock_btn = QPushButton("📥 Entrée de Stock")
        self.add_stock_btn.clicked.connect(self._add_stock_entry)

        self.remove_stock_btn = QPushButton("📤 Sortie de Stock")
        self.remove_stock_btn.clicked.connect(self._remove_stock_entry)

        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)

        button_layout.addWidget(self.add_product_btn)
        button_layout.addWidget(self.add_stock_btn)
        button_layout.addWidget(self.remove_stock_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Catégorie", "Stock actuel", "Stock min",
            "Prix unitaire", "Unité", "Actions"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.products_table)

    def refresh_data(self):
        """Rafraîchit les données affichées."""
        # Rafraîchir les alertes
        self._update_alerts()

        # Rafraîchir la table des produits
        products = self.db.get_all_products()
        self.products_table.setRowCount(len(products))

        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.category or "-"))

            # Stock actuel avec couleur
            stock_item = QTableWidgetItem(f"{int(product.current_stock)}")
            if product.current_stock == 0:
                stock_item.setBackground(QColor("#e74c3c"))
                stock_item.setForeground(QColor("white"))
            elif product.current_stock <= product.min_stock:
                stock_item.setBackground(QColor("#f39c12"))
            self.products_table.setItem(row, 3, stock_item)

            self.products_table.setItem(row, 4, QTableWidgetItem(f"{int(product.min_stock)}"))
            self.products_table.setItem(row, 5, QTableWidgetItem(f"{int(product.unit_price)} CFA"))
            self.products_table.setItem(row, 6, QTableWidgetItem(product.unit))

            # Boutons d'action
            action_btn = QPushButton("✏️ Modifier")
            action_btn.clicked.connect(lambda checked, p=product: self._edit_product(p))
            self.products_table.setCellWidget(row, 7, action_btn)

    def _update_alerts(self):
        """Met à jour l'affichage des alertes."""
        alerts = self.alert_manager.get_all_alerts()

        if not alerts:
            self.alerts_label.setText("✓ Aucune alerte")
            self.alerts_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            alert_text = f"{len(alerts)} alerte(s) active(s):\n"
            for alert in alerts[:5]:  # Afficher seulement les 5 premières
                alert_text += f"• {alert['message']}\n"
            if len(alerts) > 5:
                alert_text += f"... et {len(alerts) - 5} autre(s)"

            self.alerts_label.setText(alert_text)
            self.alerts_label.setStyleSheet("color: red; font-weight: bold;")

    def _add_product(self):
        """Ouvre le dialogue pour ajouter un produit."""
        dialog = ProductDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product = dialog.get_product()
            self.db.add_product(product)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Produit ajouté avec succès!")

    def _edit_product(self, product: Product):
        """Ouvre le dialogue pour modifier un produit."""
        dialog = ProductDialog(self.db, product=product, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_product = dialog.get_product()
            self.db.update_product(updated_product)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Produit modifié avec succès!")

    def _add_stock_entry(self):
        """Ouvre le dialogue pour une entrée de stock."""
        dialog = StockMovementDialog(self.db, movement_type="IN", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            movement = dialog.get_movement()
            self.db.add_stock_movement(movement)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Entrée de stock enregistrée!")

    def _remove_stock_entry(self):
        """Ouvre le dialogue pour une sortie de stock."""
        dialog = StockMovementDialog(self.db, movement_type="OUT", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            movement = dialog.get_movement()
            self.db.add_stock_movement(movement)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Sortie de stock enregistrée!")


class ProductDialog(QDialog):
    """Dialogue pour ajouter/modifier un produit."""

    def __init__(self, db: DatabaseManager, product: Product = None, parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.db = db
        self.product = product
        self.setWindowTitle("Nouveau Produit" if product is None else "Modifier Produit")
        self.setMinimumWidth(400)
        self._create_ui()

        if product:
            self._load_product_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QFormLayout()
        self.setLayout(layout)

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.category_input = QLineEdit()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["kg", "g", "L", "mL", "pièce", "carton", "palette"])
        self.current_stock_input = QSpinBox()
        self.current_stock_input.setMaximum(999999)
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMaximum(999999)
        self.unit_price_input = QSpinBox()
        self.unit_price_input.setMaximum(999999999)
        self.unit_price_input.setSuffix(" CFA")

        # Fournisseur avec recherche
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.supplier_combo.addItem("Aucun", None)
        suppliers = self.db.get_all_suppliers()
        for supplier in suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)

        layout.addRow("Nom *:", self.name_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Catégorie:", self.category_input)
        layout.addRow("Unité:", self.unit_combo)
        layout.addRow("Stock actuel:", self.current_stock_input)
        layout.addRow("Stock minimum:", self.min_stock_input)
        layout.addRow("Prix unitaire:", self.unit_price_input)
        layout.addRow("Fournisseur:", self.supplier_combo)

        # Boutons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def _load_product_data(self):
        """Charge les données du produit dans le formulaire."""
        self.name_input.setText(self.product.name)
        self.description_input.setText(self.product.description)
        self.category_input.setText(self.product.category or "")

        index = self.unit_combo.findText(self.product.unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)

        self.current_stock_input.setValue(self.product.current_stock)
        self.min_stock_input.setValue(self.product.min_stock)
        self.unit_price_input.setValue(self.product.unit_price)

        if self.product.supplier_id:
            for i in range(self.supplier_combo.count()):
                if self.supplier_combo.itemData(i) == self.product.supplier_id:
                    self.supplier_combo.setCurrentIndex(i)
                    break

    def get_product(self) -> Product:
        """Retourne le produit avec les données du formulaire."""
        product = self.product if self.product else Product()

        product.name = self.name_input.text()
        product.description = self.description_input.toPlainText()
        product.category = self.category_input.text()
        product.unit = self.unit_combo.currentText()
        product.current_stock = self.current_stock_input.value()
        product.min_stock = self.min_stock_input.value()
        product.unit_price = self.unit_price_input.value()
        product.supplier_id = self.supplier_combo.currentData()

        return product


class StockMovementDialog(QDialog):
    """Dialogue pour ajouter un mouvement de stock."""

    def __init__(self, db: DatabaseManager, movement_type: str = "IN", parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.db = db
        self.movement_type = movement_type
        self.setWindowTitle("Entrée de Stock" if movement_type == "IN" else "Sortie de Stock")
        self.setMinimumWidth(400)
        self._create_ui()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QFormLayout()
        self.setLayout(layout)

        # Produit avec recherche
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        products = self.db.get_all_products()
        for product in products:
            self.product_combo.addItem(
                f"{product.name} (Stock: {int(product.current_stock)} {product.unit})",
                product.id
            )

        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setMinimum(1)

        self.unit_price_input = QSpinBox()
        self.unit_price_input.setMaximum(999999999)
        self.unit_price_input.setSuffix(" CFA")

        self.expiration_date = QDateEdit()
        self.expiration_date.setDate(QDate.currentDate().addDays(30))
        self.expiration_date.setCalendarPopup(True)

        self.freeze_date = QDateEdit()
        self.freeze_date.setDate(QDate.currentDate())
        self.freeze_date.setCalendarPopup(True)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        layout.addRow("Produit *:", self.product_combo)
        layout.addRow("Quantité *:", self.quantity_input)
        layout.addRow("Prix unitaire:", self.unit_price_input)

        if self.movement_type == "IN":
            layout.addRow("Date de péremption:", self.expiration_date)
            layout.addRow("Date de congélation:", self.freeze_date)

        layout.addRow("Notes:", self.notes_input)

        # Boutons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def get_movement(self) -> StockMovement:
        """Retourne le mouvement de stock avec les données du formulaire."""
        movement = StockMovement()

        movement.product_id = self.product_combo.currentData()
        movement.movement_type = self.movement_type
        movement.quantity = self.quantity_input.value()
        movement.unit_price = self.unit_price_input.value()
        movement.notes = self.notes_input.toPlainText()

        if self.movement_type == "IN":
            exp_date = self.expiration_date.date().toPyDate()
            movement.expiration_date = datetime.combine(exp_date, datetime.min.time())

            freeze_date = self.freeze_date.date().toPyDate()
            movement.freeze_date = datetime.combine(freeze_date, datetime.min.time())

        return movement
