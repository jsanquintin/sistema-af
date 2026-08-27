import { Menu } from 'lucide-react'
import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'

import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { decodeJwtPayload, type Empresa, type Sucursal, type Usuario } from '@/lib/api'

import { Sidebar } from './Sidebar'

interface AppShellProps {
  token: string
  usuario: Usuario
  empresa: Empresa
  sucursal: Sucursal | null
  onLogout: () => void
  onCambiarEmpresa: () => void
}

export function AppShell({ token, usuario, empresa, sucursal, onLogout, onCambiarEmpresa }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const esSesionDeSoporte = Boolean(decodeJwtPayload(token)?.impersonated_by)

  return (
    <div className="flex h-svh flex-col">
      {esSesionDeSoporte && (
        <div className="flex items-center justify-center gap-3 bg-warning/15 px-4 py-1.5 text-xs text-warning">
          <span>
            Sesión de soporte — actuando dentro de {empresa.nombre_comercial ?? empresa.razon_social}
          </span>
          <Link to="/superadmin" className="cursor-pointer font-medium hover:underline">
            Volver al panel
          </Link>
        </div>
      )}
      <div className="flex min-h-0 flex-1">
        <Sidebar
          empresa={empresa}
          sucursal={sucursal}
          rol={usuario.rol}
          onCambiarEmpresa={onCambiarEmpresa}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3 sm:px-6">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon-sm"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
                aria-label="Abrir menú"
              >
                <Menu className="size-4" />
              </Button>
              <span className="h-4 w-0.5 rounded-full bg-primary" />
              <span className="font-mono text-sm font-medium tracking-tight">sistema-af</span>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              <span className="hidden text-sm text-muted-foreground sm:inline">
                {usuario.nombre_completo} · {usuario.rol}
              </span>
              <ThemeToggle />
              <Button variant="outline" size="sm" onClick={onLogout}>
                Cerrar sesión
              </Button>
            </div>
          </header>
          <main className="flex-1 overflow-auto px-4 py-4 sm:px-6 sm:py-5">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
