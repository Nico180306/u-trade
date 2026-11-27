import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState, type ReactNode } from 'react'
import { fetchCsrfCookie } from '../api/client'

export interface AppProvidersProps {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  )

  useEffect(() => {
    const controller = new AbortController()
    void fetchCsrfCookie(controller.signal).catch(() => {
      // Silencioso en bootstrap inicial; las pantallas de diagnóstico o mutaciones informan si el API no responde.
    })
    return () => controller.abort()
  }, [])

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
