import { create } from 'zustand'
import axios from 'axios'

const API_URL = '/api'

export const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null })
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await axios.post(`${API_URL}/auth/token`, formData)
      const { access_token } = response.data
      
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      const userResponse = await axios.get(`${API_URL}/auth/me`)
      
      set({
        token: access_token,
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false
      })
      
      return true
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false
      })
      return false
    }
  },

  register: async (email, username, password) => {
    set({ isLoading: true, error: null })
    try {
      await axios.post(`${API_URL}/auth/register`, {
        email,
        username,
        password
      })
      
      // Auto-login after registration
      return await get().login(username, password)
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Registration failed',
        isLoading: false
      })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    set({
      user: null,
      token: null,
      isAuthenticated: false
    })
  },

  checkAuth: async () => {
    const token = get().token
    if (!token) return false
    
    try {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const response = await axios.get(`${API_URL}/auth/me`)
      set({
        user: response.data,
        isAuthenticated: true
      })
      return true
    } catch (error) {
      get().logout()
      return false
    }
  }
}))

// Set default axios header if token exists
const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}
