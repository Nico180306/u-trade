import { useEffect, useId, useState, type ClipboardEvent, type FormEvent } from 'react'
import { ApiError } from '../../../api/client'
import { Alert, Badge, Button } from '../../../shared/components'
import {
  formatWaitDuration,
  getErrorMessage,
} from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTime } from '../../../shared/utils/format'
import type { OTPRequestResponse, PurposeEnum, UserMe } from '../api'

const DEFAULT_RESEND_COOLDOWN_SECONDS = 60

export interface OtpVerificationCardProps {
  purpose: PurposeEnum
  targetEmail: string
  title?: string
  description?: string
  initialOtpMeta?: OTPRequestResponse | null
  onRequestOtp: () => Promise<OTPRequestResponse>
  onVerifyOtp: (code: string) => Promise<UserMe>
  isRequesting: boolean
  isVerifying: boolean
  requestError: unknown
  verifyError: unknown
  onClearErrors?: () => void
  onVerified?: (user: UserMe) => void
  onChangeEmail?: () => void
}

function sanitizeOtpInput(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, 6)
}

function extractRetryAfterSeconds(error: unknown): number | null {
  if (
    error instanceof ApiError &&
    error.code === 'OTP_RATE_LIMITED' &&
    typeof error.details.retry_after_seconds === 'number' &&
    error.details.retry_after_seconds > 0
  ) {
    return Math.ceil(error.details.retry_after_seconds)
  }
  return null
}

function extractAttemptsRemaining(error: unknown): number | null {
  if (
    error instanceof ApiError &&
    error.code === 'OTP_INVALID' &&
    typeof error.details.attempts_remaining === 'number'
  ) {
    return error.details.attempts_remaining
  }
  return null
}

export function OtpVerificationCard({
  purpose,
  targetEmail,
  title,
  description,
  initialOtpMeta = null,
  onRequestOtp,
  onVerifyOtp,
  isRequesting,
  isVerifying,
  requestError,
  verifyError,
  onClearErrors,
  onVerified,
  onChangeEmail,
}: OtpVerificationCardProps) {
  const otpInputId = useId()
  const [code, setCode] = useState('')
  const [otpMeta, setOtpMeta] = useState<OTPRequestResponse | null>(initialOtpMeta)
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(() =>
    initialOtpMeta ? Date.now() + DEFAULT_RESEND_COOLDOWN_SECONDS * 1000 : null,
  )
  const [nowMs, setNowMs] = useState<number>(() => Date.now())
  const [verifiedUser, setVerifiedUser] = useState<UserMe | null>(null)

  const remainingCooldown =
    cooldownUntil !== null ? Math.max(0, Math.ceil((cooldownUntil - nowMs) / 1000)) : 0

  useEffect(() => {
    if (cooldownUntil === null) {
      return
    }
    if (cooldownUntil <= Date.now()) {
      return
    }
    const timerId = window.setInterval(() => {
      const current = Date.now()
      setNowMs(current)
      if (current >= cooldownUntil) {
        window.clearInterval(timerId)
      }
    }, 1000)

    return () => window.clearInterval(timerId)
  }, [cooldownUntil])

  const verifyApiError = verifyError instanceof ApiError ? verifyError : null
  const requestApiError = requestError instanceof ApiError ? requestError : null
  const isOtpLocked = verifyApiError?.code === 'OTP_LOCKED'
  const isOtpExpired = verifyApiError?.code === 'OTP_EXPIRED_OR_INVALID'
  const isRateLimited = requestApiError?.code === 'OTP_RATE_LIMITED'
  const attemptsRemaining = extractAttemptsRemaining(verifyError)
  const isEmailConflictOrInvalid =
    requestApiError?.code === 'INVALID_UISEK_EMAIL' ||
    requestApiError?.code === 'UISEK_EMAIL_ALREADY_IN_USE'

  const effectiveTargetEmail = otpMeta?.target_email || targetEmail
  const hasCodeBeenSent = otpMeta !== null

  async function handleRequestCode() {
    onClearErrors?.()
    try {
      const response = await onRequestOtp()
      setOtpMeta(response)
      setCode('')
      const nextNow = Date.now()
      setNowMs(nextNow)
      setCooldownUntil(nextNow + DEFAULT_RESEND_COOLDOWN_SECONDS * 1000)
    } catch (error) {
      const retryAfter = extractRetryAfterSeconds(error)
      if (retryAfter !== null) {
        const nextNow = Date.now()
        setNowMs(nextNow)
        setCooldownUntil(nextNow + retryAfter * 1000)
      }
    }
  }

  async function handleVerifySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (code.length !== 6 || isOtpLocked) {
      return
    }
    try {
      const updatedUser = await onVerifyOtp(code)
      setVerifiedUser(updatedUser)
      onVerified?.(updatedUser)
    } catch {
      // El error se refleja mediante verifyError desde TanStack Query.
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const pasted = event.clipboardData.getData('text')
    const sanitized = sanitizeOtpInput(pasted)
    if (sanitized.length > 0) {
      event.preventDefault()
      setCode(sanitized)
    }
  }

  if (verifiedUser) {
    const autoVerifiedUisek =
      purpose === 'BUYER_EMAIL' &&
      verifiedUser.is_uisek_verified &&
      Boolean(verifiedUser.uisek_email)

    return (
      <div className="space-y-4">
        <Alert variant="success" title="Correo verificado correctamente">
          Tu correo <strong>{effectiveTargetEmail}</strong> quedó confirmado.
        </Alert>

        {autoVerifiedUisek && (
          <div className="rounded-xl border border-brand-100 bg-brand-50 p-3.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">Correo institucional UISEK verificado automáticamente</Badge>
            </div>
            <p className="mt-2 text-sm text-brand-900">
              Detectamos tu correo <strong>{verifiedUser.uisek_email}</strong>: ya no necesitarás
              verificarlo de nuevo si decides vender en U-Trade.
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {(title || description) && (
        <div>
          {title && <h2 className="text-base font-bold text-ink-900">{title}</h2>}
          {description && <p className="mt-1 text-sm text-ink-700">{description}</p>}
        </div>
      )}

      <div className="rounded-xl border border-line bg-canvas p-3.5 text-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs font-medium text-ink-500">Correo destino</p>
            <p className="truncate font-semibold text-ink-900">{effectiveTargetEmail}</p>
          </div>
          {onChangeEmail && (
            <Button variant="ghost" size="md" onClick={onChangeEmail}>
              Cambiar correo
            </Button>
          )}
        </div>
        {otpMeta?.expires_at && (
          <p className="mt-2 text-xs text-ink-700">
            Código enviado. Válido hasta las{' '}
            <strong>{formatEcuadorDateTime(otpMeta.expires_at)}</strong> (hora Ecuador).
          </p>
        )}
      </div>

      {requestError !== null && requestError !== undefined && (
        <Alert variant="error">
          {isRateLimited && remainingCooldown > 0
            ? `Has alcanzado el límite de 3 envíos en 15 minutos. Podrás pedir otro código en ${formatWaitDuration(remainingCooldown)}.`
            : getErrorMessage(requestError)}
        </Alert>
      )}

      {isEmailConflictOrInvalid && onChangeEmail && (
        <Button variant="secondary" fullWidth onClick={onChangeEmail}>
          Ingresar otro correo @uisek.edu.ec
        </Button>
      )}

      {!hasCodeBeenSent ? (
        <div className="space-y-3">
          <p className="text-xs text-ink-500">
            Te enviaremos un código numérico de 6 dígitos (máx. 3 envíos cada 15 minutos, vigente
            por 10 minutos).
          </p>
          <Button
            fullWidth
            size="lg"
            loading={isRequesting}
            disabled={remainingCooldown > 0}
            onClick={() => void handleRequestCode()}
          >
            {remainingCooldown > 0
              ? `Espera ${formatWaitDuration(remainingCooldown)}`
              : 'Enviar código de 6 dígitos'}
          </Button>
        </div>
      ) : (
        <form onSubmit={(event) => void handleVerifySubmit(event)} className="space-y-4" noValidate>
          {verifyError !== null && verifyError !== undefined && (
            <Alert variant="error">
              <div className="space-y-2">
                <p>{getErrorMessage(verifyError)}</p>
                {attemptsRemaining !== null && (
                  <div>
                    <Badge variant={attemptsRemaining <= 1 ? 'danger' : 'warning'}>
                      {attemptsRemaining === 1
                        ? 'Último intento disponible'
                        : `${attemptsRemaining} intentos restantes`}
                    </Badge>
                  </div>
                )}
              </div>
            </Alert>
          )}

          {isOtpLocked ? (
            <div className="space-y-3 rounded-xl border border-line bg-canvas p-4 text-sm text-ink-700">
              <p className="font-semibold text-ink-900">Este código quedó bloqueado</p>
              <p>
                Por seguridad, tras 5 intentos fallidos debes solicitar un código nuevo para
                continuar.
              </p>
              <Button
                fullWidth
                size="lg"
                loading={isRequesting}
                disabled={remainingCooldown > 0}
                onClick={() => void handleRequestCode()}
              >
                {remainingCooldown > 0
                  ? `Solicitar nuevo código en ${formatWaitDuration(remainingCooldown)}`
                  : 'Solicitar nuevo código'}
              </Button>
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-1.5">
                <label htmlFor={otpInputId} className="text-sm font-medium text-ink-900">
                  Código de verificación (6 dígitos)
                  <span className="ml-0.5 text-feedback-error">*</span>
                </label>
                <input
                  id={otpInputId}
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\d{6}"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(event) => {
                    setCode(sanitizeOtpInput(event.target.value))
                    if (verifyError) {
                      onClearErrors?.()
                    }
                  }}
                  onPaste={handlePaste}
                  aria-invalid={verifyError ? true : undefined}
                  className={[
                    'min-h-12 w-full rounded-xl border bg-surface px-4 text-center font-mono text-2xl font-bold tracking-[0.35em] text-ink-900 placeholder:tracking-[0.2em] placeholder:text-slate-300',
                    'transition-colors focus:outline-none focus:ring-2',
                    verifyError
                      ? 'border-feedback-error focus:border-feedback-error focus:ring-rose-200'
                      : 'border-line focus:border-brand-700 focus:ring-brand-100',
                  ].join(' ')}
                  required
                />
                <p className="text-xs text-ink-500">
                  Puedes pegar el código de 6 dígitos directamente desde tu correo.
                </p>
              </div>

              <Button
                type="submit"
                fullWidth
                size="lg"
                loading={isVerifying}
                disabled={code.length !== 6}
              >
                Verificar código
              </Button>
            </>
          )}

          {!isOtpLocked && (
            <div className="space-y-2 border-t border-line pt-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-ink-500">
                  {isOtpExpired
                    ? 'Tu código anterior venció. Pide uno nuevo.'
                    : 'Máximo 3 envíos cada 15 minutos.'}
                </p>
                <Button
                  variant={isOtpExpired ? 'secondary' : 'ghost'}
                  size="md"
                  loading={isRequesting}
                  disabled={remainingCooldown > 0}
                  onClick={() => void handleRequestCode()}
                >
                  {remainingCooldown > 0
                    ? `Reenviar en ${formatWaitDuration(remainingCooldown)}`
                    : 'Reenviar código'}
                </Button>
              </div>
            </div>
          )}
        </form>
      )}
    </div>
  )
}
