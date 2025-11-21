"""Gestionnaire d'alertes pour les stocks et dates de péremption."""
from datetime import datetime, timedelta
from typing import List, Dict
from database.db_manager import DatabaseManager


class AlertManager:
    """Gestionnaire des alertes."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialise le gestionnaire d'alertes."""
        self.db = db_manager

    def check_low_stock_alerts(self) -> List[Dict]:
        """Vérifie et retourne les alertes de stock bas."""
        products = self.db.get_low_stock_products()
        alerts = []

        for product in products:
            alert = {
                'type': 'LOW_STOCK',
                'severity': 'HIGH' if product.current_stock == 0 else 'MEDIUM',
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'unit': product.unit,
                'message': f"Stock bas pour {product.name}: {product.current_stock} {product.unit} (min: {product.min_stock})"
            }

            if product.current_stock == 0:
                alert['message'] = f"RUPTURE DE STOCK: {product.name}"

            alerts.append(alert)

        return alerts

    def check_expiration_alerts(self, days: int = 7) -> List[Dict]:
        """Vérifie et retourne les alertes de produits bientôt périmés."""
        expiring_products = self.db.get_expiring_products(days=days)
        alerts = []

        for product, exp_date in expiring_products:
            days_until_expiry = (exp_date - datetime.now()).days

            if days_until_expiry < 0:
                severity = 'CRITICAL'
                message = f"PÉRIMÉ: {product.name} (périmé depuis {abs(days_until_expiry)} jours)"
            elif days_until_expiry == 0:
                severity = 'CRITICAL'
                message = f"EXPIRE AUJOURD'HUI: {product.name}"
            elif days_until_expiry <= 3:
                severity = 'HIGH'
                message = f"Expire dans {days_until_expiry} jours: {product.name}"
            else:
                severity = 'MEDIUM'
                message = f"Expire dans {days_until_expiry} jours: {product.name}"

            alert = {
                'type': 'EXPIRATION',
                'severity': severity,
                'product_id': product.id,
                'product_name': product.name,
                'expiration_date': exp_date,
                'days_until_expiry': days_until_expiry,
                'message': message
            }

            alerts.append(alert)

        return alerts

    def get_all_alerts(self) -> List[Dict]:
        """Récupère toutes les alertes actives."""
        alerts = []
        alerts.extend(self.check_low_stock_alerts())
        alerts.extend(self.check_expiration_alerts())

        # Trier par sévérité (CRITICAL > HIGH > MEDIUM > LOW)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 4))

        return alerts

    def get_alert_count(self) -> Dict[str, int]:
        """Retourne le nombre d'alertes par sévérité."""
        alerts = self.get_all_alerts()

        count = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'total': len(alerts)
        }

        for alert in alerts:
            severity = alert.get('severity', 'LOW')
            count[severity] += 1

        return count
