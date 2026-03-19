// app/(tabs)/index.tsx — Carte principale connectée à l'API
import { useState, useRef, useEffect } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, FlatList, Platform, Dimensions,
  useColorScheme, ActivityIndicator,
} from "react-native"
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import {
  useLocalisation, useLocalisationManuelle,
  usePharmaciesProches,
} from "@/hooks/usePharmacies" 
import { useLocalisationStore, useFiltresStore } from "@/store"
import {
  Colors, Spacing, BorderRadius, Shadow,
  Typography, CARTE_REGION_DEFAUT,
} from "@/constants"
import type { Pharmacie } from "@/types"

const { height } = Dimensions.get("window")
const SHEET_MIN  = 300
const SHEET_MAX  = height * 0.7

// ── Thèmes ─────────────────────────────────────────────────────────────────
const lightTheme = {
  bg: "#FFFFFF", headerBg: "#FFFFFF", headerBorder: Colors.border,
  titleTxt: Colors.gray800, subTxt: Colors.gray500,
  searchBg: Colors.gray100, searchBorder: Colors.gray200,
  searchText: Colors.gray800, searchPH: Colors.gray400,
  tagBg: Colors.gray100, tagBorder: Colors.gray200, tagText: Colors.gray600,
  tagActiveBg: Colors.primary, tagGardeBg: Colors.danger,
  sheetBg: "#FFFFFF", sheetBorder: Colors.border,
  sheetTitle: Colors.gray900, sheetSub: Colors.gray500,
  cardBg: "#FFFFFF", cardBorder: Colors.gray200,
  cardName: Colors.gray900, cardAddr: Colors.gray500, cardMeta: Colors.gray400,
  navActive: Colors.primary, pinBg: Colors.primary, pinGardeBg: Colors.danger,
}
const darkTheme = {
  bg: "#1A1A1A", headerBg: "#1A1A1A", headerBorder: "#333333",
  titleTxt: "#FFFFFF", subTxt: "#999999",
  searchBg: "#2D2D2D", searchBorder: "#444444",
  searchText: "#FFFFFF", searchPH: "#999999",
  tagBg: "#2D2D2D", tagBorder: "#444444", tagText: "#CCCCCC",
  tagActiveBg: Colors.primary, tagGardeBg: Colors.danger,
  sheetBg: "#2D2D2D", sheetBorder: "#444444",
  sheetTitle: "#FFFFFF", sheetSub: "#999999",
  cardBg: "#2D2D2D", cardBorder: "#444444",
  cardName: "#FFFFFF", cardAddr: "#999999", cardMeta: "#777777",
  navActive: Colors.primaryLight, pinBg: Colors.primaryLight, pinGardeBg: Colors.danger,
}

export default function EcranCarte() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const mapRef = useRef<MapView>(null)

  // ── GPS + ville réelle ──────────────────────────────────────────────────
  const { position, ville, chargement: locLoad } = useLocalisation()
  const { localiser, chargement: locManuel }      = useLocalisationManuelle()
  const { lat, lng, ville: villeStore }           = useLocalisationStore()
  const {
    filtreOuvert, setFiltreOuvert,
    filtreGarde,  setFiltreGarde,
  } = useFiltresStore()

  const [pharmacieActive, setPharmacieActive] = useState<Pharmacie | null>(null)
  const [sheetExpanded,   setSheetExpanded]   = useState(false)
  const [search,          setSearch]          = useState("")

  // ── Données API ─────────────────────────────────────────────────────────
  const { data, isLoading, refetch } = usePharmaciesProches(lat, lng, 5)
  const pharmaciesBrutes = data?.pages?.flatMap((p: any) => p.results) ?? []

  // Filtre client (ouvert/garde/recherche)
  const pharmacies = pharmaciesBrutes.filter((ph: Pharmacie) => {
    if (filtreOuvert && !ph.est_ouverte)      return false
    if (filtreGarde  && !ph.est_de_garde)     return false
    if (search && !ph.nom.toLowerCase().includes(search.toLowerCase()) &&
        !ph.adresse.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  // Centrer carte quand position GPS disponible
  useEffect(() => {
    if (lat && lng) {
      mapRef.current?.animateToRegion({
        latitude:       lat,
        longitude:      lng,
        latitudeDelta:  0.05,
        longitudeDelta: 0.05,
      }, 800)
    }
  }, [lat, lng])

  const centrerSurMoi = async () => {
    const pos = await localiser()
    if (pos) {
      mapRef.current?.animateToRegion({
        latitude:       pos.lat,
        longitude:      pos.lng,
        latitudeDelta:  0.03,
        longitudeDelta: 0.03,
      }, 700)
    }
  }

  const villeAffichee = villeStore || ville || "Localisation..."

  return (
    <View style={[styles.container, { backgroundColor: T.bg }]}>

      {/* ── Carte MapView ─────────────────────────────────────────── */}
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFillObject}
        provider={Platform.OS === "android" ? PROVIDER_GOOGLE : undefined}
        initialRegion={
          lat && lng
            ? { latitude: lat, longitude: lng, latitudeDelta: 0.05, longitudeDelta: 0.05 }
            : CARTE_REGION_DEFAUT
        }
        showsUserLocation
        showsMyLocationButton={false}
        customMapStyle={isDark ? MAP_DARK : []}
      >
        {pharmacies.map((ph: Pharmacie) =>
          ph.latitude && ph.longitude ? (
            <Marker
              key={ph.id}
              coordinate={{ latitude: ph.latitude, longitude: ph.longitude }}
              onPress={() => {
                setPharmacieActive(ph)
                mapRef.current?.animateToRegion({
                  latitude:       ph.latitude!,
                  longitude:      ph.longitude!,
                  latitudeDelta:  0.015,
                  longitudeDelta: 0.015,
                }, 400)
              }}
            >
              <View style={[
                styles.pin,
                { backgroundColor: ph.est_de_garde ? T.pinGardeBg : T.pinBg },
                pharmacieActive?.id === ph.id && styles.pinSelected,
              ]}>
                <Ionicons name="medkit" size={13} color="#FFFFFF" />
              </View>
            </Marker>
          ) : null
        )}
      </MapView>

      {/* ── Header ───────────────────────────────────────────────── */}
      <SafeAreaView style={styles.headerWrap} edges={["top"]}>
        <View style={[styles.headerRow, {
          backgroundColor: T.headerBg + "F0",
          borderBottomColor: T.headerBorder,
        }]}>
          <View>
            <Text style={[styles.headerTitle, { color: T.titleTxt }]}>
              PharmaLink
            </Text>
            <View style={styles.villeRow}>
              <Ionicons name="location" size={12} color={Colors.primary} />
              <Text style={[styles.villeTxt, { color: T.subTxt }]}>
                {locLoad ? "Localisation..." : villeAffichee}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.locBtn, { backgroundColor: T.searchBg }]}
            onPress={centrerSurMoi}
            disabled={locManuel}
          >
            {locManuel
              ? <ActivityIndicator size="small" color={Colors.primary} />
              : <Ionicons name="locate" size={18} color={Colors.primary} />
            }
          </TouchableOpacity>
        </View>

        {/* Barre de recherche */}
        <View style={[styles.searchRow, { backgroundColor: T.headerBg + "F0" }]}>
          <View style={[styles.searchBox, {
            backgroundColor: T.searchBg, borderColor: T.searchBorder,
          }]}>
            <Ionicons name="search" size={16} color={T.searchPH} />
            <TextInput
              style={[styles.searchInput, { color: T.searchText }]}
              placeholder="Rechercher une pharmacie..."
              placeholderTextColor={T.searchPH}
              value={search}
              onChangeText={setSearch}
            />
            {search.length > 0 && (
              <TouchableOpacity onPress={() => setSearch("")}>
                <Ionicons name="close-circle" size={15} color={T.searchPH} />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Tags filtres */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={[styles.tagsScroll, { backgroundColor: T.headerBg + "F0" }]}
          contentContainerStyle={styles.tagsContent}
        >
          <TouchableOpacity style={[styles.tag, {
            backgroundColor: T.tagBg, borderColor: T.tagBorder,
          }]}>
            <Ionicons name="location" size={12} color={T.tagText} />
            <Text style={[styles.tagText, { color: T.tagText }]}>
              {villeAffichee}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tag, {
              backgroundColor: filtreOuvert ? T.tagActiveBg : T.tagBg,
              borderColor:     filtreOuvert ? T.tagActiveBg : T.tagBorder,
            }]}
            onPress={() => setFiltreOuvert(!filtreOuvert)}
          >
            <Ionicons name="time" size={12} color={filtreOuvert ? "#FFF" : T.tagText} />
            <Text style={[styles.tagText, { color: filtreOuvert ? "#FFF" : T.tagText }]}>
              Ouvert
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tag, {
              backgroundColor: filtreGarde ? T.tagGardeBg : T.tagBg,
              borderColor:     filtreGarde ? T.tagGardeBg : T.tagBorder,
            }]}
            onPress={() => setFiltreGarde(!filtreGarde)}
          >
            <Ionicons name="shield" size={12} color={filtreGarde ? "#FFF" : T.tagText} />
            <Text style={[styles.tagText, { color: filtreGarde ? "#FFF" : T.tagText }]}>
              De garde
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tag, { backgroundColor: T.tagBg, borderColor: T.tagBorder }]}
            onPress={centrerSurMoi}
          >
            <Ionicons name="navigate" size={12} color={T.tagText} />
            <Text style={[styles.tagText, { color: T.tagText }]}>{"< 5km"}</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>

      {/* ── Bottom Sheet ─────────────────────────────────────────── */}
      <View style={[styles.sheet, {
        height:          sheetExpanded ? SHEET_MAX : SHEET_MIN,
        backgroundColor: T.sheetBg,
        borderTopColor:  T.sheetBorder,
      }]}>
        <TouchableOpacity
          style={styles.handleZone}
          onPress={() => setSheetExpanded(!sheetExpanded)}
        >
          <View style={[styles.handle, { backgroundColor: isDark ? "#555" : Colors.gray300 }]} />
        </TouchableOpacity>

        <View style={styles.sheetHeader}>
          <View>
            <Text style={[styles.sheetTitle, { color: T.sheetTitle }]}>
              {isDark ? "Pharmacies à proximité" : "Santé"}
            </Text>
            <Text style={[styles.sheetSub, { color: T.sheetSub }]}>
              {isLoading
                ? "Recherche en cours..."
                : `${pharmacies.length} établissement${pharmacies.length !== 1 ? "s" : ""} trouvé${pharmacies.length !== 1 ? "s" : ""} · ${villeAffichee}`}
            </Text>
          </View>
          <TouchableOpacity
            style={[styles.voirToutBtn, { borderColor: T.sheetBorder }]}
            onPress={() => router.push("/(tabs)/liste")}
          >
            <Text style={{ color: T.navActive, fontSize: Typography.xs, fontWeight: Typography.semibold }}>
              Voir tout
            </Text>
          </TouchableOpacity>
        </View>

        {/* Loader initial */}
        {isLoading && pharmacies.length === 0 ? (
          <View style={styles.loader}>
            <ActivityIndicator color={Colors.primary} />
            <Text style={[styles.loaderTxt, { color: T.sheetSub }]}>
              Recherche des pharmacies proches…
            </Text>
          </View>
        ) : (
          <FlatList
            data={pharmacies}
            keyExtractor={(item: Pharmacie) => String(item.id)}
            scrollEnabled={sheetExpanded}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }: { item: Pharmacie }) => (
              <PharmacieRow pharmacie={item} T={T} isDark={isDark}
                actif={pharmacieActive?.id === item.id}
                onPress={() => router.push(`/pharmacie/${item.id}`)}
                onCartePress={() => {
                  setPharmacieActive(item)
                  if (item.latitude && item.longitude) {
                    mapRef.current?.animateToRegion({
                      latitude: item.latitude, longitude: item.longitude,
                      latitudeDelta: 0.015, longitudeDelta: 0.015,
                    }, 400)
                  }
                }}
              />
            )}
            ListEmptyComponent={
              !isLoading ? (
                <View style={styles.vide}>
                  <Ionicons name="location-outline" size={36} color={T.sheetSub} />
                  <Text style={[styles.videText, { color: T.sheetSub }]}>
                    Aucune pharmacie trouvée à proximité
                  </Text>
                  {!lat && (
                    <Text style={[styles.videSubText, { color: T.sheetSub }]}>
                      Activez la localisation pour voir les pharmacies proches
                    </Text>
                  )}
                  <TouchableOpacity onPress={() => refetch()} style={styles.retryBtn}>
                    <Ionicons name="refresh" size={14} color={Colors.primary} />
                    <Text style={{ color: Colors.primary, fontSize: Typography.sm, fontWeight: Typography.medium }}>
                      Réessayer
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : null
            }
          />
        )}
      </View>

      {/* Permission refusée */}
      {!locLoad && !lat && (
        <TouchableOpacity
          style={styles.permissionBanner}
          onPress={centrerSurMoi}
        >
          <Ionicons name="location-outline" size={16} color={Colors.white} />
          <Text style={styles.permissionTxt}>
            Activer la localisation pour trouver les pharmacies proches
          </Text>
        </TouchableOpacity>
      )}
    </View>
  )
}

// ── Composant row pharmacie ────────────────────────────────────────────────
function PharmacieRow({ pharmacie, T, isDark, actif, onPress, onCartePress }: {
  pharmacie: Pharmacie; T: typeof lightTheme; isDark: boolean
  actif: boolean; onPress: () => void; onCartePress: () => void
}) {
  return (
    <TouchableOpacity
      style={[styles.card, {
        backgroundColor: T.cardBg, borderColor: actif ? Colors.primary : T.cardBorder,
        borderWidth: actif ? 1.5 : 1,
      }]}
      onPress={onPress}
      onLongPress={onCartePress}
      activeOpacity={0.85}
    >
      <View style={[styles.cardIcone, {
        backgroundColor: pharmacie.est_de_garde
          ? (isDark ? "rgba(229,57,53,0.15)" : "#FFEBEE")
          : (isDark ? "rgba(26,122,74,0.15)"  : Colors.primaryBg),
      }]}>
        <Text style={{
          fontSize: 20, fontWeight: "800",
          color: pharmacie.est_de_garde ? Colors.danger : Colors.primary,
        }}>✚</Text>
      </View>

      <View style={styles.cardBody}>
        <View style={styles.cardRow}>
          <Text style={[styles.cardName, { color: T.cardName }]} numberOfLines={1}>
            {pharmacie.nom}
          </Text>
          {pharmacie.est_de_garde ? (
            <View style={styles.badgeGarde}>
              <Text style={styles.badgeGardeTxt}>DE GARDE</Text>
            </View>
          ) : pharmacie.est_ouverte ? (
            <Text style={[styles.badgeOuvert, { color: Colors.primary }]}>OUVERT</Text>
          ) : (
            <Text style={[styles.badgeFerme, { color: T.cardMeta }]}>FERMÉ</Text>
          )}
        </View>

        {isDark && (
          <Text style={[styles.cardAddr, { color: T.cardAddr }]} numberOfLines={1}>
            {pharmacie.adresse}
          </Text>
        )}

        <View style={styles.cardMeta}>
          <Ionicons name="location-outline" size={11} color={T.cardMeta} />
          <Text style={[styles.cardMetaTxt, { color: T.cardMeta }]}>
            {pharmacie.ville || "—"}
          </Text>
          <Ionicons name="star" size={11} color="#F59E0B" style={{ marginLeft: 8 }} />
          <Text style={[styles.cardMetaTxt, { color: T.cardMeta }]}>4.8</Text>
        </View>
      </View>

      <Ionicons name="chevron-forward" size={16} color={T.cardMeta} />
    </TouchableOpacity>
  )
}

// ── Style carte sombre ─────────────────────────────────────────────────────
const MAP_DARK = [
  { elementType: "geometry",           stylers: [{ color: "#1a1a1a" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a1a" }] },
  { elementType: "labels.text.fill",   stylers: [{ color: "#666666" }] },
  { featureType: "road",         elementType: "geometry",        stylers: [{ color: "#2d2d2d" }] },
  { featureType: "road",         elementType: "geometry.stroke", stylers: [{ color: "#1a1a1a" }] },
  { featureType: "road.highway", elementType: "geometry",        stylers: [{ color: "#383838" }] },
  { featureType: "water",        elementType: "geometry",        stylers: [{ color: "#0d1117" }] },
  { featureType: "poi.park",     elementType: "geometry",        stylers: [{ color: "#1e2d1e" }] },
  { featureType: "poi",          stylers: [{ visibility: "off" }] },
  { featureType: "transit",      stylers: [{ visibility: "off" }] },
]

// ── Styles ─────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  headerWrap: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 10 },
  headerRow:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: Spacing.base, paddingTop: Spacing.sm, paddingBottom: Spacing.xs,
    borderBottomWidth: 1,
  },
  headerTitle:{ fontSize: Typography.lg, fontWeight: Typography.bold },
  villeRow:   { flexDirection: "row", alignItems: "center", gap: 3, marginTop: 1 },
  villeTxt:   { fontSize: Typography.xs },
  locBtn:     { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },

  searchRow:  { paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm },
  searchBox:  {
    flexDirection: "row", alignItems: "center",
    borderRadius: BorderRadius.full, borderWidth: 1,
    paddingHorizontal: Spacing.md, paddingVertical: 10,
    gap: Spacing.sm,
  },
  searchInput:{ flex: 1, fontSize: Typography.base, padding: 0 },

  tagsScroll: {},
  tagsContent:{ paddingHorizontal: Spacing.base, paddingBottom: Spacing.sm, gap: Spacing.sm, flexDirection: "row" },
  tag:        { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 14, paddingVertical: 8, borderRadius: BorderRadius.full, borderWidth: 1 },
  tagText:    { fontSize: Typography.sm, fontWeight: Typography.medium },

  pin:         { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: "#FFFFFF", ...Shadow.md },
  pinSelected: { width: 40, height: 40, borderRadius: 20, borderWidth: 3 },

  sheet:      { position: "absolute", bottom: 0, left: 0, right: 0, borderTopLeftRadius: BorderRadius.xl, borderTopRightRadius: BorderRadius.xl, borderTopWidth: 1, ...Shadow.lg },
  handleZone: { alignItems: "center", paddingVertical: 10 },
  handle:     { width: 40, height: 4, borderRadius: 2 },
  sheetHeader:{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: Spacing.base, marginBottom: Spacing.sm },
  sheetTitle: { fontSize: Typography.lg, fontWeight: Typography.bold },
  sheetSub:   { fontSize: Typography.sm, marginTop: 2 },
  voirToutBtn:{ borderWidth: 1, borderRadius: BorderRadius.full, paddingHorizontal: 12, paddingVertical: 6 },

  card:       { flexDirection: "row", alignItems: "center", gap: Spacing.md, marginHorizontal: Spacing.base, marginBottom: Spacing.sm, padding: Spacing.base, borderRadius: BorderRadius.lg, borderWidth: 1, ...Shadow.sm },
  cardIcone:  { width: 50, height: 50, borderRadius: BorderRadius.md, alignItems: "center", justifyContent: "center" },
  cardBody:   { flex: 1 },
  cardRow:    { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 3 },
  cardName:   { fontSize: Typography.base, fontWeight: Typography.semibold, flex: 1 },
  cardAddr:   { fontSize: Typography.xs, marginBottom: 4 },
  cardMeta:   { flexDirection: "row", alignItems: "center", gap: 3, marginTop: 3 },
  cardMetaTxt:{ fontSize: Typography.xs },

  badgeOuvert:  { fontSize: Typography.xs, fontWeight: Typography.bold },
  badgeFerme:   { fontSize: Typography.xs, fontWeight: Typography.bold },
  badgeGarde:   { borderWidth: 1.5, borderColor: Colors.danger, paddingHorizontal: 7, paddingVertical: 2, borderRadius: BorderRadius.sm },
  badgeGardeTxt:{ color: Colors.danger, fontSize: 9, fontWeight: Typography.bold, letterSpacing: 0.3 },

  loader:    { alignItems: "center", paddingVertical: Spacing.xl, gap: Spacing.sm },
  loaderTxt: { fontSize: Typography.sm },
  vide:      { alignItems: "center", paddingTop: Spacing.xxl, gap: Spacing.sm, paddingHorizontal: Spacing.xxl },
  videText:  { fontSize: Typography.sm, textAlign: "center" },
  videSubText:{ fontSize: Typography.xs, textAlign: "center" },
  retryBtn:  { flexDirection: "row", alignItems: "center", gap: 4, marginTop: Spacing.xs },

  permissionBanner: {
    position: "absolute", bottom: SHEET_MIN + 20,
    left: Spacing.base, right: Spacing.base,
    backgroundColor: Colors.primary, borderRadius: BorderRadius.lg,
    flexDirection: "row", alignItems: "center", gap: Spacing.sm,
    padding: Spacing.md, ...Shadow.md,
  },
  permissionTxt: { color: Colors.white, fontSize: Typography.sm, flex: 1, fontWeight: Typography.medium },
})