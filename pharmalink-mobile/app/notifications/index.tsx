// app/notifications/index.tsx — Notifications — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  FlatList, useColorScheme,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:            "#FFFFFF",
  headerBorder:  "#F0F0F0",
  titleTxt:      "#333333",
  iconTxt:       "#666666",
  bannerBg:      "#F0F0F0",
  bannerTxt:     "#666666",
  chipBg:        "#F5F5F5",
  chipBorder:    "#E0E0E0",
  chipTxt:       "#666666",
  chipActiveBg:  "#0066CC",
  sectionTxt:    "#FF6B6B",
  cardBg:        "#FFFFFF",
  cardBorder:    "#F0F0F0",
  cardIconBg:    "#E6F0FF",
  cardNameTxt:   "#333333",
  cardMsgTxt:    "#666666",
  cardTimeTxt:   "#999999",
  footerTxt:     "#333333",
  footerSubTxt:  "#666666",
}

const darkTheme = {
  bg:            "#1A1A1A",
  headerBorder:  "#333333",
  titleTxt:      "#FFFFFF",
  iconTxt:       "#FFFFFF",
  bannerBg:      "#2D2D2D",
  bannerTxt:     "#999999",
  chipBg:        "#333333",
  chipBorder:    "#444444",
  chipTxt:       "#999999",
  chipActiveBg:  "#0066CC",
  sectionTxt:    "#FF6B6B",
  cardBg:        "#2D2D2D",
  cardBorder:    "#444444",
  cardIconBg:    "#1A3A5F",
  cardNameTxt:   "#FFFFFF",
  cardMsgTxt:    "#999999",
  cardTimeTxt:   "#777777",
  footerTxt:     "#FFFFFF",
  footerSubTxt:  "#999999",
}

// ── Données ───────────────────────────────────────────────────────────────────
const CATEGORIES = [
  { id: "all",    label: "Toutes",  icon: "notifications" },
  { id: "alerts", label: "Alertes", icon: "warning" },
  { id: "stock",  label: "Stocks",  icon: "cube" },
  { id: "advice", label: "Conseils",icon: "bulb" },
]

const NOTIFS_LIGHT = [
  {
    id: "1", type: "urgent", category: "alerts",
    title: "Pharmacie de garde à proximité",
    message: "Pharmacie du Marché est ouverte jusqu'à 08h00 demain.",
    time: "Il y a 30 min", icon: "medical",
    action: "VOIR L'ITINÉRAIRE",
  },
  {
    id: "2", type: "update", category: "stock",
    title: "Produit de retour en stock",
    message: "Votre produit Doliprane 1000mg est de nouveau disponible",
    time: "Il y a 2h", icon: "cube",
  },
  {
    id: "3", type: "update", category: "prescription",
    title: "Ordonnance validée",
    message: "Votre ordonnance n°8829 a été traitée par la Pharmacie Centrale",
    time: "Il y a 5h", icon: "document-text",
  },
  {
    id: "4", type: "reminder", category: "advice",
    title: "Rappel de traitement",
    message: "Il est temps de prendre votre traitement du soir",
    time: "Hier", icon: "time",
  },
  {
    id: "5", type: "update", category: "account",
    title: "Compte mis à jour",
    message: "Vos informations personnelles ont été modifiées avec succès",
    time: "Hier", icon: "person",
  },
]

const NOTIFS_DARK = [
  {
    id: "1", type: "urgent", category: "alerts",
    title: "Pharmacie de garde à proximité",
    message: "La Pharmacie Centrale est ouverte jusqu'à 08h00 demain matin. Cliquez pour l'itinéraire.",
    time: "Il y a 15 min", icon: "medical", urgent: true,
  },
  {
    id: "2", type: "stock", category: "stock",
    title: "Stock disponible",
    message: "Votre médicament Dolirhume est de nouveau disponible à la Pharmacie du Parc.",
    time: "Il y a 2h", icon: "cube",
  },
  {
    id: "3", type: "prescription", category: "prescription",
    title: "Ordonnance traitée",
    message: "Votre pharmacien a validé votre renouvellement. Vous pouvez passer récupérer vos soins.",
    time: "Il y a 5h", icon: "document-text",
  },
  {
    id: "4", type: "reminder", category: "advice",
    title: "Rappel de traitement",
    message: "N'oubliez pas votre prise de midi pour le traitement Amoxicilline.",
    time: "Hier", icon: "time",
  },
]

export default function EcranNotifications() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const [categorie, setCategorie] = useState("all")

  const notifs = isDark ? NOTIFS_DARK : NOTIFS_LIGHT
  const filtrees = categorie === "all"
    ? notifs
    : notifs.filter((n) => n.category === categorie)

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <View style={[styles.header, { borderBottomColor: T.headerBorder }]}>
        <Text style={[styles.titre, { color: T.titleTxt }]}>Notifications</Text>
        <View style={styles.headerRight}>
          <TouchableOpacity style={styles.headerBtn}>
            <Ionicons name="settings-outline" size={22} color={T.iconTxt} />
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

      {/* ── Bannière paramètres (dark only) ─────────────────────────── */}
      {isDark && (
        <View style={[styles.banner, { backgroundColor: T.bannerBg }]}>
          <Text style={[styles.bannerTxt, { color: T.bannerTxt }]}>
            PARAMÈTRES DE RÉCEPTION
          </Text>
        </View>
      )}

      {/* ── Catégories ──────────────────────────────────────────────── */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.catsRow}
      >
        {CATEGORIES.map((c) => {
          const actif = categorie === c.id
          return (
            <TouchableOpacity
              key={c.id}
              style={[styles.catChip, {
                backgroundColor: actif ? T.chipActiveBg : T.chipBg,
                borderColor:     actif ? T.chipActiveBg : T.chipBorder,
              }]}
              onPress={() => setCategorie(c.id)}
            >
              <Ionicons
                name={c.icon as any}
                size={16}
                color={actif ? "#FFFFFF" : T.chipTxt}
              />
              <Text style={[styles.catTxt, {
                color: actif ? "#FFFFFF" : T.chipTxt,
              }]}>
                {c.label}
              </Text>
            </TouchableOpacity>
          )
        })}
      </ScrollView>

      {/* ── Liste ───────────────────────────────────────────────────── */}
      <FlatList
        data={filtrees}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          !isDark ? (
            <View style={styles.sectionHeader}>
              <Text style={[styles.sectionHeaderTxt, { color: T.sectionTxt }]}>
                Alertes urgentes
              </Text>
            </View>
          ) : null
        }
        ListFooterComponent={
          isDark && filtrees.length > 0 ? (
            <View style={styles.footer}>
              <Text style={[styles.footerTxt, { color: T.footerTxt }]}>
                Vous avez tout vu pour aujourd'hui
              </Text>
              <Text style={[styles.footerSubTxt, { color: T.footerSubTxt }]}>
                Revenez plus tard pour de nouvelles alertes.
              </Text>
            </View>
          ) : null
        }
        ListEmptyComponent={
          <View style={styles.vide}>
            <Ionicons name="notifications-off-outline" size={52} color={T.chipTxt} />
            <Text style={[styles.videText, { color: T.chipTxt }]}>
              Aucune notification
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <NotifCard item={item} T={T} isDark={isDark} />
        )}
      />
    </SafeAreaView>
  )
}

// ── Carte notification ────────────────────────────────────────────────────────
function NotifCard({
  item, T, isDark,
}: {
  item:   (typeof NOTIFS_LIGHT)[0] & { urgent?: boolean }
  T:      typeof lightTheme
  isDark: boolean
}) {
  const isUrgent = item.type === "urgent"

  return (
    <TouchableOpacity style={[
      styles.card,
      { backgroundColor: T.cardBg, borderColor: T.cardBorder },
      isUrgent && styles.cardUrgent,
    ]}>
      <View style={styles.cardContent}>
        {/* Icône */}
        <View style={[
          styles.cardIcone,
          { backgroundColor: isUrgent ? "#FF6B6B" : T.cardIconBg },
        ]}>
          <Ionicons
            name={(item as any).urgent ? "warning" : item.icon as any}
            size={22}
            color={isUrgent ? "#FFFFFF" : "#0066CC"}
          />
        </View>

        {/* Texte */}
        <View style={styles.cardBody}>
          {/* Titre + badge urgent */}
          <View style={styles.cardTitleRow}>
            <Text style={[
              styles.cardTitle,
              { color: isUrgent ? "#FF6B6B" : T.cardNameTxt },
            ]} numberOfLines={1}>
              {item.title}
            </Text>
            {isUrgent && (
              <View style={styles.urgentBadge}>
                <Text style={styles.urgentBadgeTxt}>URGENT</Text>
              </View>
            )}
          </View>

          {/* Message */}
          <Text style={[styles.cardMsg, { color: T.cardMsgTxt }]} numberOfLines={2}>
            {item.message}
          </Text>

          {/* Footer : temps + action */}
          <View style={styles.cardFoot}>
            <Text style={[styles.cardTime, { color: T.cardTimeTxt }]}>
              {item.time}
            </Text>
            {(item as any).action && (
              <TouchableOpacity style={styles.actionBtn}>
                <Text style={styles.actionBtnTxt}>{(item as any).action}</Text>
                <Ionicons name="arrow-forward" size={14} color="#0066CC" />
              </TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: Spacing.base, paddingVertical: Spacing.md,
    borderBottomWidth: 1,
  },
  titre:       { fontSize: Typography.xl, fontWeight: Typography.bold },
  headerRight: { flexDirection: "row", gap: Spacing.sm },
  headerBtn:   { padding: 4 },

  banner:    { paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm },
  bannerTxt: { fontSize: Typography.xs, fontWeight: Typography.semibold, letterSpacing: 0.5 },

  catsRow: {
    paddingHorizontal: Spacing.base,
    paddingVertical:   Spacing.md,
    gap:               Spacing.sm,
    flexDirection:     "row",
  },
  catChip: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: BorderRadius.full, borderWidth: 1,
  },
  catTxt: { fontSize: Typography.sm },

  list:          { paddingHorizontal: Spacing.base, paddingBottom: 40 },
  sectionHeader: { marginBottom: Spacing.sm },
  sectionHeaderTxt: { fontSize: Typography.base, fontWeight: Typography.semibold },

  card: {
    borderRadius: BorderRadius.lg, padding: Spacing.base,
    marginBottom: Spacing.md, borderWidth: 1, ...Shadow.sm,
  },
  cardUrgent:  { borderLeftWidth: 4, borderLeftColor: "#FF6B6B" },
  cardContent: { flexDirection: "row" },
  cardIcone:   {
    width: 48, height: 48, borderRadius: 24,
    alignItems: "center", justifyContent: "center",
    marginRight: Spacing.md,
  },
  cardBody:    { flex: 1 },
  cardTitleRow:{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 },
  cardTitle:   { fontSize: Typography.base, fontWeight: Typography.semibold, flex: 1 },
  urgentBadge: { backgroundColor: "#FFE5E5", paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  urgentBadgeTxt: { fontSize: 10, color: "#FF6B6B", fontWeight: Typography.semibold },
  cardMsg:     { fontSize: Typography.sm, lineHeight: 20, marginBottom: Spacing.sm },
  cardFoot:    { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  cardTime:    { fontSize: Typography.xs },
  actionBtn:   { flexDirection: "row", alignItems: "center", gap: 3 },
  actionBtnTxt:{ fontSize: Typography.xs, color: "#0066CC", fontWeight: Typography.semibold },

  footer:      { alignItems: "center", marginTop: Spacing.xl, marginBottom: Spacing.base },
  footerTxt:   { fontSize: Typography.base, fontWeight: Typography.semibold },
  footerSubTxt:{ fontSize: Typography.sm, textAlign: "center", marginTop: 4 },

  vide:     { alignItems: "center", paddingTop: 60, gap: Spacing.sm },
  videText: { fontSize: Typography.base },
})