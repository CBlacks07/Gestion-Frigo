"""Générateur de rapports et factures PDF."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from database.models import Sale, SaleItem, Client, Invoice
from database.db_manager import DatabaseManager


class ReportGenerator:
    """Générateur de rapports et factures."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialise le générateur de rapports."""
        self.db = db_manager
        self.output_dir = Path("exports")
        self.output_dir.mkdir(exist_ok=True)

    def generate_invoice_pdf(self, sale_id: int, company_info: Optional[dict] = None) -> str:
        """Génère une facture PDF pour une vente."""
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

        # Créer le nom du fichier
        invoice_number = f"INV-{sale_id:06d}"
        filename = self.output_dir / f"facture_{invoice_number}_{datetime.now().strftime('%Y%m%d')}.pdf"

        # Créer le document PDF
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=30
        )

        # Éléments du document
        elements = []

        # Titre
        elements.append(Paragraph("FACTURE", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Informations entreprise et client
        info_data = [
            [Paragraph(f"<b>{company_info['name']}</b>", styles['Normal']),
             Paragraph(f"<b>Client:</b>", styles['Normal'])],
            [Paragraph(company_info['address'], styles['Normal']),
             Paragraph(client.name if client else "Client inconnu", styles['Normal'])],
            [Paragraph(f"{company_info['postal_code']} {company_info['city']}", styles['Normal']),
             Paragraph(client.company if client and client.company else "", styles['Normal'])],
            [Paragraph(f"Tél: {company_info['phone']}", styles['Normal']),
             Paragraph(client.address if client else "", styles['Normal'])],
            [Paragraph(f"Email: {company_info['email']}", styles['Normal']),
             Paragraph(f"{client.postal_code} {client.city}" if client else "", styles['Normal'])],
        ]

        info_table = Table(info_data, colWidths=[8*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))

        # Informations facture
        invoice_info = [
            [Paragraph(f"<b>N° Facture:</b>", styles['Normal']),
             Paragraph(invoice_number, styles['Normal'])],
            [Paragraph(f"<b>Date:</b>", styles['Normal']),
             Paragraph(sale.sale_date.strftime('%d/%m/%Y') if sale.sale_date else datetime.now().strftime('%d/%m/%Y'), styles['Normal'])],
            [Paragraph(f"<b>Mode de paiement:</b>", styles['Normal']),
             Paragraph(self._get_payment_method_label(sale.payment_method), styles['Normal'])],
        ]

        invoice_table = Table(invoice_info, colWidths=[4*cm, 6*cm])
        invoice_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 1*cm))

        # Articles
        items_data = [['Produit', 'Quantité', 'Prix unitaire', 'Remise', 'Total']]

        for item in items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Produit #{item.product_id}"

            items_data.append([
                product_name,
                f"{int(item.quantity)} {product.unit if product else ''}",
                f"{int(item.unit_price)} CFA",
                f"{int(item.discount)} CFA" if item.discount > 0 else "-",
                f"{int(item.subtotal)} CFA"
            ])

        items_table = Table(items_data, colWidths=[8*cm, 3*cm, 3*cm, 2*cm, 3*cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.5*cm))

        # Total
        total_data = [
            ['', '', '', 'TOTAL:', f"{int(sale.total_amount)} CFA"],
        ]

        total_table = Table(total_data, colWidths=[8*cm, 3*cm, 3*cm, 2*cm, 3*cm])
        total_table.setStyle(TableStyle([
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (3, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (3, 0), (-1, 0), 16),
            ('LINEABOVE', (3, 0), (-1, 0), 2, colors.black),
            ('BACKGROUND', (3, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (3, 0), (-1, 0), colors.whitesmoke),
        ]))
        elements.append(total_table)

        # Notes
        if sale.notes:
            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph(f"<b>Notes:</b> {sale.notes}", styles['Normal']))

        # Pied de page
        elements.append(Spacer(1, 2*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Merci pour votre confiance | {company_info['name']} - SIRET: {company_info['siret']}",
            footer_style
        ))

        # Générer le PDF
        doc.build(elements)

        return str(filename)

    def _get_payment_method_label(self, method: str) -> str:
        """Retourne le label du mode de paiement."""
        methods = {
            'CASH': 'Espèces',
            'CARD': 'Carte bancaire',
            'TRANSFER': 'Virement',
            'CHECK': 'Chèque'
        }
        return methods.get(method, method)

    def generate_stock_report(self) -> str:
        """Génère un rapport de stock en PDF."""
        filename = self.output_dir / f"rapport_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=30
        )

        elements = []

        # Titre
        elements.append(Paragraph("RAPPORT DE STOCK", title_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 1*cm))

        # Récupérer tous les produits
        products = self.db.get_all_products()

        # Créer le tableau
        data = [['Produit', 'Catégorie', 'Stock actuel', 'Stock min', 'Statut']]

        for product in products:
            status = "OK"
            if product.current_stock == 0:
                status = "RUPTURE"
            elif product.current_stock <= product.min_stock:
                status = "BAS"

            data.append([
                product.name,
                product.category or "-",
                f"{int(product.current_stock)} {product.unit}",
                f"{int(product.min_stock)} {product.unit}",
                status
            ])

        table = Table(data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

        # Statistiques
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("<b>Statistiques:</b>", styles['Heading2']))

        low_stock = len(self.db.get_low_stock_products())
        total_products = len(products)

        stats_data = [
            ['Total de produits:', str(total_products)],
            ['Produits en stock bas:', str(low_stock)],
            ['Taux de disponibilité:', f"{((total_products - low_stock) / total_products * 100) if total_products > 0 else 0:.1f}%"]
        ]

        stats_table = Table(stats_data, colWidths=[8*cm, 8*cm])
        stats_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(stats_table)

        doc.build(elements)

        return str(filename)
