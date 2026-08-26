import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  actualizarEmpleado,
  crearEmpleado,
  eliminarEmpleado,
  getEmpleados,
  getSucursales,
  type Empleado,
  type Sucursal,
} from '@/lib/api'

interface EmpleadosPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const FORM_VACIO = {
  nombre_completo: '',
  tipo_empleado: 'fijo' as 'fijo' | 'jornalero',
  incluye_tss: true,
  sucursal_id: '',
  cedula: '',
  salario_base: '',
  tarifa_unidad: '',
  fecha_ingreso: '',
  fecha_salida: '',
}

export function EmpleadosPage({ token, empresaId }: EmpleadosPageProps) {
  const [empleados, setEmpleados] = useState<Empleado[] | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getEmpleados(token, empresaId)
      .then(setEmpleados)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los empleados'))
  }

  useEffect(cargar, [token, empresaId])
  useEffect(() => {
    getSucursales(token, empresaId).then(setSucursales).catch(() => setSucursales([]))
  }, [token, empresaId])

  function abrirNuevo() {
    setForm(FORM_VACIO)
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(empleado: Empleado) {
    setForm({
      nombre_completo: empleado.nombre_completo,
      tipo_empleado: empleado.tipo_empleado,
      incluye_tss: empleado.incluye_tss,
      sucursal_id: empleado.sucursal_id ? String(empleado.sucursal_id) : '',
      cedula: empleado.cedula ?? '',
      salario_base: empleado.salario_base != null ? String(empleado.salario_base) : '',
      tarifa_unidad: empleado.tarifa_unidad != null ? String(empleado.tarifa_unidad) : '',
      fecha_ingreso: empleado.fecha_ingreso ?? '',
      fecha_salida: empleado.fecha_salida ?? '',
    })
    setEditandoId(empleado.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    const payload = {
      empresa_id: empresaId,
      sucursal_id: form.sucursal_id ? Number(form.sucursal_id) : null,
      cedula: form.cedula || null,
      nombre_completo: form.nombre_completo,
      tipo_empleado: form.tipo_empleado,
      incluye_tss: form.incluye_tss,
      salario_base: form.salario_base ? Number(form.salario_base) : null,
      tarifa_unidad: form.tarifa_unidad ? Number(form.tarifa_unidad) : null,
      fecha_ingreso: form.fecha_ingreso || null,
      fecha_salida: form.fecha_salida || null,
    }
    try {
      if (editandoId) await actualizarEmpleado(token, editandoId, payload)
      else await crearEmpleado(token, payload)
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: editandoId ? 'Empleado actualizado' : 'Empleado creado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo guardar el empleado',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(empleado: Empleado) {
    if (!confirm(`¿Desactivar a ${empleado.nombre_completo}? No se borra el historial.`)) return
    try {
      await eliminarEmpleado(token, empleado.id)
      cargar()
      toast({ variant: 'success', title: 'Empleado desactivado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo desactivar el empleado',
        description: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Empleados</h1>
          <p className="text-sm text-muted-foreground">{empleados ? `${empleados.length} activos` : 'Cargando…'}</p>
        </div>
        {!mostrarForm && <Button onClick={abrirNuevo}>+ Nuevo empleado</Button>}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nombre_completo">Nombre completo</Label>
              <Input
                id="nombre_completo"
                required
                value={form.nombre_completo}
                onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cedula">Cédula</Label>
              <Input id="cedula" value={form.cedula} onChange={(e) => setForm({ ...form, cedula: e.target.value })} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="tipo_empleado">Tipo</Label>
              <select
                id="tipo_empleado"
                className={selectClassName}
                value={form.tipo_empleado}
                onChange={(e) => setForm({ ...form, tipo_empleado: e.target.value as 'fijo' | 'jornalero' })}
              >
                <option value="fijo">Fijo</option>
                <option value="jornalero">Jornalero</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sucursal_id">Sucursal</Label>
              <select
                id="sucursal_id"
                className={selectClassName}
                value={form.sucursal_id}
                onChange={(e) => setForm({ ...form, sucursal_id: e.target.value })}
              >
                <option value="">Sin asignar</option>
                {sucursales.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </div>
            {form.tipo_empleado === 'fijo' ? (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="salario_base">Salario base</Label>
                <Input
                  id="salario_base"
                  type="number"
                  step="0.01"
                  value={form.salario_base}
                  onChange={(e) => setForm({ ...form, salario_base: e.target.value })}
                />
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="tarifa_unidad">Tarifa por tarea/día</Label>
                <Input
                  id="tarifa_unidad"
                  type="number"
                  step="0.01"
                  value={form.tarifa_unidad}
                  onChange={(e) => setForm({ ...form, tarifa_unidad: e.target.value })}
                />
              </div>
            )}
            <div className="flex items-center gap-2 pt-6">
              <input
                id="incluye_tss"
                type="checkbox"
                checked={form.incluye_tss}
                onChange={(e) => setForm({ ...form, incluye_tss: e.target.checked })}
                className="size-4 cursor-pointer accent-primary"
              />
              <Label htmlFor="incluye_tss" className="cursor-pointer">
                Incluye TSS
              </Label>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha_ingreso">Fecha de ingreso</Label>
              <Input
                id="fecha_ingreso"
                type="date"
                value={form.fecha_ingreso}
                onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear empleado'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {empleados && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Tipo</th>
                <th className="px-3 py-2 font-medium">Sucursal</th>
                <th className="px-3 py-2 font-medium">TSS</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {empleados.map((empleado) => (
                <tr key={empleado.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-3 py-1.5">{empleado.nombre_completo}</td>
                  <td className="px-3 py-1.5 capitalize text-muted-foreground">{empleado.tipo_empleado}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">
                    {sucursales.find((s) => s.id === empleado.sucursal_id)?.nombre ?? '—'}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{empleado.incluye_tss ? 'Sí' : 'No'}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(empleado)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(empleado)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Desactivar
                    </button>
                  </td>
                </tr>
              ))}
              {empleados.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin empleados registrados todavía.
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
