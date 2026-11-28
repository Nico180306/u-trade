import { useState } from 'react'
import { Button, Modal } from '../../../shared/components'
import {
  useRequestBuyerEmailOtp,
  useVerifyBuyerEmailOtp,
  type UserMe,
} from '../api'
import { OtpVerificationCard } from './OtpVerificationCard'

export interface BuyerEmailVerificationModalProps {
  open: boolean
  onClose: () => void
  userEmail: string
  onVerified?: (user: UserMe) => void
}

interface ModalBodyProps {
  userEmail: string
  onClose: () => void
  onVerified?: (user: UserMe) => void
}

function BuyerEmailVerificationBody({ userEmail, onClose, onVerified }: ModalBodyProps) {
  const requestMutation = useRequestBuyerEmailOtp()
  const verifyMutation = useVerifyBuyerEmailOtp()
  const [completedUser, setCompletedUser] = useState<UserMe | null>(null)

  return (
    <div className="space-y-4">
      <OtpVerificationCard
        purpose="BUYER_EMAIL"
        targetEmail={userEmail}
        onRequestOtp={() => requestMutation.mutateAsync()}
        onVerifyOtp={(code) => verifyMutation.mutateAsync({ code })}
        isRequesting={requestMutation.isPending}
        isVerifying={verifyMutation.isPending}
        requestError={requestMutation.error}
        verifyError={verifyMutation.error}
        onClearErrors={() => {
          requestMutation.reset()
          verifyMutation.reset()
        }}
        onVerified={(updatedUser) => {
          setCompletedUser(updatedUser)
          onVerified?.(updatedUser)
        }}
      />

      {completedUser && (
        <Button fullWidth size="lg" onClick={onClose}>
          Continuar
        </Button>
      )}
    </div>
  )
}

export function BuyerEmailVerificationModal({
  open,
  onClose,
  userEmail,
  onVerified,
}: BuyerEmailVerificationModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Verifica tu correo electrónico"
      description="Confirmar tu correo solo toma unos segundos y te permite reservar productos en U-Trade."
    >
      {open && (
        <BuyerEmailVerificationBody
          userEmail={userEmail}
          onClose={onClose}
          onVerified={onVerified}
        />
      )}
    </Modal>
  )
}
