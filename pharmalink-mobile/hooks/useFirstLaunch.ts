// hooks/useFirstLaunch.ts
// Gère la logique de premier lancement de l'application
// - Premier lancement → Onboarding → Splash → App
// - Lancements suivants → Splash → App (uniquement si nouvelle session)
// - Si déjà connecté → App directement

import { useState, useEffect } from "react"
import AsyncStorage from "@react-native-async-storage/async-storage"

const KEY_ONBOARDING = "pharmalink_onboarding_done"
const KEY_SPLASH_DATE = "pharmalink_splash_last_date"

type LaunchState = "loading" | "onboarding" | "splash" | "app"

export const useFirstLaunch = () => {
  const [state, setState] = useState<LaunchState>("loading")

  useEffect(() => {
    const check = async () => {
      try {
        // 1. Vérifier si l'onboarding a déjà été vu
        const onboardingDone = await AsyncStorage.getItem(KEY_ONBOARDING)

        if (!onboardingDone) {
          // Première ouverture absolue → onboarding
          setState("onboarding")
          return
        }

        // 2. Vérifier si le splash a déjà été montré aujourd'hui
        const lastSplashDate = await AsyncStorage.getItem(KEY_SPLASH_DATE)
        const today          = new Date().toDateString()

        if (lastSplashDate !== today) {
          // Nouvelle session (nouveau jour ou premier lancement du jour) → splash
          setState("splash")
          return
        }

        // 3. Session déjà active aujourd'hui → aller directement à l'app
        setState("app")
      } catch {
        // En cas d'erreur, afficher le splash par défaut
        setState("splash")
      }
    }

    check()
  }, [])

  return state
}

/** Marquer l'onboarding comme terminé — appeler à la fin de l'onboarding */
export const markOnboardingDone = async () => {
  await AsyncStorage.setItem(KEY_ONBOARDING, "true")
}

/** Marquer le splash comme vu aujourd'hui — appeler à la fin du splash */
export const markSplashSeenToday = async () => {
  await AsyncStorage.setItem(KEY_SPLASH_DATE, new Date().toDateString())
}