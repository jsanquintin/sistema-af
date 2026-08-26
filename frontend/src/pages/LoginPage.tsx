import { Eye, EyeOff } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, login } from '@/lib/api'

interface LoginPageProps {
  onLoginSuccess: (token: string) => void
}

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await login(email, password)
      onLoginSuccess(access_token)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error de conexión con el servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-grid bg-glow relative flex min-h-svh items-center justify-center overflow-hidden bg-background">
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
            <CardTitle as="h1" className="text-2xl font-semibold tracking-tight">
              Inicia sesión
            </CardTitle>
            <CardDescription>Ingresa tus credenciales para continuar</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="password">Contraseña</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    className="pr-8"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="absolute inset-y-0 right-0 flex w-8 cursor-pointer items-center justify-center text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" disabled={loading}>
                {loading ? 'Ingresando…' : 'Ingresar'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
