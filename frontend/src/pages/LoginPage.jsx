import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

function LoginPage({ onLogin }) {
    const handleSuccess = async (credentialResponse) => {
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/google`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                credential: credentialResponse.credential
              })
            }
          )
      
          if (!response.ok) throw new Error('Auth failed')
      
          const data = await response.json()
          localStorage.setItem('token', data.access_token)
          localStorage.setItem('user', JSON.stringify(data.user))
          onLogin(data.user)
        } catch (err) {
          console.error('Login failed:', err)
        }
      }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center max-w-md w-full">
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">Study Tool</h1>
          <p className="text-gray-500 mb-8">
            Upload your notes, generate flashcards, and study smarter with AI.
          </p>
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => console.error('Login failed')}
            useOneTap
          />
        </div>
      </div>
    </GoogleOAuthProvider>
  )
}

export default LoginPage