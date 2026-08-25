import { useState, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import type { Usuario } from '@/lib/api'

import { Sidebar, type Seccion } from './Sidebar'

interface AppShellProps {
  usuario: Usuario
  onLogout: () => void
  children: (seccion: Seccion) => ReactNode
}

export function AppShell({ usuario, onLogout, children }: AppShellProps) {
  const [seccion, setSeccion] = useState<Seccion>('contabilidad')

  return (
    <div className="flex h-svh">
      <Sidebar seccionActiva={seccion} onCambiarSeccion={setSeccion} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-border px-6 py-3">
          <span className="text-sm font-semibold">sistema-af</span>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">
              {usuario.nombre_completo} · {usuario.rol}
            </span>
            <Button variant="outline" size="sm" onClick={onLogout}>
              Cerrar sesión
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-auto px-6 py-5">{children(seccion)}</main>
      </div>
    </div>
  )
}
