import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Input } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { useLogin } from '../hooks'

export interface LoginFormProps {
  onSuccess?: () => void
  onNavigateAway?: () => void
  submitLabel?: string
}

export function LoginForm({
  onSuccess,
  onNavigateAway,
  submitLabel = 'Iniciar sesión',
}: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const loginMutation = useLogin()
  const fieldErrors = getFieldErrors(loginMutation.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    loginMutation.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => {
          onSuccess?.()
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {loginMutation.isError && (
        <Alert variant="error">{getErrorMessage(loginMutation.error)}</Alert>
      )}

      <Input
        label="Correo electrónico"
        type="email"
        name="email"
        autoComplete="email"
        inputMode="email"
        placeholder="tu.correo@uisek.edu.ec"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={fieldErrors.email}
        required
      />

      <Input
        label="Contraseña"
        type="password"
        name="password"
        autoComplete="current-password"
        placeholder="Ingresa tu contraseña"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={fieldErrors.password}
        required
      />

      <div className="flex justify-end">
        <Link
          to="/forgot-password"
          onClick={onNavigateAway}
          className="inline-flex min-h-11 items-center text-sm font-medium text-slate-700 underline underline-offset-4 hover:text-slate-950"
        >
          ¿Olvidaste tu contraseña?
        </Link>
      </div>

      <Button type="submit" fullWidth size="lg" loading={loginMutation.isPending}>
        {submitLabel}
      </Button>
    </form>
  )
}
