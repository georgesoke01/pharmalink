// services/pharmacies.ts
// ─────────────────────────────────────────────────────────────────────────────
// Tous les services API de l'application en un seul fichier
// Pharmacies, Produits, Gardes, Auth
// ─────────────────────────────────────────────────────────────────────────────
import AsyncStorage from "@react-native-async-storage/async-storage"
import api, { tokenStorage } from "./api"
import { STORAGE_KEYS } from "@/constants"
import type {
  Pharmacie, PharmacieDetail, HorairesComplet,
  Produit, ProduitAvecStock,
  Garde,
  AuthTokens, Utilisateur,
  FiltresPharmacies, FiltresProduits,
  PageResponse,
} from "@/types" 

// ─────────────────────────────────────────────────────────────────────────────
// PHARMACIES
// ─────────────────────────────────────────────────────────────────────────────

export const pharmaciesService = {

  /** Liste des pharmacies actives avec filtres et pagination */
  async liste(filtres: FiltresPharmacies = {}): Promise<PageResponse<Pharmacie>> {
    const { data } = await api.get("/pharmacies/", { params: filtres })
    return data
  },

  /** Détail complet d'une pharmacie */
  async detail(id: number): Promise<PharmacieDetail> {
    const { data } = await api.get(`/pharmacies/${id}/`)
    return data
  },

  /** Pharmacies de garde actives en ce moment */
  async deGarde(ville?: string): Promise<PageResponse<Pharmacie>> {
    const { data } = await api.get("/pharmacies/de-garde/", {
      params: ville ? { ville } : {},
    })
    return data
  },

  /** Pharmacies proches d'une position GPS dans un rayon donné */
  async proches(
    lat: number,
    lng: number,
    rayonKm = 5,
  ): Promise<PageResponse<Pharmacie>> {
    const { data } = await api.get("/pharmacies/", {
      params: { lat, lng, rayon: rayonKm, statut: "active" },
    })
    return data
  },

  /** Horaires hebdomadaires + exceptions + statut ouverture en temps réel */
  async horaires(id: number): Promise<HorairesComplet> {
    const { data } = await api.get(`/horaires/pharmacie/${id}/`)
    return data
  },
}

// ─────────────────────────────────────────────────────────────────────────────
// PRODUITS
// ─────────────────────────────────────────────────────────────────────────────

export const produitsService = {

  /** Catalogue global des produits avec filtres */
  async liste(filtres: FiltresProduits = {}): Promise<PageResponse<Produit>> {
    const { data } = await api.get("/produits/", { params: filtres })
    return data
  },

  /** Fiche complète d'un produit */
  async detail(id: number): Promise<Produit> {
    const { data } = await api.get(`/produits/${id}/`)
    return data
  },

  /** Produits disponibles dans une pharmacie avec prix et stock en temps réel */
  async parPharmacie(
    pharmacieId: number,
    filtres: FiltresProduits = {},
  ): Promise<PageResponse<ProduitAvecStock>> {
    const { data } = await api.get(`/produits/pharmacie/${pharmacieId}/`, {
      params: { ...filtres, pharmacie_id: pharmacieId },
    })
    return data
  },
}

// ─────────────────────────────────────────────────────────────────────────────
// GARDES
// ─────────────────────────────────────────────────────────────────────────────

export const gardesService = {

  /** Gardes actives en ce moment, filtrables par ville */
  async actives(ville?: string): Promise<PageResponse<Garde>> {
    const { data } = await api.get("/gardes/", {
      params: ville ? { ville } : {},
    })
    return data
  },

  /** Gardes planifiées dans les 7 prochains jours */
  async prochaines(ville?: string): Promise<PageResponse<Garde>> {
    const { data } = await api.get("/gardes/prochaines/", {
      params: ville ? { ville } : {},
    })
    return data
  },
}

// ─────────────────────────────────────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────────────────────────────────────

export const authService = {

  /** Connexion avec email ou username + password.
   *  Stocke les tokens JWT et les infos utilisateur localement. */
  async login(login: string, password: string): Promise<AuthTokens> {
    const { data } = await api.post("/auth/token/", {
      username: login,
      password,
    })
    tokenStorage.setAccess(data.access)
    tokenStorage.setRefresh(data.refresh)
    await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user))
    return data
  },

  /** Déconnexion — blackliste le token sur le serveur puis nettoie le stockage local */
  async logout(): Promise<void> {
    const refresh = tokenStorage.getRefresh()
    if (refresh) {
      try {
        await api.post("/auth/token/logout/", { refresh })
      } catch {
        // Ignore — on nettoie quand même localement
      }
    }
    tokenStorage.clear()
    await AsyncStorage.removeItem(STORAGE_KEYS.USER)
  },

  /** Inscription d'un compte utilisateur public */
  async inscrire(payload: {
    username:    string
    email:       string
    password:    string
    password2:   string
    first_name?: string
    last_name?:  string
  }): Promise<{ user: Utilisateur }> {
    const { data } = await api.post("/users/inscription/public/", payload)
    return data
  },

  /** Retourne l'utilisateur stocké localement (AsyncStorage) */
  async getUtilisateurLocal(): Promise<Utilisateur | null> {
    const json = await AsyncStorage.getItem(STORAGE_KEYS.USER)
    return json ? JSON.parse(json) : null
  },

  /** Vérifie si un token d'accès est présent en mémoire */
  estConnecte(): boolean {
    return tokenStorage.getAccess() !== null
  },
}