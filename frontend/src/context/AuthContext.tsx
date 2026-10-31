import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api, { setAccessToken } from '../api/client'
import type { LoginRequest, UserResponse, Token } from '../types/api'

interface AuthContextType {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = async () => {
    try {
      const response = await api.get<UserResponse>('/auth/me')
      setUser(response.data)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token')
    if (storedToken) {
      setAccessToken(storedToken)
      fetchUser()
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (credentials: LoginRequest) => {
    const response = await api.post<Token>('/auth/login', credentials)
    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)
    setAccessToken(access_token)
    await fetchUser()
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      localStorage.removeItem('access_token')
      setAccessToken(null)
      setUser(null)
    }
  }

  const refresh = async () => {
    try {
      const response = await api.post<Token>('/auth/refresh')
      const { access_token } = response.data
      localStorage.setItem('access_token', access_token)
      setAccessToken(access_token)
      await fetchUser()
    } catch {
      localStorage.removeItem('access_token')
      setAccessToken(null)
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}