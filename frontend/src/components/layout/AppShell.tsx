import { Outlet } from 'react-router-dom'

import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import type { Usuario } from '@/lib/api'

import { Sidebar } from './Sidebar'

interface AppShellProps {
  usuario: Usuario
  onLogout: () => void
}

export function AppShell({ usuario, onLogout }: AppShellProps) {
  return (
    <div className="flex h-svh">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-border px-6 py-3">
          <div className="flex items-center gap-2">
            <span className="h-4 w-0.5 rounded-full bg-primary" />
            <span className="font-mono text-sm font-medium tracking-tight">sistema-af</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">
              {usuario.nombre_completo} · {usuario.rol}
            </span>
            <ThemeToggle />
            <Button variant="outline" size="sm" onClick={onLogout}>
              Cerrar sesión
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-auto px-6 py-5">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
