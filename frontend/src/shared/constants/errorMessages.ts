import type { components } from '../../api/schema'

export type OpenApiErrorCode = components['schemas']['ErrorCodeEnum']

export type FutureApiErrorCode =
  | 'EMAIL_NOT_VERIFIED'
  | 'USER_SUSPENDED'
  | 'INSUFFICIENT_STOCK'
  | 'TOO_MANY_ACTIVE_RESERVATIONS'
  | 'SALE_PHASE_INVALID'
  | 'ALREADY_DELIVERED'
  | 'QR_INVALID_OWNER'
  | 'NETWORK_ERROR'
  | 'PROXY_MISCONFIGURED'

export type ApiErrorCode = OpenApiErrorCode | FutureApiErrorCode

export const ERROR_MESSAGES: Record<ApiErrorCode, string> = {
  // Core / Seguridad HTTP
  NOT_AUTHENTICATED: 'Inicia sesión para continuar.',
  PERMISSION_DENIED: 'No tienes permiso para realizar esta acción.',
  CSRF_FAILED: 'Tu sesión de seguridad expiró. Recarga la página e inténtalo de nuevo.',
  FORBIDDEN_PROXY: 'No pudimos completar la solicitud. Inténtalo de nuevo.',
  UNAUTHORIZED: 'No autorizado.',
  NOT_FOUND: 'El recurso solicitado no existe.',
  METHOD_NOT_ALLOWED: 'Operación no permitida.',
  NOT_ACCEPTABLE: 'Formato de respuesta no soportado.',
  UNSUPPORTED_MEDIA_TYPE: 'Formato de contenido no soportado.',
  THROTTLED: 'Demasiados intentos en poco tiempo. Espera unos segundos e inténtalo de nuevo.',
  PARSE_ERROR: 'La solicitud enviada no tiene un formato válido.',
  VALIDATION_ERROR: 'Revisa los datos ingresados e inténtalo de nuevo.',
  INTERNAL_ERROR: 'Tuvimos un problema. Inténtalo de nuevo más tarde.',
  NETWORK_ERROR: 'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
  PROXY_MISCONFIGURED: 'El proxy de API no está configurado en este entorno.',

  // Auth Core
  CONSENT_REQUIRED: 'Debes aceptar los Términos de Uso y la Política de Privacidad.',
  DISPOSABLE_EMAIL:
    'No se permiten correos temporales o desechables. Usa un correo personal o institucional.',
  EMAIL_ALREADY_REGISTERED: 'Ya existe una cuenta registrada con este correo.',
  INVALID_CREDENTIALS: 'Correo o contraseña incorrectos.',
  INVALID_PASSWORD: 'La contraseña actual no es correcta.',
  INVALID_RESET_TOKEN:
    'El enlace de restablecimiento no es válido o ya expiró. Solicita uno nuevo.',

  // Verificación OTP y correos
  EMAIL_NOT_VERIFIED: 'Verifica tu correo electrónico para continuar.',
  EMAIL_ALREADY_VERIFIED: 'Este correo ya está verificado.',
  UISEK_NOT_VERIFIED: 'Verifica tu correo institucional @uisek.edu.ec para continuar.',
  UISEK_ALREADY_VERIFIED: 'Tu correo UISEK ya está verificado.',
  UISEK_EMAIL_ALREADY_IN_USE: 'Ese correo institucional ya está vinculado a otra cuenta.',
  INVALID_UISEK_EMAIL: 'Ingresa un correo institucional válido terminado en @uisek.edu.ec.',
  OTP_INVALID: 'El código no coincide. Revísalo e inténtalo otra vez.',
  OTP_EXPIRED_OR_INVALID: 'El código venció o no es válido. Solicita uno nuevo.',
  OTP_LOCKED: 'Alcanzaste el límite de intentos. Solicita un nuevo código.',
  OTP_RATE_LIMITED: 'Has solicitado varios códigos. Espera 15 minutos antes de pedir otro.',

  // Vendedores y solicitudes
  ALREADY_A_SELLER: 'Tu cuenta ya tiene un perfil de vendedor.',
  SELLER_APPLICATION_ALREADY_PENDING: 'Tu solicitud para vender ya está en revisión.',
  SELLER_APPLICATION_NOT_PENDING: 'Esta solicitud ya fue revisada y no se encuentra pendiente.',
  REJECTION_REASON_REQUIRED: 'Debes indicar el motivo de rechazo.',
  NOT_A_SELLER: 'Esta sección es exclusiva para vendedores aprobados en U-Trade.',

  // Dominios posteriores (reservas, QR, penalizaciones)
  USER_SUSPENDED: 'Tu cuenta no puede reservar por ahora. Revisa el aviso de suspensión.',
  INSUFFICIENT_STOCK: 'No hay suficientes unidades disponibles. Actualiza la cantidad.',
  TOO_MANY_ACTIVE_RESERVATIONS:
    'Puedes tener hasta 5 reservas activas. Finaliza una para reservar otra.',
  SALE_PHASE_INVALID: 'Esta venta ya no está disponible para reservar.',
  ALREADY_DELIVERED: 'Esta reserva ya fue entregada.',
  QR_INVALID_OWNER: 'No puedes validar este código desde esta cuenta.',
}

const DEFAULT_ERROR_MESSAGE = 'No pudimos completar la solicitud. Inténtalo de nuevo.'

function isApiErrorCode(code: string): code is ApiErrorCode {
  return Object.prototype.hasOwnProperty.call(ERROR_MESSAGES, code)
}

/** Devuelve el mensaje en español para un código de API o el fallback indicado. */
export function getErrorMessage(code?: string | null, fallbackMessage?: string): string {
  if (code && isApiErrorCode(code)) {
    return ERROR_MESSAGES[code]
  }

  return fallbackMessage?.trim() || DEFAULT_ERROR_MESSAGE
}
