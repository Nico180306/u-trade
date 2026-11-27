import { createContext, useContext } from 'react'
import type { AuthModalTab } from '../features/auth/components/AuthModal'

export interface AuthModalController {
  openAuthModal: (tab?: AuthModalTab) => void
}

export const AuthModalContext = createContext<AuthModalController | null>(null)

export function useAuthModal(): AuthModalController {
  const ctx = useContext(AuthModalContext)
  if (!ctx) {
    throw new Error('useAuthModal debe usarse dentro de AppLayout.')
  }
  return ctx
}
