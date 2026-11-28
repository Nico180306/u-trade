import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { BootstrapCheckPage } from '../features/auth/pages/BootstrapCheckPage'
import { ForgotPasswordPage } from '../features/auth/pages/ForgotPasswordPage'
import { HomePage } from '../features/auth/pages/HomePage'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { ProfilePage } from '../features/auth/pages/ProfilePage'
import { RegisterPage } from '../features/auth/pages/RegisterPage'
import { ResetPasswordPage } from '../features/auth/pages/ResetPasswordPage'
import { BecomeSellerPage } from '../features/seller-onboarding/pages/BecomeSellerPage'
import { PublicSellerProfilePage } from '../features/seller-onboarding/pages/PublicSellerProfilePage'
import { SellerProfilePage } from '../features/seller-onboarding/pages/SellerProfilePage'
import { AppLayout } from './AppLayout'
import { RequireAuth, RequireSeller } from './RouteGuards'

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
      { path: '/reset-password', element: <ResetPasswordPage /> },
      { path: '/profile', element: <ProfilePage /> },
      { path: '/sellers/:id', element: <PublicSellerProfilePage /> },
      { path: '/bootstrap-check', element: <BootstrapCheckPage /> },
      {
        element: <RequireAuth />,
        children: [{ path: '/become-seller', element: <BecomeSellerPage /> }],
      },
      {
        element: <RequireSeller />,
        children: [{ path: '/seller/profile', element: <SellerProfilePage /> }],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
