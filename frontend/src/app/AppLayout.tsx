import { useCallback, useMemo, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { AuthModal, type AuthModalTab } from '../features/auth/components/AuthModal'
import { useCurrentUser } from '../features/auth/hooks'
import { Alert, Button, Skeleton } from '../shared/components'
import { useOnlineStatus } from '../shared/hooks/useOnlineStatus'
import { AuthModalContext } from './authModalContext'

export function AppLayout() {
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authModalTab, setAuthModalTab] = useState<AuthModalTab>('login')

  const isOnline = useOnlineStatus()
  const { data: user, isPending } = useCurrentUser()

  const openAuthModal = useCallback((tab: AuthModalTab = 'login') => {
    setAuthModalTab(tab)
    setAuthModalOpen(true)
  }, [])

  const contextValue = useMemo(() => ({ openAuthModal }), [openAuthModal])

  const displayName = user?.full_name?.trim() || user?.email?.split('@')[0] || 'Mi perfil'

  return (
    <AuthModalContext.Provider value={contextValue}>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="mx-auto flex max-w-2xl items-center justify-between gap-2 px-4 py-2.5">
            <Link
              to="/"
              className="inline-flex min-h-11 items-center gap-2 text-lg font-extrabold tracking-tight text-slate-950"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-xs font-bold text-white">
                UT
              </span>
              <span>U-Trade</span>
            </Link>

            <nav aria-label="Navegación principal" className="flex items-center gap-1.5">
              <Link
                to="/bootstrap-check"
                className="inline-flex min-h-11 items-center rounded-xl px-2.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950"
              >
                Estado
              </Link>

              {isPending ? (
                <Skeleton className="h-11 w-24 rounded-xl" />
              ) : user ? (
                <Link
                  to="/profile"
                  className="inline-flex min-h-11 max-w-[140px] items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-semibold text-slate-900 transition-colors hover:bg-slate-100"
                >
                  <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                  <span className="truncate">{displayName}</span>
                </Link>
              ) : (
                <Button size="md" onClick={() => openAuthModal('login')}>
                  Iniciar sesión
                </Button>
              )}
            </nav>
          </div>
        </header>

        {!isOnline && (
          <div className="mx-auto max-w-2xl px-4 pt-3">
            <Alert variant="warning">
              Sin conexión a internet. Algunas acciones requieren conexión con el servidor.
            </Alert>
          </div>
        )}

        <main className="mx-auto max-w-2xl px-4 py-6">
          <Outlet />
        </main>

        <AuthModal
          open={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          initialTab={authModalTab}
        />
      </div>
    </AuthModalContext.Provider>
  )
}
