import { useEffect, useState } from 'react'

import { AppShell } from '@/components/layout/AppShell'
import type { Seccion } from '@/components/layout/Sidebar'
import { getMe, type Usuario } from '@/lib/api'
import { LoginPage } from '@/pages/LoginPage'
import { SeccionPlaceholder } from '@/pages/SeccionPlaceholder'

const TOKEN_STORAGE_KEY = 'sistema-af.token'

const PLACEHOLDERS: Record<Seccion, { titulo: string; descripcion: string }> = {
  contabilidad: {
    titulo: 'Contabilidad',
    descripcion:
      'El motor de asientos está diseñado pero bloqueado hasta cerrar las preguntas pendientes con el contador (ver docs/designs/nucleo-contabilidad-nomina.md).',
  },
  nomina: {
    titulo: 'Nómina',
    descripcion:
      'Bloqueado por el mismo gate que contabilidad: nómina compartida/separada y las tablas de ISR/TSS aún no están confirmadas.',
  },
  facturacion: {
    titulo: 'Facturación',
    descripcion:
      'Diseño nuevo — Soluflex nunca tuvo esto en uso real. Pendiente confirmar si e-CF es obligación legal activa para Agrocasa.',
  },
  inventario: {
    titulo: 'Inventario',
    descripcion: 'Diseño nuevo por finca/lote de cosecha. Sin datos históricos que migrar.',
  },
}

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
    <AppShell usuario={usuario} onLogout={handleLogout}>
      {(seccion) => {
        const { titulo, descripcion } = PLACEHOLDERS[seccion]
        return <SeccionPlaceholder titulo={titulo} descripcion={descripcion} />
      }}
    </AppShell>
  )
}

export default App
