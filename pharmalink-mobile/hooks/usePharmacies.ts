// hooks/usePharmacies.ts
// ─────────────────────────────────────────────────────────────────────────────
// Tous les hooks React Query + GPS de l'application
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect, useCallback } from "react"
import { useQuery, useInfiniteQuery } from "@tanstack/react-query"
import * as Location from "expo-location"

import {
  pharmaciesService, 
  produitsService,
  gardesService,
} from "@/services/pharmacies"
import { useLocalisationStore } from "@/store"
import type { FiltresPharmacies, FiltresProduits } from "@/types"

// ─────────────────────────────────────────────────────────────────────────────
// PHARMACIES
// ─────────────────────────────────────────────────────────────────────────────

export const usePharmacies = (filtres: FiltresPharmacies = {}) =>
  useInfiniteQuery({
    queryKey:         ["pharmacies", filtres],
    queryFn:          ({ pageParam = 1 }) =>
      pharmaciesService.liste({ ...filtres, page: pageParam as number }),
    getNextPageParam: (last: any, pages: any[]) =>
      last.next ? pages.length + 1 : undefined,
    initialPageParam: 1,
    staleTime:        1000 * 60 * 2,
  })

export const usePharmacie = (id: number) =>
  useQuery({
    queryKey:  ["pharmacie", id],
    queryFn:   () => pharmaciesService.detail(id),
    staleTime: 1000 * 60 * 5,
    enabled:   id > 0,
  })

export const usePharmaciesProches = (
  lat: number | null,
  lng: number | null,
  rayon = 5,
) =>
  useInfiniteQuery({
    queryKey:         ["pharmacies-proches", lat, lng, rayon],
    queryFn:          ({ pageParam = 1 }) =>
      pharmaciesService.proches(lat!, lng!, rayon),
    getNextPageParam: (last: any, pages: any[]) =>
      last.next ? pages.length + 1 : undefined,
    initialPageParam: 1,
    enabled:          lat !== null && lng !== null,
    staleTime:        1000 * 60 * 2,
    refetchInterval:  1000 * 60 * 5,
  })

export const usePharmaciesDeGarde = (ville?: string) =>
  useQuery({
    queryKey:        ["gardes-actives", ville],
    queryFn:         () => pharmaciesService.deGarde(ville),
    staleTime:       1000 * 60,
    refetchInterval: 1000 * 60 * 5,
  })

export const useHoraires = (pharmacieId: number) =>
  useQuery({
    queryKey:  ["horaires", pharmacieId],
    queryFn:   () => pharmaciesService.horaires(pharmacieId),
    staleTime: 1000 * 60 * 10,
    enabled:   pharmacieId > 0,
  })

// ─────────────────────────────────────────────────────────────────────────────
// PRODUITS
// ─────────────────────────────────────────────────────────────────────────────

export const useProduits = (filtres: FiltresProduits = {}) =>
  useInfiniteQuery({
    queryKey:         ["produits", filtres],
    queryFn:          ({ pageParam = 1 }) =>
      produitsService.liste({ ...filtres, page: pageParam as number }),
    getNextPageParam: (last: any, pages: any[]) =>
      last.next ? pages.length + 1 : undefined,
    initialPageParam: 1,
    staleTime:        1000 * 60 * 5,
  })

export const useProduit = (id: number) =>
  useQuery({
    queryKey:  ["produit", id],
    queryFn:   () => produitsService.detail(id),
    staleTime: 1000 * 60 * 10,
    enabled:   id > 0,
  })

export const useProduitsPharmacie = (
  pharmacieId: number,
  filtres: FiltresProduits = {},
) =>
  useInfiniteQuery({
    queryKey:         ["produits-pharmacie", pharmacieId, filtres],
    queryFn:          ({ pageParam = 1 }) =>
      produitsService.parPharmacie(pharmacieId, {
        ...filtres,
        page: pageParam as number,
      }),
    getNextPageParam: (last: any, pages: any[]) =>
      last.next ? pages.length + 1 : undefined,
    initialPageParam: 1,
    enabled:          pharmacieId > 0,
    staleTime:        1000 * 60 * 2,
  })

// ─────────────────────────────────────────────────────────────────────────────
// GARDES
// ─────────────────────────────────────────────────────────────────────────────

export const useGardesActives = (ville?: string) =>
  useQuery({
    queryKey:        ["gardes", "actives", ville],
    queryFn:         () => gardesService.actives(ville),
    staleTime:       1000 * 60,
    refetchInterval: 1000 * 60 * 5,
  })

export const useGardesProchaines = (ville?: string) =>
  useQuery({
    queryKey:  ["gardes", "prochaines", ville],
    queryFn:   () => gardesService.prochaines(ville),
    staleTime: 1000 * 60 * 10,
  })

// ─────────────────────────────────────────────────────────────────────────────
// LOCALISATION GPS + GÉOCODAGE INVERSE
// ─────────────────────────────────────────────────────────────────────────────

interface Position {
  lat: number
  lng: number
}

/**
 * Demande la permission GPS, retourne la position et détecte la ville
 * via le géocodage inverse d'Expo Location.
 *
 * Met automatiquement à jour le store (lat, lng, ville).
 */
export const useLocalisation = () => {
  const [position,   setPos]        = useState<Position | null>(null)
  const [ville,      setVilleLocal] = useState<string | null>(null)
  const [permission, setPermission] = useState<boolean | null>(null)
  const [chargement, setChargement] = useState(true)
  const [erreur,     setErreur]     = useState<string | null>(null)

  // Accès au store via sélecteurs stables
  const storeSetPosition = useLocalisationStore((s) => s.setPosition)
  const storeSetVille    = useLocalisationStore((s) => s.setVille)

  useEffect(() => {
    let annule = false

    const demander = async () => {
      try {
        // 1. Demander la permission
        const { status } = await Location.requestForegroundPermissionsAsync()
        if (annule) return

        if (status !== "granted") {
          setPermission(false)
          setChargement(false)
          return
        }

        setPermission(true)

        // 2. Obtenir les coordonnées GPS
        const loc = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        })
        if (annule) return

        const lat = loc.coords.latitude
        const lng = loc.coords.longitude
        const pos = { lat, lng }

        setPos(pos)
        storeSetPosition(lat, lng)

        // 3. Géocodage inverse — obtenir la ville réelle
        try {
          const [adresse] = await Location.reverseGeocodeAsync({ latitude: lat, longitude: lng })
          if (annule) return

          if (adresse) {
            // Priorité : city > district > subregion > region
            const villeDetectee =
              adresse.city        ||
              adresse.district    ||
              adresse.subregion   ||
              adresse.region      ||
              "Position actuelle"

            setVilleLocal(villeDetectee)
            storeSetVille(villeDetectee)
          }
        } catch {
          // Géocodage inverse échoué — garder la ville par défaut du store
        }

      } catch {
        if (!annule) setErreur("Impossible d'obtenir votre position.")
      } finally {
        if (!annule) setChargement(false)
      }
    }

    demander()
    return () => { annule = true }
  }, [])

  return { position, ville, permission, chargement, erreur }
}

/**
 * Hook pour demander manuellement la position actuelle
 * (bouton "Me localiser" sur la carte).
 */
export const useLocalisationManuelle = () => {
  const storeSetPosition = useLocalisationStore((s) => s.setPosition)
  const storeSetVille    = useLocalisationStore((s) => s.setVille)
  const [chargement, setChargement] = useState(false)

  const localiser = useCallback(async () => {
    setChargement(true)
    try {
      const { status } = await Location.requestForegroundPermissionsAsync()
      if (status !== "granted") return null

      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      })

      const lat = loc.coords.latitude
      const lng = loc.coords.longitude

      storeSetPosition(lat, lng)

      // Géocodage inverse
      try {
        const [adresse] = await Location.reverseGeocodeAsync({ latitude: lat, longitude: lng })
        if (adresse) {
          const v = adresse.city || adresse.district || adresse.subregion || "Position actuelle"
          storeSetVille(v)
        }
      } catch {}

      return { lat, lng }
    } catch {
      return null
    } finally {
      setChargement(false)
    }
  }, [storeSetPosition, storeSetVille])

  return { localiser, chargement }
}