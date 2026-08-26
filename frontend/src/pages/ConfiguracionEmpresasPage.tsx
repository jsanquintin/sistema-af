import { useEffect, useState } from 'react'

import { ApiError, getEmpresas, getSucursales, type Empresa, type Sucursal } from '@/lib/api'

interface ConfiguracionEmpresasPageProps {
  token: string
}

export function ConfiguracionEmpresasPage({ token }: ConfiguracionEmpresasPageProps) {
  const [empresas, setEmpresas] = useState<Empresa[] | null>(null)
  const [sucursalesPorEmpresa, setSucursalesPorEmpresa] = useState<Record<number, Sucursal[]>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getEmpresas(token)
      .then(async (data) => {
        setEmpresas(data)
        const entradas = await Promise.all(
          data.map(async (empresa) => [empresa.id, await getSucursales(token, empresa.id)] as const)
        )
        setSucursalesPorEmpresa(Object.fromEntries(entradas))
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las empresas'))
  }, [token])

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Empresas y sucursales</h1>
        <p className="text-sm text-muted-foreground">Empresas del tenant y sus sucursales/fincas registradas.</p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {!empresas && !error && <p className="text-sm text-muted-foreground">Cargando…</p>}

      <div className="flex flex-col gap-3">
        {empresas?.map((empresa) => {
          const sucursales = sucursalesPorEmpresa[empresa.id]
          return (
            <div key={empresa.id} className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-baseline justify-between gap-4">
                <h2 className="font-medium">{empresa.nombre_comercial ?? empresa.razon_social}</h2>
                <span className="font-tabular text-xs text-muted-foreground">RNC {empresa.rnc}</span>
              </div>
              <p className="text-sm text-muted-foreground">{empresa.razon_social}</p>

              {sucursales === undefined ? (
                <p className="mt-3 text-xs text-muted-foreground">Cargando sucursales…</p>
              ) : sucursales.length === 0 ? (
                <p className="mt-3 text-xs text-muted-foreground">Sin sucursales registradas.</p>
              ) : (
                <ul className="mt-3 flex flex-col gap-1 border-t border-border pt-3">
                  {sucursales.map((sucursal) => (
                    <li key={sucursal.id} className="flex items-center justify-between text-sm">
                      <span>{sucursal.nombre}</span>
                      <span className="text-xs text-muted-foreground capitalize">{sucursal.tipo}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
