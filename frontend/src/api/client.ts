const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '')

const MUTATING_METHODS = new Set(['POST', 'PATCH', 'PUT', 'DELETE'])

export interface ApiErrorPayload {
  code: string
  message: string
  details?: Record<string, unknown>
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>

  constructor(
    status: number,
    code: string,
    message: string,
    details: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export function getCookie(name: string): string | null {
  if (typeof document === 'undefined' || !document.cookie) {
    return null
  }
  const prefix = `${encodeURIComponent(name)}=`
  const parts = document.cookie.split(';')
  for (const part of parts) {
    const trimmed = part.trim()
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length))
    }
  }
  return null
}

export function getCsrfToken(): string | null {
  return getCookie('csrftoken')
}

export interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  headers?: Record<string, string>
}

function normalizePath(path: string): string {
  return path.startsWith('/') ? path : `/${path}`
}

function isErrorPayload(value: unknown): value is ApiErrorPayload {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const record = value as Record<string, unknown>
  return typeof record.code === 'string' && typeof record.message === 'string'
}

export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<TResponse> {
  const method = options.method ?? 'GET'
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (MUTATING_METHODS.has(method)) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken)
    }
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${normalizePath(path)}`, {
      method,
      credentials: 'include',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(
      0,
      'NETWORK_ERROR',
      'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
    )
  }

  if (response.status === 204) {
    return undefined as TResponse
  }

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  let parsedBody: unknown = null

  if (isJson) {
    try {
      parsedBody = await response.json()
    } catch {
      parsedBody = null
    }
  }

  if (!response.ok) {
    if (isErrorPayload(parsedBody)) {
      throw new ApiError(
        response.status,
        parsedBody.code,
        parsedBody.message,
        parsedBody.details ?? {},
      )
    }
    throw new ApiError(
      response.status,
      response.status >= 500 ? 'INTERNAL_ERROR' : 'HTTP_ERROR',
      `Error del servidor (HTTP ${response.status}).`,
    )
  }

  return parsedBody as TResponse
}

export function fetchCsrfCookie(signal?: AbortSignal): Promise<void> {
  return apiRequest<void>('/auth/csrf/', { method: 'GET', signal })
}
