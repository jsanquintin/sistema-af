import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  actualizarObra,
  crearObra,
  eliminarObra,
  getClientes,
  getObras,
  getSucursales,
  type Cliente,
  type Obra,
  type Sucursal,
} from '@/lib/api'

interface ObrasPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const ESTADO_LABEL: Record<Obra['estado'], string> = {
  en_proceso: 'En proceso',
  cerrada: 'Cerrada',
}

const FORM_VACIO = {
  sucursal_id: '',
  cliente_id: '',
  codigo: '',
  nombre: '',
  monto_contrato: '',
  moneda: 'DOP',
  fecha_inicio: '',
  fecha_fin_estimada: '',
}

export function ObrasPage({ token, empresaId }: ObrasPageProps) {
  const [obras, setObras] = useState<Obra[] | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getObras(token, empresaId)
      .then(setObras)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las obras'))
  }

  useEffect(() => {
    setObras(null)
    cargar()
  }, [token, empresaId])
  useEffect(() => {
    getSucursales(token, empresaId).then((todas) => setSucursales(todas.filter((s) => s.tipo === 'proyecto'))).catch(() => setSucursales([]))
    getClientes(token).then((todos) => setClientes(todos.filter((c) => c.empresa_id === empresaId))).catch(() => setClientes([]))
  }, [token, empresaId])

  function abrirNuevo() {
    setForm({ ...FORM_VACIO, sucursal_id: sucursales[0] ? String(sucursales[0].id) : '' })
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(obra: Obra) {
    setForm({
      sucursal_id: String(obra.sucursal_id),
      cliente_id: String(obra.cliente_id),
      codigo: obra.codigo,
      nombre: obra.nombre,
      monto_contrato: String(obra.monto_contrato),
      moneda: obra.moneda,
      fecha_inicio: obra.fecha_inicio,
      fecha_fin_estimada: obra.fecha_fin_estimada ?? '',
    })
    setEditandoId(obra.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    const payload = {
      empresa_id: empresaId,
      sucursal_id: Number(form.sucursal_id),
      cliente_id: Number(form.cliente_id),
      codigo: form.codigo,
      nombre: form.nombre,
      monto_contrato: Number(form.monto_contrato),
      moneda: form.moneda,
      fecha_inicio: form.fecha_inicio,
      fecha_fin_estimada: form.fecha_fin_estimada || null,
    }
    try {
      if (editandoId) await actualizarObra(token, editandoId, payload)
      else await crearObra(token, payload)
      setMostrarForm(false)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar la obra')
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(obra: Obra) {
    if (!confirm(`¿Eliminar la obra ${obra.nombre}?`)) return
    try {
      await eliminarObra(token, obra.id)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo eliminar la obra')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Obras</h1>
          <p className="text-sm text-muted-foreground">
            {obras ? `${obras.length} registradas` : 'Cargando…'} — proyectos de construcción, el objeto costeable
            que se factura por avances.
          </p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNuevo} disabled={sucursales.length === 0 || clientes.length === 0}>
            + Nueva obra
          </Button>
        )}
      </div>

      {sucursales.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Necesitas una sucursal de tipo "proyecto" para esta empresa — créala primero en Configuración.
        </p>
      )}
      {clientes.length === 0 && (
        <p className="text-sm text-muted-foreground">Necesitas al menos un cliente registrado.</p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sucursal_id">Sucursal (proyecto)</Label>
              <select
                id="sucursal_id"
                required
                className={selectClassName}
                value={form.sucursal_id}
                onChange={(e) => setForm({ ...form, sucursal_id: e.target.value })}
              >
                {sucursales.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cliente_id">Cliente</Label>
              <select
                id="cliente_id"
                required
                className={selectClassName}
                value={form.cliente_id}
                onChange={(e) => setForm({ ...form, cliente_id: e.target.value })}
              >
                <option value="">Selecciona…</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="codigo">Código</Label>
              <Input
                id="codigo"
                required
                value={form.codigo}
                onChange={(e) => setForm({ ...form, codigo: e.target.value })}
              />
            </div>
            <div className="col-span-2 flex flex-col gap-1.5">
              <Label htmlFor="nombre">Nombre</Label>
              <Input
                id="nombre"
                required
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="monto_contrato">Monto de contrato</Label>
              <Input
                id="monto_contrato"
                type="number"
                step="0.01"
                required
                value={form.monto_contrato}
                onChange={(e) => setForm({ ...form, monto_contrato: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha_inicio">Fecha de inicio</Label>
              <Input
                id="fecha_inicio"
                type="date"
                required
                value={form.fecha_inicio}
                onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha_fin_estimada">Fin estimado (opcional)</Label>
              <Input
                id="fecha_fin_estimada"
                type="date"
                value={form.fecha_fin_estimada}
                onChange={(e) => setForm({ ...form, fecha_fin_estimada: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear obra'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {obras && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Código</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Cliente</th>
                <th className="px-3 py-2 font-medium text-right">Contrato</th>
                <th className="px-3 py-2 font-medium text-right">Costo acum.</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {obras.map((obra) => (
                <tr key={obra.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="font-tabular px-3 py-1.5">{obra.codigo}</td>
                  <td className="px-3 py-1.5">{obra.nombre}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">
                    {clientes.find((c) => c.id === obra.cliente_id)?.nombre ?? '—'}
                  </td>
                  <td className="font-tabular px-3 py-1.5 text-right">
                    {obra.moneda} {obra.monto_contrato.toFixed(2)}
                  </td>
                  <td className="font-tabular px-3 py-1.5 text-right text-muted-foreground">
                    {obra.costo_acumulado.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{ESTADO_LABEL[obra.estado]}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(obra)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(obra)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {obras.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin obras registradas todavía.
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
