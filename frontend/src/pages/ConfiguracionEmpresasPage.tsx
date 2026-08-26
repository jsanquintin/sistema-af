import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, crearSucursal, getEmpresas, getSucursales, type Empresa, type Sucursal } from '@/lib/api'

interface ConfiguracionEmpresasPageProps {
  token: string
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const FORM_VACIO = { codigo: '', nombre: '', tipo: 'oficina' as Sucursal['tipo'] }

export function ConfiguracionEmpresasPage({ token }: ConfiguracionEmpresasPageProps) {
  const [empresas, setEmpresas] = useState<Empresa[] | null>(null)
  const [sucursalesPorEmpresa, setSucursalesPorEmpresa] = useState<Record<number, Sucursal[]>>({})
  const [error, setError] = useState<string | null>(null)
  const [formAbiertoPara, setFormAbiertoPara] = useState<number | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getEmpresas(token)
      .then(async (data) => {
        setEmpresas(data)
        const entradas = await Promise.all(
          data.map(async (empresa) => [empresa.id, await getSucursales(token, empresa.id)] as const)
        )
        setSucursalesPorEmpresa(Object.fromEntries(entradas))
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar las empresas'))
  }

  useEffect(cargar, [token])

  function abrirForm(empresaId: number) {
    setForm(FORM_VACIO)
    setFormAbiertoPara(empresaId)
  }

  async function handleSubmit(event: FormEvent, empresaId: number) {
    event.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await crearSucursal(token, empresaId, form)
      setFormAbiertoPara(null)
      cargar()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la sucursal')
    } finally {
      setGuardando(false)
    }
  }

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

              {formAbiertoPara === empresa.id ? (
                <form
                  onSubmit={(e) => handleSubmit(e, empresa.id)}
                  className="mt-3 flex flex-col gap-2 border-t border-border pt-3"
                >
                  <div className="grid grid-cols-3 gap-2">
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`codigo-${empresa.id}`}>Código</Label>
                      <Input
                        id={`codigo-${empresa.id}`}
                        required
                        value={form.codigo}
                        onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`nombre-${empresa.id}`}>Nombre</Label>
                      <Input
                        id={`nombre-${empresa.id}`}
                        required
                        value={form.nombre}
                        onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`tipo-${empresa.id}`}>Tipo</Label>
                      <select
                        id={`tipo-${empresa.id}`}
                        className={selectClassName}
                        value={form.tipo}
                        onChange={(e) => setForm({ ...form, tipo: e.target.value as Sucursal['tipo'] })}
                      >
                        <option value="finca">Finca</option>
                        <option value="oficina">Oficina</option>
                        <option value="proyecto">Proyecto</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" disabled={guardando} size="sm">
                      Crear sucursal
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setFormAbiertoPara(null)}>
                      Cancelar
                    </Button>
                  </div>
                </form>
              ) : (
                <button
                  type="button"
                  onClick={() => abrirForm(empresa.id)}
                  className="mt-3 cursor-pointer text-xs text-primary hover:underline"
                >
                  + Nueva sucursal
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
