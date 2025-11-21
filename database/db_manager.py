"""Gestionnaire de base de données SQLite."""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path

from .models import Product, StockMovement, Client, Supplier, Sale, SaleItem, Invoice


class DatabaseManager:
    """Gestionnaire principal de la base de données."""

    def __init__(self, db_path: str = "gestion_frigo.db"):
        """Initialise le gestionnaire de base de données."""
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._create_tables()

    def connect(self) -> sqlite3.Connection:
        """Établit une connexion à la base de données."""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def _create_tables(self):
        """Crée les tables de la base de données."""
        conn = self.connect()
        cursor = conn.cursor()

        # Table des produits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                unit TEXT DEFAULT 'kg',
                current_stock REAL DEFAULT 0.0,
                min_stock REAL DEFAULT 0.0,
                unit_price REAL DEFAULT 0.0,
                supplier_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        """)

        # Table des mouvements de stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('IN', 'OUT')),
                quantity REAL NOT NULL,
                unit_price REAL DEFAULT 0.0,
                expiration_date TIMESTAMP,
                freeze_date TIMESTAMP,
                notes TEXT,
                supplier_id INTEGER,
                sale_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)

        # Table des clients
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des fournisseurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des ventes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'COMPLETED', 'CANCELLED')),
                payment_method TEXT DEFAULT 'CASH' CHECK(payment_method IN ('CASH', 'CARD', 'TRANSFER', 'CHECK')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Table des articles de vente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL DEFAULT 0.0,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Table des factures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                total_amount REAL NOT NULL,
                tax_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'UNPAID' CHECK(status IN ('UNPAID', 'PAID', 'OVERDUE', 'CANCELLED')),
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)

        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_client ON sales(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_sale ON invoices(sale_id)")

        conn.commit()

    # --- Gestion des produits ---

    def add_product(self, product: Product) -> int:
        """Ajoute un nouveau produit."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, description, category, unit, current_stock,
                                min_stock, unit_price, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product.name, product.description, product.category, product.unit,
              product.current_stock, product.min_stock, product.unit_price, product.supplier_id))
        conn.commit()
        return cursor.lastrowid

    def update_product(self, product: Product):
        """Met à jour un produit existant."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products
            SET name=?, description=?, category=?, unit=?, current_stock=?,
                min_stock=?, unit_price=?, supplier_id=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (product.name, product.description, product.category, product.unit,
              product.current_stock, product.min_stock, product.unit_price,
              product.supplier_id, product.id))
        conn.commit()

    def delete_product(self, product_id: int):
        """Supprime un produit."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()

    def get_product(self, product_id: int) -> Optional[Product]:
        """Récupère un produit par son ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
        row = cursor.fetchone()
        if row:
            return Product(**dict(row))
        return None

    def get_all_products(self) -> List[Product]:
        """Récupère tous les produits."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY name")
        return [Product(**dict(row)) for row in cursor.fetchall()]

    def get_low_stock_products(self) -> List[Product]:
        """Récupère les produits avec un stock bas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            WHERE current_stock <= min_stock
            ORDER BY current_stock ASC
        """)
        return [Product(**dict(row)) for row in cursor.fetchall()]

    # --- Gestion des mouvements de stock ---

    def add_stock_movement(self, movement: StockMovement) -> int:
        """Ajoute un mouvement de stock et met à jour le stock du produit."""
        conn = self.connect()
        cursor = conn.cursor()

        # Ajouter le mouvement
        cursor.execute("""
            INSERT INTO stock_movements
            (product_id, movement_type, quantity, unit_price, expiration_date,
             freeze_date, notes, supplier_id, sale_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (movement.product_id, movement.movement_type, movement.quantity,
              movement.unit_price, movement.expiration_date, movement.freeze_date,
              movement.notes, movement.supplier_id, movement.sale_id, movement.created_by))

        # Mettre à jour le stock du produit
        if movement.movement_type == "IN":
            cursor.execute("""
                UPDATE products
                SET current_stock = current_stock + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (movement.quantity, movement.product_id))
        else:  # OUT
            cursor.execute("""
                UPDATE products
                SET current_stock = current_stock - ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (movement.quantity, movement.product_id))

        conn.commit()
        return cursor.lastrowid

    def get_stock_movements(self, product_id: Optional[int] = None,
                           limit: int = 100) -> List[StockMovement]:
        """Récupère les mouvements de stock."""
        conn = self.connect()
        cursor = conn.cursor()

        if product_id:
            cursor.execute("""
                SELECT * FROM stock_movements
                WHERE product_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (product_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM stock_movements
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))

        return [StockMovement(**dict(row)) for row in cursor.fetchall()]

    def get_expiring_products(self, days: int = 7) -> List[Tuple[Product, datetime]]:
        """Récupère les produits qui vont expirer dans X jours."""
        conn = self.connect()
        cursor = conn.cursor()

        expiry_limit = datetime.now() + timedelta(days=days)

        cursor.execute("""
            SELECT DISTINCT p.*, sm.expiration_date
            FROM products p
            JOIN stock_movements sm ON p.id = sm.product_id
            WHERE sm.expiration_date IS NOT NULL
            AND sm.expiration_date <= ?
            AND sm.expiration_date >= datetime('now')
            ORDER BY sm.expiration_date ASC
        """, (expiry_limit,))

        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            exp_date = row_dict.pop('expiration_date')
            product = Product(**row_dict)
            results.append((product, exp_date))

        return results

    # --- Gestion des clients ---

    def add_client(self, client: Client) -> int:
        """Ajoute un nouveau client."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (name, company, email, phone, address, city, postal_code, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (client.name, client.company, client.email, client.phone,
              client.address, client.city, client.postal_code, client.notes))
        conn.commit()
        return cursor.lastrowid

    def update_client(self, client: Client):
        """Met à jour un client existant."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients
            SET name=?, company=?, email=?, phone=?, address=?, city=?,
                postal_code=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (client.name, client.company, client.email, client.phone,
              client.address, client.city, client.postal_code, client.notes, client.id))
        conn.commit()

    def delete_client(self, client_id: int):
        """Supprime un client."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()

    def get_client(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        row = cursor.fetchone()
        if row:
            return Client(**dict(row))
        return None

    def get_all_clients(self) -> List[Client]:
        """Récupère tous les clients."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY name")
        return [Client(**dict(row)) for row in cursor.fetchall()]

    # --- Gestion des fournisseurs ---

    def add_supplier(self, supplier: Supplier) -> int:
        """Ajoute un nouveau fournisseur."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (name, company, email, phone, address, city, postal_code, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (supplier.name, supplier.company, supplier.email, supplier.phone,
              supplier.address, supplier.city, supplier.postal_code, supplier.notes))
        conn.commit()
        return cursor.lastrowid

    def update_supplier(self, supplier: Supplier):
        """Met à jour un fournisseur existant."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE suppliers
            SET name=?, company=?, email=?, phone=?, address=?, city=?,
                postal_code=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (supplier.name, supplier.company, supplier.email, supplier.phone,
              supplier.address, supplier.city, supplier.postal_code, supplier.notes, supplier.id))
        conn.commit()

    def delete_supplier(self, supplier_id: int):
        """Supprime un fournisseur."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        conn.commit()

    def get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        """Récupère un fournisseur par son ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
        row = cursor.fetchone()
        if row:
            return Supplier(**dict(row))
        return None

    def get_all_suppliers(self) -> List[Supplier]:
        """Récupère tous les fournisseurs."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        return [Supplier(**dict(row)) for row in cursor.fetchall()]

    # --- Gestion des ventes ---

    def add_sale(self, sale: Sale, items: List[SaleItem]) -> int:
        """Ajoute une nouvelle vente avec ses articles."""
        conn = self.connect()
        cursor = conn.cursor()

        # Ajouter la vente
        cursor.execute("""
            INSERT INTO sales (client_id, sale_date, total_amount, status, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sale.client_id, sale.sale_date, sale.total_amount, sale.status,
              sale.payment_method, sale.notes))

        sale_id = cursor.lastrowid

        # Ajouter les articles de vente
        for item in items:
            cursor.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal, discount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, item.product_id, item.quantity, item.unit_price,
                  item.subtotal, item.discount))

            # Créer un mouvement de stock sortant
            movement = StockMovement(
                product_id=item.product_id,
                movement_type="OUT",
                quantity=item.quantity,
                unit_price=item.unit_price,
                sale_id=sale_id,
                notes=f"Vente #{sale_id}"
            )
            self.add_stock_movement(movement)

        conn.commit()
        return sale_id

    def get_sale(self, sale_id: int) -> Optional[Sale]:
        """Récupère une vente par son ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE id=?", (sale_id,))
        row = cursor.fetchone()
        if row:
            return Sale(**dict(row))
        return None

    def get_sale_items(self, sale_id: int) -> List[SaleItem]:
        """Récupère les articles d'une vente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,))
        return [SaleItem(**dict(row)) for row in cursor.fetchall()]

    def get_all_sales(self, limit: int = 100) -> List[Sale]:
        """Récupère toutes les ventes."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales ORDER BY sale_date DESC LIMIT ?", (limit,))
        return [Sale(**dict(row)) for row in cursor.fetchall()]

    # --- Gestion des factures ---

    def add_invoice(self, invoice: Invoice) -> int:
        """Ajoute une nouvelle facture."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (sale_id, invoice_number, invoice_date, due_date,
                                total_amount, tax_amount, status, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice.sale_id, invoice.invoice_number, invoice.invoice_date,
              invoice.due_date, invoice.total_amount, invoice.tax_amount,
              invoice.status, invoice.pdf_path))
        conn.commit()
        return cursor.lastrowid

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Récupère une facture par son ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        row = cursor.fetchone()
        if row:
            return Invoice(**dict(row))
        return None

    def get_invoice_by_sale(self, sale_id: int) -> Optional[Invoice]:
        """Récupère une facture par ID de vente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE sale_id=?", (sale_id,))
        row = cursor.fetchone()
        if row:
            return Invoice(**dict(row))
        return None

    # --- Statistiques ---

    def get_total_sales(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> float:
        """Calcule le total des ventes."""
        conn = self.connect()
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) FROM sales
                WHERE status = 'COMPLETED' AND sale_date BETWEEN ? AND ?
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) FROM sales
                WHERE status = 'COMPLETED'
            """)

        return cursor.fetchone()[0]

    def get_sales_by_period(self, days: int = 30) -> List[Tuple[str, float]]:
        """Récupère les ventes par période."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(sale_date) as date, SUM(total_amount) as total
            FROM sales
            WHERE status = 'COMPLETED'
            AND sale_date >= date('now', '-' || ? || ' days')
            GROUP BY DATE(sale_date)
            ORDER BY date DESC
        """, (days,))

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_top_products(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Récupère les produits les plus vendus."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, SUM(si.quantity) as total_quantity
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.status = 'COMPLETED'
            GROUP BY p.id, p.name
            ORDER BY total_quantity DESC
            LIMIT ?
        """, (limit,))

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_top_clients(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Récupère les meilleurs clients."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.name, SUM(s.total_amount) as total_spent
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            WHERE s.status = 'COMPLETED'
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT ?
        """, (limit,))

        return [(row[0], row[1]) for row in cursor.fetchall()]
