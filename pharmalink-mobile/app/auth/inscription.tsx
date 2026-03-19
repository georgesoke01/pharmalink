// app/auth/inscription.tsx
import { useState } from "react"
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { authService } from "@/services/pharmacies"
import { Colors, Spacing, BorderRadius, Typography, Shadow } from "@/constants"

export default function EcranInscription() {
  const [username,  setUsername]  = useState("")
  const [email,     setEmail]     = useState("")
  const [password,  setPassword]  = useState("")
  const [password2, setPassword2] = useState("")
  const [showPass,  setShowPass]  = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [erreurs,   setErreurs]   = useState<Record<string, string>>({})
  const [succes,    setSucces]    = useState(false)

  const valider = () => {
    const e: Record<string, string> = {}
    if (!username.trim() || username.length < 3) e.username = "Minimum 3 caractères"
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Email invalide"
    if (password.length < 8) e.password = "Minimum 8 caractères"
    if (password !== password2) e.password2 = "Les mots de passe ne correspondent pas"
    setErreurs(e)
    return Object.keys(e).length === 0
  }

  const sInscrire = async () => {
    if (!valider()) return
    setLoading(true)
    try {
      await authService.inscrire({ username, email, password, password2 })
      setSucces(true)
    } catch (e: any) {
      const d = e?.response?.data ?? {}
      setErreurs({
        username: d.username?.[0] ?? "",
        email:    d.email?.[0] ?? "",
        password: d.password?.[0] ?? "",
        global:   d.non_field_errors?.[0] ?? (!Object.keys(d).length ? "Erreur serveur" : ""),
      })
    } finally { setLoading(false) }
  }

  if (succes) return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: Spacing.base, padding: Spacing.xxl }}>
        <Ionicons name="checkmark-circle" size={80} color={Colors.primary} />
        <Text style={{ fontSize: Typography.xxl, fontWeight: Typography.bold, color: Colors.gray900 }}>
          Compte créé !
        </Text>
        <Text style={{ fontSize: Typography.sm, color: Colors.gray400, textAlign: "center" }}>
          Votre compte a été créé avec succès. Connectez-vous maintenant.
        </Text>
        <TouchableOpacity
          style={[styles.btn, { width: "100%" }]}
          onPress={() => router.replace("/auth/connexion")}
        >
          <Text style={styles.btnText}>Se connecter</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  )

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

          <TouchableOpacity style={styles.btnFermer} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={22} color={Colors.gray700} />
          </TouchableOpacity>

          <Text style={styles.titre}>Créer un compte</Text>
          <Text style={styles.sous}>Gratuit — accès à toutes les fonctionnalités</Text>

          {erreurs.global ? (
            <View style={styles.erreurBox}>
              <Ionicons name="alert-circle" size={15} color={Colors.danger} />
              <Text style={styles.erreurText}>{erreurs.global}</Text>
            </View>
          ) : null}

          <View style={styles.form}>
            {[
              { key: "username",  label: "Nom d'utilisateur *", icon: "at",            value: username,  set: setUsername,  kb: "default", req: true },
              { key: "email",     label: "Email *",              icon: "mail-outline",  value: email,     set: setEmail,     kb: "email-address", req: true },
            ].map((f) => (
              <View key={f.key} style={styles.champ}>
                <Text style={styles.label}>{f.label}</Text>
                <View style={[styles.inputBox, erreurs[f.key] && styles.inputErreur]}>
                  <Ionicons name={f.icon as any} size={17} color={Colors.gray400} />
                  <TextInput
                    style={styles.input}
                    placeholder={f.label.replace(" *", "")}
                    placeholderTextColor={Colors.gray400}
                    value={f.value}
                    onChangeText={(t) => { f.set(t); setErreurs((e) => ({ ...e, [f.key]: "" })) }}
                    autoCapitalize="none"
                    keyboardType={f.kb as any}
                  />
                </View>
                {erreurs[f.key] ? <Text style={styles.erreurChamp}>{erreurs[f.key]}</Text> : null}
              </View>
            ))}

            <View style={styles.champ}>
              <Text style={styles.label}>Mot de passe * (min. 8 caractères)</Text>
              <View style={[styles.inputBox, erreurs.password && styles.inputErreur]}>
                <Ionicons name="lock-closed-outline" size={17} color={Colors.gray400} />
                <TextInput
                  style={styles.input}
                  placeholder="Mot de passe"
                  placeholderTextColor={Colors.gray400}
                  value={password}
                  onChangeText={(t) => { setPassword(t); setErreurs((e) => ({ ...e, password: "" })) }}
                  secureTextEntry={!showPass}
                />
                <TouchableOpacity onPress={() => setShowPass(!showPass)}>
                  <Ionicons name={showPass ? "eye-off-outline" : "eye-outline"} size={17} color={Colors.gray400} />
                </TouchableOpacity>
              </View>
              {erreurs.password ? <Text style={styles.erreurChamp}>{erreurs.password}</Text> : null}
            </View>

            <View style={styles.champ}>
              <Text style={styles.label}>Confirmer le mot de passe *</Text>
              <View style={[styles.inputBox, erreurs.password2 && styles.inputErreur]}>
                <Ionicons name="lock-closed-outline" size={17} color={Colors.gray400} />
                <TextInput
                  style={styles.input}
                  placeholder="Confirmer"
                  placeholderTextColor={Colors.gray400}
                  value={password2}
                  onChangeText={(t) => { setPassword2(t); setErreurs((e) => ({ ...e, password2: "" })) }}
                  secureTextEntry
                />
              </View>
              {erreurs.password2 ? <Text style={styles.erreurChamp}>{erreurs.password2}</Text> : null}
            </View>

            <TouchableOpacity style={[styles.btn, loading && { opacity: 0.7 }]} onPress={sInscrire} disabled={loading}>
              {loading
                ? <ActivityIndicator color={Colors.white} size="small" />
                : <Text style={styles.btnText}>Créer mon compte</Text>
              }
            </TouchableOpacity>
          </View>

          <View style={styles.footer}>
            <Text style={{ color: Colors.gray400, fontSize: Typography.sm }}>Déjà un compte ? </Text>
            <TouchableOpacity onPress={() => router.replace("/auth/connexion")}>
              <Text style={{ color: Colors.primary, fontSize: Typography.sm, fontWeight: Typography.semibold }}>
                Se connecter
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: Colors.white },
  scroll:      { flexGrow: 1, paddingHorizontal: Spacing.base, paddingBottom: Spacing.xxxl },
  btnFermer:   { padding: Spacing.sm, marginTop: Spacing.sm, alignSelf: "flex-start" },
  titre:       { fontSize: Typography.xxl, fontWeight: Typography.bold, color: Colors.gray900, marginTop: Spacing.base },
  sous:        { fontSize: Typography.sm, color: Colors.gray400, marginBottom: Spacing.xl },
  erreurBox:   { flexDirection: "row", alignItems: "center", gap: Spacing.xs, backgroundColor: Colors.dangerBg, padding: Spacing.md, borderRadius: BorderRadius.md, marginBottom: Spacing.sm },
  erreurText:  { flex: 1, fontSize: Typography.sm, color: Colors.danger },
  form:        { gap: Spacing.md },
  champ:       { gap: Spacing.xs },
  label:       { fontSize: Typography.sm, fontWeight: Typography.medium, color: Colors.gray700 },
  inputBox:    { flexDirection: "row", alignItems: "center", gap: Spacing.sm, borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.base, paddingVertical: 13, backgroundColor: Colors.gray100 },
  inputErreur: { borderColor: Colors.danger },
  input:       { flex: 1, fontSize: Typography.base, color: Colors.gray900, padding: 0 },
  erreurChamp: { fontSize: Typography.xs, color: Colors.danger },
  btn:         { backgroundColor: Colors.primary, paddingVertical: 14, borderRadius: BorderRadius.lg, alignItems: "center", marginTop: Spacing.sm, ...Shadow.sm },
  btnText:     { color: Colors.white, fontSize: Typography.base, fontWeight: Typography.semibold },
  footer:      { flexDirection: "row", justifyContent: "center", marginTop: Spacing.xl },
})