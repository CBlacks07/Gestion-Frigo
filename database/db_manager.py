"""Gestionnaire de base de données SQLite."""
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path

from .models import Product, StockMovement, Client, Supplier, Sale, SaleItem, Invoice, User, AppSettings
import hashlib


class DatabaseManager:
    """Gestionnaire principal de la base de données."""

    def __init__(self, db_path: str = None):
        """Initialise le gestionnaire de base de données."""
        if db_path is None:
            # Déterminer le meilleur emplacement pour la base de données
            if getattr(sys, 'frozen', False):
                # Si l'application est compilée avec PyInstaller
                # Utiliser le dossier AppData de l'utilisateur
                try:
                    app_data = Path(os.environ.get('APPDATA', os.path.expanduser('~')))
                    db_dir = app_data / 'Gestion-Frigo'
                    db_dir.mkdir(parents=True, exist_ok=True)
                    db_path = str(db_dir / 'gestion_frigo.db')
                    print(f"Base de données: {db_path}")
                except Exception as e:
                    print(f"Erreur création répertoire DB: {e}")
                    # Fallback: utiliser le répertoire temporaire
                    import tempfile
                    db_path = str(Path(tempfile.gettempdir()) / 'Gestion-Frigo' / 'gestion_frigo.db')
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            else:
                # En mode développement, utiliser le dossier courant
                db_path = "gestion_frigo.db"

        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

        try:
            self._create_tables()
        except Exception as e:
            print(f"ERREUR lors de la création des tables: {e}")
            print(f"Chemin de la base de données: {self.db_path}")
            raise

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

        # Table des utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN')),
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Table des paramètres de l'application
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT DEFAULT 'Gestion-Frigo',
                company_address TEXT DEFAULT '',
                company_phone TEXT DEFAULT '',
                company_email TEXT DEFAULT '',
                logo_path TEXT DEFAULT '',
                primary_color TEXT DEFAULT '#2980b9',
                show_address_on_receipt INTEGER DEFAULT 1,
                show_phone_on_receipt INTEGER DEFAULT 1,
                show_email_on_receipt INTEGER DEFAULT 0,
                receipt_footer_text TEXT DEFAULT 'Merci de votre visite !',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # Initialiser les données par défaut
        self._initialize_default_data()

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

    # --- Gestion des utilisateurs ---

    def _initialize_default_data(self):
        """Initialise les données par défaut (paramètres uniquement)."""
        conn = self.connect()
        cursor = conn.cursor()

        # Vérifier si les paramètres existent
        cursor.execute("SELECT COUNT(*) FROM app_settings")
        if cursor.fetchone()[0] == 0:
            # Créer les paramètres par défaut
            cursor.execute("""
                INSERT INTO app_settings (company_name, company_address, company_phone, company_email)
                VALUES ('Gestion-Frigo', '', '', '')
            """)

        conn.commit()

    def has_users(self) -> bool:
        """Vérifie si au moins un utilisateur existe dans la base de données."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count > 0

    def _hash_password(self, password: str) -> str:
        """Hash un mot de passe avec SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur."""
        conn = self.connect()
        cursor = conn.cursor()

        password_hash = self._hash_password(password)
        cursor.execute("""
            SELECT * FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))

        row = cursor.fetchone()
        if row:
            # Mettre à jour last_login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (row['id'],))
            conn.commit()

            return User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                last_login=datetime.now()
            )
        return None

    def add_user(self, user_or_username, password: str, full_name: str = None,
                 role: str = "USER", is_active: bool = True) -> int:
        """Ajoute un nouvel utilisateur.

        Args:
            user_or_username: Soit un objet User, soit le nom d'utilisateur (str)
            password: Le mot de passe de l'utilisateur
            full_name: Le nom complet (requis si user_or_username est une str)
            role: Le rôle de l'utilisateur (USER ou ADMIN)
            is_active: Si l'utilisateur est actif
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Si c'est un objet User, extraire les informations
        if isinstance(user_or_username, User):
            username = user_or_username.username
            full_name = user_or_username.full_name
            role = user_or_username.role
            is_active = user_or_username.is_active
        else:
            # C'est un nom d'utilisateur (str)
            username = user_or_username

        password_hash = self._hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, role, int(is_active)))

        conn.commit()
        return cursor.lastrowid

    def get_all_users(self) -> List[User]:
        """Récupère tous les utilisateurs."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users ORDER BY username")
        users = []
        for row in cursor.fetchall():
            users.append(User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                last_login=row['last_login']
            ))
        return users

    def update_user(self, user: User):
        """Met à jour un utilisateur."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET full_name = ?, role = ?, is_active = ?
            WHERE id = ?
        """, (user.full_name, user.role, int(user.is_active), user.id))

        conn.commit()

    def change_user_password(self, user_id: int, new_password: str):
        """Change le mot de passe d'un utilisateur."""
        conn = self.connect()
        cursor = conn.cursor()

        password_hash = self._hash_password(new_password)
        cursor.execute("""
            UPDATE users SET password_hash = ? WHERE id = ?
        """, (password_hash, user_id))

        conn.commit()

    def delete_user(self, user_id: int):
        """Supprime un utilisateur."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    # --- Gestion des paramètres ---

    def get_app_settings(self) -> AppSettings:
        """Récupère les paramètres de l'application."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM app_settings LIMIT 1")
        row = cursor.fetchone()

        if row:
            return AppSettings(
                id=row['id'],
                company_name=row['company_name'],
                company_address=row['company_address'],
                company_phone=row['company_phone'],
                company_email=row['company_email'],
                logo_path=row['logo_path'],
                primary_color=row['primary_color'],
                show_address_on_receipt=bool(row['show_address_on_receipt']),
                show_phone_on_receipt=bool(row['show_phone_on_receipt']),
                show_email_on_receipt=bool(row['show_email_on_receipt']),
                receipt_footer_text=row['receipt_footer_text'],
                updated_at=row['updated_at']
            )
        else:
            # Retourner les paramètres par défaut
            return AppSettings()

    def update_app_settings(self, settings: AppSettings):
        """Met à jour les paramètres de l'application."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE app_settings
            SET company_name = ?, company_address = ?, company_phone = ?,
                company_email = ?, logo_path = ?, primary_color = ?,
                show_address_on_receipt = ?, show_phone_on_receipt = ?,
                show_email_on_receipt = ?, receipt_footer_text = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (settings.company_name, settings.company_address, settings.company_phone,
              settings.company_email, settings.logo_path, settings.primary_color,
              int(settings.show_address_on_receipt), int(settings.show_phone_on_receipt),
              int(settings.show_email_on_receipt), settings.receipt_footer_text))

        conn.commit()

    # --- Maintenance et réinitialisation ---

    def reset_settings_to_default(self):
        """Réinitialise les paramètres de l'application aux valeurs par défaut."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE app_settings
            SET company_name = 'Gestion-Frigo',
                company_address = '',
                company_phone = '',
                company_email = '',
                logo_path = '',
                primary_color = '#2980b9',
                show_address_on_receipt = 1,
                show_phone_on_receipt = 1,
                show_email_on_receipt = 0,
                receipt_footer_text = 'Merci de votre visite !',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """)

        conn.commit()

    def clear_all_data(self, keep_users: bool = True):
        """Supprime toutes les données de l'application.

        Args:
            keep_users: Si True, conserve les utilisateurs et paramètres.
                       Si False, supprime tout (réinitialisation complète).
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Supprimer les données transactionnelles
        cursor.execute("DELETE FROM sale_items")
        cursor.execute("DELETE FROM invoices")
        cursor.execute("DELETE FROM sales")
        cursor.execute("DELETE FROM stock_movements")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM clients")
        cursor.execute("DELETE FROM suppliers")

        if not keep_users:
            # Réinitialisation complète : supprimer utilisateurs et paramètres
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM app_settings")

            # Recréer les paramètres par défaut
            cursor.execute("""
                INSERT INTO app_settings (company_name, company_address, company_phone, company_email)
                VALUES ('Gestion-Frigo', '', '', '')
            """)

        conn.commit()

    def create_database_backup(self) -> str:
        """Crée une sauvegarde de la base de données.

        Returns:
            Le chemin du fichier de sauvegarde.
        """
        import shutil
        from datetime import datetime

        # Créer le nom du fichier de backup avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"gestion_frigo_backup_{timestamp}.db"

        # Copier le fichier de base de données
        shutil.copy2(self.db_path, backup_path)

        return str(backup_path)
