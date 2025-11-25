"""Module d'impression de tickets de caisse."""
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import Qt, QSizeF, QMarginsF

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

    def generate_receipt_html(self, sale_id: int, company_info: Optional[dict] = None) -> str:
        """Génère le HTML d'un ticket de caisse."""
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
                'phone': 'Téléphone',
            }

        receipt_number = f"{sale_id:06d}"

        # Générer le HTML style ticket de caisse
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Ticket {receipt_number}</title>
            <style>
                @page {{
                    size: 80mm auto;
                    margin: 0;
                }}
                body {{
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 11px;
                    margin: 0;
                    padding: 5mm;
                    width: 70mm;
                    color: #000;
                }}
                .center {{
                    text-align: center;
                }}
                .bold {{
                    font-weight: bold;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 10px;
                    border-bottom: 1px dashed #000;
                    padding-bottom: 5px;
                }}
                .company-name {{
                    font-size: 14px;
                    font-weight: bold;
                    margin-bottom: 3px;
                }}
                .separator {{
                    border-top: 1px dashed #000;
                    margin: 5px 0;
                }}
                .double-separator {{
                    border-top: 2px solid #000;
                    margin: 5px 0;
                }}
                .item-line {{
                    display: flex;
                    justify-content: space-between;
                    margin: 3px 0;
                }}
                .item-name {{
                    flex: 1;
                }}
                .item-qty {{
                    width: 30px;
                    text-align: right;
                }}
                .item-price {{
                    width: 60px;
                    text-align: right;
                }}
                .total-line {{
                    font-size: 13px;
                    font-weight: bold;
                    margin-top: 8px;
                    display: flex;
                    justify-content: space-between;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 10px;
                    font-size: 10px;
                    border-top: 1px dashed #000;
                    padding-top: 5px;
                }}
                .small {{
                    font-size: 9px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="company-name">{company_info['name']}</div>
                <div class="small">{company_info['address']}</div>
                <div class="small">Tél: {company_info['phone']}</div>
            </div>

            <div class="center small">
                Ticket N°: {receipt_number}<br>
                {sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
                Client: {client.name if client else "Client"}<br>
                Paiement: {self._get_payment_method_label(sale.payment_method)}
            </div>

            <div class="separator"></div>
        """

        # Articles
        for item in items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Produit #{item.product_id}"

            # Limiter le nom à 25 caractères
            if len(product_name) > 25:
                product_name = product_name[:22] + "..."

            html += f"""
            <div style="margin: 3px 0;">
                <div>{product_name}</div>
                <div style="display: flex; justify-content: space-between; margin-left: 10px;">
                    <span>{int(item.quantity)} x {int(item.unit_price)} CFA</span>
                    <span class="bold">{int(item.subtotal)} CFA</span>
                </div>
            </div>
            """

        # Total
        html += f"""
            <div class="double-separator"></div>
            <div class="total-line">
                <span>TOTAL A PAYER</span>
                <span>{int(sale.total_amount)} CFA</span>
            </div>
            <div class="double-separator"></div>
        """

        # Notes si présentes
        if sale.notes:
            html += f"""
            <div class="center small" style="margin-top: 5px;">
                Note: {sale.notes}
            </div>
            """

        # Footer
        html += f"""
            <div class="footer">
                Merci de votre visite !<br>
                A bientôt<br>
                <div class="small" style="margin-top: 5px;">
                    Ce ticket fait office de facture
                </div>
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

    def print_receipt(self, sale_id: int, company_info: Optional[dict] = None):
        """Affiche l'aperçu d'impression pour un ticket de caisse."""
        html = self.generate_receipt_html(sale_id, company_info)
        self._show_receipt_preview(html, f"Ticket N°{sale_id:06d}")

    def print_stock_report(self):
        """Affiche l'aperçu d'impression pour un rapport de stock."""
        html = self.generate_stock_report_html()
        self._show_print_preview(html, "Rapport de Stock")

    def _show_receipt_preview(self, html: str, title: str):
        """Affiche l'aperçu d'impression pour un ticket de caisse."""
        # Créer un document texte avec le HTML
        document = QTextDocument()
        document.setHtml(html)

        # Créer un QPrinter configuré pour ticket de caisse (80mm)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        # Configuration pour ticket thermique 80mm
        page_size = QPageSize(QSizeF(80, 297), QPageSize.Unit.Millimeter)  # 80mm de large, hauteur variable
        printer.setPageSize(page_size)
        printer.setPageOrientation(QPrinter.PageOrientation.Portrait)

        # Marges minimales
        printer.setPageMargins(QMarginsF(2, 2, 2, 2), QPageLayout.Unit.Millimeter)

        # Créer le dialogue d'aperçu d'impression
        preview = QPrintPreviewDialog(printer, self.parent)
        preview.setWindowTitle(f"Aperçu d'impression - {title}")
        preview.paintRequested.connect(lambda p: document.print(p))

        # Afficher le dialogue
        preview.exec()

    def _show_print_preview(self, html: str, title: str):
        """Affiche l'aperçu d'impression avec le HTML fourni (format A4)."""
        # Créer un document texte avec le HTML
        document = QTextDocument()
        document.setHtml(html)

        # Créer un QPrinter
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)

        # Créer le dialogue d'aperçu d'impression
        preview = QPrintPreviewDialog(printer, self.parent)
        preview.setWindowTitle(f"Aperçu d'impression - {title}")
        preview.paintRequested.connect(lambda p: document.print(p))

        # Afficher le dialogue
        preview.exec()
