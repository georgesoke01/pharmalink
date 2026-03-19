// store/index.ts
import { create } from "zustand"
import type { Utilisateur } from "@/types"
import { authService } from "@/services/pharmacies"

// ── Store Auth ────────────────────────────────────────────────────────────────
interface AuthStore {
  utilisateur:   Utilisateur | null
  estConnecte:   boolean
  setUtilisateur: (u: Utilisateur | null) => void
  logout:        () => Promise<void>
  init:          () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  utilisateur:  null,
  estConnecte:  false,

  setUtilisateur: (u) => set({ utilisateur: u, estConnecte: u !== null }),

  logout: async () => {
    await authService.logout()
    set({ utilisateur: null, estConnecte: false })
  },

  init: () => {
    const u = authService.getUtilisateurLocal()
    if (u && authService.estConnecte()) {
      set({ utilisateur: u, estConnecte: true })
    }
  },
}))

// ── Store Localisation ────────────────────────────────────────────────────────
interface LocalisationStore {
  lat:         number | null
  lng:         number | null
  ville:       string
  setPosition: (lat: number, lng: number) => void
  setVille:    (ville: string) => void
}

export const useLocalisationStore = create<LocalisationStore>((set) => ({
  lat:   null,
  lng:   null,
  ville: "Parakou",

  setPosition: (lat, lng) => set({ lat, lng }),
  setVille:    (ville)    => set({ ville }),
}))

// ── Store Filtres ─────────────────────────────────────────────────────────────
interface FiltresStore {
  rechercheTexte:  string
  filtreOuvert:    boolean
  filtreGarde:     boolean
  filtreService:   string | null
  rayonKm:         number
  setRecherche:    (t: string) => void
  setFiltreOuvert: (v: boolean) => void
  setFiltreGarde:  (v: boolean) => void
  setFiltreService:(s: string | null) => void
  setRayon:        (r: number) => void
  reset:           () => void
}

export const useFiltresStore = create<FiltresStore>((set) => ({
  rechercheTexte:  "",
  filtreOuvert:    false,
  filtreGarde:     false,
  filtreService:   null,
  rayonKm:         5,

  setRecherche:    (t) => set({ rechercheTexte: t }),
  setFiltreOuvert: (v) => set({ filtreOuvert: v }),
  setFiltreGarde:  (v) => set({ filtreGarde: v }),
  setFiltreService:(s) => set({ filtreService: s }),
  setRayon:        (r) => set({ rayonKm: r }),
  reset: () => set({
    rechercheTexte: "",
    filtreOuvert:   false,
    filtreGarde:    false,
    filtreService:  null,
    rayonKm:        5,
  }),
}))