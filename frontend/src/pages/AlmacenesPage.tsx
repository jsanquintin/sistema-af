import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  actualizarAlmacen,
  crearAlmacen,
  eliminarAlmacen,
  getAlmacenes,
  getSucursales,
  type Almacen,
  type Sucursal,
} from '@/lib/api'

interface AlmacenesPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const FORM_VACIO = { sucursal_id: '', codigo: '', nombre: '' }

export function AlmacenesPage({ token, empresaId }: AlmacenesPageProps) {
  const [almacenes, setAlmacenes] = useState<Almacen[] | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getAlmacenes(token, empresaId)
      .then(setAlmacenes)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los almacenes'))
  }

  useEffect(cargar, [token, empresaId])
  useEffect(() => {
    getSucursales(token, empresaId).then(setSucursales).catch(() => setSucursales([]))
  }, [token, empresaId])

  function abrirNuevo() {
    setForm({ ...FORM_VACIO, sucursal_id: sucursales[0] ? String(sucursales[0].id) : '' })
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(almacen: Almacen) {
    setForm({ sucursal_id: String(almacen.sucursal_id), codigo: almacen.codigo, nombre: almacen.nombre })
    setEditandoId(almacen.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    const payload = { sucursal_id: Number(form.sucursal_id), codigo: form.codigo, nombre: form.nombre }
    try {
      if (editandoId) await actualizarAlmacen(token, editandoId, payload)
      else await crearAlmacen(token, payload)
      setMostrarForm(false)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar el almacén')
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(almacen: Almacen) {
    if (!confirm(`¿Desactivar el almacén ${almacen.nombre}?`)) return
    try {
      await eliminarAlmacen(token, almacen.id)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo desactivar el almacén')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Almacenes</h1>
          <p className="text-sm text-muted-foreground">{almacenes ? `${almacenes.length} activos` : 'Cargando…'}</p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNuevo} disabled={sucursales.length === 0}>
            + Nuevo almacén
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
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sucursal_id">Sucursal</Label>
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
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear almacén'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {almacenes && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Código</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Sucursal</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {almacenes.map((almacen) => (
                <tr key={almacen.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="font-tabular px-3 py-1.5">{almacen.codigo}</td>
                  <td className="px-3 py-1.5">{almacen.nombre}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">
                    {sucursales.find((s) => s.id === almacen.sucursal_id)?.nombre ?? '—'}
                  </td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(almacen)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(almacen)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Desactivar
                    </button>
                  </td>
                </tr>
              ))}
              {almacenes.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin almacenes registrados todavía.
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
