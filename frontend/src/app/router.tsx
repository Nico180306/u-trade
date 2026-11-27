import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { BootstrapCheckPage } from '../features/auth/pages/BootstrapCheckPage'
import { ForgotPasswordPage } from '../features/auth/pages/ForgotPasswordPage'
import { HomePage } from '../features/auth/pages/HomePage'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { ProfilePage } from '../features/auth/pages/ProfilePage'
import { RegisterPage } from '../features/auth/pages/RegisterPage'
import { ResetPasswordPage } from '../features/auth/pages/ResetPasswordPage'
import { AppLayout } from './AppLayout'

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
      { path: '/bootstrap-check', element: <BootstrapCheckPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
