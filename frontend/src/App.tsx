import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { getMe, type Usuario } from '@/lib/api'
import { LoginPage } from '@/pages/LoginPage'

const TOKEN_STORAGE_KEY = 'sistema-af.token'

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (!token) {
      setUsuario(null)
      return
    }
    setChecking(true)
    getMe(token)
      .then(setUsuario)
      .catch(() => {
        // Token invalido o expirado: fail-closed, se descarta y se vuelve al login.
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken(null)
        setUsuario(null)
      })
      .finally(() => setChecking(false))
  }, [token])

  function handleLoginSuccess(newToken: string) {
    localStorage.setItem(TOKEN_STORAGE_KEY, newToken)
    setToken(newToken)
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUsuario(null)
  }

  if (!token) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />
  }

  if (checking || !usuario) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-muted-foreground">Verificando sesión…</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">sistema-af</h1>
      <p className="text-muted-foreground">
        Sesión iniciada como {usuario.nombre_completo} ({usuario.rol})
      </p>
      <Button variant="outline" onClick={handleLogout}>
        Cerrar sesión
      </Button>
    </div>
  )
}

export default App
