import { Fragment, useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  calcularNomina,
  cerrarNomina,
  crearNominaCorrida,
  getEmpleados,
  getLotesCosecha,
  getNominaCorridas,
  getNominaDetalle,
  getObras,
  type Empleado,
  type LoteCosecha,
  type NominaCorrida,
  type NominaDetalle,
  type Obra,
} from '@/lib/api'

interface NominaCorridasPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const FORM_VACIO = { codigo: '', nombre: '', periodo_inicio: '', periodo_fin: '', costeable: '' }

export function NominaCorridasPage({ token, empresaId }: NominaCorridasPageProps) {
  const [corridas, setCorridas] = useState<NominaCorrida[] | null>(null)
  const [empleados, setEmpleados] = useState<Empleado[]>([])
  const [lotes, setLotes] = useState<LoteCosecha[]>([])
  const [obras, setObras] = useState<Obra[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  const [calculandoId, setCalculandoId] = useState<number | null>(null)
  const [diasPorEmpleado, setDiasPorEmpleado] = useState<Record<number, string>>({})
  const [procesando, setProcesando] = useState<number | null>(null)

  const [detalleAbierto, setDetalleAbierto] = useState<number | null>(null)
  const [detalle, setDetalle] = useState<NominaDetalle[]>([])

  function cargar() {
    getNominaCorridas(token, empresaId)
      .then(setCorridas)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las corridas'))
  }

  useEffect(() => {
    setCorridas(null)
    cargar()
  }, [token, empresaId])
  useEffect(() => {
    getEmpleados(token, empresaId).then(setEmpleados).catch(() => setEmpleados([]))
    getLotesCosecha(token, empresaId).then((todos) => setLotes(todos.filter((l) => l.estado !== 'vendido' && l.estado !== 'exportado'))).catch(() => setLotes([]))
    getObras(token, empresaId).then((todas) => setObras(todas.filter((o) => o.estado === 'en_proceso'))).catch(() => setObras([]))
  }, [token, empresaId])

  const jornaleros = empleados.filter((e) => e.tipo_empleado === 'jornalero')

  function abrirNuevo() {
    setForm(FORM_VACIO)
    setMostrarForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    const [costeableTipo, costeableIdStr] = form.costeable ? form.costeable.split(':') : [null, null]
    try {
      await crearNominaCorrida(token, {
        empresa_id: empresaId,
        sucursal_id: null,
        incluye_tss: true,
        codigo: form.codigo,
        nombre: form.nombre,
        periodo_inicio: form.periodo_inicio,
        periodo_fin: form.periodo_fin,
        costeable_tipo: costeableTipo as 'lote' | 'obra' | null,
        costeable_id: costeableIdStr ? Number(costeableIdStr) : null,
      })
      setMostrarForm(false)
      cargar()
      toast({ variant: 'success', title: 'Corrida de nómina creada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo crear la corrida',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  function abrirCalcular(corrida: NominaCorrida) {
    setCalculandoId(corrida.id)
    setDiasPorEmpleado({})
  }

  async function handleCalcular(corridaId: number) {
    setProcesando(corridaId)
    try {
      const dias = Object.fromEntries(
        Object.entries(diasPorEmpleado)
          .filter(([, v]) => v !== '')
          .map(([id, v]) => [Number(id), Number(v)])
      )
      const filas = await calcularNomina(token, corridaId, dias)
      setDetalle(filas)
      setDetalleAbierto(corridaId)
      setCalculandoId(null)
      toast({ variant: 'success', title: 'Nómina calculada', description: `${filas.length} líneas generadas` })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo calcular la nómina',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setProcesando(null)
    }
  }

  async function handleCerrar(corridaId: number) {
    if (!confirm('¿Cerrar esta corrida? Genera el asiento contable y ya no se puede recalcular.')) return
    setProcesando(corridaId)
    try {
      await cerrarNomina(token, corridaId)
      cargar()
      toast({ variant: 'success', title: 'Corrida cerrada', description: 'Asiento contable generado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo cerrar la corrida',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setProcesando(null)
    }
  }

  async function handleVerDetalle(corridaId: number) {
    if (detalleAbierto === corridaId) {
      setDetalleAbierto(null)
      return
    }
    try {
      setDetalle(await getNominaDetalle(token, corridaId))
      setDetalleAbierto(corridaId)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo cargar el detalle')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Nóminas</h1>
          <p className="text-sm text-muted-foreground">Calcular corre el motor (ISR/TSS); cerrar postea el asiento.</p>
        </div>
        {!mostrarForm && <Button onClick={abrirNuevo}>+ Nueva corrida</Button>}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="codigo">Código</Label>
              <Input
                id="codigo"
                required
                value={form.codigo}
                onChange={(e) => setForm({ ...form, codigo: e.target.value })}
              />
            </div>
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
              <Label htmlFor="periodo_inicio">Periodo — inicio</Label>
              <Input
                id="periodo_inicio"
                type="date"
                required
                value={form.periodo_inicio}
                onChange={(e) => setForm({ ...form, periodo_inicio: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="periodo_fin">Periodo — fin</Label>
              <Input
                id="periodo_fin"
                type="date"
                required
                value={form.periodo_fin}
                onChange={(e) => setForm({ ...form, periodo_fin: e.target.value })}
              />
            </div>
            <div className="col-span-2 flex flex-col gap-1.5">
              <Label htmlFor="costeable">
                Centro de costo (opcional — carga el bruto de toda la corrida a un lote u obra al cerrarla)
              </Label>
              <select
                id="costeable"
                className={selectClassName}
                value={form.costeable}
                onChange={(e) => setForm({ ...form, costeable: e.target.value })}
              >
                <option value="">Sin asignar</option>
                {lotes.length > 0 && (
                  <optgroup label="Lotes de cosecha">
                    {lotes.map((l) => (
                      <option key={`lote:${l.id}`} value={`lote:${l.id}`}>
                        {l.producto} — {l.fecha_cosecha}
                      </option>
                    ))}
                  </optgroup>
                )}
                {obras.length > 0 && (
                  <optgroup label="Obras">
                    {obras.map((o) => (
                      <option key={`obra:${o.id}`} value={`obra:${o.id}`}>
                        {o.codigo} — {o.nombre}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              Crear corrida
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {calculandoId !== null && (
        <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <p className="text-sm font-medium">Días/tareas trabajadas (solo jornaleros)</p>
          {jornaleros.length === 0 && (
            <p className="text-sm text-muted-foreground">No hay jornaleros registrados en esta empresa.</p>
          )}
          <div className="grid grid-cols-3 gap-3">
            {jornaleros.map((j) => (
              <div key={j.id} className="flex flex-col gap-1.5">
                <Label htmlFor={`dias-${j.id}`}>{j.nombre_completo}</Label>
                <Input
                  id={`dias-${j.id}`}
                  type="number"
                  step="0.5"
                  value={diasPorEmpleado[j.id] ?? ''}
                  onChange={(e) => setDiasPorEmpleado({ ...diasPorEmpleado, [j.id]: e.target.value })}
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Button size="sm" disabled={procesando === calculandoId} onClick={() => handleCalcular(calculandoId)}>
              Calcular
            </Button>
            <Button variant="outline" size="sm" onClick={() => setCalculandoId(null)}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {corridas && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Código</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Periodo</th>
                <th className="px-3 py-2 font-medium">Costeo</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {corridas.map((corrida) => (
                <Fragment key={corrida.id}>
                  <tr className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="font-tabular px-3 py-1.5">{corrida.codigo}</td>
                    <td className="px-3 py-1.5">{corrida.nombre}</td>
                    <td className="font-tabular px-3 py-1.5 text-muted-foreground">
                      {corrida.periodo_inicio} — {corrida.periodo_fin}
                    </td>
                    <td className="px-3 py-1.5 text-muted-foreground">
                      {corrida.costeable_tipo === 'lote' &&
                        (lotes.find((l) => l.id === corrida.costeable_id)?.producto ?? `Lote #${corrida.costeable_id}`)}
                      {corrida.costeable_tipo === 'obra' &&
                        (obras.find((o) => o.id === corrida.costeable_id)?.codigo ?? `Obra #${corrida.costeable_id}`)}
                      {corrida.costeable_tipo === null && '—'}
                    </td>
                    <td className="px-3 py-1.5">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          corrida.cerrada ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {corrida.cerrada ? 'Cerrada' : 'Abierta'}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => handleVerDetalle(corrida.id)}
                        className="cursor-pointer text-xs text-primary hover:underline"
                      >
                        {detalleAbierto === corrida.id ? 'Ocultar' : 'Ver detalle'}
                      </button>
                      {!corrida.cerrada && (
                        <>
                          <span className="mx-1.5 text-muted-foreground">·</span>
                          <button
                            type="button"
                            onClick={() => abrirCalcular(corrida)}
                            className="cursor-pointer text-xs text-primary hover:underline"
                          >
                            Calcular
                          </button>
                          <span className="mx-1.5 text-muted-foreground">·</span>
                          <button
                            type="button"
                            onClick={() => handleCerrar(corrida.id)}
                            disabled={procesando === corrida.id}
                            className="cursor-pointer text-xs text-primary hover:underline disabled:opacity-50"
                          >
                            Cerrar
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                  {detalleAbierto === corrida.id && (
                    <tr>
                      <td colSpan={6} className="bg-muted/30 px-3 py-2">
                        {detalle.length === 0 ? (
                          <p className="text-sm text-muted-foreground">Sin líneas calculadas todavía.</p>
                        ) : (
                          <table className="w-full border-collapse text-xs">
                            <thead>
                              <tr className="text-left text-muted-foreground uppercase">
                                <th className="py-1">Empleado</th>
                                <th className="py-1 text-right">Bruto</th>
                                <th className="py-1 text-right">ISR</th>
                                <th className="py-1 text-right">TSS</th>
                                <th className="py-1 text-right">Neto</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detalle.map((fila) => (
                                <tr key={fila.id}>
                                  <td className="font-tabular py-1">
                                    {empleados.find((e) => e.id === fila.empleado_id)?.nombre_completo ??
                                      `#${fila.empleado_id}`}
                                  </td>
                                  <td className="font-tabular py-1 text-right">{fila.monto_bruto.toFixed(2)}</td>
                                  <td className="font-tabular py-1 text-right">{fila.retencion_isr.toFixed(2)}</td>
                                  <td className="font-tabular py-1 text-right">{fila.retencion_tss.toFixed(2)}</td>
                                  <td className="font-tabular py-1 text-right">{fila.monto_neto.toFixed(2)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {corridas.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin corridas registradas todavía.
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
