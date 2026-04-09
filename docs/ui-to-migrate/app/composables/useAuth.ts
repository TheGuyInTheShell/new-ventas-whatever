export const useAuth = () => {
  const user = useState<any | null>('auth-user', () => null)
  const isLoggedIn = computed(() => !!user.value)
  const router = useRouter()
  const toast = useToast()

  // Initialize user from cookie if available (server-side or client-side init)
  // Nuxt's useCookie is reactive.
  const accessToken = useCookie('access_token')

  // Simple hydration: if we have a token but no user state, we might want to fetch user profile.
  // For now, let's assume if we have a token, we are "logged in" effectively,
  // but to have the user object we might need an endpoint like /auth/me or similar.
  // The backend doesn't seem to have a dedicated /me endpoint in the controller I saw,
  // but we can decode the token or just rely on the login response.
  // For persistence, we might want to store user details in a cookie or fetch on load.
  // Let's rely on a 'user_data' cookie for simplicity if the backend allows, or just fetch if needed.
  // Looking at the sign-in response, it sets cookies.

  // NOTE: In a real app we'd fetch /auth/me or decode the JWT.
  // For this implementation I will implement a decode helper or just store the basic user info.

  interface SignInResponse {
    access_token?: string
    refresh_token?: string
    token_type?: string
    temp_token?: string
  }

  const signIn = async (username: string, password: string) => {
    try {
      const response = await $fetch<SignInResponse>('/api/auth/sign-in', {
        method: 'POST',
        body: { username, password }
      })

      // Check if it's the 2FA partial response
      if (response && response.temp_token) {
        return {
          status: '2fa_required',
          temp_token: response.temp_token
        }
      }

      // If full success (assuming proxied response or direct)
      // The backend sets cookies.
      // We can also set the user state here if the response body contains user info.
      // The backend response for full login:
      // { access_token, refresh_token, token_type }
      // It DOES NOT return user object in the body directly based on the code I read (it returns tokens).
      // However, the tokens are in the body.
      // We might need to decode the token to get user info on the client side.

      // Let's simplisticly assume success for now and maybe fetch user later.
      // Or we can decode the token.
      if (response.access_token) {
        // We can decode to get user info if needed, or just redirect.
        // Let's set a dummy user state or try to decode if we have a library,
        // but for now let's just update the state to true.
        // Ideally we populate `user`.
        user.value = { username } // minimal info
        return { status: 'success' }
      }
    } catch (error: any) {
      // Handle 401 etc
      throw error
    }
  }

  const verifyOtp = async (otpCode: string, tempToken: string) => {
    try {
      const response = await $fetch('/api/auth/verify-otp', {
        method: 'POST',
        body: { otp_code: otpCode, temp_token: tempToken }
      })

      if (response.access_token) {
        user.value = { authenticated: true } // minimal
        return { status: 'success' }
      }
    } catch (error: any) {
      throw error
    }
  }

  const signOut = async () => {
    // Clear cookies
    const accessCookie = useCookie('access_token')
    const refreshCookie = useCookie('refresh_token')
    accessCookie.value = null
    refreshCookie.value = null
    user.value = null

    // Optional: Call backend to invalidate if needed (though JWTs are stateless usually)
    // await $fetch('/api/auth/sign-out', { method: 'POST' })

    router.push('/login')
    toast.add({ title: 'Logged out successfully' })
  }

  return {
    user,
    isLoggedIn,
    signIn,
    verifyOtp,
    signOut
  }
}
