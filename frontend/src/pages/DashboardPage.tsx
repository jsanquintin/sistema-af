import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  ApiError,
  getAsientos,
  getFacturas,
  getLotesCosecha,
  getNominaCorridas,
  getObras,
  getPlanCuentas,
  getReglasContabilizacion,
  getSucursales,
  type Asiento,
  type Factura,
  type LoteCosecha,
  type NominaCorrida,
  type Obra,
} from '@/lib/api'

interface DashboardPageProps {
  token: string
  empresaId: number
}

function esMesActual(fechaIso: string): boolean {
  const hoy = new Date()
  const [anio, mes] = fechaIso.split('-').map(Number)
  return anio === hoy.getFullYear() && mes === hoy.getMonth() + 1
}

export function DashboardPage({ token, empresaId }: DashboardPageProps) {
  const [asientos, setAsientos] = useState<Asiento[] | null>(null)
  const [nominas, setNominas] = useState<NominaCorrida[] | null>(null)
  const [facturas, setFacturas] = useState<Factura[] | null>(null)
  const [lotes, setLotes] = useState<LoteCosecha[] | null>(null)
  const [obras, setObras] = useState<Obra[] | null>(null)
  const [alertas, setAlertas] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setAsientos(null)
    setNominas(null)
    setFacturas(null)
    setLotes(null)
    setObras(null)
    setError(null)

    Promise.all([
      getAsientos(token, empresaId),
      getNominaCorridas(token, empresaId),
      getFacturas(token, empresaId),
      getLotesCosecha(token, empresaId),
      getObras(token, empresaId),
      getSucursales(token, empresaId),
      getPlanCuentas(token, empresaId),
      getReglasContabilizacion(token, empresaId),
    ])
      .then(([listaAsientos, listaNominas, listaFacturas, listaLotes, listaObras, sucursales, cuentas, reglas]) => {
        setAsientos(listaAsientos)
        setNominas(listaNominas)
        setFacturas(listaFacturas)
        setLotes(listaLotes)
        setObras(listaObras)

        const nuevasAlertas: string[] = []
        if (sucursales.length === 0) {
          nuevasAlertas.push('Sin sucursales registradas — sin esto no se puede facturar ni asignar empleados.')
        }
        if (cuentas.length === 0) {
          nuevasAlertas.push('Catálogo de cuentas vacío — sin esto no se pueden crear asientos.')
        }
        if (reglas.length === 0) {
          nuevasAlertas.push('Sin reglas de contabilización — nómina y facturas no podrán generar su asiento automático.')
        }
        setAlertas(nuevasAlertas)
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudo cargar el dashboard'))
  }, [token, empresaId])

  const cargando = asientos === null || nominas === null || facturas === null || lotes === null || obras === null

  const borradores = asientos?.filter((a) => a.estado === 'borrador').length ?? 0
  const nominasAbiertas = nominas?.filter((n) => !n.cerrada).length ?? 0

  const facturasDelMes = facturas?.filter((f) => esMesActual(f.fecha_emision)) ?? []
  const facturadoPorMoneda = facturasDelMes.reduce<Record<string, number>>((acc, f) => {
    acc[f.moneda] = (acc[f.moneda] ?? 0) + f.total
    return acc
  }, {})

  const lotesActivos = lotes?.filter((l) => l.estado === 'disponible' || l.estado === 'en_proceso') ?? []
  const costoLotesActivos = lotesActivos.reduce((acc, l) => acc + l.costo_acumulado, 0)

  const obrasActivas = obras?.filter((o) => o.estado === 'en_proceso') ?? []
  const costoObrasPorReconocer = obrasActivas.reduce((acc, o) => acc + (o.costo_acumulado - o.costo_reconocido), 0)

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Resumen de la empresa activa.</p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {alertas.length > 0 && (
        <div className="flex flex-col gap-2 rounded-lg border-l-2 border-l-warning bg-warning/10 p-3.5">
          <p className="text-sm font-medium text-warning">Configuración incompleta</p>
          <ul className="flex flex-col gap-1 text-xs text-muted-foreground">
            {alertas.map((alerta) => (
              <li key={alerta}>· {alerta}</li>
            ))}
          </ul>
        </div>
      )}

      {cargando ? (
        <p className="text-sm text-muted-foreground">Cargando…</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Tarjeta titulo="Asientos por postear" to="/contabilidad/asientos">
            <p className="font-tabular text-2xl font-semibold">{borradores}</p>
            <p className="text-xs text-muted-foreground">en borrador</p>
          </Tarjeta>

          <Tarjeta titulo="Nóminas abiertas" to="/nomina/corridas">
            <p className="font-tabular text-2xl font-semibold">{nominasAbiertas}</p>
            <p className="text-xs text-muted-foreground">sin cerrar</p>
          </Tarjeta>

          <Tarjeta titulo="Facturado este mes" to="/facturacion/facturas">
            {Object.keys(facturadoPorMoneda).length === 0 ? (
              <p className="font-tabular text-2xl font-semibold">0</p>
            ) : (
              <div className="flex flex-col">
                {Object.entries(facturadoPorMoneda).map(([moneda, total]) => (
                  <p key={moneda} className="font-tabular text-lg font-semibold">
                    {moneda} {total.toFixed(2)}
                  </p>
                ))}
              </div>
            )}
            <p className="text-xs text-muted-foreground">{facturasDelMes.length} facturas</p>
          </Tarjeta>

          <Tarjeta titulo="Lotes activos" to="/inventario/lotes">
            <p className="font-tabular text-2xl font-semibold">{lotesActivos.length}</p>
            <p className="text-xs text-muted-foreground">costo acumulado {costoLotesActivos.toFixed(2)}</p>
          </Tarjeta>

          <Tarjeta titulo="Obras en proceso" to="/inventario/obras">
            <p className="font-tabular text-2xl font-semibold">{obrasActivas.length}</p>
            <p className="text-xs text-muted-foreground">costo por reconocer {costoObrasPorReconocer.toFixed(2)}</p>
          </Tarjeta>
        </div>
      )}
    </div>
  )
}

function Tarjeta({ titulo, to, children }: { titulo: string; to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="flex flex-col gap-1 rounded-lg border border-border bg-card p-4 transition-colors hover:bg-muted/50"
    >
      <p className="text-section-label text-muted-foreground">{titulo}</p>
      {children}
    </Link>
  )
}
