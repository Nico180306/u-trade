import { apiRequest } from '../../../api/client'
import type { components } from '../../../api/schema'

export type OTPCodeRequest = components['schemas']['OTPCodeRequest']
export type OTPRequestResponse = components['schemas']['OTPRequestResponse']
export type PurposeEnum = components['schemas']['PurposeEnum']
export type UisekOTPRequestRequest = components['schemas']['UisekOTPRequestRequest']
export type UserMe = components['schemas']['UserMe']
export type SellerApplication = components['schemas']['SellerApplication']
export type SellerApplicationCreateRequest =
  components['schemas']['SellerApplicationCreateRequest']
export type SellerOwnProfile = components['schemas']['SellerOwnProfile']
export type PatchedSellerProfileUpdateRequest =
  components['schemas']['PatchedSellerProfileUpdateRequest']
export type SellerPublicProfile = components['schemas']['SellerPublicProfile']

export function requestBuyerEmailOtp(): Promise<OTPRequestResponse> {
  return apiRequest<OTPRequestResponse>('/auth/email-otp/request/', {
    method: 'POST',
  })
}

export function verifyBuyerEmailOtp(payload: OTPCodeRequest): Promise<UserMe> {
  return apiRequest<UserMe>('/auth/email-otp/verify/', {
    method: 'POST',
    body: payload,
  })
}

export function requestUisekOtp(payload: UisekOTPRequestRequest): Promise<OTPRequestResponse> {
  return apiRequest<OTPRequestResponse>('/sellers/uisek-otp/request/', {
    method: 'POST',
    body: payload,
  })
}

export function verifyUisekOtp(payload: OTPCodeRequest): Promise<UserMe> {
  return apiRequest<UserMe>('/sellers/uisek-otp/verify/', {
    method: 'POST',
    body: payload,
  })
}

export function createSellerApplication(
  payload: SellerApplicationCreateRequest,
): Promise<SellerApplication> {
  return apiRequest<SellerApplication>('/sellers/applications/', {
    method: 'POST',
    body: payload,
  })
}

export function getMySellerApplications(signal?: AbortSignal): Promise<SellerApplication[]> {
  return apiRequest<SellerApplication[]>('/sellers/applications/me/', {
    method: 'GET',
    signal,
  })
}

export function getMySellerProfile(signal?: AbortSignal): Promise<SellerOwnProfile> {
  return apiRequest<SellerOwnProfile>('/sellers/me/', {
    method: 'GET',
    signal,
  })
}

export function updateMySellerProfile(
  payload: PatchedSellerProfileUpdateRequest,
): Promise<SellerOwnProfile> {
  return apiRequest<SellerOwnProfile>('/sellers/me/', {
    method: 'PATCH',
    body: payload,
  })
}

export function getPublicSellerProfile(
  id: string,
  signal?: AbortSignal,
): Promise<SellerPublicProfile> {
  return apiRequest<SellerPublicProfile>(`/sellers/${encodeURIComponent(id)}/`, {
    method: 'GET',
    signal,
  })
}
