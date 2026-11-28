export type ApiErrorCode =
  | 'NOT_AUTHENTICATED'
  | 'FORBIDDEN_PROXY'
  | 'EMAIL_NOT_VERIFIED'
  | 'EMAIL_ALREADY_VERIFIED'
  | 'UISEK_NOT_VERIFIED'
  | 'UISEK_ALREADY_VERIFIED'
  | 'UISEK_EMAIL_ALREADY_IN_USE'
  | 'OTP_INVALID'
  | 'OTP_EXPIRED_OR_INVALID'
  | 'OTP_LOCKED'
  | 'OTP_RATE_LIMITED'
  | 'ALREADY_A_SELLER'
  | 'SELLER_APPLICATION_ALREADY_PENDING'
  | 'USER_SUSPENDED'
  | 'INSUFFICIENT_STOCK'
  | 'TOO_MANY_ACTIVE_RESERVATIONS'
  | 'SALE_PHASE_INVALID'
  | 'ALREADY_DELIVERED'
  | 'QR_INVALID_OWNER'
  | 'VALIDATION_ERROR'
  | 'INTERNAL_ERROR'

export const ERROR_MESSAGES: Record<ApiErrorCode, string> = {
  NOT_AUTHENTICATED: 'Inicia sesión para continuar.',
  FORBIDDEN_PROXY: 'No pudimos completar la solicitud. Inténtalo de nuevo.',
  EMAIL_NOT_VERIFIED: 'Verifica tu correo electrónico para continuar.',
  EMAIL_ALREADY_VERIFIED: 'Este correo ya está verificado.',
  UISEK_NOT_VERIFIED: 'Verifica tu correo institucional @uisek.edu.ec para continuar.',
  UISEK_ALREADY_VERIFIED: 'Tu correo UISEK ya está verificado.',
  UISEK_EMAIL_ALREADY_IN_USE: 'Ese correo institucional ya está vinculado a otra cuenta.',
  OTP_INVALID: 'El código no coincide. Revísalo e inténtalo otra vez.',
  OTP_EXPIRED_OR_INVALID: 'El código venció o no es válido. Solicita uno nuevo.',
  OTP_LOCKED: 'Alcanzaste el límite de intentos. Solicita un nuevo código.',
  OTP_RATE_LIMITED: 'Has solicitado varios códigos. Espera 15 minutos antes de pedir otro.',
  ALREADY_A_SELLER: 'Tu cuenta ya tiene un perfil de vendedor.',
  SELLER_APPLICATION_ALREADY_PENDING: 'Tu solicitud para vender ya está en revisión.',
  USER_SUSPENDED: 'Tu cuenta no puede reservar por ahora. Revisa el aviso de suspensión.',
  INSUFFICIENT_STOCK: 'No hay suficientes unidades disponibles. Actualiza la cantidad.',
  TOO_MANY_ACTIVE_RESERVATIONS:
    'Puedes tener hasta 5 reservas activas. Finaliza una para reservar otra.',
  SALE_PHASE_INVALID: 'Esta venta ya no está disponible para reservar.',
  ALREADY_DELIVERED: 'Esta reserva ya fue entregada.',
  QR_INVALID_OWNER: 'No puedes validar este código desde esta cuenta.',
  VALIDATION_ERROR: 'Revisa los datos ingresados e inténtalo de nuevo.',
  INTERNAL_ERROR: 'Tuvimos un problema. Inténtalo de nuevo más tarde.',
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