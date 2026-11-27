import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  changePassword,
  confirmPasswordReset,
  deleteAccount,
  fetchCsrfCookie,
  getCurrentUser,
  getHealth,
  login,
  logout,
  register,
  requestPasswordReset,
  updateProfile,
  type AccountDeleteRequest,
  type LoginRequest,
  type PasswordChangeRequest,
  type PasswordResetConfirmRequest,
  type PasswordResetRequest,
  type ProfileUpdateRequest,
  type RegisterRequest,
} from './api'

export const AUTH_QUERY_KEYS = {
  me: ['auth', 'me'] as const,
  health: ['core', 'health'] as const,
}

export function useCurrentUser() {
  return useQuery({
    queryKey: AUTH_QUERY_KEYS.me,
    queryFn: ({ signal }) => getCurrentUser(signal),
    retry: false,
    staleTime: 60_000,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: AUTH_QUERY_KEYS.health,
    queryFn: ({ signal }) => getHealth(signal),
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: LoginRequest) => login(payload),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, user)
    },
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: RegisterRequest) => register(payload),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, user)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => logout(),
    onSuccess: () => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, null)
      void fetchCsrfCookie().catch(() => undefined)
    },
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ProfileUpdateRequest) => updateProfile(payload),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, user)
    },
  })
}

export function usePasswordChange() {
  return useMutation({
    mutationFn: (payload: PasswordChangeRequest) => changePassword(payload),
  })
}

export function usePasswordResetRequest() {
  return useMutation({
    mutationFn: (payload: PasswordResetRequest) => requestPasswordReset(payload),
  })
}

export function usePasswordResetConfirm() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PasswordResetConfirmRequest) => confirmPasswordReset(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEYS.me })
    },
  })
}

export function useDeleteAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AccountDeleteRequest) => deleteAccount(payload),
    onSuccess: () => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, null)
      void fetchCsrfCookie().catch(() => undefined)
    },
  })
}
