// app/itineraire/[id].tsx — Écran itinéraire — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  Linking, Platform, useColorScheme, Dimensions,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { useLocalSearchParams, router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps"
import { usePharmacie } from "@/hooks/usePharmacies"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"

const { width } = Dimensions.get("window")

// ── Thèmes ─────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:            "#FFFFFF",
  headerBorder:  "#F0F0F0",
  titleTxt:      "#333333",
  iconTxt:       "#666666",
  transportBg:   "#F5F5F5",
  transportTxt:  "#333333",
  transportSub:  "#666666",
  transportActif:"#0066CC",
  sectionTxt:    "#333333",
  stepNumBg:     "#F0F0F0",
  stepNumTxt:    "#666666",
  stepLine:      "#E0E0E0",
  stepTxt:       "#333333",
  stepSub:       "#666666",
  stepDist:      "#666666",
  timeBadgeBg:   "#FFFFFF",
  timeBadgeTxt:  "#333333",
}

const darkTheme = {
  bg:            "#1A1A1A",
  headerBorder:  "#333333",
  titleTxt:      "#FFFFFF",
  iconTxt:       "#FFFFFF",
  transportBg:   "#333333",
  transportTxt:  "#FFFFFF",
  transportSub:  "#999999",
  transportActif:"#0066CC",
  sectionTxt:    "#FFFFFF",
  stepNumBg:     "#444444",
  stepNumTxt:    "#FFFFFF",
  stepLine:      "#444444",
  stepTxt:       "#FFFFFF",
  stepSub:       "#999999",
  stepDist:      "#999999",
  timeBadgeBg:   "#444444",
  timeBadgeTxt:  "#FFFFFF",
}

const TRANSPORTS = [
  { id: "walk", label: "Marcher",  icon: "walk",  time: "12" },
  { id: "car",  label: "Voiture", icon: "car",   time: "4"  },
  { id: "bus",  label: "Bus",     icon: "bus",   time: "8"  },
]

const INSTRUCTIONS_LIGHT = [
  { id: 1, text: "Tournez à gauche Rue de Rivoli",       detail: "Dans 50m",         dist: "50m" },
  { id: 2, text: "Continuez sur 200m",                    detail: "Tout droit",        dist: "200m" },
  { id: 3, text: "Tournez à droite Place de la Concorde", detail: "Dans 250m",        dist: "250m" },
]

const INSTRUCTIONS_DARK = [
  { id: 1, text: "Tournez à gauche Rue de Rivoli",       detail: "Dans 50 mètres",             dist: "50m",   dest: false },
  { id: 2, text: "Continuez tout droit sur 800m",        detail: "Avenue des Champs-Élysées",  dist: "800m",  dest: false },
  { id: 3, text: "Prendre à droite Rue de la Paix",      detail: "Vers votre destination",     dist: "1.2km", dest: false },
  { id: 4, text: "Pharmacie Centrale",                   detail: "Arrivée estimée à 14:45",    dist: "2.1km", dest: true  },
]

export default function EcranItineraire() {
  const { id }      = useLocalSearchParams<{ id: string }>()
  const pharmacieId = Number(id)

  const colorScheme    = useColorScheme()
  const isDark         = colorScheme === "dark"
  const T              = isDark ? darkTheme : lightTheme

  const [transport, setTransport] = useState("walk")
  const { data: pharmacie }       = usePharmacie(pharmacieId)

  const instructions = isDark ? INSTRUCTIONS_DARK : INSTRUCTIONS_LIGHT
  const duree        = TRANSPORTS.find((t) => t.id === transport)?.time ?? "?"

  const demarrerNavigation = () => {
    if (!pharmacie?.latitude || !pharmacie?.longitude) return
    const url = Platform.OS === "ios"
      ? `maps://?daddr=${pharmacie.latitude},${pharmacie.longitude}&dirflg=${
          transport === "walk" ? "w" : transport === "car" ? "d" : "r"
        }`
      : `https://www.google.com/maps/dir/?api=1&destination=${pharmacie.latitude},${pharmacie.longitude}&travelmode=${
          transport === "walk" ? "walking" : transport === "car" ? "driving" : "transit"
        }`
    Linking.openURL(url)
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <View style={[styles.header, { borderBottomColor: T.headerBorder }]}>
        <TouchableOpacity style={styles.headerBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={T.iconTxt} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: T.titleTxt }]}>Itinéraire</Text>
        <View style={styles.headerRight}>
          <TouchableOpacity style={styles.headerBtn}>
            <Ionicons name="share-social-outline" size={22} color={T.iconTxt} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn}>
            <Ionicons
              name={isDark ? "sunny-outline" : "moon-outline"}
              size={22}
              color={T.iconTxt}
            />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>

        {/* ── Carte ───────────────────────────────────────────────── */}
        <View style={styles.mapWrap}>
          {pharmacie?.latitude && pharmacie?.longitude ? (
            <MapView
              style={styles.map}
              provider={Platform.OS === "android" ? PROVIDER_GOOGLE : undefined}
              customMapStyle={isDark ? MAP_DARK : []}
              initialRegion={{
                latitude:       pharmacie.latitude,
                longitude:      pharmacie.longitude,
                latitudeDelta:  0.02,
                longitudeDelta: 0.02,
              }}
              showsUserLocation
            >
              <Marker
                coordinate={{
                  latitude:  pharmacie.latitude,
                  longitude: pharmacie.longitude,
                }}
              >
                <View style={styles.pin}>
                  <Ionicons name="medkit" size={14} color="#FFFFFF" />
                </View>
              </Marker>
            </MapView>
          ) : (
            <View style={[styles.mapPlaceholder, {
              backgroundColor: isDark ? "#2D2D2D" : "#E8EEF3",
            }]}>
              <Ionicons name="map" size={40} color={isDark ? "#555" : "#AAB8C0"} />
            </View>
          )}

          {/* Badges temps */}
          <View style={styles.timeBadges}>
            {TRANSPORTS.map((t) => (
              <View key={t.id} style={[styles.timeBadge, { backgroundColor: T.timeBadgeBg }]}>
                <Text style={[styles.timeBadgeTxt, { color: T.timeBadgeTxt }]}>
                  {t.time} min
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* ── Options de transport ─────────────────────────────────── */}
        <View style={styles.transportsRow}>
          {TRANSPORTS.map((t) => {
            const actif = transport === t.id
            return (
              <TouchableOpacity
                key={t.id}
                style={[styles.transportCard, {
                  backgroundColor: actif ? T.transportActif : T.transportBg,
                }]}
                onPress={() => setTransport(t.id)}
              >
                <Ionicons
                  name={t.icon as any}
                  size={24}
                  color={actif ? "#FFFFFF" : T.transportSub}
                />
                <Text style={[styles.transportTime, {
                  color: actif ? "#FFFFFF" : T.transportTxt,
                }]}>
                  {t.time} MIN
                </Text>
                <Text style={[styles.transportLabel, {
                  color: actif ? "rgba(255,255,255,0.85)" : T.transportSub,
                }]}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            )
          })}
        </View>

        {/* ── Instructions ─────────────────────────────────────────── */}
        <View style={styles.instructionsWrap}>
          <Text style={[styles.sectionTitle, { color: T.sectionTxt }]}>
            Instructions
          </Text>

          {instructions.map((step, index) => (
            <View key={step.id} style={styles.step}>
              {/* Numéro + ligne */}
              <View style={styles.stepLeft}>
                <View style={[
                  styles.stepNum,
                  { backgroundColor: (step as any).dest ? "#0066CC" : T.stepNumBg },
                ]}>
                  <Text style={[
                    styles.stepNumTxt,
                    { color: (step as any).dest ? "#FFFFFF" : T.stepNumTxt },
                  ]}>
                    {index + 1}
                  </Text>
                </View>
                {index < instructions.length - 1 && (
                  <View style={[styles.stepLine, { backgroundColor: T.stepLine }]} />
                )}
              </View>

              {/* Texte */}
              <View style={styles.stepContent}>
                <Text style={[
                  styles.stepTxt,
                  { color: (step as any).dest ? "#0066CC" : T.stepTxt },
                  (step as any).dest && { fontWeight: Typography.semibold },
                ]}>
                  {step.text}
                </Text>
                <Text style={[styles.stepSub, { color: T.stepSub }]}>
                  {step.detail}
                </Text>
              </View>

              <Text style={[styles.stepDist, { color: T.stepDist }]}>
                {step.dist}
              </Text>
            </View>
          ))}
        </View>

        {/* ── Bouton démarrer ──────────────────────────────────────── */}
        <TouchableOpacity
          style={styles.btnDemarrer}
          onPress={demarrerNavigation}
        >
          <Ionicons name="navigate" size={22} color="#FFFFFF" />
          <Text style={styles.btnDemarrerTxt}>Démarrer la navigation</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  )
}

const MAP_DARK = [
  { elementType: "geometry",           stylers: [{ color: "#1a1a1a" }] },
  { elementType: "labels.text.fill",   stylers: [{ color: "#666666" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a1a" }] },
  { featureType: "road",      elementType: "geometry",        stylers: [{ color: "#2d2d2d" }] },
  { featureType: "road.highway", elementType: "geometry",     stylers: [{ color: "#383838" }] },
  { featureType: "water",     elementType: "geometry",        stylers: [{ color: "#0d1117" }] },
  { featureType: "poi",       stylers: [{ visibility: "off" }] },
]

const styles = StyleSheet.create({
  container: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: Spacing.base, paddingVertical: Spacing.md,
    borderBottomWidth: 1,
  },
  headerBtn:   { padding: 4 },
  headerTitle: { fontSize: Typography.lg, fontWeight: Typography.semibold },
  headerRight: { flexDirection: "row", gap: Spacing.sm },

  mapWrap:        { margin: Spacing.base, borderRadius: BorderRadius.lg, overflow: "hidden", height: 200 },
  map:            { flex: 1 },
  mapPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center" },
  pin:            {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: Colors.primary,
    alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "#FFFFFF",
  },
  timeBadges:  { position: "absolute", bottom: 10, right: 10, flexDirection: "row", gap: 6 },
  timeBadge:   { paddingHorizontal: 8, paddingVertical: 4, borderRadius: BorderRadius.full, ...Shadow.sm },
  timeBadgeTxt:{ fontSize: Typography.xs, fontWeight: Typography.semibold },

  transportsRow: { flexDirection: "row", justifyContent: "space-around", paddingHorizontal: Spacing.base, marginBottom: Spacing.xl },
  transportCard: { alignItems: "center", padding: Spacing.md, borderRadius: BorderRadius.lg, minWidth: 100 },
  transportTime: { fontSize: Typography.lg, fontWeight: Typography.bold, marginTop: 4 },
  transportLabel:{ fontSize: Typography.xs, marginTop: 2 },

  instructionsWrap: { paddingHorizontal: Spacing.base, marginBottom: Spacing.xl },
  sectionTitle:     { fontSize: Typography.lg, fontWeight: Typography.semibold, marginBottom: Spacing.base },

  step:        { flexDirection: "row", marginBottom: Spacing.base },
  stepLeft:    { width: 30, alignItems: "center" },
  stepNum:     { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  stepNumTxt:  { fontSize: Typography.xs, fontWeight: Typography.semibold },
  stepLine:    { width: 2, flex: 1, marginTop: 4, minHeight: 24 },
  stepContent: { flex: 1, marginLeft: Spacing.md },
  stepTxt:     { fontSize: Typography.base, fontWeight: Typography.medium },
  stepSub:     { fontSize: Typography.sm, marginTop: 2 },
  stepDist:    { fontSize: Typography.sm, fontWeight: Typography.medium, alignSelf: "flex-start", marginTop: 3 },

  btnDemarrer:    {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: Spacing.sm, backgroundColor: "#0066CC",
    marginHorizontal: Spacing.base, marginBottom: Spacing.xxl,
    paddingVertical: Spacing.base, borderRadius: BorderRadius.lg,
    ...Shadow.md,
  },
  btnDemarrerTxt: { color: "#FFFFFF", fontSize: Typography.base, fontWeight: Typography.semibold },
})