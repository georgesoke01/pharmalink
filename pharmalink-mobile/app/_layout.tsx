// app/_layout.tsx
import { useEffect } from "react"
import { Stack, router } from "expo-router"
import { StatusBar } from "expo-status-bar"
import { GestureHandlerRootView } from "react-native-gesture-handler"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { SafeAreaProvider } from "react-native-safe-area-context"
import { useFirstLaunch } from "@/hooks/useFirstLaunch"
import { tokenStorage } from "@/services/api"
import { useAuthStore } from "@/store"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 1000 * 60 * 2 },
  },
})

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar style="auto" />
          <NavigationController />
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  )
}

// ── Contrôleur de navigation initial ─────────────────────────────────────────
// Séparé dans un composant pour pouvoir utiliser les hooks React Query
function NavigationController() {
  const launchState = useFirstLaunch()
  const init        = useAuthStore((s) => s.init)

  useEffect(() => {
    if (launchState === "loading") return

    const navigate = async () => {
      // Charger les tokens JWT en mémoire
      await tokenStorage.init()
      // Restaurer la session utilisateur
      await init()

      // Rediriger selon l'état du premier lancement
      switch (launchState) {
        case "onboarding":
          router.replace("/onboarding")
          break
        case "splash":
          router.replace("/splash")
          break
        case "app":
          router.replace("/(tabs)")
          break
      }
    }

    navigate()
  }, [launchState])

  return (
    <Stack screenOptions={{ headerShown: false, animation: "fade" }}>
      <Stack.Screen name="onboarding"          options={{ headerShown: false, animation: "fade" }} />
      <Stack.Screen name="splash"              options={{ headerShown: false, animation: "fade" }} />
      <Stack.Screen name="(tabs)"              options={{ headerShown: false }} />
      <Stack.Screen name="pharmacie/[id]"      options={{ presentation: "card",  animation: "slide_from_right" }} />
      <Stack.Screen name="produit/[id]"        options={{ presentation: "card",  animation: "slide_from_right" }} />
      <Stack.Screen name="itineraire/[id]"     options={{ presentation: "card",  animation: "slide_from_right" }} />
      <Stack.Screen name="notifications/index" options={{ presentation: "card",  animation: "slide_from_right" }} />
      <Stack.Screen name="auth/connexion"      options={{ presentation: "modal", animation: "slide_from_bottom" }} />
      <Stack.Screen name="auth/inscription"    options={{ presentation: "modal", animation: "slide_from_bottom" }} />
    </Stack>
  )
}