import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  crearInventarioMovimiento,
  getAlmacenes,
  getInventarioMovimientos,
  getLotesCosecha,
  type Almacen,
  type InventarioMovimiento,
  type LoteCosecha,
} from '@/lib/api'

interface InventarioMovimientosPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const TIPO_LABEL: Record<InventarioMovimiento['tipo_movimiento'], string> = {
  entrada: 'Entrada',
  salida: 'Salida',
  ajuste: 'Ajuste',
  merma: 'Merma',
  traslado: 'Traslado',
}

const FORM_VACIO = {
  lote_id: '',
  tipo_movimiento: 'entrada' as InventarioMovimiento['tipo_movimiento'],
  almacen_origen_id: '',
  almacen_destino_id: '',
  cantidad: '',
  referencia_doc: '',
  fecha: '',
}

export function InventarioMovimientosPage({ token, empresaId }: InventarioMovimientosPageProps) {
  const [movimientos, setMovimientos] = useState<InventarioMovimiento[] | null>(null)
  const [lotes, setLotes] = useState<LoteCosecha[]>([])
  const [almacenes, setAlmacenes] = useState<Almacen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getInventarioMovimientos(token, empresaId)
      .then(setMovimientos)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los movimientos'))
  }

  useEffect(cargar, [token, empresaId])
  useEffect(() => {
    getLotesCosecha(token, empresaId).then(setLotes).catch(() => setLotes([]))
    getAlmacenes(token, empresaId).then(setAlmacenes).catch(() => setAlmacenes([]))
  }, [token, empresaId])

  const necesitaOrigen = form.tipo_movimiento === 'salida' || form.tipo_movimiento === 'traslado'
  const necesitaDestino = form.tipo_movimiento === 'entrada' || form.tipo_movimiento === 'traslado'

  function abrirNuevo() {
    setForm({ ...FORM_VACIO, lote_id: lotes[0] ? String(lotes[0].id) : '' })
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    try {
      await crearInventarioMovimiento(token, {
        lote_id: Number(form.lote_id),
        tipo_movimiento: form.tipo_movimiento,
        almacen_origen_id: necesitaOrigen && form.almacen_origen_id ? Number(form.almacen_origen_id) : null,
        almacen_destino_id: necesitaDestino && form.almacen_destino_id ? Number(form.almacen_destino_id) : null,
        cantidad: Number(form.cantidad),
        referencia_doc: form.referencia_doc || null,
        fecha: form.fecha,
      })
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: 'Movimiento registrado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo registrar el movimiento',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Movimientos de Inventario</h1>
          <p className="text-sm text-muted-foreground">
            Bitácora — no se edita ni se borra, un error se corrige con un movimiento contrario.
          </p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNuevo} disabled={lotes.length === 0}>
            + Nuevo movimiento
          </Button>
        )}
      </div>

      {lotes.length === 0 && (
        <p className="text-sm text-muted-foreground">Necesitas al menos un lote de cosecha para registrar movimientos.</p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="lote_id">Lote</Label>
              <select
                id="lote_id"
                required
                className={selectClassName}
                value={form.lote_id}
                onChange={(e) => setForm({ ...form, lote_id: e.target.value })}
              >
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.producto} — {l.fecha_cosecha}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="tipo_movimiento">Tipo</Label>
              <select
                id="tipo_movimiento"
                className={selectClassName}
                value={form.tipo_movimiento}
                onChange={(e) =>
                  setForm({ ...form, tipo_movimiento: e.target.value as InventarioMovimiento['tipo_movimiento'] })
                }
              >
                {Object.entries(TIPO_LABEL).map(([valor, etiqueta]) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cantidad">Cantidad</Label>
              <Input
                id="cantidad"
                type="number"
                step="0.01"
                required
                value={form.cantidad}
                onChange={(e) => setForm({ ...form, cantidad: e.target.value })}
              />
            </div>
            {necesitaOrigen && (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="almacen_origen_id">Almacén origen</Label>
                <select
                  id="almacen_origen_id"
                  required
                  className={selectClassName}
                  value={form.almacen_origen_id}
                  onChange={(e) => setForm({ ...form, almacen_origen_id: e.target.value })}
                >
                  <option value="">Selecciona…</option>
                  {almacenes.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {necesitaDestino && (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="almacen_destino_id">Almacén destino</Label>
                <select
                  id="almacen_destino_id"
                  required
                  className={selectClassName}
                  value={form.almacen_destino_id}
                  onChange={(e) => setForm({ ...form, almacen_destino_id: e.target.value })}
                >
                  <option value="">Selecciona…</option>
                  {almacenes.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha">Fecha</Label>
              <Input
                id="fecha"
                type="date"
                required
                value={form.fecha}
                onChange={(e) => setForm({ ...form, fecha: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="referencia_doc">Referencia (factura/conduce)</Label>
              <Input
                id="referencia_doc"
                value={form.referencia_doc}
                onChange={(e) => setForm({ ...form, referencia_doc: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              Registrar movimiento
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {movimientos && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Fecha</th>
                <th className="px-3 py-2 font-medium">Tipo</th>
                <th className="px-3 py-2 font-medium">Lote</th>
                <th className="px-3 py-2 font-medium">Cantidad</th>
                <th className="px-3 py-2 font-medium">Referencia</th>
              </tr>
            </thead>
            <tbody>
              {movimientos.map((mov) => {
                const lote = lotes.find((l) => l.id === mov.lote_id)
                return (
                  <tr key={mov.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="font-tabular px-3 py-1.5 text-muted-foreground">{mov.fecha}</td>
                    <td className="px-3 py-1.5">{TIPO_LABEL[mov.tipo_movimiento]}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">
                      {lote ? `${lote.producto} — ${lote.fecha_cosecha}` : `Lote #${mov.lote_id}`}
                    </td>
                    <td className="font-tabular px-3 py-1.5">{mov.cantidad}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{mov.referencia_doc ?? '—'}</td>
                  </tr>
                )
              })}
              {movimientos.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin movimientos registrados todavía.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
