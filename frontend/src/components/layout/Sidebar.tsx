import { BookOpen, Boxes, ReceiptText, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

export type Seccion = 'contabilidad' | 'nomina' | 'facturacion' | 'inventario'

const secciones: { id: Seccion; label: string; icon: typeof BookOpen }[] = [
  { id: 'contabilidad', label: 'Contabilidad', icon: BookOpen },
  { id: 'nomina', label: 'Nómina', icon: Users },
  { id: 'facturacion', label: 'Facturación', icon: ReceiptText },
  { id: 'inventario', label: 'Inventario', icon: Boxes },
]

export function Sidebar() {
  return (
    <nav className="flex w-[200px] shrink-0 flex-col gap-1 border-r border-border p-4">
      <div className="mb-3 flex items-center gap-1.5 px-2">
        <span className="size-1.5 rounded-[2px] bg-primary" />
        <span className="text-section-label font-medium text-muted-foreground">Agrocasa/Creixa</span>
      </div>
      {secciones.map(({ id, label, icon: Icon }) => (
        <NavLink
          key={id}
          to={`/${id}`}
          className={({ isActive }) =>
            `flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ${
              isActive
                ? 'bg-primary/10 font-medium text-primary'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
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
