// constants/index.ts — Design system inspiré des maquettes

// Supprime le slash final si présent — évite les doubles slashes dans les URLs
const _rawUrl = process.env.EXPO_PUBLIC_API_URL ?? "https://flexible-lemur-strangely.ngrok-free.app/api/v1"
export const API_BASE_URL = _rawUrl.endsWith("/") ? _rawUrl.slice(0, -1) : _rawUrl

export const Colors = {
  // Vert principal — identité PharmaLink
  primary:        "#1A7A4A",
  primaryLight:   "#2ECC71",
  primaryDark:    "#0F5C34",
  primaryBg:      "#E8F5EE",
 
  // Rouge garde
  danger:         "#E53935",
  dangerBg:       "#FFEBEE",

  // Orange warning
  warning:        "#F59E0B",
  warningBg:      "#FFFBEB",

  // Succès
  success:        "#1A7A4A",

  // Info
  info:           "#2196F3",
  ordonnance:     "#E53935",

  // ── Dark theme (écran carte) ──────────────────────────────────────────────
  dark:           "#1A1F1C",
  darkCard:       "#252B27",
  darkCardLight:  "#2E3530",
  darkBorder:     "#3A4040",
  darkText:       "#FFFFFF",
  darkTextSub:    "#9BA8A0",
  darkPill:       "#2E3530",
  darkPillActive: "#1A7A4A",

  // ── Light theme (fiche, liste) ────────────────────────────────────────────
  white:          "#FFFFFF",
  background:     "#F4F7F5",
  card:           "#FFFFFF",
  border:         "#E8EDEA",

  gray100:        "#F4F7F5",
  gray200:        "#E8EDEA",
  gray300:        "#D1DAD4",
  gray400:        "#9BA8A0",
  gray500:        "#6B7875",
  gray600:        "#4A5550",
  gray700:        "#2E3530",
  gray800:        "#1E2622",
  gray900:        "#0F1410",

  black:          "#0A0F0C",
} as const

export const Typography = {
  xs:        11,
  sm:        13,
  base:      15,
  md:        17,
  lg:        20,
  xl:        24,
  xxl:       30,
  xxxl:      38,
  regular:   "400" as const,
  medium:    "500" as const,
  semibold:  "600" as const,
  bold:      "700" as const,
  extrabold: "800" as const,
} as const

export const Spacing = {
  xs:   4,
  sm:   8,
  md:   12,
  base: 16,
  lg:   20,
  xl:   24,
  xxl:  32,
  xxxl: 48,
} as const

export const BorderRadius = {
  sm:   6,
  md:   10,
  lg:   16,
  xl:   24,
  xxl:  32,
  full: 999,
} as const

export const Shadow = {
  sm: {
    shadowColor:   "#000",
    shadowOffset:  { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius:  4,
    elevation:     2,
  },
  md: {
    shadowColor:   "#000",
    shadowOffset:  { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius:  12,
    elevation:     5,
  },
  lg: {
    shadowColor:   "#000",
    shadowOffset:  { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius:  24,
    elevation:     10,
  },
  dark: {
    shadowColor:   "#000",
    shadowOffset:  { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius:  16,
    elevation:     8,
  },
} as const

export const CARTE_REGION_DEFAUT = {
  latitude:       6.3703,
  longitude:      2.3912,
  latitudeDelta:  0.08,
  longitudeDelta: 0.08,
}

export const RAYON_RECHERCHE_DEFAUT_KM = 2

export const STORAGE_KEYS = {
  ACCESS_TOKEN:  "pharmalink_access_token",
  REFRESH_TOKEN: "pharmalink_refresh_token",
  USER:          "pharmalink_user",
  VILLE_DEFAUT:  "pharmalink_ville_defaut",
} as const