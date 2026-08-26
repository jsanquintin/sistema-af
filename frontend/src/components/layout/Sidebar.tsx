import { BookOpen, Boxes, ReceiptText, Users } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import type { Empresa, Sucursal } from '@/lib/api'

export type Seccion = 'contabilidad' | 'nomina' | 'facturacion' | 'inventario'

interface SidebarProps {
  empresa: Empresa
  sucursal: Sucursal | null
  onCambiarEmpresa: () => void
}

const secciones: { id: Seccion; label: string; icon: typeof BookOpen }[] = [
  { id: 'contabilidad', label: 'Contabilidad', icon: BookOpen },
  { id: 'nomina', label: 'Nómina', icon: Users },
  { id: 'facturacion', label: 'Facturación', icon: ReceiptText },
  { id: 'inventario', label: 'Inventario', icon: Boxes },
]

export function Sidebar({ empresa, sucursal, onCambiarEmpresa }: SidebarProps) {
  return (
    <nav className="flex w-[200px] shrink-0 flex-col gap-1 border-r border-border p-4">
      <div className="mb-3 px-2">
        <div className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-[2px] bg-primary" />
          <span className="text-section-label truncate font-medium text-muted-foreground">
            {empresa.nombre_comercial ?? empresa.razon_social}
          </span>
        </div>
        <div className="mt-0.5 flex items-center justify-between pl-3">
          <span className="truncate text-xs text-muted-foreground/70">{sucursal?.nombre ?? 'Todas las sucursales'}</span>
          <Link
            to="/seleccionar-empresa"
            onClick={onCambiarEmpresa}
            className="cursor-pointer text-xs text-primary hover:underline"
          >
            Cambiar
          </Link>
        </div>
      </div>
      {secciones.map(({ id, label, icon: Icon }) => (
        <NavLink
          key={id}
          to={`/${id}`}
          className={({ isActive }) =>
            `flex cursor-pointer items-center gap-2 rounded-lg border-l-2 px-2 py-1.5 text-left text-sm transition-colors ${
              isActive
                ? 'border-l-primary bg-primary/15 font-medium text-primary'
                : 'border-l-transparent text-muted-foreground hover:bg-muted hover:text-foreground'
            }`
          }
        >
          <Icon className="size-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
