// app/(tabs)/_layout.tsx
import { Tabs } from "expo-router"
import { Platform } from "react-native"
import { Ionicons } from "@expo/vector-icons"
import { Colors, Typography } from "@/constants"

type IoniconName = React.ComponentProps<typeof Ionicons>["name"]

interface TabConfig {
  name:       string
  title:      string
  icon:       IoniconName
  iconFocused: IoniconName
}

const TABS: TabConfig[] = [
  { name: "index",    title: "Carte",     icon: "map-outline",       iconFocused: "map" },
  { name: "liste",    title: "Pharmacies", icon: "list-outline",     iconFocused: "list" },
  { name: "gardes",   title: "Gardes",    icon: "shield-outline",    iconFocused: "shield" },
  { name: "recherche",title: "Recherche", icon: "search-outline",    iconFocused: "search" },
  { name: "profil",   title: "Profil",    icon: "person-outline",    iconFocused: "person" },
]

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown:            false,
        tabBarActiveTintColor:  Colors.primary,
        tabBarInactiveTintColor: Colors.gray500,
        tabBarLabelStyle: {
          fontSize:   Typography.xs,
          fontWeight: Typography.medium,
          marginBottom: Platform.OS === "ios" ? 0 : 4,
        },
        tabBarStyle: {
          backgroundColor:  Colors.white,
          borderTopColor:   Colors.border,
          borderTopWidth:   1,
          height:           Platform.OS === "ios" ? 85 : 65,
          paddingBottom:    Platform.OS === "ios" ? 24 : 8,
          paddingTop:       8,
        },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarIcon: ({ focused, color, size }) => (
              <Ionicons
                name={focused ? tab.iconFocused : tab.icon}
                size={size}
                color={color}
              />
            ),
          }}
        />
      ))}
    </Tabs>
  )
}