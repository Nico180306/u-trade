import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { ApiError } from '../../../api/client'
import { AUTH_QUERY_KEYS } from '../../auth/hooks'
import {
  createSellerApplication,
  getMySellerApplications,
  getMySellerProfile,
  getPublicSellerProfile,
  requestBuyerEmailOtp,
  requestUisekOtp,
  updateMySellerProfile,
  verifyBuyerEmailOtp,
  verifyUisekOtp,
  type OTPCodeRequest,
  type PatchedSellerProfileUpdateRequest,
  type SellerApplicationCreateRequest,
  type UisekOTPRequestRequest,
} from './sellerApi'

export const SELLER_QUERY_KEYS = {
  applicationsMe: ['sellers', 'applications', 'me'] as const,
  sellerMe: ['sellers', 'me'] as const,
  publicProfilesRoot: ['sellers', 'public'] as const,
  publicProfile: (id: string) => ['sellers', 'public', id] as const,
}

function invalidateVerificationAndSellerQueries(queryClient: QueryClient, sellerId?: string) {
  void queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEYS.me })
  void queryClient.invalidateQueries({ queryKey: SELLER_QUERY_KEYS.applicationsMe })
  void queryClient.invalidateQueries({ queryKey: SELLER_QUERY_KEYS.sellerMe })
  void queryClient.invalidateQueries({ queryKey: SELLER_QUERY_KEYS.publicProfilesRoot })
  if (sellerId) {
    void queryClient.invalidateQueries({ queryKey: SELLER_QUERY_KEYS.publicProfile(sellerId) })
  }
}

export function useMySellerApplications(enabled = true) {
  return useQuery({
    queryKey: SELLER_QUERY_KEYS.applicationsMe,
    queryFn: ({ signal }) => getMySellerApplications(signal),
    enabled,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        return false
      }
      return failureCount < 1
    },
  })
}

export function useMySellerProfile(enabled = true) {
  return useQuery({
    queryKey: SELLER_QUERY_KEYS.sellerMe,
    queryFn: ({ signal }) => getMySellerProfile(signal),
    enabled,
    retry: (failureCount, error) => {
      if (
        error instanceof ApiError &&
        (error.status === 401 || error.status === 403 || error.code === 'NOT_A_SELLER')
      ) {
        return false
      }
      return failureCount < 1
    },
  })
}

export function usePublicSellerProfile(sellerId: string | undefined) {
  return useQuery({
    queryKey: SELLER_QUERY_KEYS.publicProfile(sellerId ?? ''),
    queryFn: ({ signal }) => getPublicSellerProfile(sellerId!, signal),
    enabled: Boolean(sellerId),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 404 || error.code === 'NOT_FOUND')) {
        return false
      }
      return failureCount < 1
    },
  })
}

export function useRequestBuyerEmailOtp() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => requestBuyerEmailOtp(),
    onSuccess: () => {
      invalidateVerificationAndSellerQueries(queryClient)
    },
  })
}

export function useVerifyBuyerEmailOtp() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: OTPCodeRequest) => verifyBuyerEmailOtp(payload),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, user)
      invalidateVerificationAndSellerQueries(queryClient, user.seller_profile_id ?? undefined)
    },
  })
}

export function useRequestUisekOtp() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UisekOTPRequestRequest) => requestUisekOtp(payload),
    onSuccess: () => {
      invalidateVerificationAndSellerQueries(queryClient)
    },
  })
}

export function useVerifyUisekOtp() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: OTPCodeRequest) => verifyUisekOtp(payload),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.me, user)
      invalidateVerificationAndSellerQueries(queryClient, user.seller_profile_id ?? undefined)
    },
  })
}

export function useCreateSellerApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SellerApplicationCreateRequest) => createSellerApplication(payload),
    onSuccess: () => {
      invalidateVerificationAndSellerQueries(queryClient)
    },
  })
}

export function useUpdateMySellerProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PatchedSellerProfileUpdateRequest) => updateMySellerProfile(payload),
    onSuccess: (profile) => {
      queryClient.setQueryData(SELLER_QUERY_KEYS.sellerMe, profile)
      invalidateVerificationAndSellerQueries(queryClient, profile.id)
    },
  })
}
