import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  actualizarLoteCosecha,
  crearLoteCosecha,
  eliminarLoteCosecha,
  getAlmacenes,
  getLotesCosecha,
  getSucursales,
  type Almacen,
  type LoteCosecha,
  type Sucursal,
} from '@/lib/api'

interface LotesCosechaPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const ESTADO_LABEL: Record<LoteCosecha['estado'], string> = {
  disponible: 'Disponible',
  en_proceso: 'En proceso',
  vendido: 'Vendido',
  exportado: 'Exportado',
}

const FORM_VACIO = {
  sucursal_id: '',
  almacen_id: '',
  producto: 'cafe',
  fecha_cosecha: '',
  cantidad: '',
  unidad: 'qq',
  calidad_grado: '',
  humedad_pct: '',
}

export function LotesCosechaPage({ token, empresaId }: LotesCosechaPageProps) {
  const [lotes, setLotes] = useState<LoteCosecha[] | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [almacenes, setAlmacenes] = useState<Almacen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getLotesCosecha(token, empresaId)
      .then(setLotes)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los lotes'))
  }

  useEffect(cargar, [token, empresaId])
  useEffect(() => {
    getSucursales(token, empresaId).then(setSucursales).catch(() => setSucursales([]))
    getAlmacenes(token, empresaId).then(setAlmacenes).catch(() => setAlmacenes([]))
  }, [token, empresaId])

  const almacenesDeSucursal = useMemo(
    () => almacenes.filter((a) => String(a.sucursal_id) === form.sucursal_id),
    [almacenes, form.sucursal_id]
  )

  function abrirNuevo() {
    setForm({ ...FORM_VACIO, sucursal_id: sucursales[0] ? String(sucursales[0].id) : '' })
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(lote: LoteCosecha) {
    setForm({
      sucursal_id: String(lote.sucursal_id),
      almacen_id: lote.almacen_id ? String(lote.almacen_id) : '',
      producto: lote.producto,
      fecha_cosecha: lote.fecha_cosecha,
      cantidad: String(lote.cantidad),
      unidad: lote.unidad,
      calidad_grado: lote.calidad_grado ?? '',
      humedad_pct: lote.humedad_pct != null ? String(lote.humedad_pct) : '',
    })
    setEditandoId(lote.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    const payload = {
      sucursal_id: Number(form.sucursal_id),
      almacen_id: form.almacen_id ? Number(form.almacen_id) : null,
      producto: form.producto,
      fecha_cosecha: form.fecha_cosecha,
      cantidad: Number(form.cantidad),
      unidad: form.unidad,
      calidad_grado: form.calidad_grado || null,
      humedad_pct: form.humedad_pct ? Number(form.humedad_pct) : null,
    }
    try {
      if (editandoId) await actualizarLoteCosecha(token, editandoId, payload)
      else await crearLoteCosecha(token, payload)
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: editandoId ? 'Lote actualizado' : 'Lote creado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo guardar el lote',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(lote: LoteCosecha) {
    if (!confirm(`¿Eliminar el lote de ${lote.producto} del ${lote.fecha_cosecha}?`)) return
    try {
      await eliminarLoteCosecha(token, lote.id)
      cargar()
      toast({ variant: 'success', title: 'Lote eliminado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo eliminar el lote',
        description: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Lotes de Cosecha</h1>
          <p className="text-sm text-muted-foreground">{lotes ? `${lotes.length} registrados` : 'Cargando…'}</p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNuevo} disabled={sucursales.length === 0}>
            + Nuevo lote
          </Button>
        )}
      </div>

      {sucursales.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No hay sucursales registradas para esta empresa — crea una primero en Configuración.
        </p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sucursal_id">Finca / sucursal</Label>
              <select
                id="sucursal_id"
                required
                className={selectClassName}
                value={form.sucursal_id}
                onChange={(e) => setForm({ ...form, sucursal_id: e.target.value, almacen_id: '' })}
              >
                {sucursales.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="almacen_id">Almacén actual</Label>
              <select
                id="almacen_id"
                className={selectClassName}
                value={form.almacen_id}
                onChange={(e) => setForm({ ...form, almacen_id: e.target.value })}
              >
                <option value="">Sin asignar</option>
                {almacenesDeSucursal.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="producto">Producto</Label>
              <select
                id="producto"
                className={selectClassName}
                value={form.producto}
                onChange={(e) => setForm({ ...form, producto: e.target.value })}
              >
                <option value="cafe">Café</option>
                <option value="cacao">Cacao</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha_cosecha">Fecha de cosecha</Label>
              <Input
                id="fecha_cosecha"
                type="date"
                required
                value={form.fecha_cosecha}
                onChange={(e) => setForm({ ...form, fecha_cosecha: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cantidad">Cantidad (qq)</Label>
              <Input
                id="cantidad"
                type="number"
                step="0.01"
                required
                value={form.cantidad}
                onChange={(e) => setForm({ ...form, cantidad: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="humedad_pct">Humedad %</Label>
              <Input
                id="humedad_pct"
                type="number"
                step="0.01"
                value={form.humedad_pct}
                onChange={(e) => setForm({ ...form, humedad_pct: e.target.value })}
              />
            </div>
            <div className="col-span-2 flex flex-col gap-1.5">
              <Label htmlFor="calidad_grado">Grado de calidad</Label>
              <Input
                id="calidad_grado"
                value={form.calidad_grado}
                onChange={(e) => setForm({ ...form, calidad_grado: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear lote'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {lotes && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Producto</th>
                <th className="px-3 py-2 font-medium">Cosecha</th>
                <th className="px-3 py-2 font-medium">Cantidad</th>
                <th className="px-3 py-2 font-medium">Finca</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {lotes.map((lote) => (
                <tr key={lote.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-3 py-1.5 capitalize">{lote.producto}</td>
                  <td className="font-tabular px-3 py-1.5 text-muted-foreground">{lote.fecha_cosecha}</td>
                  <td className="font-tabular px-3 py-1.5">
                    {lote.cantidad} {lote.unidad}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">
                    {sucursales.find((s) => s.id === lote.sucursal_id)?.nombre ?? '—'}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{ESTADO_LABEL[lote.estado]}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(lote)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(lote)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {lotes.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin lotes registrados todavía.
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
