"""Widget de gestion des fournisseurs."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMessageBox, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from database.models import Supplier


class SuppliersWidget(QWidget):
    """Widget pour gérer les fournisseurs."""

    def __init__(self, db: DatabaseManager):
        """Initialise le widget de fournisseurs."""
        super().__init__()
        self.db = db
        self._create_ui()
        self.refresh_data()

    def _create_ui(self):
        """Crée l'interface utilisateur."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        header_label = QLabel("Gestion des Fournisseurs")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Boutons d'action
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Nouveau Fournisseur")
        self.add_btn.clicked.connect(self._add_supplier)

        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table des fournisseurs
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(7)
        self.suppliers_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Entreprise", "Email", "Téléphone", "Ville", "Actions"
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.suppliers_table)

    def refresh_data(self):
        """Rafraîchit les données affichées."""
        suppliers = self.db.get_all_suppliers()
        self.suppliers_table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(str(supplier.id)))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier.name))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier.company or "-"))
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier.email or "-"))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(supplier.phone or "-"))
            self.suppliers_table.setItem(row, 5, QTableWidgetItem(supplier.city or "-"))

            # Boutons d'action
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda checked, s=supplier: self._edit_supplier(s))

            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(40)
            delete_btn.clicked.connect(lambda checked, s=supplier: self._delete_supplier(s))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()

            self.suppliers_table.setCellWidget(row, 6, action_widget)

    def _add_supplier(self):
        """Ouvre le dialogue pour ajouter un fournisseur."""
        dialog = SupplierDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            supplier = dialog.get_supplier()
            self.db.add_supplier(supplier)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Fournisseur ajouté avec succès!")

    def _edit_supplier(self, supplier: Supplier):
        """Ouvre le dialogue pour modifier un fournisseur."""
        dialog = SupplierDialog(supplier=supplier, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_supplier = dialog.get_supplier()
            self.db.update_supplier(updated_supplier)
            self.refresh_data()
            QMessageBox.information(self, "Succès", "Fournisseur modifié avec succès!")

    def _delete_supplier(self, supplier: Supplier):
        """Supprime un fournisseur après confirmation."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Êtes-vous sûr de vouloir supprimer le fournisseur "{supplier.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_supplier(supplier.id)
                self.refresh_data()
                QMessageBox.information(self, "Succès", "Fournisseur supprimé avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le fournisseur: {str(e)}")


class SupplierDialog(QDialog):
    """Dialogue pour ajouter/modifier un fournisseur."""

    def __init__(self, supplier: Supplier = None, parent=None):
        """Initialise le dialogue."""
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Nouveau Fournisseur" if supplier is None else "Modifier Fournisseur")
        self.setMinimumWidth(500)
        self._create_ui()

        if supplier:
            self._load_supplier_data()

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

    def _load_supplier_data(self):
        """Charge les données du fournisseur dans le formulaire."""
        self.name_input.setText(self.supplier.name)
        self.company_input.setText(self.supplier.company or "")
        self.email_input.setText(self.supplier.email or "")
        self.phone_input.setText(self.supplier.phone or "")
        self.address_input.setText(self.supplier.address or "")
        self.city_input.setText(self.supplier.city or "")
        self.postal_code_input.setText(self.supplier.postal_code or "")
        self.notes_input.setText(self.supplier.notes or "")

    def _validate_and_accept(self):
        """Valide les données avant d'accepter."""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire!")
            return
        self.accept()

    def get_supplier(self) -> Supplier:
        """Retourne le fournisseur avec les données du formulaire."""
        supplier = self.supplier if self.supplier else Supplier()

        supplier.name = self.name_input.text()
        supplier.company = self.company_input.text()
        supplier.email = self.email_input.text()
        supplier.phone = self.phone_input.text()
        supplier.address = self.address_input.text()
        supplier.city = self.city_input.text()
        supplier.postal_code = self.postal_code_input.text()
        supplier.notes = self.notes_input.toPlainText()

        return supplier
