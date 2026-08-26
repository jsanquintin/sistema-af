import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, getBalanceComprobacion, type BalanceComprobacionLinea } from '@/lib/api'

interface ReportesPageProps {
  token: string
  empresaId: number
}

function primerDiaDelMes(): string {
  const hoy = new Date()
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-01`
}

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10)
}

export function ReportesPage({ token, empresaId }: ReportesPageProps) {
  const [desde, setDesde] = useState(primerDiaDelMes())
  const [hasta, setHasta] = useState(hoyISO())
  const [filas, setFilas] = useState<BalanceComprobacionLinea[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setCargando(true)
    setError(null)
    try {
      setFilas(await getBalanceComprobacion(token, empresaId, desde, hasta))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo generar el balance de comprobación')
    } finally {
      setCargando(false)
    }
  }

  const totalDebe = filas?.reduce((acc, f) => acc + f.debe, 0) ?? 0
  const totalHaber = filas?.reduce((acc, f) => acc + f.haber, 0) ?? 0

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Balance de Comprobación</h1>
        <p className="text-sm text-muted-foreground">Suma de débitos y créditos por cuenta, solo asientos posteados.</p>
      </div>

      <form onSubmit={handleSubmit} className="flex items-end gap-3 rounded-lg border border-border bg-card p-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="desde">Desde</Label>
          <Input id="desde" type="date" required value={desde} onChange={(e) => setDesde(e.target.value)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="hasta">Hasta</Label>
          <Input id="hasta" type="date" required value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </div>
        <Button type="submit" disabled={cargando} size="sm">
          Generar
        </Button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {filas && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Cuenta</th>
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium text-right">Debe</th>
                <th className="px-3 py-2 font-medium text-right">Haber</th>
                <th className="px-3 py-2 font-medium text-right">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((fila) => (
                <tr key={fila.numero_cta} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="font-tabular px-3 py-1.5 text-muted-foreground">{fila.numero_cta}</td>
                  <td className="px-3 py-1.5">{fila.nombre}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">{fila.debe.toFixed(2)}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">{fila.haber.toFixed(2)}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">{fila.saldo.toFixed(2)}</td>
                </tr>
              ))}
              {filas.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin movimientos posteados en este rango.
                  </td>
                </tr>
              )}
            </tbody>
            {filas.length > 0 && (
              <tfoot>
                <tr className="border-t border-border font-medium">
                  <td className="px-3 py-1.5" colSpan={2}>
                    Total
                  </td>
                  <td className="font-tabular px-3 py-1.5 text-right">{totalDebe.toFixed(2)}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">{totalHaber.toFixed(2)}</td>
                  <td className="font-tabular px-3 py-1.5 text-right">{(totalDebe - totalHaber).toFixed(2)}</td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      )}
    </div>
  )
}
