import { ApiError } from '../../api/client'

export const ERROR_MESSAGES: Record<string, string> = {
  // Auth Core
  INVALID_CREDENTIALS: 'Correo o contraseña incorrectos.',
  EMAIL_ALREADY_REGISTERED: 'Ya existe una cuenta registrada con este correo.',
  DISPOSABLE_EMAIL:
    'No se permiten correos temporales o desechables. Usa un correo personal o institucional.',
  CONSENT_REQUIRED: 'Debes aceptar los Términos de Uso y la Política de Privacidad.',
  INVALID_PASSWORD: 'La contraseña actual no es correcta.',
  INVALID_RESET_TOKEN:
    'El enlace de restablecimiento no es válido o ya expiró. Solicita uno nuevo.',

  // Core / Seguridad HTTP
  NOT_AUTHENTICATED: 'Debes iniciar sesión para continuar.',
  PERMISSION_DENIED: 'No tienes permiso para realizar esta acción.',
  CSRF_FAILED: 'Tu sesión de seguridad expiró. Recarga la página e inténtalo de nuevo.',
  FORBIDDEN_PROXY: 'No se pudo autenticar el canal con el servidor. Intenta de nuevo.',
  UNAUTHORIZED: 'No autorizado.',
  THROTTLED: 'Demasiados intentos en poco tiempo. Espera unos segundos y vuelve a intentarlo.',
  VALIDATION_ERROR: 'Revisa los datos ingresados; algunos campos no son válidos.',
  PARSE_ERROR: 'La solicitud enviada no tiene un formato válido.',
  NOT_FOUND: 'El recurso solicitado no existe.',
  METHOD_NOT_ALLOWED: 'Operación no permitida.',
  NOT_ACCEPTABLE: 'Formato de respuesta no soportado.',
  UNSUPPORTED_MEDIA_TYPE: 'Formato de contenido no soportado.',
  INTERNAL_ERROR: 'Ocurrió un error interno en el servidor. Intenta nuevamente más tarde.',
  NETWORK_ERROR: 'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
  PROXY_MISCONFIGURED: 'El proxy de API no está configurado en este entorno.',
}

function firstDetailMessage(details: Record<string, unknown>): string | null {
  for (const value of Object.values(details)) {
    if (typeof value === 'string' && value.trim()) {
      return value
    }
    if (Array.isArray(value)) {
      const firstText = value.find((item): item is string => typeof item === 'string' && item.trim().length > 0)
      if (firstText) {
        return firstText
      }
    }
  }
  return null
}

export function getFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) {
    return {}
  }

  const fieldErrors: Record<string, string> = {}
  for (const [key, value] of Object.entries(error.details)) {
    if (typeof value === 'string' && value.trim()) {
      fieldErrors[key] = value
    } else if (Array.isArray(value)) {
      const texts = value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
      if (texts.length > 0) {
        fieldErrors[key] = texts.join(' ')
      }
    }
  }
  return fieldErrors
}

export function getErrorMessage(
  error: unknown,
  fallback = 'Ocurrió un error inesperado. Intenta nuevamente.',
): string {
  if (error instanceof ApiError) {
    if (error.code === 'THROTTLED' && typeof error.details.wait_seconds === 'number') {
      return `Demasiados intentos. Intenta nuevamente en ${error.details.wait_seconds} segundos.`
    }
    if (error.code === 'VALIDATION_ERROR') {
      const detail = firstDetailMessage(error.details)
      if (detail) {
        return detail
      }
    }
    return ERROR_MESSAGES[error.code] ?? (error.message || fallback)
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}
