const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(
  method: string,
  path: string,
  token: string | null,
  body?: unknown,
  fallbackError = 'Error de conexión con el servidor'
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const errBody = await res.json().catch(() => null)
    throw new ApiError(res.status, errBody?.detail ?? fallbackError)
  }
  if (res.status === 204) return undefined as T
  return res.json()
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

export interface PlanCuenta {
  id: number
  numero_cta: string
  nivel: number
  tipo_cta: number
  nombre: string
  activo: boolean
}

export interface Empleado {
  id: number
  empresa_id: number
  sucursal_id: number | null
  cedula: string | null
  nombre_completo: string
  tipo_empleado: 'fijo' | 'jornalero'
  incluye_tss: boolean
  salario_base: number | null
  tarifa_unidad: number | null
  fecha_ingreso: string | null
  fecha_salida: string | null
  activo: boolean
}
export type EmpleadoInput = Omit<Empleado, 'id' | 'activo'>

export interface Cliente {
  id: number
  empresa_id: number
  rnc_cedula: string | null
  nombre: string
  pais: string
  es_exterior: boolean
}
export type ClienteInput = Omit<Cliente, 'id'>

export interface Almacen {
  id: number
  sucursal_id: number
  codigo: string
  nombre: string
  activo: boolean
}
export type AlmacenInput = Omit<Almacen, 'id' | 'activo'>

export interface LoteCosecha {
  id: number
  sucursal_id: number
  almacen_id: number | null
  producto: string
  fecha_cosecha: string
  cantidad: number
  unidad: string
  calidad_grado: string | null
  humedad_pct: number | null
  costo_acumulado: number
  estado: 'disponible' | 'en_proceso' | 'vendido' | 'exportado'
}
export type LoteCosechaInput = Omit<LoteCosecha, 'id' | 'costo_acumulado' | 'estado'>

export interface InventarioMovimiento {
  id: number
  lote_id: number
  tipo_movimiento: 'entrada' | 'salida' | 'ajuste' | 'merma' | 'traslado'
  almacen_origen_id: number | null
  almacen_destino_id: number | null
  cantidad: number
  referencia_doc: string | null
  fecha: string
}
export type InventarioMovimientoInput = Omit<InventarioMovimiento, 'id'>

export async function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('POST', '/auth/login', null, { email, password }, 'No se pudo iniciar sesión')
}

export async function getMe(token: string): Promise<Usuario> {
  return request<Usuario>('GET', '/auth/me', token, undefined, 'Sesión inválida o expirada')
}

export const getEmpresas = (token: string) =>
  request<Empresa[]>('GET', '/empresas', token, undefined, 'No se pudieron cargar las empresas')

export const getSucursales = (token: string, empresaId: number) =>
  request<Sucursal[]>('GET', `/empresas/${empresaId}/sucursales`, token, undefined, 'No se pudieron cargar las sucursales')

export const getPlanCuentas = (token: string) =>
  request<PlanCuenta[]>('GET', '/plan-cuentas', token, undefined, 'No se pudo cargar el plan de cuentas')

export const getEmpleados = (token: string) =>
  request<Empleado[]>('GET', '/empleados', token, undefined, 'No se pudieron cargar los empleados')
export const crearEmpleado = (token: string, data: EmpleadoInput) =>
  request<Empleado>('POST', '/empleados', token, data, 'No se pudo crear el empleado')
export const actualizarEmpleado = (token: string, id: number, data: EmpleadoInput) =>
  request<Empleado>('PUT', `/empleados/${id}`, token, data, 'No se pudo actualizar el empleado')
export const eliminarEmpleado = (token: string, id: number) =>
  request<void>('DELETE', `/empleados/${id}`, token, undefined, 'No se pudo eliminar el empleado')

export const getClientes = (token: string) =>
  request<Cliente[]>('GET', '/clientes', token, undefined, 'No se pudieron cargar los clientes')
export const crearCliente = (token: string, data: ClienteInput) =>
  request<Cliente>('POST', '/clientes', token, data, 'No se pudo crear el cliente')
export const actualizarCliente = (token: string, id: number, data: ClienteInput) =>
  request<Cliente>('PUT', `/clientes/${id}`, token, data, 'No se pudo actualizar el cliente')
export const eliminarCliente = (token: string, id: number) =>
  request<void>('DELETE', `/clientes/${id}`, token, undefined, 'No se pudo eliminar el cliente')

export const getAlmacenes = (token: string) =>
  request<Almacen[]>('GET', '/almacenes', token, undefined, 'No se pudieron cargar los almacenes')
export const crearAlmacen = (token: string, data: AlmacenInput) =>
  request<Almacen>('POST', '/almacenes', token, data, 'No se pudo crear el almacén')
export const actualizarAlmacen = (token: string, id: number, data: AlmacenInput) =>
  request<Almacen>('PUT', `/almacenes/${id}`, token, data, 'No se pudo actualizar el almacén')
export const eliminarAlmacen = (token: string, id: number) =>
  request<void>('DELETE', `/almacenes/${id}`, token, undefined, 'No se pudo eliminar el almacén')

export const getLotesCosecha = (token: string) =>
  request<LoteCosecha[]>('GET', '/lotes-cosecha', token, undefined, 'No se pudieron cargar los lotes')
export const crearLoteCosecha = (token: string, data: LoteCosechaInput) =>
  request<LoteCosecha>('POST', '/lotes-cosecha', token, data, 'No se pudo crear el lote')
export const actualizarLoteCosecha = (token: string, id: number, data: LoteCosechaInput) =>
  request<LoteCosecha>('PUT', `/lotes-cosecha/${id}`, token, data, 'No se pudo actualizar el lote')
export const eliminarLoteCosecha = (token: string, id: number) =>
  request<void>('DELETE', `/lotes-cosecha/${id}`, token, undefined, 'No se pudo eliminar el lote')

export const getInventarioMovimientos = (token: string) =>
  request<InventarioMovimiento[]>('GET', '/inventario-movimientos', token, undefined, 'No se pudieron cargar los movimientos')
export const crearInventarioMovimiento = (token: string, data: InventarioMovimientoInput) =>
  request<InventarioMovimiento>('POST', '/inventario-movimientos', token, data, 'No se pudo crear el movimiento')
