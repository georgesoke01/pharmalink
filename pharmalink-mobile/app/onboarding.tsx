// app/onboarding.tsx — Onboarding — Light & Dark
import { useState, useRef } from "react"
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, Dimensions, useColorScheme,
} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { router } from "expo-router"
import { Ionicons } from "@expo/vector-icons"
import { Colors, Spacing, BorderRadius, Typography } from "@/constants"
import { markOnboardingDone } from "@/hooks/useFirstLaunch"

const { width } = Dimensions.get("window")

const lightTheme = {
  bg: "#FFFFFF", title: "#333333", desc: "#666666",
  iconBg: "#F5F5F5", dot: "#DDDDDD", skip: "#666666",
}
const darkTheme = {
  bg: "#1A1A1A", title: "#FFFFFF", desc: "#999999",
  iconBg: "#2D2D2D", dot: "#444444", skip: "#999999",
}

const SLIDES = [
  {
    id: "1", color: "#1A7A4A",
    icon: "medkit",
    title: "Trouvez les pharmacies autour de vous",
    description: "Localisez instantanément les officines ouvertes à proximité grâce à notre carte interactive en temps réel.",
  },
  {
    id: "2", color: "#FF6B6B",
    icon: "moon",
    title: "Gardes et urgences 24h/24",
    description: "Repérez les pharmacies de garde la nuit, le dimanche et les jours fériés avec notre système d'alerte.",
  },
  {
    id: "3", color: "#2ECC71",
    icon: "list",
    title: "Catalogue de médicaments",
    description: "Consultez les prix, disponibilités et comparez les offres des pharmacies autour de vous en un clin d'œil.",
  },
  {
    id: "4", color: "#0F5C34",
    icon: "document-text",
    title: "Préparez vos ordonnances",
    description: "Téléchargez vos ordonnances, recevez des rappels de traitement et gérez vos achats simplement.",
  },
]

export default function Onboarding() {
  const colorScheme = useColorScheme()
  const isDark      = colorScheme === "dark"
  const T           = isDark ? darkTheme : lightTheme

  const [index, setIndex] = useState(0)
  const flatRef           = useRef<FlatList>(null)

  const goNext = async () => {
    if (index < SLIDES.length - 1) {
      flatRef.current?.scrollToIndex({ index: index + 1, animated: true })
      setIndex(index + 1)
    } else {
      // Marquer l'onboarding comme vu — ne sera plus affiché
      await markOnboardingDone()
      router.replace("/splash")
    }
  }

  const skip = async () => {
    await markOnboardingDone()
    router.replace("/splash")
  }


  return (
    <SafeAreaView style={[styles.container, { backgroundColor: T.bg }]} edges={["top", "bottom"]}>

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={skip}>
          <Text style={[styles.skip, { color: T.skip }]}>Passer</Text>
        </TouchableOpacity>
        <TouchableOpacity>
          <Ionicons
            name={isDark ? "sunny-outline" : "moon-outline"}
            size={22}
            color={T.skip}
          />
        </TouchableOpacity>
      </View>

      {/* Slides */}
      <FlatList
        ref={flatRef}
        data={SLIDES}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        keyExtractor={(item) => item.id}
        onMomentumScrollEnd={(e) => {
          setIndex(Math.round(e.nativeEvent.contentOffset.x / width))
        }}
        renderItem={({ item, index: i }) => (
          <View style={[styles.slide, { width }]}>
            {/* Icône */}
            <View style={[styles.iconCircle, { backgroundColor: T.iconBg }]}>
              <Ionicons name={item.icon as any} size={80} color={item.color} />
            </View>

            {/* Texte */}
            <Text style={[styles.title, { color: T.title }]}>{item.title}</Text>
            <Text style={[styles.desc,  { color: T.desc  }]}>{item.description}</Text>

            {/* Dots */}
            <View style={styles.dots}>
              {SLIDES.map((_, di) => (
                <View
                  key={di}
                  style={[
                    styles.dot,
                    {
                      backgroundColor: di === i ? item.color : T.dot,
                      width: di === i ? 24 : 8,
                    },
                  ]}
                />
              ))}
            </View>
          </View>
        )}
      />

      {/* Bouton suivant */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.btnNext, { backgroundColor: SLIDES[index].color }]}
          onPress={goNext}
        >
          <Text style={styles.btnNextTxt}>
            {index === SLIDES.length - 1 ? "Commencer" : "Suivant"}
          </Text>
          <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header:    {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center", paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.md,
  },
  skip:  { fontSize: Typography.base, fontWeight: Typography.medium },
  slide: {
    flex: 1, alignItems: "center", justifyContent: "center",
    paddingHorizontal: Spacing.xxl,
  },
  iconCircle: {
    width: 160, height: 160, borderRadius: 80,
    alignItems: "center", justifyContent: "center",
    marginBottom: Spacing.xxl,
  },
  title: {
    fontSize: Typography.xxl, fontWeight: Typography.bold,
    textAlign: "center", marginBottom: Spacing.base,
  },
  desc:  {
    fontSize: Typography.base, textAlign: "center",
    lineHeight: 24, paddingHorizontal: Spacing.lg,
  },
  dots: { flexDirection: "row", marginTop: Spacing.xxl, gap: Spacing.xs },
  dot:  { height: 8, borderRadius: 4 },
  footer: {
    paddingHorizontal: Spacing.xl,
    paddingBottom:     Spacing.xl,
  },
  btnNext: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    paddingVertical: Spacing.base, borderRadius: BorderRadius.lg, gap: Spacing.sm,
  },
  btnNextTxt: { color: "#FFFFFF", fontSize: Typography.lg, fontWeight: Typography.semibold },
})