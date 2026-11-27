import { useState, type FormEvent } from 'react'
import { Alert, Button, Input } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { useRegister } from '../hooks'

export interface RegisterFormProps {
  onSuccess?: () => void
  submitLabel?: string
}

export function RegisterForm({
  onSuccess,
  submitLabel = 'Crear cuenta',
}: RegisterFormProps) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [password, setPassword] = useState('')
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [acceptPrivacy, setAcceptPrivacy] = useState(false)
  const [clientError, setClientError] = useState<string | null>(null)

  const registerMutation = useRegister()
  const fieldErrors = getFieldErrors(registerMutation.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setClientError(null)

    if (!acceptTerms || !acceptPrivacy) {
      setClientError(
        'Debes aceptar los Términos de Uso y la Política de Privacidad (LOPDP) para crear tu cuenta.',
      )
      return
    }

    registerMutation.mutate(
      {
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        phone_number: phoneNumber.trim(),
        accept_terms: acceptTerms,
        accept_privacy: acceptPrivacy,
      },
      {
        onSuccess: () => {
          onSuccess?.()
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {(clientError || registerMutation.isError) && (
        <Alert variant="error">
          {clientError ?? getErrorMessage(registerMutation.error)}
        </Alert>
      )}

      <Input
        label="Nombre completo"
        type="text"
        name="full_name"
        autoComplete="name"
        placeholder="Ej. María Pérez"
        maxLength={150}
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        error={fieldErrors.full_name}
      />

      <Input
        label="Correo electrónico"
        type="email"
        name="email"
        autoComplete="email"
        inputMode="email"
        placeholder="tu.correo@ejemplo.com"
        hint="Aceptamos correos personales o @uisek.edu.ec (no correos desechables)."
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={fieldErrors.email}
        required
      />

      <Input
        label="Teléfono (opcional)"
        type="tel"
        name="phone_number"
        autoComplete="tel"
        inputMode="tel"
        placeholder="0991234567"
        maxLength={20}
        value={phoneNumber}
        onChange={(event) => setPhoneNumber(event.target.value)}
        error={fieldErrors.phone_number}
      />

      <Input
        label="Contraseña"
        type="password"
        name="password"
        autoComplete="new-password"
        placeholder="Mínimo 8 caracteres"
        hint="Usa al menos 8 caracteres combinando letras y números."
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={fieldErrors.password}
        required
      />

      <fieldset className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
          Consentimiento obligatorio (LOPDP)
        </legend>

        <label className="flex min-h-11 cursor-pointer items-start gap-3 py-1 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(event) => {
              setAcceptTerms(event.target.checked)
              if (clientError) setClientError(null)
            }}
            className="mt-1 h-5 w-5 shrink-0 rounded border-slate-300 text-slate-900 accent-slate-900"
            required
          />
          <span>
            Acepto los <strong>Términos de Uso</strong> de U-Trade, incluyendo las reglas de
            reservas, ausencias automáticas (strikes) y disputas.
          </span>
        </label>

        <label className="flex min-h-11 cursor-pointer items-start gap-3 py-1 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={acceptPrivacy}
            onChange={(event) => {
              setAcceptPrivacy(event.target.checked)
              if (clientError) setClientError(null)
            }}
            className="mt-1 h-5 w-5 shrink-0 rounded border-slate-300 text-slate-900 accent-slate-900"
            required
          />
          <span>
            Acepto la <strong>Política de Privacidad</strong> y el tratamiento de mis datos
            personales conforme a la LOPDP (Ecuador).
          </span>
        </label>
      </fieldset>

      <Button type="submit" fullWidth size="lg" loading={registerMutation.isPending}>
        {submitLabel}
      </Button>
    </form>
  )
}
