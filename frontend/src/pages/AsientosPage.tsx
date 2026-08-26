import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  crearAsiento,
  getAsientos,
  getSucursales,
  postearAsiento,
  type Asiento,
  type AsientoDetalleInput,
  type Sucursal,
} from '@/lib/api'

interface AsientosPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const ORIGEN_LABEL: Record<Asiento['origen_tipo'], string> = {
  manual: 'Manual',
  nomina: 'Nómina',
  factura: 'Factura',
  inventario: 'Inventario',
  apertura: 'Apertura',
}

const LINEA_VACIA: AsientoDetalleInput = { numero_cta: '', sucursal_id: null, debcred: 'D', monto: 0 }

export function AsientosPage({ token, empresaId }: AsientosPageProps) {
  const [asientos, setAsientos] = useState<Asiento[] | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [fecha, setFecha] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [lineas, setLineas] = useState<AsientoDetalleInput[]>([{ ...LINEA_VACIA }, { ...LINEA_VACIA }])
  const [guardando, setGuardando] = useState(false)
  const [posteando, setPosteando] = useState<number | null>(null)

  function cargar() {
    getAsientos(token, empresaId)
      .then(setAsientos)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los asientos'))
  }

  useEffect(() => {
    setAsientos(null)
    cargar()
  }, [token, empresaId])
  useEffect(() => {
    getSucursales(token, empresaId).then(setSucursales).catch(() => setSucursales([]))
  }, [token, empresaId])

  function abrirNuevo() {
    setFecha('')
    setDescripcion('')
    setLineas([{ ...LINEA_VACIA }, { ...LINEA_VACIA }])
    setMostrarForm(true)
  }

  function actualizarLinea(indice: number, cambios: Partial<AsientoDetalleInput>) {
    setLineas((prev) => prev.map((linea, i) => (i === indice ? { ...linea, ...cambios } : linea)))
  }

  const totalDebe = lineas.filter((l) => l.debcred === 'D').reduce((acc, l) => acc + Number(l.monto || 0), 0)
  const totalHaber = lineas.filter((l) => l.debcred === 'C').reduce((acc, l) => acc + Number(l.monto || 0), 0)
  const cuadra = lineas.length > 0 && totalDebe === totalHaber && totalDebe > 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await crearAsiento(token, empresaId, {
        fecha,
        descripcion: descripcion || null,
        lineas: lineas.filter((l) => l.numero_cta && l.monto > 0),
      })
      setMostrarForm(false)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear el asiento')
    } finally {
      setGuardando(false)
    }
  }

  async function handlePostear(asiento: Asiento) {
    setPosteando(asiento.id)
    setError(null)
    try {
      await postearAsiento(token, asiento.id)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo postear el asiento')
    } finally {
      setPosteando(null)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Asientos</h1>
          <p className="text-sm text-muted-foreground">
            Un asiento nace en borrador — se postea cuando cuadra (debe = haber) y ya no se puede editar.
          </p>
        </div>
        {!mostrarForm && <Button onClick={abrirNuevo}>+ Nuevo asiento</Button>}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha">Fecha</Label>
              <Input id="fecha" type="date" required value={fecha} onChange={(e) => setFecha(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="descripcion">Descripción</Label>
              <Input id="descripcion" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            {lineas.map((linea, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_100px_140px_32px] items-end gap-2">
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Cuenta</Label>}
                  <Input
                    placeholder="Número de cuenta"
                    required
                    value={linea.numero_cta}
                    onChange={(e) => actualizarLinea(i, { numero_cta: e.target.value })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Sucursal (opcional)</Label>}
                  <select
                    className={selectClassName}
                    value={linea.sucursal_id ?? ''}
                    onChange={(e) => actualizarLinea(i, { sucursal_id: e.target.value ? Number(e.target.value) : null })}
                  >
                    <option value="">—</option>
                    {sucursales.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>D/C</Label>}
                  <select
                    className={selectClassName}
                    value={linea.debcred}
                    onChange={(e) => actualizarLinea(i, { debcred: e.target.value as 'D' | 'C' })}
                  >
                    <option value="D">Débito</option>
                    <option value="C">Crédito</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Monto</Label>}
                  <Input
                    type="number"
                    step="0.01"
                    required
                    value={linea.monto || ''}
                    onChange={(e) => actualizarLinea(i, { monto: Number(e.target.value) })}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setLineas((prev) => prev.filter((_, idx) => idx !== i))}
                  className="h-8 cursor-pointer text-xs text-destructive hover:underline"
                  disabled={lineas.length <= 2}
                >
                  Quitar
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() => setLineas((prev) => [...prev, { ...LINEA_VACIA }])}
              className="cursor-pointer self-start text-xs text-primary hover:underline"
            >
              + Agregar línea
            </button>
          </div>

          <p className={`font-tabular text-xs ${cuadra ? 'text-muted-foreground' : 'text-destructive'}`}>
            Debe: {totalDebe.toFixed(2)} — Haber: {totalHaber.toFixed(2)}
            {!cuadra && ' (no cuadra todavía, se puede guardar como borrador)'}
          </p>

          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              Crear borrador
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {asientos && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Fecha</th>
                <th className="px-3 py-2 font-medium">Origen</th>
                <th className="px-3 py-2 font-medium">Descripción</th>
                <th className="px-3 py-2 font-medium">Total</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {asientos.map((asiento) => {
                const total = asiento.lineas.filter((l) => l.debcred === 'D').reduce((acc, l) => acc + l.monto, 0)
                return (
                  <tr key={asiento.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="font-tabular px-3 py-1.5 text-muted-foreground">{asiento.fecha}</td>
                    <td className="px-3 py-1.5">{ORIGEN_LABEL[asiento.origen_tipo]}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{asiento.descripcion ?? '—'}</td>
                    <td className="font-tabular px-3 py-1.5">{total.toFixed(2)}</td>
                    <td className="px-3 py-1.5">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          asiento.estado === 'posteado'
                            ? 'bg-primary/15 text-primary'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {asiento.estado === 'posteado' ? 'Posteado' : 'Borrador'}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right whitespace-nowrap">
                      {asiento.estado === 'borrador' && (
                        <button
                          type="button"
                          onClick={() => handlePostear(asiento)}
                          disabled={posteando === asiento.id}
                          className="cursor-pointer text-xs text-primary hover:underline disabled:opacity-50"
                        >
                          Postear
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
              {asientos.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin asientos registrados todavía.
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
