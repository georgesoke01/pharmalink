// app/(tabs)/recherche.tsx — Catalogue produits — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, FlatList, ActivityIndicator, useColorScheme,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { useProduits, usePharmacies } from "@/hooks/usePharmacies"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import type { Produit, Pharmacie } from "@/types"

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:            "#FFFFFF",
  headerBorder:  "#F0F0F0",
  title:         "#333333",
  iconTxt:       "#666666",
  searchBg:      "#F5F5F5",
  searchBorder:  "#E0E0E0",
  searchText:    "#333333",
  searchPH:      "#666666",
  chipBg:        "#F5F5F5",
  chipBorder:    "#E0E0E0",
  chipTxt:       "#666666",
  chipActiveBg:  "#0066CC",
  darkChipBg:    "#333333",
  statsTxt:      "#666666",
  cardBg:        "#FFFFFF",
  cardBorder:    "#F0F0F0",
  cardFoot:      "#F0F0F0",
  nameTxt:       "#333333",
  subTxt:        "#666666",
  priceTxt:      "#333333",
  bannerBg:      "#2D2D2D",
  bannerBorder:  "#444444",
}
const darkTheme = {
  bg:            "#1A1A1A",
  headerBorder:  "#333333",
  title:         "#FFFFFF",
  iconTxt:       "#FFFFFF",
  searchBg:      "#333333",
  searchBorder:  "#444444",
  searchText:    "#FFFFFF",
  searchPH:      "#999999",
  chipBg:        "#333333",
  chipBorder:    "#444444",
  chipTxt:       "#FFFFFF",
  chipActiveBg:  "#0066CC",
  darkChipBg:    "#333333",
  statsTxt:      "#999999",
  cardBg:        "#2D2D2D",
  cardBorder:    "#444444",
  cardFoot:      "#444444",
  nameTxt:       "#FFFFFF",
  subTxt:        "#999999",
  priceTxt:      "#FFFFFF",
  bannerBg:      "#2D2D2D",
  bannerBorder:  "#444444",
}

const FILTRES_LIGHT = ["Tous", "Sans ordonnance", "Avec ordonnance"]
const FILTRES_DARK  = [
  { label: "Sans ordonnance", icon: "chevron-down" },
  { label: "Prix",            icon: "chevron-down" },
  { label: "Pharmacie",       icon: "chevron-down" },
]

export default function EcranRecherche() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const [query,  setQuery]  = useState("")
  const [filtre, setFiltre] = useState("Tous")

  const filtresProduits = {
    search:         query || undefined,
    sur_ordonnance: filtre === "Avec ordonnance" ? true
                  : filtre === "Sans ordonnance"  ? false
                  : undefined,
    page_size: 20,
  }

  const {
    data: pData, isLoading: lP, fetchNextPage: fP, hasNextPage: hP,
  } = useProduits(filtresProduits)

  const produits = pData?.pages.flatMap((p) => p.results) ?? []
  const total    = pData?.pages[0]?.count ?? 0

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <View style={[styles.header, { borderBottomColor: T.headerBorder }]}>
        <Text style={[styles.titre, { color: T.title }]}>
          {isDark ? "PharmaLoc" : "Catalogue Produits"}
        </Text>
        <TouchableOpacity>
          <Ionicons
            name={isDark ? "sunny-outline" : "moon-outline"}
            size={22}
            color={T.iconTxt}
          />
        </TouchableOpacity>
      </View>

      {/* ── Recherche ─────────────────────────────────────────────── */}
      <View style={[styles.searchBox, {
        backgroundColor: T.searchBg, borderColor: T.searchBorder,
      }]}>
        <Ionicons name="search" size={20} color={T.searchPH} />
        <TextInput
          style={[styles.searchInput, { color: T.searchText }]}
          placeholder={isDark ? "Doliprane..." : "Rechercher un médicament..."}
          placeholderTextColor={T.searchPH}
          value={query}
          onChangeText={setQuery}
        />
        {isDark && (
          <TouchableOpacity>
            <Ionicons name="options" size={20} color={T.searchPH} />
          </TouchableOpacity>
        )}
        {query.length > 0 && !isDark && (
          <TouchableOpacity onPress={() => setQuery("")}>
            <Ionicons name="close-circle" size={18} color={T.searchPH} />
          </TouchableOpacity>
        )}
      </View>

      {/* ── Filtres ───────────────────────────────────────────────── */}
      {isDark ? (
        <View style={styles.darkFiltresRow}>
          {FILTRES_DARK.map((f) => (
            <TouchableOpacity
              key={f.label}
              style={[styles.darkChip, { backgroundColor: T.chipBg, borderColor: T.chipBorder }]}
            >
              <Text style={[styles.darkChipTxt, { color: T.chipTxt }]}>{f.label}</Text>
              <Ionicons name="chevron-down" size={16} color={T.chipTxt} />
            </TouchableOpacity>
          ))}
        </View>
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtresRow}
        >
          {FILTRES_LIGHT.map((f) => {
            const actif = filtre === f
            return (
              <TouchableOpacity
                key={f}
                style={[styles.chip, {
                  backgroundColor: actif ? T.chipActiveBg : T.chipBg,
                  borderColor:     actif ? T.chipActiveBg : T.chipBorder,
                }]}
                onPress={() => setFiltre(f)}
              >
                <Text style={[styles.chipTxt, { color: actif ? "#FFFFFF" : T.chipTxt }]}>
                  {f}
                </Text>
              </TouchableOpacity>
            )
          })}
        </ScrollView>
      )}

      {/* ── Compteur + tri ────────────────────────────────────────── */}
      <View style={styles.statsRow}>
        <Text style={[styles.statsTxt, { color: T.statsTxt }]}>
          Résultats ({total})
        </Text>
        {isDark && (
          <TouchableOpacity style={styles.triBtn}>
            <Text style={styles.triTxt}>Trier par</Text>
            <Ionicons name="swap-vertical" size={16} color="#0066CC" />
          </TouchableOpacity>
        )}
      </View>

      {/* ── Liste ─────────────────────────────────────────────────── */}
      <FlatList
        data={produits}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        onEndReached={() => hP && fP()}
        onEndReachedThreshold={0.3}
        ListEmptyComponent={
          lP ? (
            <ActivityIndicator color={Colors.primary} style={{ marginTop: 40 }} />
          ) : (
            <View style={styles.vide}>
              <Ionicons name="medical-outline" size={48} color={T.statsTxt} />
              <Text style={[styles.videText, { color: T.statsTxt }]}>
                Aucun produit trouvé
              </Text>
            </View>
          )
        }
        ListFooterComponent={
          isDark ? (
            <View style={[styles.banner, {
              backgroundColor: T.bannerBg, borderColor: T.bannerBorder,
            }]}>
              <View style={styles.bannerContent}>
                <Ionicons name="bulb" size={24} color="#FFD700" />
                <View style={{ flex: 1 }}>
                  <Text style={styles.bannerLabel}>CONSEIL SANTÉ</Text>
                  <Text style={styles.bannerTitre}>Votre ordonnance en 1h</Text>
                  <Text style={styles.bannerDesc}>
                    Faites-vous livrer vos médicaments urgents directement chez vous.
                  </Text>
                </View>
              </View>
              <TouchableOpacity style={{ alignSelf: "flex-end" }}>
                <Text style={{ color: "#0066CC", fontWeight: Typography.semibold, fontSize: Typography.sm }}>
                  En savoir plus
                </Text>
              </TouchableOpacity>
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <ProduitCard produit={item} T={T} isDark={isDark} />
        )}
      />
    </SafeAreaView>
  )
}

// ── Carte produit ─────────────────────────────────────────────────────────────
function ProduitCard({
  produit, T, isDark,
}: { produit: Produit; T: typeof lightTheme; isDark: boolean }) {
  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: T.cardBg, borderColor: T.cardBorder }]}
      onPress={() => router.push(`/produit/${produit.id}`)}
    >
      {/* Nom + icône */}
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}>
          <Text style={[styles.cardNom, { color: T.nameTxt }]} numberOfLines={1}>
            {produit.nom}
          </Text>
          <Text style={[styles.cardSub, { color: T.subTxt }]} numberOfLines={1}>
            {produit.nom_generique || produit.laboratoire} • {produit.dosage}
          </Text>
        </View>
        <Ionicons name="medical" size={28} color="#0066CC" />
      </View>

      {/* Badge prescription (light only) */}
      {!isDark && !produit.sur_ordonnance && (
        <View style={styles.rxBadge}>
          <Text style={styles.rxTxt}>SANS ORDONNANCE</Text>
        </View>
      )}

      {/* Footer prix + actions */}
      <View style={[styles.cardFoot, { borderTopColor: T.cardFoot }]}>
        <View style={styles.prixRow}>
          <Text style={[styles.prixLabel, { color: T.subTxt }]}>Dès</Text>
          <Text style={[styles.prixVal, { color: T.priceTxt }]}>
            {produit.sur_ordonnance ? "Sur ordonnance" : "—"}
          </Text>
        </View>

        {!isDark && (
          <View style={styles.pharmaciesRow}>
            <Ionicons name="medical" size={14} color={T.subTxt} />
            <Text style={[styles.pharmaciesTxt, { color: T.subTxt }]}>
              Vérifier en pharmacie
            </Text>
          </View>
        )}

        <TouchableOpacity style={styles.btnComparer}>
          <Text style={styles.btnComparerTxt}>Comparer</Text>
          <Ionicons name="git-compare" size={16} color="#0066CC" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: Spacing.base, paddingVertical: Spacing.md, borderBottomWidth: 1,
  },
  titre: { fontSize: Typography.xl, fontWeight: Typography.bold },

  searchBox: {
    flexDirection: "row", alignItems: "center",
    marginHorizontal: Spacing.base, marginVertical: Spacing.md,
    paddingHorizontal: Spacing.md, paddingVertical: 11,
    borderRadius: BorderRadius.lg, borderWidth: 1, gap: Spacing.sm,
  },
  searchInput: { flex: 1, fontSize: Typography.base, padding: 0 },

  filtresRow:     { paddingHorizontal: Spacing.base, gap: Spacing.sm, flexDirection: "row" },
  chip:           { paddingHorizontal: 14, paddingVertical: 8, borderRadius: BorderRadius.full, borderWidth: 1 },
  chipTxt:        { fontSize: Typography.sm, fontWeight: Typography.medium },

  darkFiltresRow: { flexDirection: "row", paddingHorizontal: Spacing.base, gap: Spacing.sm, marginBottom: Spacing.sm },
  darkChip:       { flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: Spacing.md, paddingVertical: 7, borderRadius: BorderRadius.full, borderWidth: 1 },
  darkChipTxt:    { fontSize: Typography.sm },

  statsRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm },
  statsTxt: { fontSize: Typography.sm },
  triBtn:   { flexDirection: "row", alignItems: "center", gap: 4 },
  triTxt:   { fontSize: Typography.sm, color: "#0066CC", fontWeight: Typography.medium },

  list: { paddingHorizontal: Spacing.base, paddingBottom: 100 },

  card: { borderRadius: BorderRadius.lg, padding: Spacing.base, marginBottom: Spacing.md, borderWidth: 1, ...Shadow.sm },
  cardHeader:   { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: Spacing.sm },
  cardNom:      { fontSize: Typography.lg, fontWeight: Typography.semibold },
  cardSub:      { fontSize: Typography.sm, marginTop: 2 },
  rxBadge:      { alignSelf: "flex-start", backgroundColor: "#E6F0FF", paddingHorizontal: 10, paddingVertical: 4, borderRadius: BorderRadius.full, marginBottom: Spacing.sm },
  rxTxt:        { fontSize: 10, color: "#0066CC", fontWeight: Typography.semibold },
  cardFoot:     { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingTop: Spacing.sm, borderTopWidth: 1, marginTop: Spacing.xs },
  prixRow:      { flexDirection: "row", alignItems: "baseline", gap: 3 },
  prixLabel:    { fontSize: Typography.xs },
  prixVal:      { fontSize: Typography.lg, fontWeight: Typography.bold },
  pharmaciesRow:{ flexDirection: "row", alignItems: "center", gap: 3 },
  pharmaciesTxt:{ fontSize: Typography.xs },
  btnComparer:  { flexDirection: "row", alignItems: "center", gap: 4, backgroundColor: "#F5F5F5", paddingHorizontal: 10, paddingVertical: 5, borderRadius: BorderRadius.full },
  btnComparerTxt: { fontSize: Typography.xs, color: "#0066CC", fontWeight: Typography.semibold },

  banner: { borderRadius: BorderRadius.lg, padding: Spacing.base, marginBottom: Spacing.base, borderWidth: 1 },
  bannerContent: { flexDirection: "row", gap: Spacing.md, marginBottom: Spacing.md },
  bannerLabel:   { fontSize: Typography.xs, color: "#FFD700", fontWeight: Typography.semibold, marginBottom: 4 },
  bannerTitre:   { fontSize: Typography.base, color: "#FFFFFF", fontWeight: Typography.semibold },
  bannerDesc:    { fontSize: Typography.xs, color: "#999999", marginTop: 2 },

  vide:     { alignItems: "center", paddingTop: 60, gap: Spacing.sm },
  videText: { fontSize: Typography.base },
})