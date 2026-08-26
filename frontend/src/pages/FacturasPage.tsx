import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  crearFactura,
  getClientes,
  getFacturas,
  getLotesCosecha,
  getObras,
  getSucursales,
  type Cliente,
  type Factura,
  type FacturaDetalleInput,
  type LoteCosecha,
  type Obra,
  type Sucursal,
} from '@/lib/api'

interface FacturasPageProps {
  token: string
  empresaId: number
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const ESTADO_ECF_LABEL: Record<Factura['estado_ecf'], string> = {
  pendiente: 'Pendiente',
  aceptado: 'Aceptado',
  rechazado: 'Rechazado',
  no_aplica: 'No aplica',
}

const LINEA_VACIA: FacturaDetalleInput = { descripcion: '', cantidad: 1, precio_unitario: 0 }

export function FacturasPage({ token, empresaId }: FacturasPageProps) {
  const [facturas, setFacturas] = useState<Factura[] | null>(null)
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [sucursales, setSucursales] = useState<Sucursal[]>([])
  const [lotes, setLotes] = useState<LoteCosecha[]>([])
  const [obras, setObras] = useState<Obra[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const [sucursalId, setSucursalId] = useState('')
  const [clienteId, setClienteId] = useState('')
  const [tipoFactura, setTipoFactura] = useState<'local' | 'exportacion'>('local')
  const [fechaEmision, setFechaEmision] = useState('')
  const [loteId, setLoteId] = useState('')
  const [obraId, setObraId] = useState('')
  const [lineas, setLineas] = useState<FacturaDetalleInput[]>([{ ...LINEA_VACIA }])

  function cargar() {
    getFacturas(token, empresaId)
      .then(setFacturas)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las facturas'))
  }

  useEffect(() => {
    setFacturas(null)
    cargar()
  }, [token, empresaId])
  useEffect(() => {
    getClientes(token).then((todos) => setClientes(todos.filter((c) => c.empresa_id === empresaId))).catch(() => setClientes([]))
    getSucursales(token, empresaId).then(setSucursales).catch(() => setSucursales([]))
    getLotesCosecha(token).then((todos) => setLotes(todos.filter((l) => l.estado === 'disponible'))).catch(() => setLotes([]))
    getObras(token, empresaId).then((todas) => setObras(todas.filter((o) => o.estado === 'en_proceso'))).catch(() => setObras([]))
  }, [token, empresaId])

  function abrirNuevo() {
    setSucursalId(sucursales[0] ? String(sucursales[0].id) : '')
    setClienteId('')
    setTipoFactura('local')
    setFechaEmision('')
    setLoteId('')
    setObraId('')
    setLineas([{ ...LINEA_VACIA }])
    setMostrarForm(true)
  }

  function actualizarLinea(indice: number, cambios: Partial<FacturaDetalleInput>) {
    setLineas((prev) => prev.map((linea, i) => (i === indice ? { ...linea, ...cambios } : linea)))
  }

  const subtotal = lineas.reduce((acc, l) => acc + l.cantidad * l.precio_unitario, 0)
  const itbis = tipoFactura === 'local' ? subtotal * 0.18 : 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await crearFactura(token, {
        empresa_id: empresaId,
        sucursal_id: Number(sucursalId),
        cliente_id: Number(clienteId),
        tipo_factura: tipoFactura,
        fecha_emision: fechaEmision,
        moneda: tipoFactura === 'exportacion' ? 'USD' : 'DOP',
        lote_id: loteId ? Number(loteId) : null,
        obra_id: obraId ? Number(obraId) : null,
        lineas: lineas.filter((l) => l.descripcion && l.cantidad > 0),
      })
      setMostrarForm(false)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la factura')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Facturas</h1>
          <p className="text-sm text-muted-foreground">
            {facturas ? `${facturas.length} registradas` : 'Cargando…'}
          </p>
        </div>
        {!mostrarForm && (
          <Button onClick={abrirNuevo} disabled={clientes.length === 0 || sucursales.length === 0}>
            + Nueva factura
          </Button>
        )}
      </div>

      {clientes.length === 0 && (
        <p className="text-sm text-muted-foreground">Necesitas al menos un cliente registrado para facturar.</p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {mostrarForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cliente_id">Cliente</Label>
              <select
                id="cliente_id"
                required
                className={selectClassName}
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
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
              <Label htmlFor="sucursal_id">Sucursal (define secuencia e-CF)</Label>
              <select
                id="sucursal_id"
                required
                className={selectClassName}
                value={sucursalId}
                onChange={(e) => setSucursalId(e.target.value)}
              >
                {sucursales.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="tipo_factura">Tipo</Label>
              <select
                id="tipo_factura"
                className={selectClassName}
                value={tipoFactura}
                onChange={(e) => setTipoFactura(e.target.value as 'local' | 'exportacion')}
              >
                <option value="local">Local (ITBIS 18%)</option>
                <option value="exportacion">Exportación (ITBIS 0%)</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fecha_emision">Fecha de emisión</Label>
              <Input
                id="fecha_emision"
                type="date"
                required
                value={fechaEmision}
                onChange={(e) => setFechaEmision(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="lote_id">Lote de cosecha (genera salida de inventario)</Label>
              <select
                id="lote_id"
                className={selectClassName}
                value={loteId}
                disabled={obraId !== ''}
                onChange={(e) => setLoteId(e.target.value)}
              >
                <option value="">Sin lote</option>
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.producto} — {l.fecha_cosecha} ({l.cantidad} {l.unidad})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="obra_id">Obra (reconoce costo incurrido desde la última factura)</Label>
              <select
                id="obra_id"
                className={selectClassName}
                value={obraId}
                disabled={loteId !== ''}
                onChange={(e) => setObraId(e.target.value)}
              >
                <option value="">Sin obra</option>
                {obras.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.codigo} — {o.nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {lotes.length === 0 && obras.length === 0 && (
            <p className="text-xs text-muted-foreground">
              Sin lote ni obra: factura de servicio, no genera salida de inventario ni costo de venta automático.
            </p>
          )}

          <div className="flex flex-col gap-2">
            {lineas.map((linea, i) => (
              <div key={i} className="grid grid-cols-[1fr_120px_140px_32px] items-end gap-2">
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Descripción</Label>}
                  <Input
                    required
                    value={linea.descripcion}
                    onChange={(e) => actualizarLinea(i, { descripcion: e.target.value })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Cantidad</Label>}
                  <Input
                    type="number"
                    step="0.01"
                    required
                    value={linea.cantidad || ''}
                    onChange={(e) => actualizarLinea(i, { cantidad: Number(e.target.value) })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  {i === 0 && <Label>Precio unitario</Label>}
                  <Input
                    type="number"
                    step="0.01"
                    required
                    value={linea.precio_unitario || ''}
                    onChange={(e) => actualizarLinea(i, { precio_unitario: Number(e.target.value) })}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setLineas((prev) => prev.filter((_, idx) => idx !== i))}
                  className="h-8 cursor-pointer text-xs text-destructive hover:underline"
                  disabled={lineas.length <= 1}
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

          <p className="font-tabular text-xs text-muted-foreground">
            Subtotal: {subtotal.toFixed(2)} — ITBIS: {itbis.toFixed(2)} — Total: {(subtotal + itbis).toFixed(2)}
          </p>

          <div className="flex gap-2">
            <Button type="submit" disabled={guardando} size="sm">
              Crear factura
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setMostrarForm(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {facturas && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">e-CF</th>
                <th className="px-3 py-2 font-medium">Fecha</th>
                <th className="px-3 py-2 font-medium">Cliente</th>
                <th className="px-3 py-2 font-medium">Tipo</th>
                <th className="px-3 py-2 font-medium text-right">Total</th>
                <th className="px-3 py-2 font-medium">e-CF estado</th>
              </tr>
            </thead>
            <tbody>
              {facturas.map((factura) => (
                <tr key={factura.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="font-tabular px-3 py-1.5 text-muted-foreground">{factura.e_ncf ?? '—'}</td>
                  <td className="font-tabular px-3 py-1.5 text-muted-foreground">{factura.fecha_emision}</td>
                  <td className="px-3 py-1.5">
                    {clientes.find((c) => c.id === factura.cliente_id)?.nombre ?? `#${factura.cliente_id}`}
                  </td>
                  <td className="px-3 py-1.5 capitalize">{factura.tipo_factura}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">
                    {factura.moneda} {factura.total.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{ESTADO_ECF_LABEL[factura.estado_ecf]}</td>
                </tr>
              ))}
              {facturas.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin facturas registradas todavía.
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
