// app/pharmacie/[id].tsx — Fiche détaillée pharmacie — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  FlatList, Linking, Platform, ActivityIndicator,
  useColorScheme, Dimensions,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { useLocalSearchParams, router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { Image } from "expo-image"
import {
  usePharmacie, useHoraires, useProduitsPharmacie,
} from "@/hooks/usePharmacies"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import { SERVICES_LABELS } from "@/types"
import type { HoraireSemaine, ProduitAvecStock } from "@/types"

const { width } = Dimensions.get("window")

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:             "#FFFFFF",
  headerBg:       "#FFFFFF",
  headerBorder:   "#F0F0F0",
  headerTitle:    "#333333",
  headerIcon:     "#666666",
  nameTxt:        "#333333",
  addrTxt:        "#666666",
  metaTxt:        "#666666",
  ratingBg:       "#F5F5F5",
  ratingTxt:      "#666666",
  actionBg:       "#F5F5F5",
  actionTxt:      "#0066CC",
  tabBorder:      "#F0F0F0",
  tabTxt:         "#666666",
  tabActiveTxt:   "#0066CC",
  tabActiveBar:   "#0066CC",
  sectionTxt:     "#333333",
  hoursDay:       "#666666",
  hoursVal:       "#333333",
  hoursToday:     "#0066CC",
  hoursFerme:     "#FF6B6B",
  serviceCardBg:  "#F5F5F5",
  serviceCardBrd: "#E0E0E0",
  serviceTxt:     "#333333",
  serviceSubTxt:  "#666666",
  productCardBg:  "#FFFFFF",
  productCardBrd: "#F0F0F0",
  productName:    "#333333",
  productDesc:    "#666666",
  productPrice:   "#333333",
  rxBg:           "#FFE5E5",
  rxTxt:          "#FF6B6B",
  divider:        "#F0F0F0",
}

const darkTheme = {
  bg:             "#1A1A1A",
  headerBg:       "#1A1A1A",
  headerBorder:   "#333333",
  headerTitle:    "#FFFFFF",
  headerIcon:     "#FFFFFF",
  nameTxt:        "#FFFFFF",
  addrTxt:        "#999999",
  metaTxt:        "#999999",
  ratingBg:       "#333333",
  ratingTxt:      "#FFFFFF",
  actionBg:       "#333333",
  actionTxt:      "#0066CC",
  tabBorder:      "#333333",
  tabTxt:         "#999999",
  tabActiveTxt:   "#0066CC",
  tabActiveBar:   "#0066CC",
  sectionTxt:     "#FFFFFF",
  hoursDay:       "#999999",
  hoursVal:       "#999999",
  hoursToday:     "#0066CC",
  hoursFerme:     "#FF6B6B",
  serviceCardBg:  "#333333",
  serviceCardBrd: "#444444",
  serviceTxt:     "#FFFFFF",
  serviceSubTxt:  "#999999",
  productCardBg:  "#2D2D2D",
  productCardBrd: "#444444",
  productName:    "#FFFFFF",
  productDesc:    "#999999",
  productPrice:   "#FFFFFF",
  rxBg:           "rgba(255,107,107,0.15)",
  rxTxt:          "#FF6B6B",
  divider:        "#333333",
}

const JOURS = ["Dim","Lun","Mar","Mer","Jeu","Ven","Sam"]
const JOURS_COMPLETS = [
  "Dimanche","Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"
]

export default function FichePharmacie() {
  const { id }      = useLocalSearchParams<{ id: string }>()
  const pharmacieId = Number(id)

  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const [onglet,  setOnglet]  = useState<"Infos"|"Services"|"Produits">("Infos")
  const [favori,  setFavori]  = useState(false)

  const { data: pharmacie, isLoading } = usePharmacie(pharmacieId)
  const { data: horaires }             = useHoraires(pharmacieId)
  const {
    data: prodData, isLoading: loadPr,
    fetchNextPage, hasNextPage,
  } = useProduitsPharmacie(pharmacieId, { page_size: 5 })

  const produits   = prodData?.pages.flatMap((p) => p.results) ?? []
  const jourActuel = new Date().getDay()

  const appeler = () => {
    if (pharmacie?.telephone) Linking.openURL(`tel:${pharmacie.telephone}`)
  }

  const itineraire = () => {
    if (!pharmacie?.latitude || !pharmacie?.longitude) return
    const url = Platform.OS === "ios"
      ? `maps://?daddr=${pharmacie.latitude},${pharmacie.longitude}`
      : `https://www.google.com/maps/dir/?api=1&destination=${pharmacie.latitude},${pharmacie.longitude}`
    Linking.openURL(url)
  }

  if (isLoading) return (
    <View style={[styles.loader, { backgroundColor: T.bg }]}>
      <ActivityIndicator color={Colors.primary} size="large" />
    </View>
  )

  if (!pharmacie) return (
    <View style={[styles.loader, { backgroundColor: T.bg }]}>
      <Text style={{ color: T.addrTxt }}>Pharmacie introuvable</Text>
    </View>
  )

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <View style={[styles.header, {
        backgroundColor: T.headerBg,
        borderBottomColor: T.headerBorder,
      }]}>
        <TouchableOpacity style={styles.headerBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={T.headerIcon} />
        </TouchableOpacity>

        <Text style={[styles.headerTitle, { color: T.headerTitle }]} numberOfLines={1}>
          {isDark ? "PharmaLoc" : pharmacie.nom}
        </Text>

        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.headerBtn}
            onPress={() => setFavori(!favori)}
          >
            <Ionicons
              name={favori ? "heart" : "heart-outline"}
              size={22}
              color={favori ? Colors.danger : T.headerIcon}
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn}>
            <Ionicons
              name={isDark ? "sunny-outline" : "moon-outline"}
              size={22}
              color={T.headerIcon}
            />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={{ flex: 1, backgroundColor: T.bg }}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Info pharmacie ──────────────────────────────────────────── */}
        <View style={[styles.infoSection, { borderBottomColor: T.divider }]}>

          {/* Nom + Note */}
          <View style={styles.namRow}>
            <Text style={[styles.nomPharmacie, { color: T.nameTxt }]}>
              {pharmacie.nom}
            </Text>
            <View style={[styles.ratingBox, { backgroundColor: T.ratingBg }]}>
              <Ionicons name="star" size={14} color="#FFD700" />
              <Text style={[styles.ratingTxt, { color: T.ratingTxt }]}>4.8</Text>
            </View>
          </View>

          {/* Adresse */}
          <Text style={[styles.adresse, { color: T.addrTxt }]}>
            {pharmacie.adresse}{pharmacie.ville ? `, ${pharmacie.ville}` : ""}
          </Text>

          {/* Meta */}
          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="location-outline" size={15} color={T.metaTxt} />
              <Text style={[styles.metaTxt, { color: T.metaTxt }]}>~0.4 km</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="time-outline" size={15} color={T.metaTxt} />
              <Text style={[styles.metaTxt, { color: T.metaTxt }]}>
                {isDark ? "🔒 " : "• "}
                {pharmacie.est_ouverte ? "Ouvert jusqu'à 20:00" : "Fermé — Ouvre à 08:30"}
              </Text>
            </View>
          </View>

          {/* Boutons action */}
          <View style={styles.actionsRow}>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: T.actionBg }]}
              onPress={appeler}
            >
              <Ionicons name="call" size={18} color={T.actionTxt} />
              <Text style={[styles.actionTxt, { color: T.actionTxt }]}>Appeler</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: T.actionBg }]}
              onPress={itineraire}
            >
              <Ionicons name="navigate" size={18} color={T.actionTxt} />
              <Text style={[styles.actionTxt, { color: T.actionTxt }]}>Itinéraire</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* ── Onglets ─────────────────────────────────────────────────── */}
        <View style={[styles.tabsRow, { borderBottomColor: T.tabBorder }]}>
          {(["Infos", "Services", "Produits"] as const).map((tab) => (
            <TouchableOpacity
              key={tab}
              style={styles.tab}
              onPress={() => setOnglet(tab)}
            >
              <Text style={[
                styles.tabTxt,
                { color: onglet === tab ? T.tabActiveTxt : T.tabTxt },
                onglet === tab && { fontWeight: Typography.semibold },
              ]}>
                {tab}
              </Text>
              {onglet === tab && (
                <View style={[styles.tabBar, { backgroundColor: T.tabActiveBar }]} />
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* ── Contenu ─────────────────────────────────────────────────── */}
        <View style={styles.tabContent}>

          {/* ── INFOS ─────────────────────────────────────────────────── */}
          {onglet === "Infos" && (
            <View>
              <Text style={[styles.sectionTitle, { color: T.sectionTxt }]}>
                Horaires d'ouverture
              </Text>
              {horaires?.semaine.map((h: HoraireSemaine) => {
                const isToday = jourActuel === (h.jour + 1) % 7
                return (
                  <View key={h.id} style={styles.hoursRow}>
                    <Text style={[
                      styles.hoursDay,
                      { color: isToday ? T.hoursToday : T.hoursDay },
                      isToday && { fontWeight: Typography.semibold },
                    ]}>
                      {JOURS_COMPLETS[(h.jour + 1) % 7]}
                      {isToday ? " (Aujourd'hui)" : ""}
                    </Text>
                    <Text style={[
                      styles.hoursVal,
                      h.est_ferme
                        ? { color: T.hoursFerme }
                        : { color: isToday ? T.hoursToday : T.hoursVal },
                    ]}>
                      {h.est_ferme
                        ? "Fermé"
                        : `${h.heure_ouverture?.slice(0,5)} - ${h.heure_fermeture?.slice(0,5)}`
                      }
                    </Text>
                  </View>
                )
              })}

              {/* Fallback si pas d'horaires */}
              {!horaires && (
                <Text style={{ color: T.addrTxt, fontSize: Typography.sm }}>
                  Horaires non disponibles
                </Text>
              )}
            </View>
          )}

          {/* ── SERVICES ─────────────────────────────────────────────── */}
          {onglet === "Services" && (
            <View>
              {(pharmacie.services ?? []).length === 0 ? (
                <Text style={{ color: T.addrTxt, fontSize: Typography.sm }}>
                  Aucun service renseigné
                </Text>
              ) : (
                (pharmacie.services ?? []).map((s: string) => (
                  <View key={s} style={[styles.serviceCard, {
                    backgroundColor: T.serviceCardBg,
                    borderColor:     T.serviceCardBrd,
                  }]}>
                    <View style={styles.serviceHeader}>
                      <Ionicons name="checkmark-circle" size={22} color="#0066CC" />
                      <Text style={[styles.serviceName, { color: T.serviceTxt }]}>
                        {SERVICES_LABELS[s] ?? s}
                      </Text>
                    </View>
                    <Text style={[styles.serviceDesc, { color: T.serviceSubTxt }]}>
                      Disponible dans cette pharmacie
                    </Text>
                    <View style={[styles.serviceFoot, { borderTopColor: T.serviceCardBrd }]}>
                      <View style={styles.deliveryRow}>
                        <Ionicons name="bicycle" size={14} color={T.serviceSubTxt} />
                        <Text style={[styles.deliveryTxt, { color: T.serviceSubTxt }]}>
                          Livraison à domicile
                        </Text>
                      </View>
                      <Text style={[styles.deliveryTime, { color: T.serviceSubTxt }]}>
                        Sous 2h dans le quartier
                      </Text>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}

          {/* ── PRODUITS ─────────────────────────────────────────────── */}
          {onglet === "Produits" && (
            <View>
              <View style={styles.produitsHeader}>
                <Text style={[styles.sectionTitle, { color: T.sectionTxt }]}>
                  Produits populaires
                </Text>
                {isDark && (
                  <TouchableOpacity onPress={() => fetchNextPage()}>
                    <Text style={{ color: "#0066CC", fontWeight: Typography.semibold, fontSize: Typography.sm }}>
                      Voir tout
                    </Text>
                  </TouchableOpacity>
                )}
              </View>

              {loadPr && produits.length === 0 ? (
                <ActivityIndicator color={Colors.primary} />
              ) : produits.length === 0 ? (
                <Text style={{ color: T.addrTxt, fontSize: Typography.sm }}>
                  Catalogue non disponible
                </Text>
              ) : (
                produits.map((p: ProduitAvecStock) => (
                  <TouchableOpacity
                    key={p.id}
                    style={[styles.productCard, {
                      backgroundColor: T.productCardBg,
                      borderColor:     T.productCardBrd,
                    }]}
                    onPress={() => router.push(`/produit/${p.id}`)}
                  >
                    {/* Image placeholder */}
                    <View style={[styles.productImg, { backgroundColor: isDark ? "#333" : "#F5F5F5" }]}>
                      <Ionicons
                        name="medical"
                        size={24}
                        color={isDark ? "#0066CC" : Colors.gray400}
                      />
                    </View>

                    {/* Infos */}
                    <View style={styles.productBody}>
                      <Text style={[styles.productName, { color: T.productName }]} numberOfLines={1}>
                        {p.nom}
                      </Text>
                      <Text style={[styles.productDesc, { color: T.productDesc }]} numberOfLines={1}>
                        {p.dosage}{p.forme ? ` - ${p.forme}` : ""}
                      </Text>
                      <View style={styles.productFoot}>
                        <Text style={[styles.productPrice, { color: T.productPrice }]}>
                          {p.prix_fcfa
                            ? `${(p.prix_fcfa / 655.957).toFixed(2)}€`
                            : "—"}
                        </Text>
                        {!isDark && p.sur_ordonnance && (
                          <View style={[styles.rxBadge, { backgroundColor: T.rxBg }]}>
                            <Text style={[styles.rxTxt, { color: T.rxTxt }]}>
                              PRESCRIPTION
                            </Text>
                          </View>
                        )}
                        {isDark && (
                          <View style={[styles.rxBadge, { backgroundColor: T.rxBg }]}>
                            <Text style={[styles.rxTxt, { color: T.rxTxt }]}>
                              {p.disponible ? "EN STOCK" : "RUPTURE"}
                            </Text>
                          </View>
                        )}
                      </View>
                    </View>

                    {/* Bouton panier */}
                    <TouchableOpacity style={styles.cartBtn}>
                      <Ionicons name="cart-outline" size={22} color="#0066CC" />
                    </TouchableOpacity>
                  </TouchableOpacity>
                ))
              )}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },
  loader:    { flex: 1, alignItems: "center", justifyContent: "center" },

  // Header
  header: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.base,
    paddingVertical:   Spacing.md,
    borderBottomWidth: 1,
  },
  headerBtn:   { padding: 4 },
  headerTitle: { flex: 1, textAlign: "center", fontSize: Typography.md, fontWeight: Typography.semibold, marginHorizontal: Spacing.sm },
  headerRight: { flexDirection: "row", gap: Spacing.sm },

  // Info section
  infoSection: {
    padding: Spacing.base,
    borderBottomWidth: 1,
  },
  namRow: {
    flexDirection:  "row",
    alignItems:     "center",
    justifyContent: "space-between",
    marginBottom:   Spacing.xs,
  },
  nomPharmacie: { fontSize: Typography.xl, fontWeight: Typography.bold, flex: 1 },
  ratingBox:    {
    flexDirection: "row", alignItems: "center",
    gap: 4, paddingHorizontal: 8, paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  ratingTxt:    { fontSize: Typography.sm, fontWeight: Typography.semibold },
  adresse:      { fontSize: Typography.sm, marginBottom: Spacing.sm },
  metaRow:      { flexDirection: "row", gap: Spacing.lg, marginBottom: Spacing.base },
  metaItem:     { flexDirection: "row", alignItems: "center", gap: 4 },
  metaTxt:      { fontSize: Typography.sm },

  // Boutons action
  actionsRow: { flexDirection: "row", gap: Spacing.md },
  actionBtn:  {
    flex: 1, flexDirection: "row", alignItems: "center",
    justifyContent: "center",
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    gap: 8,
  },
  actionTxt:  { fontSize: Typography.base, fontWeight: Typography.semibold },

  // Onglets
  tabsRow: {
    flexDirection: "row",
    paddingHorizontal: Spacing.base,
    borderBottomWidth: 1,
  },
  tab:    { flex: 1, alignItems: "center", paddingVertical: Spacing.md, position: "relative" },
  tabTxt: { fontSize: Typography.base },
  tabBar: { position: "absolute", bottom: -1, left: 0, right: 0, height: 2 },

  // Contenu onglets
  tabContent: { padding: Spacing.base, paddingBottom: 100 },
  sectionTitle: { fontSize: Typography.lg, fontWeight: Typography.semibold, marginBottom: Spacing.md },

  // Horaires
  hoursRow: {
    flexDirection:  "row",
    justifyContent: "space-between",
    paddingVertical: 7,
  },
  hoursDay: { fontSize: Typography.sm },
  hoursVal: { fontSize: Typography.sm, fontWeight: Typography.medium },

  // Services
  serviceCard: {
    borderRadius: BorderRadius.lg,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
  },
  serviceHeader: { flexDirection: "row", alignItems: "center", gap: Spacing.sm, marginBottom: Spacing.xs },
  serviceName:   { fontSize: Typography.base, fontWeight: Typography.semibold },
  serviceDesc:   { fontSize: Typography.sm, marginBottom: Spacing.md },
  serviceFoot:   { borderTopWidth: 1, paddingTop: Spacing.sm },
  deliveryRow:   { flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 4 },
  deliveryTxt:   { fontSize: Typography.sm },
  deliveryTime:  { fontSize: Typography.xs, marginLeft: 18 },

  // Produits
  produitsHeader: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between", marginBottom: Spacing.md,
  },
  productCard: {
    flexDirection: "row", alignItems: "center",
    borderRadius: BorderRadius.lg, padding: Spacing.md,
    marginBottom: Spacing.sm, borderWidth: 1,
    ...Shadow.sm,
  },
  productImg:   {
    width: 52, height: 52, borderRadius: BorderRadius.md,
    alignItems: "center", justifyContent: "center",
    marginRight: Spacing.md,
  },
  productBody:  { flex: 1 },
  productName:  { fontSize: Typography.base, fontWeight: Typography.semibold, marginBottom: 2 },
  productDesc:  { fontSize: Typography.xs, marginBottom: 4 },
  productFoot:  { flexDirection: "row", alignItems: "center", gap: Spacing.sm },
  productPrice: { fontSize: Typography.base, fontWeight: Typography.semibold },
  rxBadge:      { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  rxTxt:        { fontSize: 9, fontWeight: Typography.bold, letterSpacing: 0.3 },
  cartBtn:      { padding: Spacing.sm },
})