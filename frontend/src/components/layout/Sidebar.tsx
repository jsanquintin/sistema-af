import { BookOpen, Boxes, ReceiptText, Users } from 'lucide-react'

export type Seccion = 'contabilidad' | 'nomina' | 'facturacion' | 'inventario'

interface SidebarProps {
  seccionActiva: Seccion
  onCambiarSeccion: (seccion: Seccion) => void
}

const secciones: { id: Seccion; label: string; icon: typeof BookOpen }[] = [
  { id: 'contabilidad', label: 'Contabilidad', icon: BookOpen },
  { id: 'nomina', label: 'Nómina', icon: Users },
  { id: 'facturacion', label: 'Facturación', icon: ReceiptText },
  { id: 'inventario', label: 'Inventario', icon: Boxes },
]

export function Sidebar({ seccionActiva, onCambiarSeccion }: SidebarProps) {
  return (
    <nav className="flex w-[200px] shrink-0 flex-col gap-1 border-r border-border p-4">
      <span className="mb-3 px-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        Agrocasa/Creixa
      </span>
      {secciones.map(({ id, label, icon: Icon }) => {
        const activa = id === seccionActiva
        return (
          <button
            key={id}
            type="button"
            onClick={() => onCambiarSeccion(id)}
            className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ${
              activa
                ? 'bg-primary/10 font-medium text-primary'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <Icon className="size-4" />
            {label}
          </button>
        )
      })}
    </nav>
  )
}
