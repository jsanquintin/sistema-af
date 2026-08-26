import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  actualizarEmpresa,
  actualizarSucursal,
  crearSucursal,
  getEmpresas,
  getSucursales,
  type Empresa,
  type Sucursal,
} from '@/lib/api'

interface ConfiguracionEmpresasPageProps {
  token: string
}

const selectClassName =
  'h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const SUCURSAL_VACIA = { codigo: '', nombre: '', tipo: 'oficina' as Sucursal['tipo'] }

export function ConfiguracionEmpresasPage({ token }: ConfiguracionEmpresasPageProps) {
  const [empresas, setEmpresas] = useState<Empresa[] | null>(null)
  const [sucursalesPorEmpresa, setSucursalesPorEmpresa] = useState<Record<number, Sucursal[]>>({})
  const [error, setError] = useState<string | null>(null)

  const [editandoEmpresaId, setEditandoEmpresaId] = useState<number | null>(null)
  const [formEmpresa, setFormEmpresa] = useState({ rnc: '', razon_social: '', nombre_comercial: '' })

  const [formSucursalPara, setFormSucursalPara] = useState<number | null>(null)
  const [editandoSucursalId, setEditandoSucursalId] = useState<number | null>(null)
  const [formSucursal, setFormSucursal] = useState(SUCURSAL_VACIA)

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

  function abrirEditarEmpresa(empresa: Empresa) {
    setFormEmpresa({
      rnc: empresa.rnc,
      razon_social: empresa.razon_social,
      nombre_comercial: empresa.nombre_comercial ?? '',
    })
    setEditandoEmpresaId(empresa.id)
  }

  async function handleSubmitEmpresa(event: FormEvent, empresaId: number) {
    event.preventDefault()
    setGuardando(true)
    try {
      await actualizarEmpresa(token, empresaId, {
        rnc: formEmpresa.rnc,
        razon_social: formEmpresa.razon_social,
        nombre_comercial: formEmpresa.nombre_comercial || null,
      })
      setEditandoEmpresaId(null)
      cargar()
      toast({ variant: 'success', title: 'Empresa actualizada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo actualizar la empresa',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  function abrirNuevaSucursal(empresaId: number) {
    setFormSucursal(SUCURSAL_VACIA)
    setEditandoSucursalId(null)
    setFormSucursalPara(empresaId)
  }

  function abrirEditarSucursal(empresaId: number, sucursal: Sucursal) {
    setFormSucursal({ codigo: sucursal.codigo, nombre: sucursal.nombre, tipo: sucursal.tipo })
    setEditandoSucursalId(sucursal.id)
    setFormSucursalPara(empresaId)
  }

  async function handleSubmitSucursal(event: FormEvent, empresaId: number) {
    event.preventDefault()
    setGuardando(true)
    try {
      if (editandoSucursalId) await actualizarSucursal(token, empresaId, editandoSucursalId, formSucursal)
      else await crearSucursal(token, empresaId, formSucursal)
      setFormSucursalPara(null)
      cargar()
      toast({ variant: 'success', title: editandoSucursalId ? 'Sucursal actualizada' : 'Sucursal creada' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo guardar la sucursal',
        description: err instanceof ApiError ? err.message : undefined,
      })
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
              {editandoEmpresaId === empresa.id ? (
                <form
                  onSubmit={(e) => handleSubmitEmpresa(e, empresa.id)}
                  className="flex flex-col gap-2"
                >
                  <div className="grid grid-cols-3 gap-2">
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`rnc-${empresa.id}`}>RNC</Label>
                      <Input
                        id={`rnc-${empresa.id}`}
                        required
                        value={formEmpresa.rnc}
                        onChange={(e) => setFormEmpresa({ ...formEmpresa, rnc: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`razon-${empresa.id}`}>Razón social</Label>
                      <Input
                        id={`razon-${empresa.id}`}
                        required
                        value={formEmpresa.razon_social}
                        onChange={(e) => setFormEmpresa({ ...formEmpresa, razon_social: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`comercial-${empresa.id}`}>Nombre comercial</Label>
                      <Input
                        id={`comercial-${empresa.id}`}
                        value={formEmpresa.nombre_comercial}
                        onChange={(e) => setFormEmpresa({ ...formEmpresa, nombre_comercial: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" disabled={guardando} size="sm">
                      Guardar cambios
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setEditandoEmpresaId(null)}>
                      Cancelar
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="flex items-baseline justify-between gap-4">
                  <div>
                    <h2 className="font-medium">{empresa.nombre_comercial ?? empresa.razon_social}</h2>
                    <p className="text-sm text-muted-foreground">{empresa.razon_social}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-tabular text-xs text-muted-foreground">RNC {empresa.rnc}</span>
                    <button
                      type="button"
                      onClick={() => abrirEditarEmpresa(empresa)}
                      className="cursor-pointer text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                  </div>
                </div>
              )}

              {sucursales === undefined ? (
                <p className="mt-3 text-xs text-muted-foreground">Cargando sucursales…</p>
              ) : sucursales.length === 0 ? (
                <p className="mt-3 text-xs text-muted-foreground">Sin sucursales registradas.</p>
              ) : (
                <ul className="mt-3 flex flex-col gap-1 border-t border-border pt-3">
                  {sucursales.map((sucursal) => (
                    <li key={sucursal.id} className="flex items-center justify-between text-sm">
                      <span>{sucursal.nombre}</span>
                      <span className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground capitalize">{sucursal.tipo}</span>
                        <button
                          type="button"
                          onClick={() => abrirEditarSucursal(empresa.id, sucursal)}
                          className="cursor-pointer text-xs text-primary hover:underline"
                        >
                          Editar
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              )}

              {formSucursalPara === empresa.id ? (
                <form
                  onSubmit={(e) => handleSubmitSucursal(e, empresa.id)}
                  className="mt-3 flex flex-col gap-2 border-t border-border pt-3"
                >
                  <div className="grid grid-cols-3 gap-2">
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`codigo-${empresa.id}`}>Código</Label>
                      <Input
                        id={`codigo-${empresa.id}`}
                        required
                        value={formSucursal.codigo}
                        onChange={(e) => setFormSucursal({ ...formSucursal, codigo: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`nombre-${empresa.id}`}>Nombre</Label>
                      <Input
                        id={`nombre-${empresa.id}`}
                        required
                        value={formSucursal.nombre}
                        onChange={(e) => setFormSucursal({ ...formSucursal, nombre: e.target.value })}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`tipo-${empresa.id}`}>Tipo</Label>
                      <select
                        id={`tipo-${empresa.id}`}
                        className={selectClassName}
                        value={formSucursal.tipo}
                        onChange={(e) => setFormSucursal({ ...formSucursal, tipo: e.target.value as Sucursal['tipo'] })}
                      >
                        <option value="finca">Finca</option>
                        <option value="oficina">Oficina</option>
                        <option value="proyecto">Proyecto</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" disabled={guardando} size="sm">
                      {editandoSucursalId ? 'Guardar cambios' : 'Crear sucursal'}
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setFormSucursalPara(null)}>
                      Cancelar
                    </Button>
                  </div>
                </form>
              ) : (
                <button
                  type="button"
                  onClick={() => abrirNuevaSucursal(empresa.id)}
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
