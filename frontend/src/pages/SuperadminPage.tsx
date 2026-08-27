import { useEffect, useState, type FormEvent } from 'react'

import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import {
  ApiError,
  TENANT_TOKEN_STORAGE_KEY,
  actualizarTenant,
  crearTenant,
  entrarATenant,
  getTenants,
  type Tenant,
} from '@/lib/api'

interface SuperadminPageProps {
  token: string
  onLogout: () => void
}

const NUEVO_TENANT_VACIO = { nombre: '', admin_email: '', admin_password: '', admin_nombre_completo: '' }

export function SuperadminPage({ token, onLogout }: SuperadminPageProps) {
  const [tenants, setTenants] = useState<Tenant[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mostrandoForm, setMostrandoForm] = useState(false)
  const [formTenant, setFormTenant] = useState(NUEVO_TENANT_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [entrandoId, setEntrandoId] = useState<string | null>(null)

  function cargar() {
    getTenants(token)
      .then(setTenants)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los tenants'))
  }

  useEffect(cargar, [token])

  async function handleCrearTenant(event: FormEvent) {
    event.preventDefault()
    setGuardando(true)
    try {
      const { tenant } = await crearTenant(token, formTenant)
      setMostrandoForm(false)
      setFormTenant(NUEVO_TENANT_VACIO)
      cargar()
      toast({ variant: 'success', title: `Tenant "${tenant.nombre}" creado` })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo crear el tenant',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  async function handleToggleActivo(tenant: Tenant) {
    try {
      await actualizarTenant(token, tenant.id, !tenant.activo)
      cargar()
      toast({ variant: 'success', title: tenant.activo ? 'Tenant desactivado' : 'Tenant activado' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo actualizar el tenant',
        description: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  async function handleEntrar(tenant: Tenant) {
    setEntrandoId(tenant.id)
    try {
      const { access_token } = await entrarATenant(token, tenant.id)
      localStorage.setItem(TENANT_TOKEN_STORAGE_KEY, access_token)
      window.location.href = '/dashboard'
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo entrar al tenant',
        description: err instanceof ApiError ? err.message : undefined,
      })
      setEntrandoId(null)
    }
  }

  return (
    <div className="min-h-svh bg-background">
      <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="h-4 w-0.5 rounded-full bg-primary" />
          <span className="font-mono text-sm font-medium tracking-tight">
            sistema-af <span className="text-muted-foreground">· superadmin</span>
          </span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={onLogout}>
            Cerrar sesión
          </Button>
        </div>
      </header>

      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
        <div className="flex items-baseline justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Tenants</h1>
            <p className="text-sm text-muted-foreground">
              {tenants ? `${tenants.length} tenants` : 'Cargando…'}
            </p>
          </div>
          {!mostrandoForm && (
            <Button size="sm" onClick={() => setMostrandoForm(true)}>
              + Nuevo tenant
            </Button>
          )}
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {mostrandoForm && (
          <form
            onSubmit={handleCrearTenant}
            className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4"
          >
            <div className="flex flex-col gap-1">
              <Label htmlFor="tenant-nombre">Nombre del tenant</Label>
              <Input
                id="tenant-nombre"
                required
                value={formTenant.nombre}
                onChange={(e) => setFormTenant({ ...formTenant, nombre: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor="admin-nombre">Nombre del admin</Label>
                <Input
                  id="admin-nombre"
                  required
                  value={formTenant.admin_nombre_completo}
                  onChange={(e) => setFormTenant({ ...formTenant, admin_nombre_completo: e.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="admin-email">Email del admin</Label>
                <Input
                  id="admin-email"
                  type="email"
                  required
                  value={formTenant.admin_email}
                  onChange={(e) => setFormTenant({ ...formTenant, admin_email: e.target.value })}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="admin-password">Contraseña inicial del admin</Label>
              <Input
                id="admin-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={formTenant.admin_password}
                onChange={(e) => setFormTenant({ ...formTenant, admin_password: e.target.value })}
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={guardando} size="sm">
                Crear tenant
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setMostrandoForm(false)
                  setFormTenant(NUEVO_TENANT_VACIO)
                }}
              >
                Cancelar
              </Button>
            </div>
          </form>
        )}

        {tenants && (
          <div className="overflow-auto rounded-lg border border-border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                  <th className="px-3 py-2 font-medium">Nombre</th>
                  <th className="px-3 py-2 font-medium">Estado</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((tenant) => (
                  <tr key={tenant.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="px-3 py-1.5">{tenant.nombre}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{tenant.activo ? 'Activo' : 'Inactivo'}</td>
                    <td className="px-3 py-1.5 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => handleToggleActivo(tenant)}
                        className="cursor-pointer text-xs text-primary hover:underline"
                      >
                        {tenant.activo ? 'Desactivar' : 'Activar'}
                      </button>
                      <span className="mx-2 text-border">|</span>
                      <button
                        type="button"
                        disabled={entrandoId === tenant.id}
                        onClick={() => handleEntrar(tenant)}
                        className="cursor-pointer text-xs text-primary hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {entrandoId === tenant.id ? 'Entrando…' : 'Entrar'}
                      </button>
                    </td>
                  </tr>
                ))}
                {tenants.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-6 text-center text-sm text-muted-foreground">
                      Sin tenants registrados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
