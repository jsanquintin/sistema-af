import { BookOpen, Boxes, ReceiptText, Settings, Users } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import type { Empresa, Sucursal } from '@/lib/api'

interface SidebarProps {
  empresa: Empresa
  sucursal: Sucursal | null
  onCambiarEmpresa: () => void
  open: boolean
  onClose: () => void
}

interface SubItem {
  path: string
  label: string
}

interface Modulo {
  id: string
  label: string
  icon: typeof BookOpen
  items: SubItem[]
}

const modulos: Modulo[] = [
  {
    id: 'contabilidad',
    label: 'Contabilidad',
    icon: BookOpen,
    items: [
      { path: 'plan-cuentas', label: 'Plan de Cuentas' },
      { path: 'asientos', label: 'Asientos' },
      { path: 'reportes', label: 'Reportes' },
    ],
  },
  {
    id: 'nomina',
    label: 'Nómina',
    icon: Users,
    items: [
      { path: 'empleados', label: 'Empleados' },
      { path: 'corridas', label: 'Nóminas' },
    ],
  },
  {
    id: 'facturacion',
    label: 'Facturación',
    icon: ReceiptText,
    items: [
      { path: 'clientes', label: 'Clientes' },
      { path: 'facturas', label: 'Facturas' },
    ],
  },
  {
    id: 'inventario',
    label: 'Inventario',
    icon: Boxes,
    items: [
      { path: 'almacenes', label: 'Almacenes' },
      { path: 'movimientos', label: 'Movimientos' },
      { path: 'lotes', label: 'Lotes de Cosecha' },
    ],
  },
  {
    id: 'configuracion',
    label: 'Configuración',
    icon: Settings,
    items: [{ path: 'empresas', label: 'Empresas y Sucursales' }],
  },
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
        className={`fixed inset-y-0 left-0 z-50 flex w-[240px] shrink-0 flex-col gap-4 overflow-y-auto border-r border-border bg-card p-4 transition-transform duration-200 ease-out lg:static lg:z-auto lg:w-[220px] lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="px-2">
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

        {modulos.map(({ id, label, icon: Icon, items }) => (
          <div key={id}>
            <div className="mb-1 flex items-center gap-1.5 px-2 text-xs font-medium text-muted-foreground">
              <Icon className="size-3.5" />
              {label}
            </div>
            <div className="flex flex-col gap-0.5">
              {items.map((item) => (
                <NavLink
                  key={item.path}
                  to={`/${id}/${item.path}`}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `cursor-pointer rounded-lg border-l-2 py-1.5 pr-2 pl-4 text-left text-sm transition-colors ${
                      isActive
                        ? 'border-l-primary bg-primary/15 font-medium text-primary'
                        : 'border-l-transparent text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </>
  )
}
