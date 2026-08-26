const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface Usuario {
  id: string
  email: string
  nombre_completo: string
  rol: string
  tenant_id: string
}

export interface Empresa {
  id: number
  rnc: string
  razon_social: string
  nombre_comercial: string | null
}

export interface Sucursal {
  id: number
  empresa_id: number
  codigo: string
  nombre: string
  tipo: string
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? 'No se pudo iniciar sesión')
  }

  return res.json()
}

export async function getMe(token: string): Promise<Usuario> {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!res.ok) {
    throw new ApiError(res.status, 'Sesión inválida o expirada')
  }

  return res.json()
}

export async function getEmpresas(token: string): Promise<Empresa[]> {
  const res = await fetch(`${API_URL}/empresas`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!res.ok) {
    throw new ApiError(res.status, 'No se pudieron cargar las empresas')
  }

  return res.json()
}

export async function getSucursales(token: string, empresaId: number): Promise<Sucursal[]> {
  const res = await fetch(`${API_URL}/empresas/${empresaId}/sucursales`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!res.ok) {
    throw new ApiError(res.status, 'No se pudieron cargar las sucursales')
  }

  return res.json()
}
