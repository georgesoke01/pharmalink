// app/produit/[id].tsx  — Fiche détaillée d'un médicament
import { useState } from "react"
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, ActivityIndicator,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { useLocalSearchParams, router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { Image } from "expo-image"
import { useProduit, useProduitsPharmacie } from "@/hooks/usePharmacies"
import { usePharmacies } from "@/hooks/usePharmacies"
import { Colors, Spacing, BorderRadius, Shadow, Typography } from "@/constants"
import type { ProduitAvecStock } from "@/types"

export default function FicheProduit() {
  const { id }      = useLocalSearchParams<{ id: string }>()
  const produitId   = Number(id)
  const [onglet, setOnglet] = useState<"info" | "disponibilite">("info")

  const { data: produit, isLoading } = useProduit(produitId)

  // Recherche des pharmacies où ce produit est disponible
  const { data: phData, isLoading: loadPh, fetchNextPage, hasNextPage } =
    usePharmacies({ page_size: 10 })

  const pharmacies = phData?.pages.flatMap((p) => p.results) ?? []

  if (isLoading) {
    return (
      <View style={styles.loader}>
        <ActivityIndicator color={Colors.primary} size="large" />
      </View>
    )
  }

  if (!produit) {
    return (
      <View style={styles.loader}>
        <Text style={styles.erreurText}>Produit introuvable</Text>
      </View>
    )
  }

  const categorieLabel: Record<string, string> = {
    medicament:   "Médicament",
    parapharmacie:"Parapharmacie",
    materiel:     "Matériel médical",
    autre:        "Autre",
  }

  const formeLabel: Record<string, string> = {
    comprimes:    "Comprimés",
    gelules:      "Gélules",
    sirop:        "Sirop",
    injection:    "Injectable",
    creme:        "Crème / Pommade",
    gouttes:      "Gouttes",
    suppositoire: "Suppositoire",
    sachet:       "Sachet",
    spray:        "Spray",
    autre:        "Autre",
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.btnRetour} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={Colors.gray900} />
        </TouchableOpacity>
        <Text style={styles.headerTitre} numberOfLines={1}>
          {produit.nom}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero ────────────────────────────────────────────────────── */}
        <View style={styles.hero}>
          {produit.image ? (
            <Image
              source={{ uri: produit.image }}
              style={styles.image}
              contentFit="contain"
            />
          ) : (
            <View style={[
              styles.imagePlaceholder,
              produit.sur_ordonnance && { backgroundColor: "#F3E5F5" },
            ]}>
              <Ionicons
                name="medical"
                size={48}
                color={produit.sur_ordonnance ? Colors.ordonnance : Colors.primary}
              />
            </View>
          )}

          <View style={styles.heroInfo}>
            <Text style={styles.nomProduit}>{produit.nom}</Text>

            {produit.nom_generique ? (
              <Text style={styles.nomGenerique}>{produit.nom_generique}</Text>
            ) : null}

            {/* Badges */}
            <View style={styles.badgesRow}>
              <BadgeProduit
                label={categorieLabel[produit.categorie] ?? produit.categorie}
                color={Colors.primary}
                bg={Colors.primaryBg}
              />
              {produit.sur_ordonnance && (
                <BadgeProduit
                  label="📋 Ordonnance"
                  color={Colors.ordonnance}
                  bg="#F3E5F5"
                />
              )}
              {produit.forme ? (
                <BadgeProduit
                  label={formeLabel[produit.forme] ?? produit.forme}
                  color={Colors.gray600}
                  bg={Colors.gray100}
                />
              ) : null}
            </View>
          </View>
        </View>

        {/* ── Onglets ─────────────────────────────────────────────────── */}
        <View style={styles.onglets}>
          {(["info", "disponibilite"] as const).map((o) => (
            <TouchableOpacity
              key={o}
              style={[styles.onglet, onglet === o && styles.ongletActif]}
              onPress={() => setOnglet(o)}
            >
              <Text style={[styles.ongletText, onglet === o && styles.ongletTextActif]}>
                {o === "info" ? "Informations" : "Où trouver ?"}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* ── Onglet Informations ──────────────────────────────────────── */}
        {onglet === "info" && (
          <View style={styles.section}>

            {/* Informations médicales */}
            <View style={styles.infoCard}>
              {produit.laboratoire ? (
                <InfoLigne icon="business" label="Laboratoire" valeur={produit.laboratoire} />
              ) : null}
              {produit.dosage ? (
                <InfoLigne icon="flask" label="Dosage" valeur={produit.dosage} />
              ) : null}
              {produit.forme ? (
                <InfoLigne icon="tablet-portrait" label="Forme" valeur={formeLabel[produit.forme] ?? produit.forme} />
              ) : null}
              {produit.code_cip13 ? (
                <InfoLigne icon="barcode" label="Code CIP13" valeur={produit.code_cip13} />
              ) : null}
              <InfoLigne
                icon="medical"
                label="Catégorie"
                valeur={categorieLabel[produit.categorie] ?? produit.categorie}
              />
              <InfoLigne
                icon="document-text"
                label="Ordonnance"
                valeur={produit.sur_ordonnance ? "Requise" : "Non requise"}
                valueColor={produit.sur_ordonnance ? Colors.ordonnance : Colors.success}
              />
            </View>

            {/* Description */}
            {produit.description ? (
              <View style={styles.blocTexte}>
                <Text style={styles.blocTitre}>Description</Text>
                <Text style={styles.blocContenu}>{produit.description}</Text>
              </View>
            ) : null}

            {/* Contre-indications */}
            {produit.contre_indications ? (
              <View style={[styles.blocTexte, styles.blocWarning]}>
                <View style={styles.blocWarningHeader}>
                  <Ionicons name="warning" size={16} color={Colors.warning} />
                  <Text style={[styles.blocTitre, { color: Colors.warning }]}>
                    Contre-indications
                  </Text>
                </View>
                <Text style={styles.blocContenu}>
                  {produit.contre_indications}
                </Text>
              </View>
            ) : null}

            {/* Avertissement ordonnance */}
            {produit.sur_ordonnance && (
              <View style={styles.avertissement}>
                <Ionicons name="alert-circle" size={20} color={Colors.ordonnance} />
                <Text style={styles.avertissementTexte}>
                  Ce médicament nécessite une ordonnance médicale valide.
                  Ne pas s'automédicamenter.
                </Text>
              </View>
            )}
          </View>
        )}

        {/* ── Onglet Disponibilité ─────────────────────────────────────── */}
        {onglet === "disponibilite" && (
          <View style={styles.section}>
            <Text style={styles.disponibiliteIntro}>
              Pharmacies où ce produit est répertorié
            </Text>

            {loadPh && pharmacies.length === 0 ? (
              <ActivityIndicator color={Colors.primary} style={{ marginTop: 20 }} />
            ) : pharmacies.length === 0 ? (
              <View style={styles.vide}>
                <Ionicons name="storefront-outline" size={48} color={Colors.gray300} />
                <Text style={styles.videText}>
                  Aucune pharmacie ne répertorie ce produit pour l'instant
                </Text>
              </View>
            ) : (
              <>
                {pharmacies.map((ph) => (
                  <DisponibilitePharmacie
                    key={ph.id}
                    pharmacieId={ph.id}
                    pharmacieNom={ph.nom}
                    pharmacieVille={ph.ville}
                    pharmacieOuverte={ph.est_ouverte}
                    produitId={produitId}
                  />
                ))}
                {hasNextPage && (
                  <TouchableOpacity
                    style={styles.btnVoirPlus}
                    onPress={() => fetchNextPage()}
                  >
                    <Text style={styles.btnVoirPlusText}>
                      Voir plus de pharmacies
                    </Text>
                  </TouchableOpacity>
                )}
              </>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}

// ── Disponibilité dans une pharmacie ─────────────────────────────────────────
function DisponibilitePharmacie({
  pharmacieId, pharmacieNom, pharmacieVille, pharmacieOuverte, produitId,
}: {
  pharmacieId:     number
  pharmacieNom:    string
  pharmacieVille:  string
  pharmacieOuverte: boolean
  produitId:       number
}) {
  const { data, isLoading } = useProduitsPharmacie(pharmacieId, {
    page_size: 1,
  })

  const produit = data?.pages[0]?.results?.find((p) => p.id === produitId) as ProduitAvecStock | undefined

  if (isLoading) return (
    <View style={styles.dispoCarte}>
      <ActivityIndicator color={Colors.primary} size="small" />
    </View>
  )

  // Ne pas afficher si le produit n'est pas dans cette pharmacie
  if (!produit) return null

  return (
    <TouchableOpacity
      style={styles.dispoCarte}
      onPress={() => router.push(`/pharmacie/${pharmacieId}`)}
      activeOpacity={0.85}
    >
      <View style={styles.dispoIcone}>
        <Ionicons
          name="storefront"
          size={18}
          color={pharmacieOuverte ? Colors.primary : Colors.gray400}
        />
      </View>

      <View style={{ flex: 1 }}>
        <Text style={styles.dispoNom} numberOfLines={1}>{pharmacieNom}</Text>
        <Text style={styles.dispoVille}>{pharmacieVille}</Text>
        <View style={styles.dispoStatuts}>
          <Text style={[
            styles.dispoOuvert,
            { color: pharmacieOuverte ? Colors.success : Colors.danger }
          ]}>
            {pharmacieOuverte ? "● Ouverte" : "● Fermée"}
          </Text>
          <Text style={styles.dispoDivider}>·</Text>
          <Text style={[
            styles.dispoStock,
            { color: produit.disponible ? Colors.success : Colors.danger }
          ]}>
            {produit.disponible ? "En stock" : "Rupture"}
          </Text>
        </View>
      </View>

      <View style={styles.dispoPrix}>
        {produit.prix_fcfa ? (
          <Text style={styles.dispoPrixTexte}>
            {produit.prix_fcfa.toLocaleString()}
          </Text>
        ) : null}
        {produit.prix_fcfa ? (
          <Text style={styles.dispoPrixDevise}>FCFA</Text>
        ) : null}
      </View>

      <Ionicons name="chevron-forward" size={16} color={Colors.gray300} />
    </TouchableOpacity>
  )
}

// ── Sous-composants ───────────────────────────────────────────────────────────

function BadgeProduit({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
    </View>
  )
}

function InfoLigne({ icon, label, valeur, valueColor }: {
  icon: string; label: string; valeur: string; valueColor?: string
}) {
  return (
    <View style={styles.infoLigne}>
      <Ionicons name={icon as any} size={16} color={Colors.gray400} style={{ width: 20 }} />
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValeur, valueColor ? { color: valueColor } : {}]}>
        {valeur}
      </Text>
    </View>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: Colors.background },
  loader:       { flex: 1, alignItems: "center", justifyContent: "center" },
  erreurText:   { color: Colors.gray600, fontSize: Typography.base },
  scrollContent:{ paddingBottom: Spacing.xxxl },

  header:       { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm, backgroundColor: Colors.white, borderBottomWidth: 1, borderBottomColor: Colors.border },
  btnRetour:    { width: 40, height: 40, alignItems: "center", justifyContent: "center" },
  headerTitre:  { flex: 1, textAlign: "center", fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.gray900 },

  hero:         { backgroundColor: Colors.white, padding: Spacing.base, flexDirection: "row", gap: Spacing.base, alignItems: "flex-start" },
  image:        { width: 88, height: 88, borderRadius: BorderRadius.md },
  imagePlaceholder: { width: 88, height: 88, borderRadius: BorderRadius.md, backgroundColor: Colors.primaryBg, alignItems: "center", justifyContent: "center" },
  heroInfo:     { flex: 1, gap: Spacing.xs },
  nomProduit:   { fontSize: Typography.lg, fontWeight: Typography.bold, color: Colors.gray900, lineHeight: 24 },
  nomGenerique: { fontSize: Typography.sm, color: Colors.gray500, fontStyle: "italic" },
  badgesRow:    { flexDirection: "row", flexWrap: "wrap", gap: Spacing.xs, marginTop: 4 },
  badge:        { paddingHorizontal: 8, paddingVertical: 3, borderRadius: BorderRadius.full },
  badgeText:    { fontSize: Typography.xs, fontWeight: Typography.medium },

  onglets:      { flexDirection: "row", backgroundColor: Colors.white, marginTop: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.border },
  onglet:       { flex: 1, paddingVertical: Spacing.md, alignItems: "center" },
  ongletActif:  { borderBottomWidth: 2, borderBottomColor: Colors.primary },
  ongletText:   { fontSize: Typography.sm, color: Colors.gray500, fontWeight: Typography.medium },
  ongletTextActif: { color: Colors.primary, fontWeight: Typography.semibold },

  section:      { padding: Spacing.base, gap: Spacing.base },

  infoCard:     { backgroundColor: Colors.white, borderRadius: BorderRadius.md, overflow: "hidden", ...Shadow.sm },
  infoLigne:    { flexDirection: "row", alignItems: "center", gap: Spacing.sm, paddingVertical: Spacing.sm, paddingHorizontal: Spacing.base, borderBottomWidth: 1, borderBottomColor: Colors.gray100 },
  infoLabel:    { flex: 1, fontSize: Typography.sm, color: Colors.gray500 },
  infoValeur:   { fontSize: Typography.sm, fontWeight: Typography.medium, color: Colors.gray800 },

  blocTexte:    { backgroundColor: Colors.white, borderRadius: BorderRadius.md, padding: Spacing.base, gap: Spacing.sm, ...Shadow.sm },
  blocTitre:    { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.gray800 },
  blocContenu:  { fontSize: Typography.sm, color: Colors.gray600, lineHeight: 20 },
  blocWarning:  { borderLeftWidth: 3, borderLeftColor: Colors.warning },
  blocWarningHeader: { flexDirection: "row", alignItems: "center", gap: Spacing.xs },

  avertissement:{ flexDirection: "row", alignItems: "flex-start", gap: Spacing.sm, backgroundColor: "#F3E5F5", borderRadius: BorderRadius.md, padding: Spacing.base },
  avertissementTexte: { flex: 1, fontSize: Typography.sm, color: Colors.ordonnance, lineHeight: 18 },

  disponibiliteIntro: { fontSize: Typography.sm, color: Colors.gray500, marginBottom: Spacing.xs },

  dispoCarte:   { flexDirection: "row", alignItems: "center", gap: Spacing.sm, backgroundColor: Colors.white, borderRadius: BorderRadius.md, padding: Spacing.base, marginBottom: Spacing.xs, ...Shadow.sm },
  dispoIcone:   { width: 40, height: 40, borderRadius: BorderRadius.md, backgroundColor: Colors.gray100, alignItems: "center", justifyContent: "center" },
  dispoNom:     { fontSize: Typography.base, fontWeight: Typography.medium, color: Colors.gray900 },
  dispoVille:   { fontSize: Typography.xs, color: Colors.gray400, marginTop: 1 },
  dispoStatuts: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 3 },
  dispoOuvert:  { fontSize: Typography.xs, fontWeight: Typography.medium },
  dispoDivider: { fontSize: Typography.xs, color: Colors.gray400 },
  dispoStock:   { fontSize: Typography.xs, fontWeight: Typography.medium },
  dispoPrix:    { alignItems: "flex-end" },
  dispoPrixTexte: { fontSize: Typography.base, fontWeight: Typography.bold, color: Colors.primary },
  dispoPrixDevise:{ fontSize: Typography.xs, color: Colors.gray400 },

  vide:         { alignItems: "center", paddingTop: Spacing.xxl, gap: Spacing.sm },
  videText:     { fontSize: Typography.sm, color: Colors.gray500, textAlign: "center" },
  btnVoirPlus:  { alignItems: "center", paddingVertical: Spacing.base },
  btnVoirPlusText: { color: Colors.primary, fontWeight: Typography.semibold, fontSize: Typography.sm },
})