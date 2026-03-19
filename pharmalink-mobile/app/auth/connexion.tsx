// app/auth/connexion.tsx
import { useState } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { useAuthStore } from "@/store"
import { authService } from "@/services/pharmacies"
import { Colors, Spacing, BorderRadius, Typography, Shadow } from "@/constants"

export default function EcranConnexion() {
  const { setUtilisateur } = useAuthStore()
  const [login,      setLogin]      = useState("")
  const [password,   setPassword]   = useState("")
  const [showPass,   setShowPass]   = useState(false)
  const [loading,    setLoading]    = useState(false)
  const [erreur,     setErreur]     = useState("")

  const seConnecter = async () => {
    if (!login.trim() || !password.trim()) {
      setErreur("Veuillez remplir tous les champs")
      return
    }
    setLoading(true)
    setErreur("")
    try {
      const data = await authService.login(login.trim(), password)
      setUtilisateur(data.user)
      router.back()
    } catch (e: any) {
      setErreur(
        e?.response?.data?.detail ??
        e?.response?.data?.non_field_errors?.[0] ??
        "Identifiant ou mot de passe incorrect"
      )
    } finally { setLoading(false) }
  }

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

          <TouchableOpacity style={styles.btnFermer} onPress={() => router.back()}>
            <Ionicons name="close" size={24} color={Colors.gray600} />
          </TouchableOpacity>

          {/* Logo */}
          <View style={styles.logoSection}>
            <View style={styles.logoBox}>
              <Text style={styles.logoCroix}>✚</Text>
            </View>
            <Text style={styles.appName}>PharmaLink</Text>
            <Text style={styles.tagline}>Votre pharmacie à portée de main</Text>
          </View>

          {/* Formulaire */}
          <View style={styles.form}>
            <Text style={styles.formTitre}>Connexion</Text>

            {erreur ? (
              <View style={styles.erreurBox}>
                <Ionicons name="alert-circle" size={15} color={Colors.danger} />
                <Text style={styles.erreurText}>{erreur}</Text>
              </View>
            ) : null}

            <View style={styles.champ}>
              <Text style={styles.label}>Email ou nom d'utilisateur</Text>
              <View style={[styles.inputBox, erreur && styles.inputBoxErreur]}>
                <Ionicons name="person-outline" size={17} color={Colors.gray400} />
                <TextInput
                  style={styles.input}
                  placeholder="email ou username"
                  placeholderTextColor={Colors.gray400}
                  value={login}
                  onChangeText={(t) => { setLogin(t); setErreur("") }}
                  autoCapitalize="none"
                  keyboardType="email-address"
                />
              </View>
            </View>

            <View style={styles.champ}>
              <Text style={styles.label}>Mot de passe</Text>
              <View style={[styles.inputBox, erreur && styles.inputBoxErreur]}>
                <Ionicons name="lock-closed-outline" size={17} color={Colors.gray400} />
                <TextInput
                  style={styles.input}
                  placeholder="Votre mot de passe"
                  placeholderTextColor={Colors.gray400}
                  value={password}
                  onChangeText={(t) => { setPassword(t); setErreur("") }}
                  secureTextEntry={!showPass}
                  onSubmitEditing={seConnecter}
                />
                <TouchableOpacity onPress={() => setShowPass(!showPass)}>
                  <Ionicons name={showPass ? "eye-off-outline" : "eye-outline"} size={17} color={Colors.gray400} />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.btnLogin, loading && { opacity: 0.7 }]}
              onPress={seConnecter}
              disabled={loading}
            >
              {loading
                ? <ActivityIndicator color={Colors.white} size="small" />
                : <Text style={styles.btnLoginText}>Se connecter</Text>
              }
            </TouchableOpacity>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Pas encore de compte ? </Text>
            <TouchableOpacity onPress={() => router.replace("/auth/inscription")}>
              <Text style={styles.footerLien}>Créer un compte</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity onPress={() => router.back()} style={{ alignItems: "center", marginTop: Spacing.lg }}>
            <Text style={{ color: Colors.gray400, fontSize: Typography.sm }}>
              Continuer sans compte →
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: Colors.white },
  scroll:     { flexGrow: 1, paddingHorizontal: Spacing.base, paddingBottom: Spacing.xxxl },
  btnFermer:  { alignSelf: "flex-end", padding: Spacing.sm, marginTop: Spacing.sm },
  logoSection:{ alignItems: "center", marginVertical: Spacing.xl, gap: Spacing.sm },
  logoBox:    { width: 80, height: 80, borderRadius: 22, backgroundColor: Colors.primary, alignItems: "center", justifyContent: "center", ...Shadow.md },
  logoCroix:  { color: Colors.white, fontSize: 36, fontWeight: "800" },
  appName:    { fontSize: Typography.xxl, fontWeight: Typography.extrabold, color: Colors.gray900 },
  tagline:    { fontSize: Typography.sm, color: Colors.gray400 },
  form:       { gap: Spacing.base },
  formTitre:  { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.gray900 },
  erreurBox:  { flexDirection: "row", alignItems: "center", gap: Spacing.xs, backgroundColor: Colors.dangerBg, padding: Spacing.md, borderRadius: BorderRadius.md },
  erreurText: { flex: 1, fontSize: Typography.sm, color: Colors.danger },
  champ:      { gap: Spacing.xs },
  label:      { fontSize: Typography.sm, fontWeight: Typography.medium, color: Colors.gray700 },
  inputBox:   { flexDirection: "row", alignItems: "center", gap: Spacing.sm, borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.base, paddingVertical: 13, backgroundColor: Colors.gray100 },
  inputBoxErreur: { borderColor: Colors.danger },
  input:      { flex: 1, fontSize: Typography.base, color: Colors.gray900, padding: 0 },
  btnLogin:   { backgroundColor: Colors.primary, paddingVertical: 14, borderRadius: BorderRadius.lg, alignItems: "center", ...Shadow.sm },
  btnLoginText:{ color: Colors.white, fontSize: Typography.base, fontWeight: Typography.semibold },
  footer:     { flexDirection: "row", justifyContent: "center", marginTop: Spacing.xl },
  footerText: { color: Colors.gray500, fontSize: Typography.sm },
  footerLien: { color: Colors.primary, fontSize: Typography.sm, fontWeight: Typography.semibold },
})