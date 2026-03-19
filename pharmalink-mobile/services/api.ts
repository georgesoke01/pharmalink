// services/api.ts
// Client Axios centralisé — gère JWT, refresh automatique, erreurs
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios"
import AsyncStorage from "@react-native-async-storage/async-storage"
import { API_BASE_URL, STORAGE_KEYS } from "@/constants"

// ── Helpers stockage token (synchrone en mémoire + persistance AsyncStorage) ──
let _accessToken:  string | null = null
let _refreshToken: string | null = null

export const tokenStorage = {
  getAccess:  () => _accessToken,
  getRefresh: () => _refreshToken,

  setAccess: async (t: string) => {
    _accessToken = t
    await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, t)
  },

  setRefresh: async (t: string) => {
    _refreshToken = t
    await AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, t)
  },

  clear: async () => {
    _accessToken  = null
    _refreshToken = null
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER,
    ])
  },

  /** Charge les tokens depuis AsyncStorage au démarrage de l'app */
  init: async () => {
    _accessToken  = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    _refreshToken = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
  },
}

// ── Instance Axios ─────────────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type":              "application/json",
    "ngrok-skip-browser-warning": "true",  // bypass la page d'avertissement ngrok
  },
})

// ── Intercepteur requête — injecte le token JWT ────────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.getAccess()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// ── Intercepteur réponse — refresh automatique si 401 ─────────────────────────
let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          })
        })
      }

      original._retry = true
      isRefreshing    = true

      try {
        const refresh = tokenStorage.getRefresh()
        if (!refresh) throw new Error("Pas de refresh token")

        const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh,
        })
         
        
 
        await tokenStorage.setAccess(data.access)

        pendingRequests.forEach((cb) => cb(data.access))
        pendingRequests = []

        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        await tokenStorage.clear()
        pendingRequests = []
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default api