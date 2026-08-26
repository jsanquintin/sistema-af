import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import { ApiError, getUsuarios, restablecerPasswordUsuario, type UsuarioGestionado } from '@/lib/api'

interface UsuariosPageProps {
  token: string
}

const ROL_LABEL: Record<UsuarioGestionado['rol'], string> = {
  admin: 'Administrador',
  contador: 'Contador',
  nomina: 'Nómina',
  facturacion: 'Facturación',
  consulta: 'Consulta',
}

export function UsuariosPage({ token }: UsuariosPageProps) {
  const [usuarios, setUsuarios] = useState<UsuarioGestionado[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [restableciendoId, setRestableciendoId] = useState<string | null>(null)
  const [nuevaPassword, setNuevaPassword] = useState('')
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    getUsuarios(token)
      .then(setUsuarios)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los usuarios'))
  }

  useEffect(cargar, [token])

  function abrirRestablecer(usuarioId: string) {
    setNuevaPassword('')
    setRestableciendoId(usuarioId)
  }

  async function handleRestablecer(event: FormEvent, usuario: UsuarioGestionado) {
    event.preventDefault()
    setGuardando(true)
    try {
      await restablecerPasswordUsuario(token, usuario.id, nuevaPassword)
      setRestableciendoId(null)
      toast({ variant: 'success', title: `Contraseña restablecida para ${usuario.email}` })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'No se pudo restablecer la contraseña',
        description: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Usuarios</h1>
        <p className="text-sm text-muted-foreground">
          {usuarios ? `${usuarios.length} usuarios` : 'Cargando…'} — solo un administrador puede restablecer
          contraseñas. Recuperación por correo todavía no está configurada.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {usuarios && (
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                <th className="px-3 py-2 font-medium">Nombre</th>
                <th className="px-3 py-2 font-medium">Email</th>
                <th className="px-3 py-2 font-medium">Rol</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((usuario) => (
                <>
                  <tr key={usuario.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="px-3 py-1.5">{usuario.nombre_completo}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{usuario.email}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{ROL_LABEL[usuario.rol]}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{usuario.activo ? 'Activo' : 'Inactivo'}</td>
                    <td className="px-3 py-1.5 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => abrirRestablecer(usuario.id)}
                        className="cursor-pointer text-xs text-primary hover:underline"
                      >
                        Restablecer contraseña
                      </button>
                    </td>
                  </tr>
                  {restableciendoId === usuario.id && (
                    <tr key={`${usuario.id}-form`}>
                      <td colSpan={5} className="bg-muted/30 px-3 py-3">
                        <form
                          onSubmit={(e) => handleRestablecer(e, usuario)}
                          className="flex items-end gap-2"
                        >
                          <div className="flex flex-col gap-1.5">
                            <Label htmlFor={`nueva-password-${usuario.id}`}>Nueva contraseña</Label>
                            <Input
                              id={`nueva-password-${usuario.id}`}
                              type="password"
                              required
                              minLength={8}
                              autoComplete="new-password"
                              value={nuevaPassword}
                              onChange={(e) => setNuevaPassword(e.target.value)}
                              className="w-64"
                            />
                          </div>
                          <Button type="submit" disabled={guardando} size="sm">
                            Guardar
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setRestableciendoId(null)}
                          >
                            Cancelar
                          </Button>
                        </form>
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {usuarios.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-muted-foreground">
                    Sin usuarios registrados.
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
