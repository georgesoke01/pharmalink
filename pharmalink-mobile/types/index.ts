// types/index.ts
// ─────────────────────────────────────────────────────────────────────────────
// Types TypeScript partagés dans toute l'application
// ─────────────────────────────────────────────────────────────────────────────

// ── Pharmacie ─────────────────────────────────────────────────────────────────
export interface Coordonnees {
  lat: number
  lng: number
}

export interface Pharmacie {
  id:               number
  nom:              string
  adresse:          string
  ville:            string
  code_postal:      string
  telephone:        string
  email:            string
  site_web:         string
  description:      string
  logo:             string | null
  services:         string[]
  latitude:         number | null
  longitude:        number | null
  coordonnees:      Coordonnees | null
  est_ouverte:      boolean
  est_de_garde:     boolean
  est_active:       boolean
  pharmacien_nom:   string
  statut:           "en_attente" | "active" | "suspendue"
  distance?:        number   // ajouté côté client (en km)
}

export interface PharmacieDetail extends Pharmacie {
  horaires:  HoraireSemaine[]
  exceptions: HoraireExceptionnel[]
  est_ouverte_maintenant: boolean
}

// ── Produit ───────────────────────────────────────────────────────────────────
export type CategorieProduirt = "medicament" | "parapharmacie" | "materiel" | "autre"
export type FormeProduit =
  | "comprimes" | "gelules" | "sirop" | "injection"
  | "creme" | "gouttes" | "suppositoire" | "sachet" | "spray" | "autre"

export interface Produit {
  id:               number
  code_cip13:       string
  nom:              string
  nom_generique:    string
  laboratoire:      string
  categorie:        CategorieProduirt
  forme:            FormeProduit | ""
  dosage:           string
  sur_ordonnance:   boolean
  contre_indications: string
  description:      string
  image:            string | null
}

export interface ProduitAvecStock extends Produit {
  prix_fcfa:   number | null
  disponible:  boolean | null
  quantite:    number | null
}

// ── Horaires ──────────────────────────────────────────────────────────────────
export interface HoraireSemaine {
  id:              number
  jour:            number
  jour_label:      string
  heure_ouverture: string | null
  heure_fermeture: string | null
  pause_debut:     string | null
  pause_fin:       string | null
  est_ferme:       boolean
}

export interface HoraireExceptionnel {
  id:              number
  date:            string
  motif:           string
  heure_ouverture: string | null
  heure_fermeture: string | null
  est_ferme:       boolean
}

export interface HorairesComplet {
  semaine:                  HoraireSemaine[]
  exceptions:               HoraireExceptionnel[]
  est_ouverte_maintenant:   boolean
}

// ── Garde ─────────────────────────────────────────────────────────────────────
export interface Garde {
  id:                    number
  pharmacie:             number
  pharmacie_nom:         string
  pharmacie_adresse:     string
  pharmacie_ville:       string
  date_debut:            string
  date_fin:              string
  telephone_effectif:    string
  zone_ville:            string
  zone_quartier:         string
  note:                  string
  statut:                "planifiee" | "en_cours" | "terminee" | "annulee"
  est_active_maintenant: boolean
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface Utilisateur {
  id:          number
  username:    string
  email:       string
  nom_complet: string
  role:        "public" | "pharmacien" | "super_admin"
  is_approved: boolean
  avatar:      string | null
}

export interface AuthTokens {
  access:  string
  refresh: string
  user:    Utilisateur
}

// ── API ───────────────────────────────────────────────────────────────────────
export interface PageResponse<T> {
  count:       number
  total_pages: number
  next:        string | null
  previous:    string | null
  results:     T[]
}

export interface ApiError {
  message: string
  detail?: string
  errors?: Record<string, string[]>
}

// ── Filtres ───────────────────────────────────────────────────────────────────
export interface FiltresPharmacies {
  ville?:        string
  est_ouverte?:  boolean
  est_de_garde?: boolean
  service?:      string
  lat?:          number
  lng?:          number
  rayon?:        number
  search?:       string
  page_size?:    number
}

export interface FiltresProduits {
  search?:         string
  categorie?:      CategorieProduirt
  sur_ordonnance?: boolean
  forme?:          FormeProduit
  disponible?:     boolean
  pharmacie_id?:   number
  page_size?:      number
}

// ── Services disponibles ──────────────────────────────────────────────────────
export const SERVICES_LABELS: Record<string, string> = {
  livraison:           "Livraison",
  urgences:            "Urgences",
  vaccins:             "Vaccins",
  bebe:                "Bébé",
  dermatologie:        "Dermatologie",
  veterinaire:         "Vétérinaire",
  garde_nuit:          "Garde de nuit",
  ordonnance_en_ligne: "Ordonnance en ligne",
}