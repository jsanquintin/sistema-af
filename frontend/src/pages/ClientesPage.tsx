import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  actualizarCliente,
  crearCliente,
  eliminarCliente,
  getClientes,
  type Cliente,
} from '@/lib/api'

interface ClientesPageProps {
  token: string
  empresaId: number
}

const FORM_VACIO = { nombre: '', rnc_cedula: '', pais: 'República Dominicana', es_exterior: false }

export function ClientesPage({ token, empresaId }: ClientesPageProps) {
  const [clientes, setClientes] = useState<Cliente[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getClientes(token, empresaId)
      .then(setClientes)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los clientes'))
  }

  useEffect(cargar, [token, empresaId])

  function abrirNuevo() {
    setForm(FORM_VACIO)
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(cliente: Cliente) {
    setForm({
      nombre: cliente.nombre,
      rnc_cedula: cliente.rnc_cedula ?? '',
      pais: cliente.pais,
      es_exterior: cliente.es_exterior,
    })
    setEditandoId(cliente.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    const payload = {
      empresa_id: empresaId,
      rnc_cedula: form.rnc_cedula || null,
      nombre: form.nombre,
      pais: form.pais,
      es_exterior: form.es_exterior,
    }
    try {
      if (editandoId) await actualizarCliente(token, editandoId, payload)
      else await crearCliente(token, payload)
      setMostrarForm(false)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar el cliente')
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(cliente: Cliente) {
    if (!confirm(`¿Eliminar a ${cliente.nombre}? Esta acción no se puede deshacer.`)) return
    try {
      await eliminarCliente(token, cliente.id)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo eliminar el cliente')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Clientes</h1>
          <p className="text-sm text-muted-foreground">{clientes ? `${clientes.length} registrados` : 'Cargando…'}</p>
        </div>
        {!mostrarForm && <Button onClick={abrirNuevo}>+ Nuevo cliente</Button>}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nombre">Nombre</Label>
              <Input
                id="nombre"
                required
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rnc_cedula">RNC / Cédula</Label>
              <Input
                id="rnc_cedula"
                value={form.rnc_cedula}
                onChange={(e) => setForm({ ...form, rnc_cedula: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pais">País</Label>
              <Input id="pais" value={form.pais} onChange={(e) => setForm({ ...form, pais: e.target.value })} />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                id="es_exterior"
                type="checkbox"
                checked={form.es_exterior}
                onChange={(e) => setForm({ ...form, es_exterior: e.target.checked })}
                className="size-4 cursor-pointer accent-primary"
              />
              <Label htmlFor="es_exterior" className="cursor-pointer">
                Cliente de exportación
              </Label>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear cliente'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {clientes && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">RNC/Cédula</th>
                <th className="px-3 py-2 font-medium">País</th>
                <th className="px-3 py-2 font-medium">Exterior</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((cliente) => (
                <tr key={cliente.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-3 py-1.5">{cliente.nombre}</td>
                  <td className="font-tabular px-3 py-1.5 text-muted-foreground">{cliente.rnc_cedula ?? '—'}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">{cliente.pais}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">{cliente.es_exterior ? 'Sí' : 'No'}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(cliente)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(cliente)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {clientes.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin clientes registrados todavía.
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
