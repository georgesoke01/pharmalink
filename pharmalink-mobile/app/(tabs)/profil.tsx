// app/(tabs)/profil.tsx — Profil & Paramètres — Light & Dark
import { useState } from "react"
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  Switch, Alert, useColorScheme,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { useAuthStore } from "@/store"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import type { Utilisateur } from "@/types"

// ── Thèmes ────────────────────────────────────────────────────────────────────
const lightTheme = {
  bg:           "#FFFFFF",
  headerBorder: "#F0F0F0",
  title:        "#333333",
  iconTxt:      "#666666",
  cardBg:       "#F9F9F9",
  cardBorder:   "#F0F0F0",
  nameTxt:      "#333333",
  emailTxt:     "#666666",
  editBorder:   "#0066CC",
  sectionTxt:   "#666666",
  itemBg:       "#FFFFFF",
  itemBorder:   "#F0F0F0",
  itemTxt:      "#333333",
  itemSubTxt:   "#666666",
  itemChevron:  "#999999",
  trackBg:      "#FFFFFF",
  trackBorder:  "#F0F0F0",
  version:      "#999999",
}
const darkTheme = {
  bg:           "#1A1A1A",
  headerBorder: "#333333",
  title:        "#FFFFFF",
  iconTxt:      "#FFFFFF",
  cardBg:       "#2D2D2D",
  cardBorder:   "#444444",
  nameTxt:      "#FFFFFF",
  emailTxt:     "#999999",
  editBorder:   "#0066CC",
  sectionTxt:   "#999999",
  itemBg:       "#2D2D2D",
  itemBorder:   "#444444",
  itemTxt:      "#FFFFFF",
  itemSubTxt:   "#999999",
  itemChevron:  "#999999",
  trackBg:      "#2D2D2D",
  trackBorder:  "#444444",
  version:      "#666666",
}

const FAVORIS_LIGHT = [
  { id: "1", nom: "Pharmacie Centrale",  statut: "Ouvert", dist: "0.4 km" },
  { id: "2", nom: "Pharmacie des Lilas", statut: "Fermé",  dist: "1.2 km" },
]
const FAVORIS_DARK = [
  { id: "1", nom: "Pharmacie Centrale",  statut: "Ouvert", dist: "0.8 km" },
]

export default function EcranProfil() {
  const colorScheme           = useColorScheme()
  const isDark                = colorScheme === "dark"
  const T                     = isDark ? darkTheme : lightTheme

  const { utilisateur, estConnecte, logout } = useAuthStore()
  const [notifs,   setNotifs]   = useState(true)
  const [rayon,    setRayon]    = useState("10 km")

  const favoris = isDark ? FAVORIS_DARK : FAVORIS_LIGHT

  const confirmerLogout = () => {
    Alert.alert(
      "Déconnexion",
      "Voulez-vous vraiment vous déconnecter ?",
      [
        { text: "Annuler", style: "cancel" },
        { text: "Se déconnecter", style: "destructive", onPress: logout },
      ]
    )
  }

  // ── Non connecté ─────────────────────────────────────────────────────────────
  if (!estConnecte) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>
        <View style={styles.nonConnecte}>
          <View style={[styles.avatarGrand, { backgroundColor: "#0066CC" }]}>
            <Ionicons name="person" size={48} color="#FFFFFF" />
          </View>
          <Text style={[styles.nonConnecteTitre, { color: T.nameTxt }]}>
            Connectez-vous
          </Text>
          <Text style={[styles.nonConnecteDesc, { color: T.emailTxt }]}>
            Accédez à vos pharmacies favorites et suivez vos traitements
          </Text>
          <TouchableOpacity
            style={styles.btnLogin}
            onPress={() => router.push("/auth/connexion")}
          >
            <Text style={styles.btnLoginTxt}>Se connecter</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btnRegister, { borderColor: T.editBorder }]}
            onPress={() => router.push("/auth/inscription")}
          >
            <Text style={[styles.btnRegisterTxt, { color: T.editBorder }]}>
              Créer un compte
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <View style={[styles.header, { borderBottomColor: T.headerBorder }]}>
        <Text style={[styles.titre, { color: T.title }]}>
          Profil et Paramètres
        </Text>
        <TouchableOpacity>
          <Ionicons
            name={isDark ? "sunny-outline" : "moon-outline"}
            size={22}
            color={T.iconTxt}
          />
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}>

        {/* ── Carte profil ─────────────────────────────────────────── */}
        <View style={[styles.profileCard, { backgroundColor: T.cardBg, borderColor: T.cardBorder }]}>
          {/* Avatar */}
          <View style={[styles.avatar, { backgroundColor: isDark ? "#1A3A5F" : "#0066CC" }]}>
            <Text style={styles.avatarInitiales}>
              {utilisateur?.nom_complet?.split(" ").map((n) => n[0]).join("") ?? "U"}
            </Text>
          </View>

          {/* Infos */}
          <View style={styles.profileInfo}>
            <Text style={[styles.profileNom,   { color: T.nameTxt }]}>
              {utilisateur?.nom_complet ?? "Utilisateur"}
            </Text>
            <Text style={[styles.profileEmail, { color: T.emailTxt }]}>
              {utilisateur?.email ?? ""}
            </Text>
          </View>

          {/* Bouton modifier */}
          <TouchableOpacity style={[styles.btnEdit, { borderColor: T.editBorder }]}>
            <Text style={[styles.btnEditTxt, { color: T.editBorder }]}>Modifier</Text>
          </TouchableOpacity>
        </View>

        {/* ── Pharmacies favorites ─────────────────────────────────── */}
        <Section titre="MES PHARMACIES FAVORITES" T={T}>
          {favoris.map((ph) => (
            <TouchableOpacity
              key={ph.id}
              style={[styles.favItem, { backgroundColor: T.itemBg, borderColor: T.itemBorder }]}
            >
              <View style={styles.favLeft}>
                <Ionicons name="medical" size={22} color="#0066CC" />
                <View>
                  <Text style={[styles.favNom, { color: T.itemTxt }]}>{ph.nom}</Text>
                  <View style={styles.favMeta}>
                    <Text style={{
                      fontSize: Typography.xs, fontWeight: Typography.medium,
                      color: ph.statut === "Ouvert" ? "#4CAF50" : "#FF6B6B",
                    }}>
                      {ph.statut}
                    </Text>
                    <Text style={[{ fontSize: Typography.xs, color: T.itemSubTxt }]}>
                      · {ph.dist}
                    </Text>
                  </View>
                </View>
              </View>
              <View style={styles.favRight}>
                <Text style={{ fontSize: Typography.xs, color: "#0066CC" }}>Modifier</Text>
                <Ionicons name="chevron-forward" size={18} color={T.itemChevron} />
              </View>
            </TouchableOpacity>
          ))}
        </Section>

        {/* ── Suivi produits ───────────────────────────────────────── */}
        <Section titre="SUIVI DE PRODUITS" T={T}>
          <View style={[styles.trackCard, { backgroundColor: T.trackBg, borderColor: T.trackBorder }]}>
            <View style={styles.trackLeft}>
              <Ionicons name="medical" size={22} color="#0066CC" />
              <View>
                <Text style={[styles.trackTitre, { color: T.itemTxt }]}>
                  {isDark ? "Alerte Disponibilité" : "Mes rappels de traitement"}
                </Text>
                <Text style={[styles.trackSub, { color: T.itemSubTxt }]}>
                  {isDark ? "2 produits surveillés" : "3 médicaments actifs"}
                </Text>
              </View>
            </View>
            <TouchableOpacity style={styles.favRight}>
              <Text style={{ fontSize: Typography.xs, color: "#0066CC" }}>Modifier</Text>
              <Ionicons name="chevron-forward" size={18} color={T.itemChevron} />
            </TouchableOpacity>
          </View>
        </Section>

        {/* ── Préférences ──────────────────────────────────────────── */}
        <Section titre="PRÉFÉRENCES" T={T}>
          <SettingItem
            icon="navigate" label={isDark ? "Rayon de recherche (km)" : "Distance maximale"}
            value={rayon} type="value" T={T} onPress={() => {}}
          />
          <SettingItem
            icon="notifications" label="Notifications Push"
            value={notifs} type="switch" T={T}
            onPress={() => setNotifs(!notifs)}
          />
          <SettingItem
            icon="moon" label="Mode sombre"
            value={isDark} type="switch" T={T} onPress={() => {}}
          />
          <SettingItem icon="information-circle" label="À propos"       T={T} onPress={() => {}} />
          <SettingItem icon="document-text"      label="Mentions légales" T={T} onPress={() => {}} />
        </Section>

        <Text style={[styles.version, { color: T.version }]}>
          Version 1.0.0 — PharmaLink Bénin
        </Text>

        {/* ── Déconnexion ──────────────────────────────────────────── */}
        <TouchableOpacity
          style={[styles.btnLogout, { borderTopColor: isDark ? "#444" : "#F0F0F0" }]}
          onPress={confirmerLogout}
        >
          <Ionicons name="log-out-outline" size={20} color="#FF6B6B" />
          <Text style={styles.btnLogoutTxt}>Déconnexion</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  )
}

// ── Composants réutilisables ──────────────────────────────────────────────────
function Section({ titre, children, T }: {
  titre: string; children: React.ReactNode; T: typeof lightTheme
}) {
  return (
    <View style={styles.section}>
      <Text style={[styles.sectionTitre, { color: T.sectionTxt }]}>{titre}</Text>
      {children}
    </View>
  )
}

function SettingItem({ icon, label, value, type, T, onPress }: {
  icon: string; label: string; T: typeof lightTheme
  value?: any; type?: "switch" | "value" | "default"; onPress: () => void
}) {
  return (
    <TouchableOpacity
      style={[styles.settingItem, { backgroundColor: T.itemBg, borderBottomColor: T.itemBorder }]}
      onPress={onPress}
    >
      <View style={styles.settingLeft}>
        <Ionicons name={icon as any} size={20} color={T.iconTxt === "#FFFFFF" ? "#0066CC" : "#666666"} />
        <Text style={[styles.settingLabel, { color: T.itemTxt }]}>{label}</Text>
      </View>
      {type === "switch" ? (
        <Switch
          value={Boolean(value)}
          onValueChange={onPress}
          trackColor={{ false: "#DDDDDD", true: "#0066CC" }}
          thumbColor="#FFFFFF"
        />
      ) : type === "value" ? (
        <View style={styles.settingRight}>
          <Text style={[styles.settingVal, { color: T.itemSubTxt }]}>{value}</Text>
          <Ionicons name="chevron-forward" size={18} color={T.itemChevron} />
        </View>
      ) : (
        <Ionicons name="chevron-forward" size={18} color={T.itemChevron} />
      )}
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
  titre: { fontSize: Typography.xl, fontWeight: Typography.bold },

  nonConnecte: { flex: 1, alignItems: "center", justifyContent: "center", padding: Spacing.xxl, gap: Spacing.base },
  avatarGrand: { width: 80, height: 80, borderRadius: 40, alignItems: "center", justifyContent: "center" },
  nonConnecteTitre: { fontSize: Typography.xl, fontWeight: Typography.bold, textAlign: "center" },
  nonConnecteDesc:  { fontSize: Typography.sm, textAlign: "center", lineHeight: 20 },
  btnLogin:    { width: "100%", backgroundColor: "#0066CC", paddingVertical: Spacing.md, borderRadius: BorderRadius.lg, alignItems: "center" },
  btnLoginTxt: { color: "#FFFFFF", fontSize: Typography.base, fontWeight: Typography.semibold },
  btnRegister: { width: "100%", borderWidth: 1.5, paddingVertical: Spacing.md, borderRadius: BorderRadius.lg, alignItems: "center" },
  btnRegisterTxt: { fontSize: Typography.base, fontWeight: Typography.semibold },

  profileCard: {
    flexDirection: "row", alignItems: "center",
    marginHorizontal: Spacing.base, marginTop: Spacing.base,
    marginBottom: Spacing.xs, padding: Spacing.base,
    borderRadius: BorderRadius.lg, borderWidth: 1,
  },
  avatar:         { width: 60, height: 60, borderRadius: 30, alignItems: "center", justifyContent: "center", marginRight: Spacing.base },
  avatarInitiales:{ fontSize: Typography.xl, color: "#FFFFFF", fontWeight: Typography.semibold },
  profileInfo:    { flex: 1 },
  profileNom:     { fontSize: Typography.base, fontWeight: Typography.semibold },
  profileEmail:   { fontSize: Typography.sm, marginTop: 2 },
  btnEdit:        { borderWidth: 1, borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 5 },
  btnEditTxt:     { fontSize: Typography.xs, fontWeight: Typography.semibold },

  section:      { paddingHorizontal: Spacing.base, marginTop: Spacing.xl },
  sectionTitre: { fontSize: Typography.xs, fontWeight: Typography.semibold, letterSpacing: 0.8, marginBottom: Spacing.sm },

  favItem:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: Spacing.md, borderRadius: BorderRadius.md, marginBottom: Spacing.xs, borderWidth: 1 },
  favLeft:  { flexDirection: "row", alignItems: "center", gap: Spacing.md },
  favNom:   { fontSize: Typography.base, fontWeight: Typography.medium },
  favMeta:  { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 2 },
  favRight: { flexDirection: "row", alignItems: "center" },

  trackCard:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: Spacing.base, borderRadius: BorderRadius.md, borderWidth: 1 },
  trackLeft:  { flexDirection: "row", alignItems: "center", gap: Spacing.md },
  trackTitre: { fontSize: Typography.base, fontWeight: Typography.medium },
  trackSub:   { fontSize: Typography.xs, marginTop: 2 },

  settingItem:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: Spacing.md, paddingHorizontal: Spacing.base, borderBottomWidth: 1 },
  settingLeft:  { flexDirection: "row", alignItems: "center", gap: Spacing.md },
  settingLabel: { fontSize: Typography.base },
  settingRight: { flexDirection: "row", alignItems: "center", gap: 4 },
  settingVal:   { fontSize: Typography.sm },

  version:    { textAlign: "center", fontSize: Typography.xs, marginTop: Spacing.xl, marginBottom: Spacing.sm },
  btnLogout:  { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: Spacing.sm, paddingVertical: Spacing.base, marginHorizontal: Spacing.base, marginBottom: Spacing.base, borderTopWidth: 1 },
  btnLogoutTxt: { fontSize: Typography.base, color: "#FF6B6B", fontWeight: Typography.semibold },
})