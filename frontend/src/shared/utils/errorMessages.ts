import { ApiError } from '../../api/client'
import {
  ERROR_MESSAGES,
  getErrorMessage as getCodeErrorMessage,
} from '../constants/errorMessages'

export { ERROR_MESSAGES }

export function formatWaitDuration(seconds: number): string {
  const safeSeconds = Math.max(1, Math.ceil(seconds))
  if (safeSeconds < 60) {
    return `${safeSeconds} ${safeSeconds === 1 ? 'segundo' : 'segundos'}`
  }
  const minutes = Math.floor(safeSeconds / 60)
  const remainder = safeSeconds % 60
  if (remainder === 0) {
    return `${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`
  }
  return `${minutes} min ${remainder} s`
}

function firstDetailMessage(details: Record<string, unknown>): string | null {
  for (const value of Object.values(details)) {
    if (typeof value === 'string' && value.trim()) {
      return value
    }
    if (Array.isArray(value)) {
      const firstText = value.find(
        (item): item is string => typeof item === 'string' && item.trim().length > 0,
      )
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
      const texts = value.filter(
        (item): item is string => typeof item === 'string' && item.trim().length > 0,
      )
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
    if (error.code === 'OTP_INVALID' && typeof error.details.attempts_remaining === 'number') {
      const remaining = error.details.attempts_remaining
      return remaining === 1
        ? 'El código no coincide. Te queda 1 intento antes de bloquear este código.'
        : `El código no coincide. Te quedan ${remaining} intentos.`
    }
    if (
      error.code === 'OTP_RATE_LIMITED' &&
      typeof error.details.retry_after_seconds === 'number'
    ) {
      return `Has alcanzado el límite de 3 envíos en 15 minutos. Intenta de nuevo en ${formatWaitDuration(error.details.retry_after_seconds)}.`
    }
    if (error.code === 'THROTTLED' && typeof error.details.wait_seconds === 'number') {
      return `Demasiados intentos. Intenta nuevamente en ${formatWaitDuration(error.details.wait_seconds)}.`
    }
    if (error.code === 'VALIDATION_ERROR') {
      const detail = firstDetailMessage(error.details)
      if (detail) {
        return detail
      }
    }
    return getCodeErrorMessage(error.code, error.message || fallback)
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}
