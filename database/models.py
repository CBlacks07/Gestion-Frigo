"""Modèles de données pour l'application."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    """Modèle pour un produit."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    category: str = ""
    unit: str = "kg"  # kg, pièce, litre, etc.
    current_stock: float = 0.0
    min_stock: float = 0.0
    unit_price: float = 0.0
    supplier_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class StockMovement:
    """Modèle pour un mouvement de stock."""
    id: Optional[int] = None
    product_id: int = 0
    movement_type: str = "IN"  # IN (entrée) ou OUT (sortie)
    quantity: float = 0.0
    unit_price: float = 0.0
    expiration_date: Optional[datetime] = None
    freeze_date: Optional[datetime] = None
    notes: str = ""
    supplier_id: Optional[int] = None
    sale_id: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: str = ""


@dataclass
class Client:
    """Modèle pour un client."""
    id: Optional[int] = None
    name: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Supplier:
    """Modèle pour un fournisseur."""
    id: Optional[int] = None
    name: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Sale:
    """Modèle pour une vente."""
    id: Optional[int] = None
    client_id: int = 0
    sale_date: Optional[datetime] = None
    total_amount: float = 0.0
    status: str = "PENDING"  # PENDING, COMPLETED, CANCELLED
    payment_method: str = "CASH"  # CASH, CARD, TRANSFER, CHECK
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SaleItem:
    """Modèle pour un article de vente."""
    id: Optional[int] = None
    sale_id: int = 0
    product_id: int = 0
    quantity: float = 0.0
    unit_price: float = 0.0
    subtotal: float = 0.0
    discount: float = 0.0


@dataclass
class Invoice:
    """Modèle pour une facture."""
    id: Optional[int] = None
    sale_id: int = 0
    invoice_number: str = ""
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    total_amount: float = 0.0
    tax_amount: float = 0.0
    status: str = "UNPAID"  # UNPAID, PAID, OVERDUE, CANCELLED
    pdf_path: str = ""
    created_at: Optional[datetime] = None


@dataclass
class User:
    """Modèle pour un utilisateur."""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "USER"  # USER ou ADMIN
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


@dataclass
class AppSettings:
    """Modèle pour les paramètres de l'application."""
    id: Optional[int] = None
    company_name: str = "Gestion-Frigo"
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    logo_path: str = ""
    primary_color: str = "#2980b9"
    show_address_on_receipt: bool = True
    show_phone_on_receipt: bool = True
    show_email_on_receipt: bool = False
    receipt_footer_text: str = "Merci de votre visite !"
    updated_at: Optional[datetime] = None
