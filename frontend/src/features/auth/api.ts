import { apiRequest, ApiError, fetchCsrfCookie } from '../../api/client'
import type { components } from '../../api/schema'

export type UserMe = components['schemas']['UserMe']
export type LoginRequest = components['schemas']['LoginRequest']
export type RegisterRequest = components['schemas']['RegisterRequest']
export type ProfileUpdateRequest = components['schemas']['PatchedProfileUpdateRequest']
export type PasswordChangeRequest = components['schemas']['PasswordChangeRequest']
export type PasswordResetRequest = components['schemas']['PasswordResetRequestRequest']
export type PasswordResetConfirmRequest = components['schemas']['PasswordResetConfirmRequest']
export type AccountDeleteRequest = components['schemas']['AccountDeleteRequest']
export type HealthResponse = components['schemas']['HealthResponse']

export async function getCurrentUser(signal?: AbortSignal): Promise<UserMe | null> {
  try {
    return await apiRequest<UserMe>('/auth/me/', { method: 'GET', signal })
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.code === 'NOT_AUTHENTICATED' || error.status === 401)
    ) {
      return null
    }
    throw error
  }
}

export function login(payload: LoginRequest): Promise<UserMe> {
  return apiRequest<UserMe>('/auth/login/', { method: 'POST', body: payload })
}

export function register(payload: RegisterRequest): Promise<UserMe> {
  return apiRequest<UserMe>('/auth/register/', { method: 'POST', body: payload })
}

export function logout(): Promise<void> {
  return apiRequest<void>('/auth/logout/', { method: 'POST' })
}

export function updateProfile(payload: ProfileUpdateRequest): Promise<UserMe> {
  return apiRequest<UserMe>('/auth/me/', { method: 'PATCH', body: payload })
}

export function changePassword(payload: PasswordChangeRequest): Promise<void> {
  return apiRequest<void>('/auth/password-change/', { method: 'POST', body: payload })
}

export function requestPasswordReset(payload: PasswordResetRequest): Promise<void> {
  return apiRequest<void>('/auth/password-reset/request/', { method: 'POST', body: payload })
}

export function confirmPasswordReset(payload: PasswordResetConfirmRequest): Promise<void> {
  return apiRequest<void>('/auth/password-reset/confirm/', { method: 'POST', body: payload })
}

export function deleteAccount(payload: AccountDeleteRequest): Promise<void> {
  return apiRequest<void>('/auth/me/delete/', { method: 'POST', body: payload })
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health/', { method: 'GET', signal })
}

export { fetchCsrfCookie }
