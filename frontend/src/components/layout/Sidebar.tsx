import { BookOpen, Boxes, ReceiptText, Users } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import type { Empresa, Sucursal } from '@/lib/api'

export type Seccion = 'contabilidad' | 'nomina' | 'facturacion' | 'inventario'

interface SidebarProps {
  empresa: Empresa
  sucursal: Sucursal | null
  onCambiarEmpresa: () => void
  open: boolean
  onClose: () => void
}

const secciones: { id: Seccion; label: string; icon: typeof BookOpen }[] = [
  { id: 'contabilidad', label: 'Contabilidad', icon: BookOpen },
  { id: 'nomina', label: 'Nómina', icon: Users },
  { id: 'facturacion', label: 'Facturación', icon: ReceiptText },
  { id: 'inventario', label: 'Inventario', icon: Boxes },
]

export function Sidebar({ empresa, sucursal, onCambiarEmpresa, open, onClose }: SidebarProps) {
  return (
    <>
      {/* Scrim: solo existe (y solo importa) por debajo de lg, donde el
          sidebar es un overlay en vez de estar siempre visible. */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <nav
        className={`fixed inset-y-0 left-0 z-50 flex w-[240px] shrink-0 flex-col gap-1 border-r border-border bg-card p-4 transition-transform duration-200 ease-out lg:static lg:z-auto lg:w-[200px] lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="mb-3 px-2">
          <div className="flex items-center gap-1.5">
            <span className="size-1.5 rounded-[2px] bg-primary" />
            <span className="text-section-label truncate font-medium text-muted-foreground">
              {empresa.nombre_comercial ?? empresa.razon_social}
            </span>
          </div>
          <div className="mt-0.5 flex items-center justify-between pl-3">
            <span className="truncate text-xs text-muted-foreground/70">
              {sucursal?.nombre ?? 'Todas las sucursales'}
            </span>
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
            onClick={onClose}
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
    </>
  )
}
