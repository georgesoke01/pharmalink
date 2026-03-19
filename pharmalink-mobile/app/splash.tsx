// app/splash.tsx — Écran de démarrage animé (Light + Dark)
// Inspiré des maquettes fournies
import { useEffect, useRef, useState } from "react"
import {
  View, Text, StyleSheet, Animated, Easing,
  useColorScheme, Dimensions, StatusBar,
} from "react-native"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { tokenStorage } from "@/services/api"
import { useAuthStore } from "@/store"
import { markSplashSeenToday } from "@/hooks/useFirstLaunch"

const { width } = Dimensions.get("window")

// ── Étapes de chargement ──────────────────────────────────────────────────────
const ETAPES = [
  { label: "Initialisation...",            pct: 15,  duree: 400 },
  { label: "Chargement des données...",    pct: 35,  duree: 500 },
  { label: "Localisation en cours...",     pct: 60,  duree: 600 },
  { label: "Localizing pharmacies nearby...", pct: 80, duree: 500 },
  { label: "Prêt !",                       pct: 100, duree: 300 },
]

export default function SplashScreen() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const theme       = isDark ? DARK : LIGHT

  const init    = useAuthStore((s) => s.init)

  // Animations
  const logoScale   = useRef(new Animated.Value(0)).current
  const logoOpacity = useRef(new Animated.Value(0)).current
  const titleY      = useRef(new Animated.Value(30)).current
  const titleOpacity= useRef(new Animated.Value(0)).current
  const barOpacity  = useRef(new Animated.Value(0)).current
  const barWidth    = useRef(new Animated.Value(0)).current
  const badgeOpacity= useRef(new Animated.Value(0)).current
  const badgeY      = useRef(new Animated.Value(20)).current

  const [etapeIndex, setEtapeIndex] = useState(0)
  const [pct,        setPct]        = useState(0)

  useEffect(() => {
    // 1. Init tokens + session
    tokenStorage.init().then(() => init())

    // 2. Animation d'entrée séquencée
    Animated.sequence([
      // Logo pop-in
      Animated.parallel([
        Animated.spring(logoScale, {
          toValue: 1, tension: 60, friction: 8,
          useNativeDriver: true,
        }),
        Animated.timing(logoOpacity, {
          toValue: 1, duration: 400,
          useNativeDriver: true,
        }),
      ]),

      // Titre slide up
      Animated.parallel([
        Animated.timing(titleY, {
          toValue: 0, duration: 500,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(titleOpacity, {
          toValue: 1, duration: 500,
          useNativeDriver: true,
        }),
      ]),

      // Barre de progression fade in
      Animated.timing(barOpacity, {
        toValue: 1, duration: 300,
        useNativeDriver: true,
      }),
    ]).start()

    // Badge "Secure & Verified" avec délai
    Animated.sequence([
      Animated.delay(600),
      Animated.parallel([
        Animated.timing(badgeOpacity, {
          toValue: 1, duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(badgeY, {
          toValue: 0, duration: 500,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]),
    ]).start()

    // 3. Progression séquencée
    let index = 0
    const avancer = () => {
      if (index >= ETAPES.length) return
      const etape = ETAPES[index]

      setEtapeIndex(index)
      setPct(etape.pct)

      Animated.timing(barWidth, {
        toValue: (etape.pct / 100) * (width - 80),
        duration: etape.duree,
        easing: Easing.out(Easing.quad),
        useNativeDriver: false,
      }).start()

      index++
      if (index < ETAPES.length) {
        setTimeout(avancer, etape.duree + 100)
      } else {
        // Navigation vers l'app principale
        setTimeout(async () => {
          await markSplashSeenToday()
          router.replace("/(tabs)")
        }, 600)
      }
    }

    setTimeout(avancer, 800)
  }, [])

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <StatusBar
        barStyle={isDark ? "light-content" : "dark-content"}
        backgroundColor={theme.bg}
      />

      {/* ── Lignes verticales décoratives (light only) ─────────────────── */}
      {!isDark && <GridLines />}

      {/* ── Carte en arrière-plan (dark only) ─────────────────────────── */}
      {isDark && <MapOverlay />}

      {/* ── Logo ──────────────────────────────────────────────────────── */}
      <View style={styles.topSection}>
        <Animated.View style={[
          styles.logoWrap,
          { backgroundColor: theme.logoBg },
          {
            transform: [{ scale: logoScale }],
            opacity:    logoOpacity,
          },
        ]}>
          <View style={[styles.logoBox, { backgroundColor: theme.logoBox }]}>
            <Ionicons name="medkit" size={42} color={theme.logoIcon} />
          </View>
        </Animated.View>

        {/* ── Titre ────────────────────────────────────────────────── */}
        <Animated.View style={[
          styles.titleWrap,
          {
            transform:  [{ translateY: titleY }],
            opacity:     titleOpacity,
          },
        ]}>
          <Text style={[styles.appName, { color: theme.title }]}>
            PharmaLoc
          </Text>
          <Text style={[styles.tagline, { color: theme.tagline }]}>
            YOUR NEIGHBORHOOD PHARMACY FINDER
          </Text>
        </Animated.View>
      </View>

      {/* ── Barre de progression ──────────────────────────────────────── */}
      <Animated.View style={[styles.progressSection, { opacity: barOpacity }]}>
        <View style={styles.progressHeader}>
          <Text style={[styles.progressLabel, { color: theme.progressLabel }]}>
            {ETAPES[etapeIndex]?.label ?? ""}
          </Text>
          <Text style={[styles.progressPct, { color: theme.accent }]}>
            {pct}%
          </Text>
        </View>

        {/* Track */}
        <View style={[styles.progressTrack, { backgroundColor: theme.trackBg }]}>
          <Animated.View
            style={[
              styles.progressBar,
              {
                width:           barWidth,
                backgroundColor: theme.accent,
              },
            ]}
          />
        </View>
      </Animated.View>

      {/* ── Badge "Secure & Verified" ─────────────────────────────────── */}
      <Animated.View style={[
        styles.badge,
        { backgroundColor: theme.badgeBg, borderColor: theme.badgeBorder },
        {
          opacity:   badgeOpacity,
          transform: [{ translateY: badgeY }],
        },
      ]}>
        <Ionicons name="shield-checkmark" size={16} color={theme.accent} />
        <Text style={[styles.badgeText, { color: theme.badgeText }]}>
          SECURE & VERIFIED
        </Text>
      </Animated.View>
    </View>
  )
}

// ── Lignes verticales décoratives (mode clair) ────────────────────────────────
function GridLines() {
  return (
    <View style={StyleSheet.absoluteFillObject} pointerEvents="none">
      {Array.from({ length: 9 }).map((_, i) => (
        <View
          key={i}
          style={[
            styles.gridLine,
            { left: `${(i + 1) * 10}%` as any },
          ]}
        />
      ))}
    </View>
  )
}

// ── Carte en arrière-plan semi-transparente (mode sombre) ─────────────────────
function MapOverlay() {
  return (
    <View style={styles.mapOverlay} pointerEvents="none">
      {/* Simulation de la carte avec des formes géométriques */}
      <View style={styles.mapLine1} />
      <View style={styles.mapLine2} />
      <View style={styles.mapLine3} />
      <View style={styles.mapCircle1} />
      <View style={styles.mapCircle2} />
      {/* Dégradé assombri */}
      <View style={styles.mapDarken} />
    </View>
  )
}

// ── Thèmes ────────────────────────────────────────────────────────────────────
const LIGHT = {
  bg:            "#EFF3F0",
  logoBg:        "rgba(26, 122, 74, 0.10)",
  logoBox:       "#1A7A4A",
  logoIcon:      "#FFFFFF",
  title:         "#0F1A14",
  tagline:       "#6B7875",
  accent:        "#1A7A4A",
  progressLabel: "#2E3530",
  trackBg:       "rgba(26, 122, 74, 0.15)",
  badgeBg:       "#FFFFFF",
  badgeBorder:   "rgba(26, 122, 74, 0.2)",
  badgeText:     "#2E3530",
}

const DARK = {
  bg:            "#0A0F0C",
  logoBg:        "rgba(26, 122, 74, 0.15)",
  logoBox:       "#1A7A4A",
  logoIcon:      "#FFFFFF",
  title:         "#FFFFFF",
  tagline:       "#9BA8A0",
  accent:        "#2ECC71",
  progressLabel: "#FFFFFF",
  trackBg:       "rgba(46, 204, 113, 0.15)",
  badgeBg:       "rgba(46, 204, 113, 0.08)",
  badgeBorder:   "rgba(46, 204, 113, 0.2)",
  badgeText:     "#9BA8A0",
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems:     "center",
    justifyContent: "space-between",
    paddingVertical: 64,
    paddingHorizontal: 40,
  },

  // Top section
  topSection: {
    flex: 1,
    alignItems:     "center",
    justifyContent: "center",
    gap: 28,
    width: "100%",
  },

  // Logo
  logoWrap: {
    width:         120,
    height:        120,
    borderRadius:  28,
    alignItems:    "center",
    justifyContent:"center",
  },
  logoBox: {
    width:         80,
    height:        80,
    borderRadius:  18,
    alignItems:    "center",
    justifyContent:"center",
  },

  // Titre
  titleWrap: {
    alignItems: "center",
    gap: 8,
  },
  appName: {
    fontSize:   42,
    fontWeight: "800",
    letterSpacing: -1,
  },
  tagline: {
    fontSize:      11,
    fontWeight:    "600",
    letterSpacing: 2.5,
    textAlign:     "center",
  },

  // Barre de progression
  progressSection: {
    width: "100%",
    gap:   10,
    marginBottom: 40,
  },
  progressHeader: {
    flexDirection:  "row",
    justifyContent: "space-between",
    alignItems:     "center",
  },
  progressLabel: {
    fontSize:   13,
    fontWeight: "500",
  },
  progressPct: {
    fontSize:   13,
    fontWeight: "700",
  },
  progressTrack: {
    width:        "100%",
    height:       6,
    borderRadius: 3,
    overflow:     "hidden",
  },
  progressBar: {
    height:       6,
    borderRadius: 3,
  },

  // Badge
  badge: {
    flexDirection:  "row",
    alignItems:     "center",
    gap:            8,
    paddingHorizontal: 24,
    paddingVertical:   12,
    borderRadius:   999,
    borderWidth:    1,
  },
  badgeText: {
    fontSize:      12,
    fontWeight:    "600",
    letterSpacing: 1.5,
  },

  // Lignes grille (light)
  gridLine: {
    position:  "absolute",
    top:       0,
    bottom:    0,
    width:     1,
    backgroundColor: "rgba(26, 122, 74, 0.06)",
  },

  // Map overlay (dark)
  mapOverlay: {
    ...StyleSheet.absoluteFillObject,
    overflow: "hidden",
  },
  mapLine1: {
    position:        "absolute",
    bottom:          200,
    left:            -40,
    right:           -40,
    height:          2,
    backgroundColor: "rgba(46, 204, 113, 0.08)",
    transform:       [{ rotate: "-8deg" }],
  },
  mapLine2: {
    position:        "absolute",
    bottom:          240,
    left:            -40,
    right:           -40,
    height:          1,
    backgroundColor: "rgba(46, 204, 113, 0.05)",
    transform:       [{ rotate: "-8deg" }],
  },
  mapLine3: {
    position:        "absolute",
    bottom:          280,
    left:            -40,
    right:           -40,
    height:          1,
    backgroundColor: "rgba(46, 204, 113, 0.05)",
    transform:       [{ rotate: "-8deg" }],
  },
  mapCircle1: {
    position:        "absolute",
    bottom:          160,
    left:            width * 0.3,
    width:           80,
    height:          80,
    borderRadius:    40,
    borderWidth:     1,
    borderColor:     "rgba(46, 204, 113, 0.08)",
  },
  mapCircle2: {
    position:        "absolute",
    bottom:          220,
    right:           width * 0.2,
    width:           50,
    height:          50,
    borderRadius:    25,
    borderWidth:     1,
    borderColor:     "rgba(46, 204, 113, 0.06)",
  },
  mapDarken: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(10, 15, 12, 0.85)",
  },
})