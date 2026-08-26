import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  actualizarPlanCuenta,
  crearPlanCuenta,
  eliminarPlanCuenta,
  getPlanCuentas,
  type PlanCuenta,
} from '@/lib/api'

interface PlanCuentasPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

// Verificado contra los niveles 1 (raiz) del catalogo real
// (catalogo_cuentas_agrocasa.csv), no inventado.
const TIPO_LABEL: Record<PlanCuenta['tipo_cta'], string> = {
  1: 'Activos',
  2: 'Pasivos',
  3: 'Capital',
  4: 'Ingresos',
  5: 'Costos',
  6: 'Gastos',
}

const FORM_VACIO = { numero_cta: '', nivel: '1', tipo_cta: '1' as string, nombre: '' }

export function PlanCuentasPage({ token, empresaId }: PlanCuentasPageProps) {
  const [cuentas, setCuentas] = useState<PlanCuenta[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getPlanCuentas(token, empresaId)
      .then(setCuentas)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudo cargar el plan de cuentas'))
  }

  useEffect(() => {
    setCuentas(null)
    cargar()
  }, [token, empresaId])

  const filtradas = useMemo(() => {
    if (!cuentas) return []
    const q = busqueda.trim().toLowerCase()
    if (!q) return cuentas
    return cuentas.filter(
      (c) => c.numero_cta.toLowerCase().includes(q) || c.nombre.toLowerCase().includes(q)
    )
  }, [cuentas, busqueda])

  function abrirNueva() {
    setForm(FORM_VACIO)
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(cuenta: PlanCuenta) {
    setForm({
      numero_cta: cuenta.numero_cta,
      nivel: String(cuenta.nivel),
      tipo_cta: String(cuenta.tipo_cta),
      nombre: cuenta.nombre,
    })
    setEditandoId(cuenta.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    const payload = {
      empresa_id: empresaId,
      numero_cta: form.numero_cta,
      nivel: Number(form.nivel),
      tipo_cta: Number(form.tipo_cta) as PlanCuenta['tipo_cta'],
      nombre: form.nombre,
    }
    try {
      if (editandoId) await actualizarPlanCuenta(token, editandoId, payload)
      else await crearPlanCuenta(token, payload)
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: editandoId ? 'Cuenta actualizada' : 'Cuenta creada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo guardar la cuenta',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(cuenta: PlanCuenta) {
    if (!confirm(`¿Desactivar la cuenta ${cuenta.numero_cta} — ${cuenta.nombre}?`)) return
    try {
      await eliminarPlanCuenta(token, cuenta.id)
      cargar()
      toast({ variant: 'success', title: 'Cuenta desactivada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo desactivar la cuenta',
        description: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Plan de Cuentas</h1>
          <p className="text-sm text-muted-foreground">
            {cuentas ? `${cuentas.length.toLocaleString('es-DO')} cuentas` : 'Cargando…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Buscar por número o nombre…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="max-w-xs"
          />
          {!mostrarForm && <Button onClick={abrirNueva}>+ Nueva cuenta</Button>}
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-4 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="numero_cta">Número de cuenta</Label>
              <Input
                id="numero_cta"
                required
                value={form.numero_cta}
                onChange={(e) => setForm({ ...form, numero_cta: e.target.value })}
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
              <Label htmlFor="tipo_cta">Tipo</Label>
              <select
                id="tipo_cta"
                className={selectClassName}
                value={form.tipo_cta}
                onChange={(e) => setForm({ ...form, tipo_cta: e.target.value })}
              >
                {Object.entries(TIPO_LABEL).map(([valor, etiqueta]) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nivel">Nivel (jerarquía)</Label>
              <Input
                id="nivel"
                type="number"
                min={1}
                required
                value={form.nivel}
                onChange={(e) => setForm({ ...form, nivel: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear cuenta'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {cuentas && (
        <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-card">
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Número</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Tipo</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {filtradas.map((cuenta) => (
                <tr key={cuenta.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="font-tabular px-3 py-1.5 whitespace-nowrap text-muted-foreground">
                    {cuenta.numero_cta}
                  </td>
                  <td
                    className="px-3 py-1.5"
                    style={{ paddingLeft: `${0.75 + (cuenta.nivel - 1) * 1}rem` }}
                  >
                    {cuenta.nombre}
                  </td>
                  <td className="px-3 py-1.5 text-xs text-muted-foreground">{TIPO_LABEL[cuenta.tipo_cta]}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(cuenta)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(cuenta)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Desactivar
                    </button>
                  </td>
                </tr>
              ))}
              {filtradas.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    {busqueda ? `Sin resultados para "${busqueda}".` : 'Sin cuentas registradas todavía.'}
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
