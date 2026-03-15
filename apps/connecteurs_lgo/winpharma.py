# apps/connecteurs_lgo/winpharma.py
# ─────────────────────────────────────────────────────────────────────────────
# Connecteur Winpharma — LECTURE SEULE
#
# Winpharma utilise MySQL comme base de données.
# Chemin typique : serveur MySQL local sur port 3306
# Base de données : winpharma (ou wpharm selon la version)
# ─────────────────────────────────────────────────────────────────────────────
import logging
from typing import List
from .base_connector import BaseConnecteurLGO, ProduitLGO, ConnexionLGOError

logger = logging.getLogger(__name__)


class ConnecteurWinpharma(BaseConnecteurLGO):
    """Connecteur pour Winpharma (base MySQL).

    Config attendue (générée par Tauri) :
    {
        "db_type": "mysql",
        "db_host": "127.0.0.1",
        "db_port": 3306,
        "db_name": "winpharma",
        "db_user": "readonly_user",
        "db_password": "..."
    }

    Note : L'utilisateur MySQL doit avoir uniquement les droits SELECT.
    Cet utilisateur est créé automatiquement par l'installeur Tauri
    lors de la configuration initiale.
    """

    QUERY_PRODUITS = """
        SELECT
            p.cip13             AS code_cip13,
            p.designation       AS nom,
            p.denomination      AS nom_generique,
            p.laboratoire       AS laboratoire,
            p.famille           AS categorie,
            p.forme             AS forme,
            p.dosage            AS dosage,
            p.ordonnance        AS sur_ordonnance,
            COALESCE(s.qte, 0)  AS quantite_stock,
            COALESCE(t.pu_vente, 0) AS prix_vente
        FROM produit p
        LEFT JOIN stock s ON s.ref_produit = p.ref_produit
        LEFT JOIN tarif t ON t.ref_produit = p.ref_produit
        WHERE p.actif = 1
        ORDER BY p.designation
    """

    def _get_connection(self):
        """Ouvre une connexion MySQL en lecture seule.

        Raises:
            ConnexionLGOError: Si la connexion échoue.
        """
        try:
            import pymysql
        except ImportError:
            raise ConnexionLGOError(
                "pymysql n'est pas installé. "
                "Ajoutez 'pymysql' aux requirements."
            )

        try:
            conn = pymysql.connect(
                host     = self.config.get("db_host", "127.0.0.1"),
                port     = int(self.config.get("db_port", 3306)),
                database = self.config.get("db_name", "winpharma"),
                user     = self.config.get("db_user", ""),
                password = self.config.get("db_password", ""),
                charset  = "utf8mb4",
                connect_timeout = 10,
                cursorclass = pymysql.cursors.DictCursor,
            )
            return conn
        except Exception as e:
            raise ConnexionLGOError(f"Connexion MySQL Winpharma échouée : {e}")

    def tester_connexion(self) -> bool:
        """Teste la connexion à la base Winpharma."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as nb FROM produit LIMIT 1")
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"[Winpharma] Test connexion échoué : {e}")
            return False

    def extraire_produits(self) -> List[ProduitLGO]:
        """Extrait tous les produits actifs depuis Winpharma.

        Returns:
            Liste de ProduitLGO prête pour la synchronisation.
        """
        conn = self._get_connection()
        produits = []

        try:
            with conn.cursor() as cursor:
                cursor.execute(self.QUERY_PRODUITS)
                rows = cursor.fetchall()

            for row in rows:
                try:
                    # Winpharma stocke les prix en centimes d'euros
                    prix_eur  = float(row["prix_vente"]) / 100
                    prix_fcfa = int(prix_eur * 655.957)

                    produits.append(ProduitLGO(
                        code_cip13     = str(row["code_cip13"] or ""),
                        nom            = str(row["nom"] or ""),
                        nom_generique  = str(row["nom_generique"] or ""),
                        laboratoire    = str(row["laboratoire"] or ""),
                        categorie      = self._mapper_categorie(str(row["categorie"] or "")),
                        forme          = str(row["forme"] or ""),
                        dosage         = str(row["dosage"] or ""),
                        sur_ordonnance = bool(row["sur_ordonnance"]),
                        quantite_stock = int(row["quantite_stock"] or 0),
                        prix_fcfa      = max(0, prix_fcfa),
                    ))
                except Exception as e:
                    logger.warning(f"[Winpharma] Produit ignoré ({row.get('nom', '?')}): {e}")

        except Exception as e:
            raise ConnexionLGOError(f"Erreur lecture Winpharma : {e}")
        finally:
            conn.close()

        logger.info(f"[Winpharma] {len(produits)} produits extraits")
        return produits

    @staticmethod
    def _mapper_categorie(categorie_lgo: str) -> str:
        mapping = {
            "MED":     "medicament",
            "MEDIC":   "medicament",
            "PARA":    "parapharmacie",
            "MAT":     "materiel",
            "DISPO":   "materiel",
        }
        return mapping.get(categorie_lgo.upper(), "autre")