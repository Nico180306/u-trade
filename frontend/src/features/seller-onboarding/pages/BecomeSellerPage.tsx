import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Badge, Button, Input, Skeleton, Textarea } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTime } from '../../../shared/utils/format'
import { useCurrentUser } from '../../auth/hooks'
import {
  useCreateSellerApplication,
  useMySellerApplications,
  useRequestUisekOtp,
  useVerifyUisekOtp,
  type OTPRequestResponse,
  type SellerApplication,
} from '../api'
import { OtpVerificationCard } from '../components/OtpVerificationCard'

const UISEK_EMAIL_PATTERN = /^[^\s@]+@uisek\.edu\.ec$/i
const PHONE_PATTERN = /^\+?[0-9][0-9 -]{6,18}$/
const INSTAGRAM_PATTERN = /^@?[A-Za-z0-9._]{1,30}$/

interface StepUisekVerificationProps {
  defaultEmail: string
}

function StepUisekVerification({ defaultEmail }: StepUisekVerificationProps) {
  const [uisekEmail, setUisekEmail] = useState(
    UISEK_EMAIL_PATTERN.test(defaultEmail) ? defaultEmail : '',
  )
  const [emailClientError, setEmailClientError] = useState<string | null>(null)
  const [sentOtpMeta, setSentOtpMeta] = useState<OTPRequestResponse | null>(null)

  const requestUisekOtpMutation = useRequestUisekOtp()
  const verifyUisekOtpMutation = useVerifyUisekOtp()
  const requestFieldErrors = getFieldErrors(requestUisekOtpMutation.error)

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setEmailClientError(null)

    const normalized = uisekEmail.trim().toLowerCase()
    if (!UISEK_EMAIL_PATTERN.test(normalized)) {
      setEmailClientError(
        'Ingresa un correo institucional válido terminado en @uisek.edu.ec.',
      )
      return
    }

    try {
      const response = await requestUisekOtpMutation.mutateAsync({ uisek_email: normalized })
      setUisekEmail(normalized)
      setSentOtpMeta(response)
    } catch {
      // El error se muestra con requestUisekOtpMutation.error.
    }
  }

  return (
    <section className="space-y-4 rounded-2xl border border-line bg-surface p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Badge variant="info">Paso 1 de 2</Badge>
        <span className="text-xs font-medium text-ink-500">Verificación estudiantil UISEK</span>
      </div>

      <div>
        <h1 className="text-xl font-bold tracking-tight text-ink-900">
          Verifica tu correo @uisek.edu.ec
        </h1>
        <p className="mt-1 text-sm text-ink-700">
          Vender en U-Trade es exclusivo para estudiantes de la UISEK. Confirma tu correo
          institucional con un código de 6 dígitos para habilitar tu solicitud.
        </p>
      </div>

      {sentOtpMeta ? (
        <OtpVerificationCard
          purpose="UISEK_SELLER"
          targetEmail={sentOtpMeta.target_email}
          initialOtpMeta={sentOtpMeta}
          onRequestOtp={() =>
            requestUisekOtpMutation.mutateAsync({ uisek_email: uisekEmail.trim().toLowerCase() })
          }
          onVerifyOtp={(code) => verifyUisekOtpMutation.mutateAsync({ code })}
          isRequesting={requestUisekOtpMutation.isPending}
          isVerifying={verifyUisekOtpMutation.isPending}
          requestError={requestUisekOtpMutation.error}
          verifyError={verifyUisekOtpMutation.error}
          onClearErrors={() => {
            requestUisekOtpMutation.reset()
            verifyUisekOtpMutation.reset()
          }}
          onChangeEmail={() => {
            setSentOtpMeta(null)
            requestUisekOtpMutation.reset()
            verifyUisekOtpMutation.reset()
          }}
        />
      ) : (
        <form onSubmit={(event) => void handleEmailSubmit(event)} className="space-y-4" noValidate>
          {(emailClientError || requestUisekOtpMutation.isError) && (
            <Alert variant="error">
              {emailClientError ?? getErrorMessage(requestUisekOtpMutation.error)}
            </Alert>
          )}

          <Input
            label="Correo institucional UISEK"
            type="email"
            name="uisek_email"
            autoComplete="email"
            inputMode="email"
            placeholder="tu.nombre@uisek.edu.ec"
            hint="Solo se aceptan correos @uisek.edu.ec (máx. 3 envíos cada 15 minutos)."
            value={uisekEmail}
            onChange={(event) => {
              setUisekEmail(event.target.value)
              if (emailClientError) setEmailClientError(null)
              if (requestUisekOtpMutation.isError) requestUisekOtpMutation.reset()
            }}
            error={requestFieldErrors.uisek_email}
            required
          />

          <Button
            type="submit"
            fullWidth
            size="lg"
            loading={requestUisekOtpMutation.isPending}
          >
            Enviar código de verificación
          </Button>
        </form>
      )}
    </section>
  )
}

interface SellerApplicationFormProps {
  uisekEmail: string | null
  rejectedApplication: SellerApplication | null
  defaultPhone: string
}

function SellerApplicationForm({
  uisekEmail,
  rejectedApplication,
  defaultPhone,
}: SellerApplicationFormProps) {
  const [ventureName, setVentureName] = useState(rejectedApplication?.venture_name ?? '')
  const [description, setDescription] = useState(rejectedApplication?.description ?? '')
  const [contactPhone, setContactPhone] = useState(
    rejectedApplication?.contact_phone ?? defaultPhone,
  )
  const [instagramHandle, setInstagramHandle] = useState(
    rejectedApplication?.instagram_handle ?? '',
  )
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})

  const createMutation = useCreateSellerApplication()
  const serverFieldErrors = getFieldErrors(createMutation.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedName = ventureName.trim()
    const trimmedDescription = description.trim()
    const trimmedPhone = contactPhone.trim()
    const trimmedInstagram = instagramHandle.trim()

    const nextErrors: Record<string, string> = {}
    if (!trimmedName) {
      nextErrors.venture_name = 'Ingresa el nombre de tu emprendimiento.'
    }
    if (!trimmedDescription) {
      nextErrors.description = 'Describe brevemente qué vendes en el campus.'
    }
    if (!PHONE_PATTERN.test(trimmedPhone)) {
      nextErrors.contact_phone =
        'Ingresa un teléfono válido (7 a 19 dígitos, por ejemplo 0991234567 o +593 99 123 4567).'
    }
    if (trimmedInstagram && !INSTAGRAM_PATTERN.test(trimmedInstagram)) {
      nextErrors.instagram_handle =
        'Usuario de Instagram inválido (solo letras, números, puntos y guiones bajos, máx. 30 caracteres).'
    }

    if (Object.keys(nextErrors).length > 0) {
      setClientErrors(nextErrors)
      return
    }

    setClientErrors({})
    createMutation.mutate({
      venture_name: trimmedName,
      description: trimmedDescription,
      contact_phone: trimmedPhone,
      instagram_handle: trimmedInstagram,
    })
  }

  return (
    <section className="space-y-4 rounded-2xl border border-line bg-surface p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Badge variant="info">Paso 2 de 2</Badge>
        {uisekEmail && <Badge variant="success">UISEK: {uisekEmail}</Badge>}
      </div>

      <div>
        <h1 className="text-xl font-bold tracking-tight text-ink-900">
          Solicitud de emprendimiento
        </h1>
        <p className="mt-1 text-sm text-ink-700">
          Cuéntanos sobre tu emprendimiento estudiantil. Un administrador revisará tu solicitud
          para activar tu perfil de vendedor.
        </p>
      </div>

      {rejectedApplication && (
        <Alert variant="warning" title="Tu solicitud anterior fue rechazada">
          <p>{rejectedApplication.rejection_reason || 'No se especificó un motivo.'}</p>
          {rejectedApplication.reviewed_at && (
            <p className="mt-1.5 text-xs">
              Revisada el {formatEcuadorDateTime(rejectedApplication.reviewed_at)} (hora Ecuador).
              Puedes corregir los datos abajo y enviar una nueva solicitud.
            </p>
          )}
        </Alert>
      )}

      {createMutation.isError && (
        <Alert variant="error">{getErrorMessage(createMutation.error)}</Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Nombre del emprendimiento"
          type="text"
          name="venture_name"
          maxLength={100}
          placeholder="Ej. Brownies del Campus"
          value={ventureName}
          onChange={(event) => {
            setVentureName(event.target.value)
            if (clientErrors.venture_name) {
              setClientErrors((prev) => ({ ...prev, venture_name: '' }))
            }
          }}
          error={clientErrors.venture_name || serverFieldErrors.venture_name}
          required
        />

        <Textarea
          label="Descripción"
          name="description"
          maxLength={1000}
          rows={4}
          placeholder="Cuenta qué productos ofreces, ingredientes o detalles útiles para los compradores."
          hint={`${description.trim().length}/1000 caracteres`}
          value={description}
          onChange={(event) => {
            setDescription(event.target.value)
            if (clientErrors.description) {
              setClientErrors((prev) => ({ ...prev, description: '' }))
            }
          }}
          error={clientErrors.description || serverFieldErrors.description}
          required
        />

        <Input
          label="Teléfono de contacto"
          type="tel"
          name="contact_phone"
          autoComplete="tel"
          inputMode="tel"
          maxLength={20}
          placeholder="0991234567"
          hint="Solo para coordinación administrativa. Nunca se muestra en tu perfil público (LOPDP)."
          value={contactPhone}
          onChange={(event) => {
            setContactPhone(event.target.value)
            if (clientErrors.contact_phone) {
              setClientErrors((prev) => ({ ...prev, contact_phone: '' }))
            }
          }}
          error={clientErrors.contact_phone || serverFieldErrors.contact_phone}
          required
        />

        <Input
          label="Instagram (opcional)"
          type="text"
          name="instagram_handle"
          maxLength={31}
          placeholder="@tu_emprendimiento"
          hint="Opcional. Sin espacios ni URL completa."
          value={instagramHandle}
          onChange={(event) => {
            setInstagramHandle(event.target.value)
            if (clientErrors.instagram_handle) {
              setClientErrors((prev) => ({ ...prev, instagram_handle: '' }))
            }
          }}
          error={clientErrors.instagram_handle || serverFieldErrors.instagram_handle}
        />

        <Button type="submit" fullWidth size="lg" loading={createMutation.isPending}>
          {rejectedApplication ? 'Enviar solicitud corregida' : 'Enviar solicitud de vendedor'}
        </Button>
      </form>
    </section>
  )
}

export function BecomeSellerPage() {
  const userQuery = useCurrentUser()
  const user = userQuery.data

  const applicationsQuery = useMySellerApplications(Boolean(user && !user.is_seller))

  if (userQuery.isPending || (user && !user.is_seller && applicationsQuery.isPending)) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    )
  }

  if (userQuery.isError) {
    return (
      <Alert variant="error" title="No se pudo verificar tu cuenta">
        {getErrorMessage(userQuery.error)}
      </Alert>
    )
  }

  if (!user) {
    return null
  }

  // Caso A: ya es vendedor activo
  if (user.is_seller) {
    return (
      <section className="space-y-4 rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <Badge variant="success">Vendedor activo</Badge>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink-900">
            Tu emprendimiento ya está aprobado
          </h1>
          <p className="mt-1 text-sm text-ink-700">
            Puedes editar la información de tu emprendimiento y revisar tus métricas desde tu
            perfil de vendedor.
          </p>
        </div>

        <div className="flex flex-col gap-2.5 sm:flex-row">
          <Link
            to="/seller/profile"
            className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-brand-700 px-5 text-base font-semibold text-white transition-colors hover:bg-brand-900"
          >
            Ir a mi emprendimiento
          </Link>
          {user.seller_profile_id && (
            <Link
              to={`/sellers/${user.seller_profile_id}`}
              className="inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-line bg-surface px-5 text-base font-semibold text-ink-900 transition-colors hover:bg-canvas"
            >
              Ver perfil público
            </Link>
          )}
        </div>
      </section>
    )
  }

  if (applicationsQuery.isError) {
    return (
      <Alert variant="error" title="No se pudo consultar tus solicitudes">
        {getErrorMessage(applicationsQuery.error)}
      </Alert>
    )
  }

  const latestApplication = applicationsQuery.data?.[0] ?? null

  // Caso B: todavía no tiene correo UISEK verificado
  if (!user.is_uisek_verified) {
    return <StepUisekVerification defaultEmail={user.uisek_email || user.email} />
  }

  // Caso D: tiene una solicitud PENDING en revisión
  if (latestApplication?.status === 'PENDING') {
    return (
      <section className="space-y-4 rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Badge variant="warning">Solicitud en revisión</Badge>
          <span className="text-xs text-ink-500">
            Enviada el {formatEcuadorDateTime(latestApplication.created_at)}
          </span>
        </div>

        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink-900">
            Recibimos tu solicitud para vender
          </h1>
          <p className="mt-1 text-sm text-ink-700">
            El equipo administrativo de U-Trade revisará tu emprendimiento pronto. Cuando sea
            aprobado, se habilitará automáticamente tu sección «Mi emprendimiento».
          </p>
        </div>

        <dl className="space-y-3 rounded-xl border border-line bg-canvas p-4 text-sm">
          <div>
            <dt className="text-xs font-medium text-ink-500">Emprendimiento</dt>
            <dd className="mt-0.5 font-semibold text-ink-900">
              {latestApplication.venture_name}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-ink-500">Descripción</dt>
            <dd className="mt-0.5 whitespace-pre-line text-ink-700">
              {latestApplication.description}
            </dd>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium text-ink-500">Teléfono de contacto</dt>
              <dd className="mt-0.5 font-medium text-ink-900">
                {latestApplication.contact_phone}
              </dd>
            </div>
            {latestApplication.instagram_handle && (
              <div>
                <dt className="text-xs font-medium text-ink-500">Instagram</dt>
                <dd className="mt-0.5 font-medium text-ink-900">
                  {latestApplication.instagram_handle}
                </dd>
              </div>
            )}
          </div>
          <div>
            <dt className="text-xs font-medium text-ink-500">Fecha de envío (hora Ecuador)</dt>
            <dd className="mt-0.5 text-ink-700">
              {formatEcuadorDateTime(latestApplication.created_at)}
            </dd>
          </div>
        </dl>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button
            variant="secondary"
            fullWidth
            loading={applicationsQuery.isFetching || userQuery.isFetching}
            onClick={() => {
              void Promise.all([userQuery.refetch(), applicationsQuery.refetch()])
            }}
          >
            Actualizar estado
          </Button>
          <Link
            to="/profile"
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-line bg-surface px-4 text-sm font-semibold text-ink-900 hover:bg-canvas"
          >
            Volver a mi perfil
          </Link>
        </div>
      </section>
    )
  }

  // Caso C: UISEK verificado y sin solicitud PENDING (nunca postuló o última REJECTED)
  return (
    <SellerApplicationForm
      key={latestApplication?.id ?? 'new'}
      uisekEmail={user.uisek_email}
      rejectedApplication={latestApplication?.status === 'REJECTED' ? latestApplication : null}
      defaultPhone={user.phone_number}
    />
  )
}
