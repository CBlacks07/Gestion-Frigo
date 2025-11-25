"""Générateur de rapports et factures PDF."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from database.models import Sale, SaleItem, Client, Invoice
from database.db_manager import DatabaseManager


class ReportGenerator:
    """Générateur de rapports et factures."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialise le générateur de rapports."""
        self.db = db_manager
        self.output_dir = Path("exports")
        self.output_dir.mkdir(exist_ok=True)

    def generate_receipt_pdf(self, sale_id: int, company_info: Optional[dict] = None) -> str:
        """Génère un ticket de caisse PDF (format 80mm)."""
        # Récupérer les données
        sale = self.db.get_sale(sale_id)
        if not sale:
            raise ValueError(f"Vente {sale_id} introuvable")

        client = self.db.get_client(sale.client_id)
        items = self.db.get_sale_items(sale_id)

        # Récupérer les paramètres de l'application
        settings = self.db.get_app_settings()

        # Utiliser les paramètres de l'application
        if not company_info:
            company_info = {
                'name': settings.company_name,
                'address': settings.company_address if settings.show_address_on_receipt else '',
                'phone': settings.company_phone if settings.show_phone_on_receipt else '',
                'email': settings.company_email if settings.show_email_on_receipt else '',
            }

        # Créer le nom du fichier
        receipt_number = f"{sale_id:06d}"
        filename = self.output_dir / f"ticket_{receipt_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Créer le document PDF avec taille ticket (80mm de large)
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=(80*mm, 297*mm),  # 80mm de large, hauteur A4
            rightMargin=2*mm,
            leftMargin=2*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )

        # Styles
        styles = getSampleStyleSheet()

        # Style pour l'en-tête
        header_style = ParagraphStyle(
            'ReceiptHeader',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=3
        )

        # Style normal centré
        center_style = ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=2
        )

        # Style petit
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            spaceAfter=2
        )

        # Éléments du document
        elements = []

        # En-tête
        elements.append(Paragraph(company_info['name'], header_style))

        # Afficher adresse seulement si remplie
        if company_info.get('address') and company_info['address'].strip():
            elements.append(Paragraph(company_info['address'], small_style))

        # Afficher téléphone seulement si rempli
        if company_info.get('phone') and company_info['phone'].strip():
            elements.append(Paragraph(f"Tél: {company_info['phone']}", small_style))

        # Afficher email seulement si rempli
        if company_info.get('email') and company_info['email'].strip():
            elements.append(Paragraph(f"Email: {company_info['email']}", small_style))

        elements.append(Spacer(1, 3*mm))

        # Ligne de séparation
        sep_line = Table([['='*40]], colWidths=[76*mm])
        sep_line.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sep_line)
        elements.append(Spacer(1, 2*mm))

        # Informations du ticket
        elements.append(Paragraph(f"Ticket N°: {receipt_number}", center_style))
        elements.append(Paragraph(
            sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else datetime.now().strftime('%d/%m/%Y %H:%M'),
            center_style
        ))

        # Client seulement si existe
        if client and client.name:
            elements.append(Paragraph(f"Client: {client.name}", center_style))

        # Mode de paiement
        payment_labels = {
            'CASH': 'Espèces',
            'CARD': 'Carte',
            'TRANSFER': 'Virement',
            'CHECK': 'Chèque'
        }
        elements.append(Paragraph(f"Paiement: {payment_labels.get(sale.payment_method, sale.payment_method)}", center_style))

        elements.append(Spacer(1, 2*mm))

        # Ligne de séparation
        elements.append(sep_line)
        elements.append(Spacer(1, 2*mm))

        # Articles
        for item in items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Produit #{item.product_id}"

            # Limiter le nom du produit
            if len(product_name) > 30:
                product_name = product_name[:27] + "..."

            # Nom du produit
            elements.append(Paragraph(product_name, styles['Normal']))

            # Quantité x Prix = Total
            item_detail = Table(
                [[f"{int(item.quantity)} x {int(item.unit_price)} CFA", f"{int(item.subtotal)} CFA"]],
                colWidths=[50*mm, 26*mm]
            )
            item_detail.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGNMENT', (0, 0), (0, 0), 'LEFT'),
                ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (0, 0), 3*mm),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ]))
            elements.append(item_detail)
            elements.append(Spacer(1, 2*mm))

        # Ligne de séparation double
        double_sep = Table([['='*40]], colWidths=[76*mm])
        double_sep.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(double_sep)
        elements.append(Spacer(1, 3*mm))

        # Total
        total_table = Table(
            [['TOTAL A PAYER', f"{int(sale.total_amount)} CFA"]],
            colWidths=[40*mm, 36*mm]
        )
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGNMENT', (0, 0), (0, 0), 'LEFT'),
            ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 3*mm))
        elements.append(double_sep)

        # Notes si présentes
        if sale.notes and sale.notes.strip():
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph(f"Note: {sale.notes}", small_style))

        # Footer
        elements.append(Spacer(1, 5*mm))
        footer_sep = Table([['-'*40]], colWidths=[76*mm])
        footer_sep.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(footer_sep)
        elements.append(Spacer(1, 2*mm))

        # Utiliser le texte de pied de page personnalisé
        footer_text = settings.receipt_footer_text or "Merci de votre visite !"
        elements.append(Paragraph(footer_text, center_style))
        elements.append(Paragraph("A bientôt", center_style))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("Ce ticket fait office de facture", small_style))

        # Générer le PDF
        doc.build(elements)

        return str(filename)

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
