import { useEffect, useMemo, useState } from 'react'

import { Input } from '@/components/ui/input'
import { ApiError, getPlanCuentas, type PlanCuenta } from '@/lib/api'

interface PlanCuentasPageProps {
  token: string
  empresaId: number
}

// Verificado contra los niveles 1 (raiz) del catalogo real
// (catalogo_cuentas_agrocasa.csv), no inventado.
const TIPO_LABEL: Record<number, string> = {
  1: 'Activos',
  2: 'Pasivos',
  3: 'Capital',
  4: 'Ingresos',
  5: 'Costos',
  6: 'Gastos',
}

export function PlanCuentasPage({ token, empresaId }: PlanCuentasPageProps) {
  const [cuentas, setCuentas] = useState<PlanCuenta[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')

  useEffect(() => {
    setCuentas(null)
    getPlanCuentas(token, empresaId)
      .then(setCuentas)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudo cargar el plan de cuentas'))
  }, [token, empresaId])

  const filtradas = useMemo(() => {
    if (!cuentas) return []
    const q = busqueda.trim().toLowerCase()
    if (!q) return cuentas
    return cuentas.filter(
      (c) => c.numero_cta.toLowerCase().includes(q) || c.nombre.toLowerCase().includes(q)
    )
  }, [cuentas, busqueda])

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Plan de Cuentas</h1>
          <p className="text-sm text-muted-foreground">
            {cuentas ? `${cuentas.length.toLocaleString('es-DO')} cuentas` : 'Cargando…'}
          </p>
        </div>
        <Input
          placeholder="Buscar por número o nombre…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {cuentas && (
        <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-card">
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Número</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Tipo</th>
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
                  <td className="px-3 py-1.5 text-xs text-muted-foreground">
                    {TIPO_LABEL[cuenta.tipo_cta] ?? cuenta.tipo_cta}
                  </td>
                </tr>
              ))}
              {filtradas.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin resultados para "{busqueda}".
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
