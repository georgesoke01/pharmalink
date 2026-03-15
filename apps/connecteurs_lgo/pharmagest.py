# apps/connecteurs_lgo/pharmagest.py
# ─────────────────────────────────────────────────────────────────────────────
# Connecteur Pharmagest — LECTURE SEULE
#
# Pharmagest utilise une base SQLite locale sur le poste Windows.
# Chemin typique : C:\Pharmagest\Data\pharma.db
# ou              C:\Program Files\Pharmagest\database\pharmagest.db
#
# Ce connecteur est appelé depuis le backend Django via Celery.
# Il accède à la DB SQLite via le réseau (chemin partagé ou SSH tunnel)
# ou en local si Django tourne sur la même machine.
# ─────────────────────────────────────────────────────────────────────────────
import sqlite3
import logging
from typing import List
from .base_connector import BaseConnecteurLGO, ProduitLGO, ConnexionLGOError

logger = logging.getLogger(__name__)


class ConnecteurPharmagest(BaseConnecteurLGO):
    """Connecteur pour Pharmagest (base SQLite).

    Config attendue (générée par Tauri) :
    {
        "db_path": "C:\\Pharmagest\\Data\\pharma.db",
        "db_type": "sqlite"
    }
    """

    # Mapping des colonnes Pharmagest → ProduitLGO
    # Ces noms de colonnes correspondent aux tables réelles de Pharmagest v8+
    # À ajuster selon la version exacte lors de la Phase 5 (analyse LGO)
    QUERY_PRODUITS = """
        SELECT
            p.CodeCIP13         AS code_cip13,
            p.Designation       AS nom,
            p.DesignationGen    AS nom_generique,
            p.Laboratoire       AS laboratoire,
            p.Famille           AS categorie,
            p.Forme             AS forme,
            p.Dosage            AS dosage,
            p.Ordonnance        AS sur_ordonnance,
            COALESCE(s.QteStock, 0) AS quantite_stock,
            COALESCE(t.PrixVente, 0) AS prix_vente
        FROM Produits p
        LEFT JOIN Stocks s   ON s.CodeProduit = p.CodeProduit
        LEFT JOIN Tarifs t   ON t.CodeProduit = p.CodeProduit
        WHERE p.Actif = 1
        ORDER BY p.Designation
    """

    def _get_connection(self):
        """Ouvre une connexion SQLite en lecture seule.

        Raises:
            ConnexionLGOError: Si le fichier DB est introuvable ou illisible.
        """
        db_path = self.config.get("db_path")
        if not db_path:
            raise ConnexionLGOError("Chemin de base de données Pharmagest non défini.")

        try:
            # uri=True + mode=ro → lecture seule stricte (SQLite ne peut pas écrire)
            conn = sqlite3.connect(
                f"file:{db_path}?mode=ro",
                uri=True,
                timeout=10,
            )
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            raise ConnexionLGOError(
                f"Impossible d'ouvrir la base Pharmagest ({db_path}): {e}"
            )

    def tester_connexion(self) -> bool:
        """Teste la connexion à la DB Pharmagest."""
        try:
            conn = self._get_connection()
            conn.execute("SELECT COUNT(*) FROM Produits LIMIT 1")
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"[Pharmagest] Test connexion échoué : {e}")
            return False

    def get_version(self) -> str:
        """Tente de lire la version de Pharmagest depuis la DB."""
        try:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT Valeur FROM Configuration WHERE Cle = 'VERSION' LIMIT 1"
            ).fetchone()
            conn.close()
            return row["Valeur"] if row else ""
        except Exception:
            return ""

    def extraire_produits(self) -> List[ProduitLGO]:
        """Extrait tous les produits actifs depuis Pharmagest.

        Returns:
            Liste de ProduitLGO prête pour la synchronisation.

        Raises:
            ConnexionLGOError: Si la lecture échoue.
        """
        conn = self._get_connection()
        produits = []

        try:
            rows = conn.execute(self.QUERY_PRODUITS).fetchall()

            for row in rows:
                try:
                    # Conversion prix LGO (en centimes ou euros) → FCFA
                    # 1 EUR ≈ 655.957 FCFA (taux fixe XOF/EUR)
                    # Pharmagest stocke les prix en centimes d'euros
                    prix_eur    = float(row["prix_vente"]) / 100
                    prix_fcfa   = int(prix_eur * 655.957)

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
                    logger.warning(f"[Pharmagest] Produit ignoré ({row['nom']}): {e}")

        except sqlite3.Error as e:
            raise ConnexionLGOError(f"Erreur lecture Pharmagest : {e}")
        finally:
            conn.close()

        logger.info(f"[Pharmagest] {len(produits)} produits extraits")
        return produits

    @staticmethod
    def _mapper_categorie(categorie_lgo: str) -> str:
        """Convertit la catégorie Pharmagest vers les choix PharmaLink."""
        mapping = {
            "MEDICAMENT":    "medicament",
            "PARA":          "parapharmacie",
            "PARAPHARMACIE": "parapharmacie",
            "MATERIEL":      "materiel",
            "DISPOSITIF":    "materiel",
        }
        return mapping.get(categorie_lgo.upper(), "autre")