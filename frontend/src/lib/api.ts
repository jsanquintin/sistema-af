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
  empresa_id: number
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

export interface Obra {
  id: number
  empresa_id: number
  sucursal_id: number
  cliente_id: number
  codigo: string
  nombre: string
  monto_contrato: number
  moneda: string
  fecha_inicio: string
  fecha_fin_estimada: string | null
  costo_acumulado: number
  costo_reconocido: number
  estado: 'en_proceso' | 'cerrada'
}
export type ObraInput = Omit<Obra, 'id' | 'costo_acumulado' | 'costo_reconocido' | 'estado'>

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

export const getPlanCuentas = (token: string, empresaId: number) =>
  request<PlanCuenta[]>(
    'GET',
    `/plan-cuentas?empresa_id=${empresaId}`,
    token,
    undefined,
    'No se pudo cargar el plan de cuentas'
  )

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

export const getObras = (token: string, empresaId: number) =>
  request<Obra[]>('GET', `/obras?empresa_id=${empresaId}`, token, undefined, 'No se pudieron cargar las obras')
export const crearObra = (token: string, data: ObraInput) =>
  request<Obra>('POST', '/obras', token, data, 'No se pudo crear la obra')
export const actualizarObra = (token: string, id: number, data: ObraInput) =>
  request<Obra>('PUT', `/obras/${id}`, token, data, 'No se pudo actualizar la obra')
export const eliminarObra = (token: string, id: number) =>
  request<void>('DELETE', `/obras/${id}`, token, undefined, 'No se pudo eliminar la obra')

export const getInventarioMovimientos = (token: string) =>
  request<InventarioMovimiento[]>('GET', '/inventario-movimientos', token, undefined, 'No se pudieron cargar los movimientos')
export const crearInventarioMovimiento = (token: string, data: InventarioMovimientoInput) =>
  request<InventarioMovimiento>('POST', '/inventario-movimientos', token, data, 'No se pudo crear el movimiento')

// ── Contabilidad: asientos y reglas ────────────────────────────────────

export interface AsientoDetalle {
  id: number
  empresa_id: number
  numero_cta: string
  sucursal_id: number | null
  debcred: 'D' | 'C'
  monto: number
}
export type AsientoDetalleInput = Omit<AsientoDetalle, 'id' | 'empresa_id'>

export interface Asiento {
  id: number
  empresa_id: number
  fecha: string
  origen_tipo: 'factura' | 'nomina' | 'manual' | 'inventario' | 'apertura'
  origen_id: number | null
  descripcion: string | null
  creado_por: string | null
  creado_en: string
  estado: 'borrador' | 'posteado'
  lineas: AsientoDetalle[]
}
export interface AsientoInput {
  fecha: string
  descripcion: string | null
  lineas: AsientoDetalleInput[]
}

export const getAsientos = (token: string, empresaId: number) =>
  request<Asiento[]>('GET', `/asientos?empresa_id=${empresaId}`, token, undefined, 'No se pudieron cargar los asientos')
export const crearAsiento = (token: string, empresaId: number, data: AsientoInput) =>
  request<Asiento>('POST', `/asientos?empresa_id=${empresaId}`, token, data, 'No se pudo crear el asiento')
export const postearAsiento = (token: string, asientoId: number) =>
  request<Asiento>('POST', `/asientos/${asientoId}/postear`, token, {}, 'No se pudo postear el asiento')

export interface ReglaContabilizacion {
  id: number
  empresa_id: number
  origen_tipo: string
  codigo_evento: string
  numero_cta: string
  debcred: 'D' | 'C'
}
export type ReglaContabilizacionInput = Omit<ReglaContabilizacion, 'id'>

export const getReglasContabilizacion = (token: string, empresaId: number) =>
  request<ReglaContabilizacion[]>(
    'GET',
    `/reglas-contabilizacion?empresa_id=${empresaId}`,
    token,
    undefined,
    'No se pudieron cargar las reglas de contabilización'
  )
export const crearReglaContabilizacion = (token: string, data: ReglaContabilizacionInput) =>
  request<ReglaContabilizacion>('POST', '/reglas-contabilizacion', token, data, 'No se pudo crear la regla')
export const eliminarReglaContabilizacion = (token: string, id: number) =>
  request<void>('DELETE', `/reglas-contabilizacion/${id}`, token, undefined, 'No se pudo eliminar la regla')

export interface BalanceComprobacionLinea {
  numero_cta: string
  nombre: string
  debe: number
  haber: number
  saldo: number
}

export const getBalanceComprobacion = (token: string, empresaId: number, desde: string, hasta: string) =>
  request<BalanceComprobacionLinea[]>(
    'GET',
    `/reportes/balance-comprobacion?empresa_id=${empresaId}&desde=${desde}&hasta=${hasta}`,
    token,
    undefined,
    'No se pudo generar el balance de comprobación'
  )

// ── Nómina: corridas y cálculo ──────────────────────────────────────────

export interface NominaCorrida {
  id: number
  empresa_id: number
  sucursal_id: number | null
  codigo: string
  nombre: string
  periodo_inicio: string
  periodo_fin: string
  incluye_tss: boolean
  costeable_tipo: 'lote' | 'obra' | null
  costeable_id: number | null
  cerrada: boolean
  asiento_id: number | null
}
export type NominaCorridaInput = Omit<NominaCorrida, 'id' | 'cerrada' | 'asiento_id'>

export interface NominaDetalle {
  id: number
  empleado_id: number
  sucursal_id: number | null
  dias_unidades: number | null
  monto_bruto: number
  retencion_isr: number
  retencion_tss: number
  monto_neto: number
}

export const getNominaCorridas = (token: string, empresaId: number) =>
  request<NominaCorrida[]>(
    'GET',
    `/nomina-corridas?empresa_id=${empresaId}`,
    token,
    undefined,
    'No se pudieron cargar las corridas de nómina'
  )
export const crearNominaCorrida = (token: string, data: NominaCorridaInput) =>
  request<NominaCorrida>('POST', '/nomina-corridas', token, data, 'No se pudo crear la corrida')
export const getNominaDetalle = (token: string, corridaId: number) =>
  request<NominaDetalle[]>(
    'GET',
    `/nomina-corridas/${corridaId}/detalle`,
    token,
    undefined,
    'No se pudo cargar el detalle de la corrida'
  )
export const calcularNomina = (token: string, corridaId: number, diasPorEmpleado: Record<number, number>) =>
  request<NominaDetalle[]>(
    'POST',
    `/nomina-corridas/${corridaId}/calcular`,
    token,
    { dias_por_empleado: diasPorEmpleado },
    'No se pudo calcular la nómina'
  )
export const cerrarNomina = (token: string, corridaId: number) =>
  request<NominaCorrida>('POST', `/nomina-corridas/${corridaId}/cerrar`, token, {}, 'No se pudo cerrar la corrida')

// ── Facturación ──────────────────────────────────────────────────────────

export interface FacturaDetalle {
  id: number
  descripcion: string
  cantidad: number
  precio_unitario: number
  monto: number
}
export type FacturaDetalleInput = Omit<FacturaDetalle, 'id' | 'monto'>

export interface Factura {
  id: number
  empresa_id: number
  sucursal_id: number
  cliente_id: number
  tipo_factura: 'local' | 'exportacion'
  e_ncf: string | null
  tipo_ecf: string | null
  fecha_emision: string
  moneda: string
  subtotal: number
  itbis_pct: number
  itbis_monto: number
  total: number
  estado_ecf: 'pendiente' | 'aceptado' | 'rechazado' | 'no_aplica'
  lote_id: number | null
  obra_id: number | null
  asiento_id: number | null
  lineas: FacturaDetalle[]
}
export interface FacturaInput {
  empresa_id: number
  sucursal_id: number
  cliente_id: number
  tipo_factura: 'local' | 'exportacion'
  fecha_emision: string
  moneda: string
  lote_id: number | null
  obra_id: number | null
  lineas: FacturaDetalleInput[]
}

export const getFacturas = (token: string, empresaId: number) =>
  request<Factura[]>('GET', `/facturas?empresa_id=${empresaId}`, token, undefined, 'No se pudieron cargar las facturas')
export const crearFactura = (token: string, data: FacturaInput) =>
  request<Factura>('POST', '/facturas', token, data, 'No se pudo crear la factura')

// ── Parámetros de nómina (referencia, solo lectura) ─────────────────────

export interface ParametroNomina {
  id: number
  anio_fiscal: number
  isr_tramo1_hasta: number
  isr_tramo2_hasta: number
  isr_tramo3_hasta: number
  isr_tramo2_tasa: number
  isr_tramo3_tasa: number
  isr_tramo4_tasa: number
  tss_sfs_empleado_pct: number
  tss_sfs_patronal_pct: number
  tss_afp_empleado_pct: number
  tss_afp_patronal_pct: number
  tss_riesgos_laborales_pct: number
  tss_infotep_pct: number
  tss_tope_sfs_salarios_minimos: number
  tss_tope_afp_salarios_minimos: number
  salario_minimo_referencia: number
  notas: string | null
}

export const getParametrosNomina = (token: string) =>
  request<ParametroNomina[]>('GET', '/parametros-nomina', token, undefined, 'No se pudieron cargar los parámetros de nómina')
