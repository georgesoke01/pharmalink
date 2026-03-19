// app/(tabs)/liste.tsx — Liste pharmacies — Light & Dark
import { useState, useCallback } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, FlatList, RefreshControl, ActivityIndicator,
  Linking, Platform, useColorScheme,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { usePharmacies } from "@/hooks/usePharmacies"
import { useFiltresStore } from "@/store"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import type { Pharmacie } from "@/types"

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:           "#FFFFFF",
  headerBg:     "#FFFFFF",
  headerBorder: "#F0F0F0",
  title:        "#333333",
  subtitle:     "#666666",
  searchBg:     "#F5F5F5",
  searchBorder: "#E0E0E0",
  searchText:   "#333333",
  searchPH:     "#666666",
  chipBg:       "#F0F0F0",
  chipBorder:   "#E0E0E0",
  chipText:     "#666666",
  chipActiveBg: Colors.primary,
  cardBg:       "#FFFFFF",
  cardBorder:   "#F0F0F0",
  cardName:     "#333333",
  cardAddr:     "#666666",
  cardMeta:     "#666666",
  divider:      "#F0F0F0",
  navBg:        "#FFFFFF",
  navBorder:    "#F0F0F0",
  navActive:    "#0066CC",
  navInactive:  "#666666",
  ratingBg:     "#F5F5F5",
  ratingText:   "#666666",
  itiBorder:    "#F0F0F0",
}

const darkTheme = {
  bg:           "#1A1A1A",
  headerBg:     "#1A1A1A",
  headerBorder: "#333333",
  title:        "#FFFFFF",
  subtitle:     "#999999",
  searchBg:     "#333333",
  searchBorder: "#444444",
  searchText:   "#FFFFFF",
  searchPH:     "#999999",
  chipBg:       "#333333",
  chipBorder:   "#444444",
  chipText:     "#FFFFFF",
  chipActiveBg: Colors.primary,
  cardBg:       "#2D2D2D",
  cardBorder:   "#444444",
  cardName:     "#FFFFFF",
  cardAddr:     "#999999",
  cardMeta:     "#999999",
  divider:      "#444444",
  navBg:        "#2D2D2D",
  navBorder:    "#444444",
  navActive:    "#0066CC",
  navInactive:  "#999999",
  ratingBg:     "#333333",
  ratingText:   "#999999",
  itiBorder:    "#444444",
}

// ── Filtres ───────────────────────────────────────────────────────────────────
const FILTRES_LIGHT = [
  { key: "toutes",    label: "Toutes",          icon: "apps" },
  { key: "ouvert",    label: "Ouvert maintenant",icon: "time" },
  { key: "garde",     label: "De garde",         icon: "shield" },
]

const FILTRES_DARK = [
  { key: "ouvert",    label: "Ouvert",   icon: "time" },
  { key: "garde",     label: "De garde", icon: "shield" },
  { key: "proximite", label: "Proximité",icon: "navigate" },
]

export default function EcranListe() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const {
    rechercheTexte, setRecherche,
    filtreOuvert,   setFiltreOuvert,
    filtreGarde,    setFiltreGarde,
    reset,
  } = useFiltresStore()

  const [filtreActif, setFiltreActif] = useState(isDark ? "ouvert" : "toutes")

  const filtres = {
    search:       rechercheTexte || undefined,
    est_ouverte:  filtreOuvert || undefined,
    est_de_garde: filtreGarde  || undefined,
    page_size:    20,
  }

  const {
    data, isLoading, fetchNextPage,
    hasNextPage, refetch, isFetchingNextPage,
  } = usePharmacies(filtres)

  const pharmacies = data?.pages.flatMap((p) => p.results) ?? []
  const total      = data?.pages[0]?.count ?? 0

  const handleFiltre = (key: string) => {
    setFiltreActif(key)
    setFiltreOuvert(key === "ouvert")
    setFiltreGarde(key === "garde")
    if (key === "toutes") reset()
  }

  const FILTRES = isDark ? FILTRES_DARK : FILTRES_LIGHT

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <View style={[styles.header, {
        backgroundColor: T.headerBg,
        borderBottomColor: T.headerBorder,
      }]}>
        <View style={styles.headerTop}>
          <Text style={[styles.titre, { color: T.title }]}>
            {isDark ? "PharmaLoc" : "Pharmacies"}
          </Text>
          <TouchableOpacity
            style={[styles.themeBtn, { backgroundColor: T.searchBg }]}
            onPress={() => {/* géré automatiquement par le système */}}
          >
            <Ionicons
              name={isDark ? "sunny" : "moon"}
              size={18}
              color={isDark ? "#FFD700" : T.navInactive}
            />
          </TouchableOpacity>
        </View>

        {/* Barre de recherche */}
        <View style={[styles.searchBox, {
          backgroundColor: T.searchBg,
          borderColor:     T.searchBorder,
        }]}>
          <Ionicons name="search" size={20} color={T.searchPH} />
          <TextInput
            style={[styles.searchInput, { color: T.searchText }]}
            placeholder="Rechercher une pharmacie..."
            placeholderTextColor={T.searchPH}
            value={rechercheTexte}
            onChangeText={setRecherche}
          />
          {rechercheTexte.length > 0 && (
            <TouchableOpacity onPress={() => setRecherche("")}>
              <Ionicons name="close-circle" size={18} color={T.searchPH} />
            </TouchableOpacity>
          )}
        </View>

        {/* Chips filtres */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipsRow}
        >
          {FILTRES.map((f) => {
            const actif = filtreActif === f.key
            return (
              <TouchableOpacity
                key={f.key}
                style={[styles.chip, {
                  backgroundColor: actif ? T.chipActiveBg : T.chipBg,
                  borderColor:     actif ? T.chipActiveBg : T.chipBorder,
                }]}
                onPress={() => handleFiltre(f.key)}
              >
                <Ionicons
                  name={f.icon as any}
                  size={13}
                  color={actif ? "#FFFFFF" : T.chipText}
                />
                <Text style={[styles.chipText, {
                  color: actif ? "#FFFFFF" : T.chipText,
                }]}>
                  {f.label}
                </Text>
              </TouchableOpacity>
            )
          })}
        </ScrollView>
      </View>

      {/* ── Compteur ──────────────────────────────────────────────────────── */}
      <FlatList
        data={pharmacies}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={[styles.list, { paddingBottom: 100 }]}
        showsVerticalScrollIndicator={false}
        onEndReached={() => hasNextPage && fetchNextPage()}
        onEndReachedThreshold={0.3}
        refreshControl={
          <RefreshControl
            refreshing={isLoading && pharmacies.length > 0}
            onRefresh={refetch}
            tintColor={Colors.primary}
          />
        }
        ListHeaderComponent={
          <Text style={[styles.compteur, { color: T.subtitle }]}>
            {isLoading
              ? "Recherche en cours..."
              : `${total} résultat${total > 1 ? "s" : ""}`}
          </Text>
        }
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.vide}>
              <Ionicons name="search-outline" size={48} color={T.subtitle} />
              <Text style={[styles.videText, { color: T.subtitle }]}>
                Aucune pharmacie trouvée
              </Text>
              <TouchableOpacity onPress={reset}>
                <Text style={{ color: Colors.primary, fontWeight: Typography.semibold }}>
                  Réinitialiser les filtres
                </Text>
              </TouchableOpacity>
            </View>
          ) : (
            <ActivityIndicator
              color={Colors.primary}
              style={{ marginTop: 40 }}
            />
          )
        }
        ListFooterComponent={
          isFetchingNextPage
            ? <ActivityIndicator color={Colors.primary} style={{ marginVertical: 16 }} />
            : null
        }
        renderItem={({ item }) => (
          <PharmacieCard
            pharmacie={item}
            T={T}
            isDark={isDark}
          />
        )}
      />
    </SafeAreaView>
  )
}

// ── Carte pharmacie ───────────────────────────────────────────────────────────
function PharmacieCard({
  pharmacie, T, isDark,
}: {
  pharmacie: Pharmacie
  T: typeof lightTheme
  isDark: boolean
}) {
  const ouvrirItineraire = () => {
    if (!pharmacie.latitude || !pharmacie.longitude) return
    const url = Platform.OS === "ios"
      ? `maps://?daddr=${pharmacie.latitude},${pharmacie.longitude}`
      : `https://www.google.com/maps/dir/?api=1&destination=${pharmacie.latitude},${pharmacie.longitude}`
    Linking.openURL(url)
  }

  return (
    <TouchableOpacity
      style={[styles.card, {
        backgroundColor: T.cardBg,
        borderColor:     T.cardBorder,
      }]}
      onPress={() => router.push(`/pharmacie/${pharmacie.id}`)}
      activeOpacity={0.85}
    >
      <View style={styles.cardContent}>

        {/* ── Nom + Note ──────────────────────────────────────────────── */}
        <View style={styles.cardHeader}>
          <Text style={[styles.cardName, { color: T.cardName }]} numberOfLines={1}>
            {pharmacie.nom}
          </Text>
          {!isDark && (
            <View style={[styles.ratingBox, { backgroundColor: T.ratingBg }]}>
              <Ionicons name="star" size={14} color="#FFD700" />
              <Text style={[styles.ratingText, { color: T.ratingText }]}>4.8</Text>
            </View>
          )}
        </View>

        {/* ── Adresse ─────────────────────────────────────────────────── */}
        <Text style={[styles.cardAddr, { color: T.cardAddr }]} numberOfLines={1}>
          {pharmacie.adresse}{pharmacie.ville ? `, ${pharmacie.ville}` : ""}
        </Text>

        {/* ── Détails ─────────────────────────────────────────────────── */}
        <View style={styles.cardDetails}>
          {/* Horaire (dark : schedule, light : heure si ouvert) */}
          {isDark && (
            <View style={styles.detailItem}>
              <Ionicons name="time-outline" size={14} color={T.cardMeta} />
              <Text style={[styles.detailText, { color: T.cardMeta }]}>
                {pharmacie.est_ouverte ? "Ferme à 20:00" : "Ouvre à 08:30"}
              </Text>
            </View>
          )}
          {!isDark && pharmacie.est_ouverte && (
            <View style={styles.detailItem}>
              <Ionicons name="time-outline" size={14} color={T.cardMeta} />
              <Text style={[styles.detailText, { color: T.cardMeta }]}>8 min</Text>
            </View>
          )}

          {/* Distance */}
          <View style={styles.detailItem}>
            <Ionicons name="location-outline" size={14} color={T.cardMeta} />
            <Text style={[styles.detailText, { color: T.cardMeta }]}>~450m</Text>
          </View>

          {/* Statut si fermé (light only) */}
          {!isDark && !pharmacie.est_ouverte && (
            <View style={styles.detailItem}>
              <Ionicons name="time-outline" size={14} color={T.cardMeta} />
              <Text style={[styles.detailText, { color: T.cardMeta }]}>
                Ouvre à 08:30
              </Text>
            </View>
          )}
        </View>

        {/* ── Bouton Itinéraire ────────────────────────────────────────── */}
        <TouchableOpacity
          style={[styles.itiRow, { borderTopColor: T.itiBorder }]}
          onPress={ouvrirItineraire}
        >
          <Text style={styles.itiText}>Itinéraire</Text>
          <Ionicons name="navigate" size={18} color="#02420d" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  // Header
  header: {
    borderBottomWidth: 1,
    paddingBottom:     Spacing.sm,
  },
  headerTop: {
    flexDirection:   "row",
    alignItems:      "center",
    justifyContent:  "space-between",
    paddingHorizontal: Spacing.base,
    paddingTop:      Spacing.sm,
    paddingBottom:   Spacing.sm,
  },
  titre:    { fontSize: Typography.xl, fontWeight: Typography.bold },
  themeBtn: {
    width: 36, height: 36, borderRadius: 18,
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

  // Chips
  chipsRow: {
    paddingHorizontal: Spacing.base,
    gap:               Spacing.sm,
    flexDirection:     "row",
    paddingBottom:     4,
  },
  chip: {
    flexDirection:   "row",
    alignItems:      "center",
    gap:             5,
    paddingHorizontal: 14,
    paddingVertical:   8,
    borderRadius:    BorderRadius.full,
    borderWidth:     1,
  },
  chipText: { fontSize: Typography.sm, fontWeight: Typography.medium },

  // Liste
  list:     { paddingHorizontal: Spacing.base },
  compteur: { fontSize: Typography.sm, marginBottom: Spacing.md, marginTop: Spacing.sm },

  // Card
  card: {
    borderRadius:  BorderRadius.lg,
    marginBottom:  Spacing.md,
    borderWidth:   1,
    ...Shadow.sm,
  },
  cardContent: { padding: Spacing.base },
  cardHeader:  {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    marginBottom:   Spacing.xs,
  },
  cardName:    { fontSize: Typography.md, fontWeight: Typography.semibold, flex: 1 },
  ratingBox:   {
    flexDirection: "row", alignItems: "center",
    gap: 3, paddingHorizontal: 8, paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  ratingText:  { fontSize: Typography.sm, fontWeight: Typography.semibold },
  cardAddr:    { fontSize: Typography.sm, marginBottom: Spacing.sm },
  cardDetails: {
    flexDirection: "row", flexWrap: "wrap",
    gap: Spacing.md, marginBottom: Spacing.sm,
  },
  detailItem:  { flexDirection: "row", alignItems: "center", gap: 4 },
  detailText:  { fontSize: Typography.sm },

  // Bouton Itinéraire
  itiRow: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "flex-end",
    gap:            Spacing.xs,
    paddingTop:     Spacing.sm,
    borderTopWidth: 1,
  },
  itiText: {
    fontSize:   Typography.sm,
    fontWeight: Typography.semibold,
    color:      "#0066CC",
  },

  // Vide
  vide:     { alignItems: "center", paddingTop: 60, gap: Spacing.base },
  videText: { fontSize: Typography.base, fontWeight: Typography.semibold },
})