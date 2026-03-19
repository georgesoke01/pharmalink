# apps/connecteurs_lgo/base_connector.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class ProduitLGO:
    """Structure de données brute extraite depuis un LGO.

    Attributes:
        code_cip13:     Code CIP13 du médicament (peut être vide)
        nom:            Nom commercial du produit
        nom_generique:  DCI / nom générique (optionnel)
        laboratoire:    Fabricant
        categorie:      Catégorie (medicament | parapharmacie | materiel | autre)
        forme:          Forme pharmaceutique (optionnel)
        dosage:         Dosage (optionnel)
        sur_ordonnance: True si médicament sur prescription
        quantite_stock: Quantité en stock
        prix_fcfa:      Prix de vente en FCFA
    """
    code_cip13:     str
    nom:            str
    quantite_stock: int
    prix_fcfa:      int
    nom_generique:  str  = ""
    laboratoire:    str  = ""
    categorie:      str  = "medicament"
    forme:          str  = ""
    dosage:         str  = ""
    sur_ordonnance: bool = False


class BaseConnecteurLGO(ABC):
    """Classe abstraite pour tous les connecteurs LGO.

    ⚠️ LECTURE SEULE — ces connecteurs ne modifient JAMAIS les données du LGO.

    Chaque connecteur concret (ConnecteurPharmagest, ConnecteurWinpharma...)
    hérite de cette classe et implémente tester_connexion() et extraire_produits().

    La méthode synchroniser() orchestre la sync complète et est commune
    à tous les connecteurs — pas besoin de la réimplémenter.
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Dictionnaire généré par l'auto-détection Tauri.
                    Clés standard : db_path, db_type, db_host, db_port, db_name
        """
        self.config = config

    # ── Méthodes abstraites — à implémenter par chaque connecteur ─────────────

    @abstractmethod
    def tester_connexion(self) -> bool:
        """Vérifie que la connexion au LGO est opérationnelle.

        Returns:
            True si la connexion fonctionne, False sinon.
        """

    @abstractmethod
    def extraire_produits(self) -> List[ProduitLGO]:
        """Extrait le catalogue complet depuis le LGO en lecture seule.

        Returns:
            Liste de ProduitLGO avec stock et prix inclus.

        Raises:
            ConnexionLGOError: Si la connexion échoue pendant l'extraction.
        """

    def get_version(self) -> str:
        """Retourne la version du LGO si détectable. Optionnel."""
        return ""

    # ── Méthode commune — synchronisation complète ────────────────────────────

    def synchroniser(self, pharmacie_id: int, declenchement: str = "auto") -> dict:
        """Orchestre la synchronisation complète LGO → API PharmaLink.

        Lit le LGO en lecture seule, transforme les données et les
        enregistre dans PostgreSQL via update_or_create.

        Args:
            pharmacie_id:  ID de la pharmacie à synchroniser.
            declenchement: "auto" | "manuel" | "installation"

        Returns:
            Dictionnaire avec les compteurs : produits, stocks, prix, erreurs, duree.
        """
        import time
        from apps.produits.models import Produit, Stock, Prix
        from apps.pharmacies.models import Pharmacie as PharmacieModel

        debut = time.time()
        stats = {"produits": 0, "stocks": 0, "prix": 0, "erreurs": []}

        pharmacie    = PharmacieModel.objects.get(pk=pharmacie_id)
        produits_lgo = self.extraire_produits()

        for p in produits_lgo:
            try:
                # ── Produit global ────────────────────────────────────────────
                lookup = {"code_cip13": p.code_cip13} if p.code_cip13 else {"nom": p.nom}
                produit, _ = Produit.objects.update_or_create(
                    **lookup,
                    defaults={
                        "nom":            p.nom,
                        "nom_generique":  p.nom_generique,
                        "laboratoire":    p.laboratoire,
                        "categorie":      p.categorie,
                        "forme":          p.forme,
                        "dosage":         p.dosage,
                        "sur_ordonnance": p.sur_ordonnance,
                    },
                )
                stats["produits"] += 1

                # ── Stock de la pharmacie ─────────────────────────────────────
                Stock.objects.update_or_create(
                    pharmacie=pharmacie,
                    produit=produit,
                    defaults={
                        "quantite":   p.quantite_stock,
                        "disponible": p.quantite_stock > 0,
                    },
                )
                stats["stocks"] += 1

                # ── Prix de la pharmacie ──────────────────────────────────────
                Prix.objects.update_or_create(
                    pharmacie=pharmacie,
                    produit=produit,
                    defaults={"prix_fcfa": p.prix_fcfa},
                )
                stats["prix"] += 1

            except Exception as e:
                stats["erreurs"].append(f"{p.nom}: {str(e)}")

        stats["duree"] = round(time.time() - debut, 2)
        return stats


class ConnexionLGOError(Exception):
    """Exception levée lors d'une erreur de connexion ou lecture du LGO."""