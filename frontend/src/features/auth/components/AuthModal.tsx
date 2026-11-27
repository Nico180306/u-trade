import { useState } from 'react'
import { Modal } from '../../../shared/components'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

export type AuthModalTab = 'login' | 'register'

export interface AuthModalProps {
  open: boolean
  onClose: () => void
  initialTab?: AuthModalTab
  onAuthenticated?: () => void
}

interface AuthModalBodyProps {
  initialTab: AuthModalTab
  onClose: () => void
  onAuthenticated?: () => void
}

function AuthModalBody({ initialTab, onClose, onAuthenticated }: AuthModalBodyProps) {
  const [activeTab, setActiveTab] = useState<AuthModalTab>(initialTab)

  function handleSuccess() {
    onAuthenticated?.()
    onClose()
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={activeTab === 'login' ? 'Inicia sesión en U-Trade' : 'Crea tu cuenta en U-Trade'}
      description="Ingresa en segundos para reservar en ventas estudiantiles del campus."
    >
      <div
        role="tablist"
        aria-label="Opciones de acceso"
        className="mb-5 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1"
      >
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'login'}
          onClick={() => setActiveTab('login')}
          className={[
            'min-h-11 cursor-pointer rounded-lg px-3 text-sm font-semibold transition-colors',
            activeTab === 'login'
              ? 'bg-white text-slate-950 shadow-xs'
              : 'text-slate-600 hover:text-slate-900',
          ].join(' ')}
        >
          Iniciar sesión
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'register'}
          onClick={() => setActiveTab('register')}
          className={[
            'min-h-11 cursor-pointer rounded-lg px-3 text-sm font-semibold transition-colors',
            activeTab === 'register'
              ? 'bg-white text-slate-950 shadow-xs'
              : 'text-slate-600 hover:text-slate-900',
          ].join(' ')}
        >
          Crear cuenta
        </button>
      </div>

      {activeTab === 'login' ? (
        <LoginForm onSuccess={handleSuccess} onNavigateAway={onClose} />
      ) : (
        <RegisterForm onSuccess={handleSuccess} />
      )}
    </Modal>
  )
}

export function AuthModal({
  open,
  onClose,
  initialTab = 'login',
  onAuthenticated,
}: AuthModalProps) {
  if (!open) {
    return null
  }

  return (
    <AuthModalBody
      key={initialTab}
      initialTab={initialTab}
      onClose={onClose}
      onAuthenticated={onAuthenticated}
    />
  )
}
