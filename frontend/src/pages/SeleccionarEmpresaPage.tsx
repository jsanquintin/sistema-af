import { useEffect, useState, type FormEvent } from 'react'

import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { ApiError, getEmpresas, getSucursales, type Empresa, type Sucursal } from '@/lib/api'

interface SeleccionarEmpresaPageProps {
  token: string
  onSeleccionado: (empresa: Empresa, sucursal: Sucursal | null) => void
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

export function SeleccionarEmpresaPage({ token, onSeleccionado }: SeleccionarEmpresaPageProps) {
  const [empresas, setEmpresas] = useState<Empresa[] | null>(null)
  const [empresaId, setEmpresaId] = useState<number | null>(null)
  const [sucursales, setSucursales] = useState<Sucursal[] | null>(null)
  const [sucursalId, setSucursalId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getEmpresas(token)
      .then((data) => {
        setEmpresas(data)
        if (data.length === 1) setEmpresaId(data[0].id)
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las empresas'))
  }, [token])

  useEffect(() => {
    if (empresaId == null) {
      setSucursales(null)
      setSucursalId(null)
      return
    }
    getSucursales(token, empresaId)
      .then((data) => {
        setSucursales(data)
        setSucursalId(data.length === 1 ? data[0].id : null)
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las sucursales'))
  }, [empresaId, token])

  const necesitaElegirSucursal = (sucursales?.length ?? 0) > 1
  const puedeContinuar = empresaId != null && (!necesitaElegirSucursal || sucursalId != null)

  function handleContinuar(event: FormEvent) {
    event.preventDefault()
    const empresa = empresas?.find((e) => e.id === empresaId)
    if (!empresa) return
    const sucursal = sucursales?.find((s) => s.id === sucursalId) ?? null
    onSeleccionado(empresa, sucursal)
  }

  return (
    <div className="bg-ledger bg-glow relative flex min-h-svh items-center justify-center overflow-hidden bg-background px-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="animate-enter w-full max-w-sm">
        <div className="mb-10 flex items-center gap-3 px-1">
          <span className="h-8 w-1 rounded-full bg-primary" />
          <span className="font-mono text-2xl font-semibold tracking-tight text-foreground">
            sistema-af
          </span>
        </div>
        <Card className="border-t-2 border-t-primary">
          <CardHeader>
            <CardTitle as="h1" className="text-xl font-semibold tracking-tight">
              Selecciona dónde trabajar
            </CardTitle>
            <CardDescription>Empresa y sucursal para esta sesión</CardDescription>
          </CardHeader>
          <CardContent>
            {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
            {!empresas && !error && (
              <p className="text-sm text-muted-foreground">Cargando empresas…</p>
            )}
            {empresas && (
              <form className="flex flex-col gap-4" onSubmit={handleContinuar}>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="empresa">Empresa</Label>
                  <select
                    id="empresa"
                    className={selectClassName}
                    value={empresaId ?? ''}
                    onChange={(e) => setEmpresaId(e.target.value ? Number(e.target.value) : null)}
                  >
                    <option value="" disabled>
                      Selecciona una empresa
                    </option>
                    {empresas.map((empresa) => (
                      <option key={empresa.id} value={empresa.id}>
                        {empresa.nombre_comercial ?? empresa.razon_social}
                      </option>
                    ))}
                  </select>
                </div>
                {necesitaElegirSucursal && sucursales && (
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="sucursal">Sucursal</Label>
                    <select
                      id="sucursal"
                      className={selectClassName}
                      value={sucursalId ?? ''}
                      onChange={(e) => setSucursalId(e.target.value ? Number(e.target.value) : null)}
                    >
                      <option value="" disabled>
                        Selecciona una sucursal
                      </option>
                      {sucursales.map((sucursal) => (
                        <option key={sucursal.id} value={sucursal.id}>
                          {sucursal.nombre}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <Button type="submit" disabled={!puedeContinuar}>
                  Continuar
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
