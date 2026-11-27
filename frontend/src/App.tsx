import { useEffect, useState } from 'react'

type HealthState =
  | { status: 'checking' }
  | { status: 'ok'; database: string }
  | { status: 'error'; message: string }

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
).replace(/\/+$/, '')

function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'checking' })

  useEffect(() => {
    const controller = new AbortController()

    async function checkHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health/`, {
          signal: controller.signal,
        })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const data: { status: string; database: string } = await response.json()
        setHealth({ status: 'ok', database: data.database })
      } catch (err) {
        if (controller.signal.aborted) return
        const message = err instanceof Error ? err.message : 'Sin conexion con el backend'
        setHealth({ status: 'error', message })
      }
    }

    void checkHealth()
    return () => controller.abort()
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold tracking-tight">U-Trade</h1>
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
            Bootstrap PWA
          </span>
        </div>

        <p className="mt-2 text-sm text-slate-400">
          Verificacion inicial de React, Tailwind CSS, PWA y conexion con Django API.
        </p>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-sm">
          <p className="text-xs uppercase tracking-wider text-slate-500">Estado del Backend</p>
          {health.status === 'checking' && (
            <p className="mt-2 font-medium text-amber-400">Consultando /api/health/...</p>
          )}
          {health.status === 'ok' && (
            <p className="mt-2 font-medium text-emerald-400">
              API activa - Base de datos: {health.database}
            </p>
          )}
          {health.status === 'error' && (
            <p className="mt-2 font-medium text-rose-400">Error de conexion: {health.message}</p>
          )}
        </div>
      </section>
    </main>
  )
}

export default App
