"""Module d'impression HTML utilisant la méthode du navigateur."""
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt6.QtGui import QTextDocument
from PyQt6.QtCore import Qt, QSizeF

from database.models import Sale, Client
from database.db_manager import DatabaseManager


class HTMLPrinter:
    """Générateur d'impressions HTML."""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        """Initialise le générateur d'impressions."""
        self.db = db_manager
        self.parent = parent

    def _get_payment_method_label(self, method: str) -> str:
        """Retourne le label du mode de paiement."""
        methods = {
            'CASH': 'Espèces',
            'CARD': 'Carte bancaire',
            'TRANSFER': 'Virement',
            'CHECK': 'Chèque'
        }
        return methods.get(method, method)

    def generate_invoice_html(self, sale_id: int, company_info: Optional[dict] = None) -> str:
        """Génère le HTML d'une facture."""
        # Récupérer les données
        sale = self.db.get_sale(sale_id)
        if not sale:
            raise ValueError(f"Vente {sale_id} introuvable")

        client = self.db.get_client(sale.client_id)
        items = self.db.get_sale_items(sale_id)

        # Informations par défaut de l'entreprise
        if not company_info:
            company_info = {
                'name': 'Gestion-Frigo',
                'address': 'Adresse de votre entreprise',
                'city': 'Ville',
                'postal_code': '00000',
                'phone': 'Téléphone',
                'email': 'email@entreprise.com',
                'siret': 'N° SIRET'
            }

        invoice_number = f"INV-{sale_id:06d}"

        # Générer le HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Facture {invoice_number}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    font-size: 28px;
                    margin-bottom: 10px;
                }}
                .info-section {{
                    display: table;
                    width: 100%;
                    margin-bottom: 30px;
                }}
                .info-column {{
                    display: table-cell;
                    width: 50%;
                    vertical-align: top;
                }}
                .info-column h3 {{
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .invoice-details {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-left: 4px solid #3498db;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .total-row {{
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .total-row td {{
                    padding: 15px;
                    border: none;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                }}
                .notes {{
                    background-color: #fff3cd;
                    padding: 15px;
                    margin-top: 20px;
                    border-left: 4px solid #ffc107;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FACTURE</h1>
            </div>

            <div class="info-section">
                <div class="info-column">
                    <h3>{company_info['name']}</h3>
                    <p>{company_info['address']}<br>
                    {company_info['postal_code']} {company_info['city']}<br>
                    Tél: {company_info['phone']}<br>
                    Email: {company_info['email']}</p>
                </div>
                <div class="info-column">
                    <h3>Client</h3>
                    <p><strong>{client.name if client else "Client inconnu"}</strong><br>
                    {client.company if client and client.company else ""}<br>
                    {client.address if client else ""}<br>
                    {f"{client.postal_code} {client.city}" if client else ""}</p>
                </div>
            </div>

            <div class="invoice-details">
                <strong>N° Facture:</strong> {invoice_number}<br>
                <strong>Date:</strong> {sale.sale_date.strftime('%d/%m/%Y') if sale.sale_date else datetime.now().strftime('%d/%m/%Y')}<br>
                <strong>Mode de paiement:</strong> {self._get_payment_method_label(sale.payment_method)}
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th style="text-align: right;">Quantité</th>
                        <th style="text-align: right;">Prix unitaire</th>
                        <th style="text-align: right;">Remise</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
        """

        for item in items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Produit #{item.product_id}"
            unit = product.unit if product else ''

            html += f"""
                    <tr>
                        <td>{product_name}</td>
                        <td style="text-align: right;">{int(item.quantity)} {unit}</td>
                        <td style="text-align: right;">{int(item.unit_price)} CFA</td>
                        <td style="text-align: right;">{"" if item.discount == 0 else f"{int(item.discount)} CFA"}</td>
                        <td style="text-align: right;">{int(item.subtotal)} CFA</td>
                    </tr>
            """

        html += f"""
                    <tr class="total-row">
                        <td colspan="4" style="text-align: right;">TOTAL</td>
                        <td style="text-align: right;">{int(sale.total_amount)} CFA</td>
                    </tr>
                </tbody>
            </table>
        """

        if sale.notes:
            html += f"""
            <div class="notes">
                <strong>Notes:</strong> {sale.notes}
            </div>
            """

        html += f"""
            <div class="footer">
                Merci pour votre confiance<br>
                {company_info['name']} - SIRET: {company_info['siret']}
            </div>
        </body>
        </html>
        """

        return html

    def generate_stock_report_html(self) -> str:
        """Génère le HTML d'un rapport de stock."""
        products = self.db.get_all_products()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Rapport de Stock</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    font-size: 28px;
                    margin-bottom: 5px;
                }}
                .header p {{
                    color: #7f8c8d;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 30px;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .status-ok {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .status-low {{
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .status-out {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .statistics {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin-top: 30px;
                }}
                .statistics h2 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                }}
                .stat-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RAPPORT DE STOCK</h1>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th>Catégorie</th>
                        <th style="text-align: center;">Stock actuel</th>
                        <th style="text-align: center;">Stock min</th>
                        <th style="text-align: center;">Statut</th>
                    </tr>
                </thead>
                <tbody>
        """

        for product in products:
            status = "OK"
            status_class = "status-ok"
            if product.current_stock == 0:
                status = "RUPTURE"
                status_class = "status-out"
            elif product.current_stock <= product.min_stock:
                status = "BAS"
                status_class = "status-low"

            html += f"""
                    <tr>
                        <td>{product.name}</td>
                        <td>{product.category or "-"}</td>
                        <td style="text-align: center;">{int(product.current_stock)} {product.unit}</td>
                        <td style="text-align: center;">{int(product.min_stock)} {product.unit}</td>
                        <td style="text-align: center;"><span class="{status_class}">{status}</span></td>
                    </tr>
            """

        # Statistiques
        low_stock = len(self.db.get_low_stock_products())
        total_products = len(products)
        availability_rate = ((total_products - low_stock) / total_products * 100) if total_products > 0 else 0

        html += f"""
                </tbody>
            </table>

            <div class="statistics">
                <h2>Statistiques</h2>
                <div class="stat-item">
                    <strong>Total de produits:</strong> {total_products}
                </div>
                <div class="stat-item">
                    <strong>Produits en stock bas:</strong> {low_stock}
                </div>
                <div class="stat-item">
                    <strong>Taux de disponibilité:</strong> {availability_rate:.1f}%
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def print_invoice(self, sale_id: int, company_info: Optional[dict] = None):
        """Affiche l'aperçu d'impression pour une facture."""
        html = self.generate_invoice_html(sale_id, company_info)
        self._show_print_preview(html, f"Facture INV-{sale_id:06d}")

    def print_stock_report(self):
        """Affiche l'aperçu d'impression pour un rapport de stock."""
        html = self.generate_stock_report_html()
        self._show_print_preview(html, "Rapport de Stock")

    def _show_print_preview(self, html: str, title: str):
        """Affiche l'aperçu d'impression avec le HTML fourni."""
        # Créer un document texte avec le HTML
        document = QTextDocument()
        document.setHtml(html)

        # Créer un QPrinter
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPrinter.PageSize.A4)
        printer.setPageMargins(15, 15, 15, 15, QPrinter.Unit.Millimeter)

        # Créer le dialogue d'aperçu d'impression
        preview = QPrintPreviewDialog(printer, self.parent)
        preview.setWindowTitle(f"Aperçu d'impression - {title}")
        preview.paintRequested.connect(lambda p: document.print(p))

        # Afficher le dialogue
        preview.exec()
