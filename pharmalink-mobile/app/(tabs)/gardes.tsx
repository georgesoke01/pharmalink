// app/(tabs)/gardes.tsx — Pharmacies de garde — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, FlatList, Linking, Platform,
  ActivityIndicator, useColorScheme, Dimensions,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { useGardesActives, useGardesProchaines } from "@/hooks/usePharmacies"
import { useLocalisationStore } from "@/store"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import type { Garde } from "@/types"

const { width } = Dimensions.get("window")

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:           "#FFFFFF",
  title:        "#333333",
  subtitle:     "#666666",
  searchBg:     "#F5F5F5",
  searchBorder: "#E0E0E0",
  searchText:   "#333333",
  searchPH:     "#666666",
  dayBg:        "#F5F5F5",
  dayBorder:    "#E0E0E0",
  dayTxt:       "#666666",
  dayDate:      "#999999",
  dayActiveBg:  "#0066CC",
  filterBg:     "#F5F5F5",
  filterBorder: "#E0E0E0",
  filterTxt:    "#666666",
  filterActiveBg: "#0066CC",
  statsBorder:  "#F0F0F0",
  statsTxt:     "#666666",
  cardBg:       "#FFFFFF",
  cardBorder:   "#F0F0F0",
  cardName:     "#333333",
  cardAddr:     "#666666",
  cardMeta:     "#666666",
  cardFootBrd:  "#F0F0F0",
  zoneBg:       "#F0F0F0",
  zoneTxt:      "#666666",
  itiBorder:    "#F0F0F0",
}

const darkTheme = {
  bg:           "#1A1A1A",
  title:        "#FFFFFF",
  subtitle:     "#999999",
  searchBg:     "#333333",
  searchBorder: "#444444",
  searchText:   "#FFFFFF",
  searchPH:     "#999999",
  dayBg:        "#333333",
  dayBorder:    "#444444",
  dayTxt:       "#CCCCCC",
  dayDate:      "#999999",
  dayActiveBg:  "#0066CC",
  filterBg:     "#333333",
  filterBorder: "#444444",
  filterTxt:    "#999999",
  filterActiveBg: "#0066CC",
  statsBorder:  "#333333",
  statsTxt:     "#999999",
  cardBg:       "#2D2D2D",
  cardBorder:   "#444444",
  cardName:     "#FFFFFF",
  cardAddr:     "#999999",
  cardMeta:     "#999999",
  cardFootBrd:  "#444444",
  zoneBg:       "#333333",
  zoneTxt:      "#999999",
  itiBorder:    "#444444",
}

// ── Données statiques ─────────────────────────────────────────────────────────
const JOURS = [
  { id: "today",    label: "Aujourd'hui", date: "19 mars" },
  { id: "tomorrow", label: "Demain",      date: "20 mars" },
  { id: "sunday",   label: "Dimanche",    date: "21 mars" },
]

const FILTRES = [
  { id: "all",    label: "Toutes",    icon: "apps" },
  { id: "night",  label: "De nuit",   icon: "moon" },
  { id: "24h",    label: "24h/24",    icon: "time" },
  { id: "sunday", label: "Dimanche",  icon: "calendar" },
]

const GARDE_COLORS: Record<string, string> = {
  "24h":    "#4CAF50",
  night:    "#2196F3",
  sunday:   "#FF9800",
  default:  "#9C27B0",
}

export default function EcranGardes() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const { ville }          = useLocalisationStore()
  const [search,    setSearch]    = useState("")
  const [jourActif, setJourActif] = useState("today")
  const [filtre,    setFiltre]    = useState("all")

  const { data: gA, isLoading: lA, refetch: rA } = useGardesActives(ville)
  const { data: gP, isLoading: lP }               = useGardesProchaines(ville)

  // Sélection des données selon le jour choisi
  const gardes: Garde[] = (
    jourActif === "today"
      ? gA?.results
      : gP?.results
  ) ?? []

  const isLoading = jourActif === "today" ? lA : lP

  // Filtrage par type de garde
  const gardesFiltrees = gardes.filter((g) => {
    if (filtre === "all")    return true
    if (filtre === "night")  return !g.est_active_maintenant
    if (filtre === "24h")    return g.note?.toLowerCase().includes("24")
    if (filtre === "sunday") return g.zone_quartier?.toLowerCase().includes("dim")
    return true
  })

  const fmt = (iso: string) =>
    new Date(iso).toLocaleString("fr-FR", {
      day: "numeric", month: "short",
      hour: "2-digit", minute: "2-digit",
    })

  const getGardeType = (g: Garde) =>
    g.note?.toLowerCase().includes("24") ? "24h"
    : g.est_active_maintenant ? "night"
    : "sunday"

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.titre, { color: T.title }]}>
            Pharmacies de garde
          </Text>
          <Text style={[styles.sousTitre, { color: T.subtitle }]}>
            Trouvez une pharmacie ouverte
          </Text>
        </View>
        <TouchableOpacity style={[styles.themeBtn, { backgroundColor: T.searchBg }]}>
          <Ionicons
            name={isDark ? "sunny-outline" : "moon-outline"}
            size={20}
            color={isDark ? "#FFD700" : T.subtitle}
          />
        </TouchableOpacity>
      </View>

      {/* ── Recherche ─────────────────────────────────────────────────── */}
      <View style={[styles.searchBox, {
        backgroundColor: T.searchBg, borderColor: T.searchBorder,
      }]}>
        <Ionicons name="search" size={20} color={T.searchPH} />
        <TextInput
          style={[styles.searchInput, { color: T.searchText }]}
          placeholder="Rechercher une pharmacie de garde..."
          placeholderTextColor={T.searchPH}
          value={search}
          onChangeText={setSearch}
        />
        {search.length > 0 && (
          <TouchableOpacity onPress={() => setSearch("")}>
            <Ionicons name="close-circle" size={18} color={T.searchPH} />
          </TouchableOpacity>
        )}
      </View>

      {/* ── Sélecteur de jours ────────────────────────────────────────── */}
      <FlatList
        data={JOURS}
        horizontal
        keyExtractor={(item) => item.id}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.joursRow}
        renderItem={({ item }) => {
          const actif = jourActif === item.id
          return (
            <TouchableOpacity
              style={[styles.jourChip, {
                backgroundColor: actif ? T.dayActiveBg : T.dayBg,
                borderColor:     actif ? T.dayActiveBg : T.dayBorder,
              }]}
              onPress={() => setJourActif(item.id)}
            >
              <Text style={[
                styles.jourLabel,
                { color: actif ? "#FFFFFF" : T.dayTxt },
              ]}>
                {item.label}
              </Text>
              <Text style={[
                styles.jourDate,
                { color: actif ? "rgba(255,255,255,0.85)" : T.dayDate },
              ]}>
                {item.date}
              </Text>
            </TouchableOpacity>
          )
        }}
      />

      {/* ── Filtres type de garde ─────────────────────────────────────── */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filtresRow}
      >
        {FILTRES.map((f) => {
          const actif = filtre === f.id
          return (
            <TouchableOpacity
              key={f.id}
              style={[styles.filtreChip, {
                backgroundColor: actif ? T.filterActiveBg : T.filterBg,
                borderColor:     actif ? T.filterActiveBg : T.filterBorder,
              }]}
              onPress={() => setFiltre(f.id)}
            >
              <Ionicons
                name={f.icon as any}
                size={16}
                color={actif ? "#FFFFFF" : T.filterTxt}
              />
              <Text style={[
                styles.filtreTxt,
                { color: actif ? "#FFFFFF" : T.filterTxt },
              ]}>
                {f.label}
              </Text>
            </TouchableOpacity>
          )
        })}
      </ScrollView>

      {/* ── Stats + bouton carte ──────────────────────────────────────── */}
      <View style={[styles.statsRow, { borderBottomColor: T.statsBorder }]}>
        <Text style={[styles.statsTxt, { color: T.statsTxt }]}>
          {isLoading
            ? "Recherche..."
            : `${gardesFiltrees.length} pharmacie${gardesFiltrees.length !== 1 ? "s" : ""} de garde trouvée${gardesFiltrees.length !== 1 ? "s" : ""}`}
        </Text>
        <TouchableOpacity
          style={styles.voirCarteBtn}
          onPress={() => router.push("/(tabs)")}
        >
          <Ionicons name="map" size={18} color="#0066CC" />
          <Text style={styles.voirCarteTxt}>Voir sur la carte</Text>
        </TouchableOpacity>
      </View>

      {/* ── Liste ─────────────────────────────────────────────────────── */}
      <FlatList
        data={gardesFiltrees.filter((g) =>
          search.length === 0 ||
          g.pharmacie_nom.toLowerCase().includes(search.toLowerCase()) ||
          g.pharmacie_adresse.toLowerCase().includes(search.toLowerCase())
        )}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <GardeCard
            garde={item}
            T={T}
            isDark={isDark}
            gardeType={getGardeType(item)}
            fmt={fmt}
          />
        )}
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.vide}>
              <Ionicons name="medical-outline" size={56} color={T.statsTxt} />
              <Text style={[styles.videText, { color: T.subtitle }]}>
                Aucune pharmacie de garde trouvée
              </Text>
              <Text style={[styles.videSubText, { color: T.statsTxt }]}>
                à {ville}
              </Text>
            </View>
          ) : (
            <ActivityIndicator color={Colors.primary} style={{ marginTop: 40 }} />
          )
        }
      />
    </SafeAreaView>
  )
}

// ── Carte pharmacie de garde ──────────────────────────────────────────────────
function GardeCard({
  garde, T, isDark, gardeType, fmt,
}: {
  garde:     Garde
  T:         typeof lightTheme
  isDark:    boolean
  gardeType: string
  fmt:       (iso: string) => string
}) {
  const gardeColor = GARDE_COLORS[gardeType] ?? GARDE_COLORS.default

  const appeler = () => {
    if (garde.telephone_effectif)
      Linking.openURL(`tel:${garde.telephone_effectif}`)
  }

  const itineraire = () => {
    // Navigation vers la fiche pour l'itinéraire
    router.push(`/pharmacie/${garde.pharmacie}`)
  }

  return (
    <TouchableOpacity
      style={[styles.card, {
        backgroundColor: T.cardBg,
        borderColor:     T.cardBorder,
      }]}
      onPress={() => router.push(`/pharmacie/${garde.pharmacie}`)}
      activeOpacity={0.85}
    >
      {/* ── En-tête : nom + badge ────────────────────────────────────── */}
      <View style={styles.cardHeader}>
        <View style={styles.cardNameRow}>
          <Text style={[styles.cardName, { color: T.cardName }]} numberOfLines={1}>
            {garde.pharmacie_nom}
          </Text>
          {!isDark && (
            <View style={[styles.ratingBox, { backgroundColor: T.searchBg }]}>
              <Ionicons name="star" size={12} color="#FFD700" />
              <Text style={[styles.ratingTxt, { color: T.cardMeta }]}>4.5</Text>
            </View>
          )}
        </View>

        <View style={[styles.gardeBadge, { backgroundColor: gardeColor }]}>
          <Ionicons
            name={gardeType === "24h" ? "time" : "shield"}
            size={10}
            color="#FFFFFF"
          />
          <Text style={styles.gardeBadgeTxt}>
            {gardeType === "24h" ? "24h" : "GARDE"}
          </Text>
        </View>
      </View>

      {/* ── Adresse ─────────────────────────────────────────────────── */}
      <Text style={[styles.cardAddr, { color: T.cardAddr }]} numberOfLines={1}>
        {garde.pharmacie_adresse}
      </Text>

      {/* ── Détails ─────────────────────────────────────────────────── */}
      <View style={styles.cardDetails}>
        <View style={styles.detailItem}>
          <Ionicons name="location-outline" size={14} color={T.cardMeta} />
          <Text style={[styles.detailTxt, { color: T.cardMeta }]}>~0.8 km</Text>
        </View>

        {!isDark && garde.telephone_effectif && (
          <View style={styles.detailItem}>
            <Ionicons name="call-outline" size={14} color={T.cardMeta} />
            <Text style={[styles.detailTxt, { color: T.cardMeta }]}>
              {garde.telephone_effectif}
            </Text>
          </View>
        )}

        <View style={styles.detailItem}>
          <Ionicons name="time-outline" size={14} color={T.cardMeta} />
          <Text style={[styles.detailTxt, { color: T.cardMeta }]}>
            {gardeType === "24h"
              ? "24h/24"
              : `${fmt(garde.date_debut)} → ${fmt(garde.date_fin)}`}
          </Text>
        </View>
      </View>

      {/* ── Footer light : zone + itinéraire ────────────────────────── */}
      {!isDark && (
        <View style={[styles.cardFoot, { borderTopColor: T.cardFootBrd }]}>
          <View style={[styles.zoneTag, { backgroundColor: T.zoneBg }]}>
            <Text style={[styles.zoneTxt, { color: T.zoneTxt }]}>
              {garde.zone_quartier || garde.zone_ville || "Centre"}
            </Text>
          </View>
          <TouchableOpacity style={styles.itiBtn} onPress={itineraire}>
            <Text style={styles.itiTxt}>Itinéraire</Text>
            <Ionicons name="navigate" size={16} color="#0066CC" />
          </TouchableOpacity>
        </View>
      )}

      {/* ── Footer dark : itinéraire seul ────────────────────────────── */}
      {isDark && (
        <TouchableOpacity
          style={[styles.darkItiRow, { borderTopColor: T.cardFootBrd }]}
          onPress={itineraire}
        >
          <Text style={styles.itiTxt}>Itinéraire</Text>
          <Ionicons name="navigate" size={16} color="#0066CC" />
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  // Header
  header: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.base,
    paddingVertical:   Spacing.md,
  },
  titre:    { fontSize: Typography.xl, fontWeight: Typography.bold },
  sousTitre:{ fontSize: Typography.sm, marginTop: 2 },
  themeBtn: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
  },

  // Recherche
  searchBox: {
    flexDirection:   "row",
    alignItems:      "center",
    marginHorizontal: Spacing.base,
    marginBottom:    Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical:   11,
    borderRadius:    BorderRadius.lg,
    borderWidth:     1,
    gap:             Spacing.sm,
  },
  searchInput: { flex: 1, fontSize: Typography.base, padding: 0 },

  // Jours
  joursRow: {
    paddingHorizontal: Spacing.base,
    gap:               Spacing.sm,
    marginBottom:      Spacing.sm,
    flexDirection:     "row",
  },
  jourChip: {
    paddingHorizontal: Spacing.base,
    paddingVertical:   Spacing.sm,
    borderRadius:      BorderRadius.md,
    borderWidth:       1,
    alignItems:        "center",
    minWidth:          90,
  },
  jourLabel:{ fontSize: Typography.sm, fontWeight: Typography.semibold },
  jourDate: { fontSize: Typography.xs, marginTop: 2 },

  // Filtres
  filtresRow: {
    paddingHorizontal: Spacing.base,
    gap:               Spacing.sm,
    marginBottom:      Spacing.sm,
    flexDirection:     "row",
  },
  filtreChip: {
    flexDirection:   "row",
    alignItems:      "center",
    gap:             5,
    paddingHorizontal: 13,
    paddingVertical:   8,
    borderRadius:    BorderRadius.full,
    borderWidth:     1,
  },
  filtreTxt: { fontSize: Typography.sm },

  // Stats
  statsRow: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.base,
    paddingVertical:   Spacing.sm,
    borderBottomWidth: 1,
    marginBottom:      Spacing.sm,
  },
  statsTxt:    { fontSize: Typography.sm },
  voirCarteBtn:{ flexDirection: "row", alignItems: "center", gap: 4 },
  voirCarteTxt:{ fontSize: Typography.sm, color: "#0066CC", fontWeight: Typography.semibold },

  // Liste
  list: { paddingHorizontal: Spacing.base, paddingBottom: 100 },

  // Card
  card: {
    borderRadius: BorderRadius.lg,
    padding:      Spacing.base,
    marginBottom: Spacing.md,
    borderWidth:  1,
    ...Shadow.sm,
  },
  cardHeader:  {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    marginBottom:   Spacing.xs,
  },
  cardNameRow: {
    flex:          1,
    flexDirection: "row",
    alignItems:    "center",
    gap:           Spacing.xs,
    marginRight:   Spacing.sm,
  },
  cardName:  { fontSize: Typography.base, fontWeight: Typography.semibold, flex: 1 },
  ratingBox: {
    flexDirection: "row", alignItems: "center",
    gap: 2, paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  ratingTxt: { fontSize: Typography.xs, fontWeight: Typography.semibold },
  gardeBadge:{
    flexDirection: "row", alignItems: "center",
    gap: 3, paddingHorizontal: 8, paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  gardeBadgeTxt: { color: "#FFFFFF", fontSize: 10, fontWeight: Typography.bold },

  cardAddr:    { fontSize: Typography.xs, marginBottom: Spacing.sm },
  cardDetails: {
    flexDirection: "row", flexWrap: "wrap",
    gap: Spacing.md, marginBottom: Spacing.sm,
  },
  detailItem:  { flexDirection: "row", alignItems: "center", gap: 4 },
  detailTxt:   { fontSize: Typography.xs },

  // Footer
  cardFoot: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    paddingTop:     Spacing.sm,
    borderTopWidth: 1,
    marginTop:      Spacing.xs,
  },
  zoneTag:   {
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: BorderRadius.sm,
  },
  zoneTxt:   { fontSize: Typography.xs },
  itiBtn:    { flexDirection: "row", alignItems: "center", gap: 4 },
  itiTxt:    { fontSize: Typography.sm, fontWeight: Typography.semibold, color: "#0066CC" },
  darkItiRow:{
    flexDirection: "row", alignItems: "center",
    justifyContent: "flex-end", gap: 4,
    paddingTop: Spacing.sm, borderTopWidth: 1, marginTop: Spacing.xs,
  },

  // Vide
  vide:        { alignItems: "center", paddingTop: 60, gap: Spacing.sm },
  videText:    { fontSize: Typography.base, fontWeight: Typography.semibold, textAlign: "center" },
  videSubText: { fontSize: Typography.sm, textAlign: "center" },
})