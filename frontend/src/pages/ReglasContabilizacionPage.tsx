import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  actualizarReglaContabilizacion,
  crearReglaContabilizacion,
  eliminarReglaContabilizacion,
  getPlanCuentas,
  getReglasContabilizacion,
  type PlanCuenta,
  type ReglaContabilizacion,
} from '@/lib/api'

interface ReglasContabilizacionPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'
const inputClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const ORIGEN_LABEL: Record<string, string> = { nomina: 'Nómina', factura: 'Factura' }

// Codigos de evento que el motor puede generar hoy -- ver
// app/services/nomina_eventos.py (bases x sufijos condicionales segun
// el resultado del calculo) y app/services/facturacion.py. Es una guia
// para no adivinar el nombre exacto, no una lista cerrada -- el backend
// acepta cualquier string, pero si no coincide con lo que el motor
// genera, la regla nunca se usa.
const EVENTOS_POR_ORIGEN: Record<string, string[]> = {
  nomina: ['JORNALES_COSECHA', 'JORNALES_PROYECTO', 'SALARIOS_FINCA', 'SALARIOS_ADMIN', 'SALARIOS_PROYECTO'].flatMap(
    (base) => [base, `${base}_NETO`, `${base}_ISR`, `${base}_TSS`, `${base}_TSS_PATRONAL`, `${base}_INFOTEP`, `${base}_RIESGOS`]
  ),
  factura: ['VENTA_TOTAL', 'VENTA_LOCAL', 'VENTA_EXPORT', 'ITBIS_18', 'COSTO_VENTA'],
}

const FORM_VACIO = { origen_tipo: 'nomina', codigo_evento: '', numero_cta: '', debcred: 'D' as 'D' | 'C' }

export function ReglasContabilizacionPage({ token, empresaId }: ReglasContabilizacionPageProps) {
  const [reglas, setReglas] = useState<ReglaContabilizacion[] | null>(null)
  const [cuentas, setCuentas] = useState<PlanCuenta[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getReglasContabilizacion(token, empresaId)
      .then(setReglas)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las reglas'))
  }

  useEffect(() => {
    setReglas(null)
    cargar()
  }, [token, empresaId])
  useEffect(() => {
    getPlanCuentas(token, empresaId).then(setCuentas).catch(() => setCuentas([]))
  }, [token, empresaId])

  function abrirNueva() {
    setForm({ ...FORM_VACIO, numero_cta: cuentas[0] ? cuentas[0].numero_cta : '' })
    setEditandoId(null)
    setMostrarForm(true)
  }

  function abrirEditar(regla: ReglaContabilizacion) {
    setForm({
      origen_tipo: regla.origen_tipo,
      codigo_evento: regla.codigo_evento,
      numero_cta: regla.numero_cta,
      debcred: regla.debcred,
    })
    setEditandoId(regla.id)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    const payload = { empresa_id: empresaId, ...form }
    try {
      if (editandoId) await actualizarReglaContabilizacion(token, editandoId, payload)
      else await crearReglaContabilizacion(token, payload)
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: editandoId ? 'Regla actualizada' : 'Regla creada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo guardar la regla',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  async function handleEliminar(regla: ReglaContabilizacion) {
    if (!confirm(`¿Eliminar la regla ${regla.codigo_evento} → ${regla.numero_cta}?`)) return
    try {
      await eliminarReglaContabilizacion(token, regla.id)
      cargar()
      toast({ variant: 'success', title: 'Regla eliminada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo eliminar la regla',
        description: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Reglas de Contabilización</h1>
          <p className="text-sm text-muted-foreground">
            {reglas ? `${reglas.length} reglas` : 'Cargando…'} — mapean cada evento de nómina/factura a una cuenta
            del catálogo, para que el asiento se genere solo.
          </p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNueva} disabled={cuentas.length === 0}>
            + Nueva regla
          </Button>
        )}
      </div>

      {cuentas.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Necesitas cuentas en el catálogo de esta empresa primero — créalas en Plan de Cuentas.
        </p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-4 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="origen_tipo">Origen</Label>
              <select
                id="origen_tipo"
                className={selectClassName}
                value={form.origen_tipo}
                onChange={(e) => setForm({ ...form, origen_tipo: e.target.value, codigo_evento: '' })}
              >
                <option value="nomina">Nómina</option>
                <option value="factura">Factura</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="codigo_evento">Código de evento</Label>
              <input
                id="codigo_evento"
                required
                list="codigos-evento"
                className={inputClassName}
                value={form.codigo_evento}
                onChange={(e) => setForm({ ...form, codigo_evento: e.target.value.toUpperCase() })}
              />
              <datalist id="codigos-evento">
                {(EVENTOS_POR_ORIGEN[form.origen_tipo] ?? []).map((codigo) => (
                  <option key={codigo} value={codigo} />
                ))}
              </datalist>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="numero_cta">Cuenta</Label>
              <select
                id="numero_cta"
                required
                className={selectClassName}
                value={form.numero_cta}
                onChange={(e) => setForm({ ...form, numero_cta: e.target.value })}
              >
                {cuentas.map((c) => (
                  <option key={c.id} value={c.numero_cta}>
                    {c.numero_cta} — {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="debcred">Débito/Crédito</Label>
              <select
                id="debcred"
                className={selectClassName}
                value={form.debcred}
                onChange={(e) => setForm({ ...form, debcred: e.target.value as 'D' | 'C' })}
              >
                <option value="D">Débito</option>
                <option value="C">Crédito</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              {editandoId ? 'Guardar cambios' : 'Crear regla'}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {reglas && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Origen</th>
                <th className="px-3 py-2 font-medium">Código de evento</th>
                <th className="px-3 py-2 font-medium">Cuenta</th>
                <th className="px-3 py-2 font-medium">D/C</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {reglas.map((regla) => (
                <tr key={regla.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-3 py-1.5">{ORIGEN_LABEL[regla.origen_tipo] ?? regla.origen_tipo}</td>
                  <td className="font-tabular px-3 py-1.5">{regla.codigo_evento}</td>
                  <td className="px-3 py-1.5 text-muted-foreground">
                    {regla.numero_cta} — {cuentas.find((c) => c.numero_cta === regla.numero_cta)?.nombre ?? '—'}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{regla.debcred === 'D' ? 'Débito' : 'Crédito'}</td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => abrirEditar(regla)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <span className="mx-1.5 text-muted-foreground">·</span>
                    <button
                      type="button"
                      onClick={() => handleEliminar(regla)}
                      className="cursor-pointer text-xs text-destructive hover:underline"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {reglas.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin reglas registradas todavía.
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
