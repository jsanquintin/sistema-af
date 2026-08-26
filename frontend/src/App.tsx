import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { getEmpresas, getMe, getSucursales, type Empresa, type Sucursal, type Usuario } from '@/lib/api'
import { ConfiguracionEmpresasPage } from '@/pages/ConfiguracionEmpresasPage'
import { LoginPage } from '@/pages/LoginPage'
import { PlanCuentasPage } from '@/pages/PlanCuentasPage'
import { SeccionPlaceholder } from '@/pages/SeccionPlaceholder'
import { SeleccionarEmpresaPage } from '@/pages/SeleccionarEmpresaPage'

const TOKEN_STORAGE_KEY = 'sistema-af.token'
const EMPRESA_STORAGE_KEY = 'sistema-af.empresaId'
const SUCURSAL_STORAGE_KEY = 'sistema-af.sucursalId'

// Secciones sin motor de negocio todavia. Dos categorias, no las mezclamos:
// "bloqueado" depende de una respuesta pendiente del contador (no es tarea
// de codigo); las demas simplemente no se han construido todavia pero no
// tienen ningun gate de negocio -- son el proximo trabajo natural.
const PLACEHOLDERS: { path: string; titulo: string; descripcion: string }[] = [
  {
    path: '/contabilidad/asientos',
    titulo: 'Asientos',
    descripcion:
      'Bloqueado: el motor de asientos está diseñado pero depende de preguntas pendientes con el contador (numeración de comprobantes, saldo de apertura). Ver docs/designs/nucleo-contabilidad-nomina.md.',
  },
  {
    path: '/contabilidad/reportes',
    titulo: 'Reportes',
    descripcion: 'Bloqueado: depende de que existan asientos reales primero.',
  },
  {
    path: '/nomina/empleados',
    titulo: 'Empleados',
    descripcion: 'Diseñado, pendiente de construir — no bloqueado por el contador.',
  },
  {
    path: '/nomina/corridas',
    titulo: 'Nóminas',
    descripcion:
      'Bloqueado: si la nómina es compartida o separada entre Agrocasa y Creixa, y las tablas de ISR/TSS, aún no están confirmadas.',
  },
  {
    path: '/facturacion/clientes',
    titulo: 'Clientes',
    descripcion: 'Diseñado, pendiente de construir — no bloqueado por el contador.',
  },
  {
    path: '/facturacion/facturas',
    titulo: 'Facturas',
    descripcion: 'Bloqueado: falta confirmar si e-CF es obligación legal activa para Agrocasa.',
  },
  {
    path: '/inventario/almacenes',
    titulo: 'Almacenes',
    descripcion: 'Diseñado, pendiente de construir — no bloqueado por el contador.',
  },
  {
    path: '/inventario/movimientos',
    titulo: 'Movimientos',
    descripcion: 'Diseñado, pendiente de construir — no bloqueado por el contador.',
  },
  {
    path: '/inventario/lotes',
    titulo: 'Lotes de Cosecha',
    descripcion:
      'Diseñado, pendiente de construir — no bloqueado por el contador. Sin datos históricos que migrar.',
  },
]

// Resuelve la empresa/sucursal activa sin molestar al usuario cuando la
// respuesta es obvia: una sola empresa, o una sola sucursal, se auto-elige.
// Solo cuando hay mas de una opcion y no hay una eleccion previa valida se
// deja sin resolver, para que la ruta de seleccion manual se muestre.
async function resolverEmpresaYSucursal(
  token: string
): Promise<{ empresa: Empresa | null; sucursal: Sucursal | null }> {
  const empresas = await getEmpresas(token)
  const empresaGuardada = localStorage.getItem(EMPRESA_STORAGE_KEY)
  const empresa =
    empresas.find((e) => String(e.id) === empresaGuardada) ?? (empresas.length === 1 ? empresas[0] : null)

  if (!empresa) return { empresa: null, sucursal: null }
  localStorage.setItem(EMPRESA_STORAGE_KEY, String(empresa.id))

  const sucursales = await getSucursales(token, empresa.id)
  if (sucursales.length === 0) return { empresa, sucursal: null }

  const sucursalGuardada = localStorage.getItem(SUCURSAL_STORAGE_KEY)
  const sucursal =
    sucursales.find((s) => String(s.id) === sucursalGuardada) ?? (sucursales.length === 1 ? sucursales[0] : null)

  if (!sucursal) {
    // Mas de una sucursal y ninguna guardada valida: se deja sin resolver
    // a proposito para forzar el paso de seleccion manual.
    return { empresa: null, sucursal: null }
  }

  localStorage.setItem(SUCURSAL_STORAGE_KEY, String(sucursal.id))
  return { empresa, sucursal }
}

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [checking, setChecking] = useState(false)
  const [empresa, setEmpresa] = useState<Empresa | null>(null)
  const [sucursal, setSucursal] = useState<Sucursal | null>(null)
  // Empieza en true (no false): evita que, justo despues de que `usuario`
  // se resuelva pero antes de que este efecto alcance a correr, la ruta
  // protegida vea "empresa=null" y mande al usuario a /seleccionar-empresa
  // por error incluso cuando la empresa se iba a auto-resolver sola.
  const [resolviendoEmpresa, setResolviendoEmpresa] = useState(true)

  useEffect(() => {
    if (!token) {
      setUsuario(null)
      return
    }
    setChecking(true)
    getMe(token)
      .then(setUsuario)
      .catch(() => {
        // Token invalido o expirado: fail-closed, se descarta y se vuelve al login.
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken(null)
        setUsuario(null)
      })
      .finally(() => setChecking(false))
  }, [token])

  useEffect(() => {
    if (!token || !usuario || empresa) return
    setResolviendoEmpresa(true)
    resolverEmpresaYSucursal(token)
      .then(({ empresa: e, sucursal: s }) => {
        setEmpresa(e)
        setSucursal(s)
      })
      .finally(() => setResolviendoEmpresa(false))
  }, [token, usuario, empresa])

  function handleLoginSuccess(newToken: string) {
    localStorage.setItem(TOKEN_STORAGE_KEY, newToken)
    setToken(newToken)
  }

  function handleSeleccionEmpresa(nuevaEmpresa: Empresa, nuevaSucursal: Sucursal | null) {
    localStorage.setItem(EMPRESA_STORAGE_KEY, String(nuevaEmpresa.id))
    if (nuevaSucursal) localStorage.setItem(SUCURSAL_STORAGE_KEY, String(nuevaSucursal.id))
    else localStorage.removeItem(SUCURSAL_STORAGE_KEY)
    setEmpresa(nuevaEmpresa)
    setSucursal(nuevaSucursal)
  }

  function handleCambiarEmpresa() {
    // No toca el token/sesion -- solo limpia la eleccion guardada para que
    // el efecto de resolucion no la vuelva a auto-elegir de inmediato.
    localStorage.removeItem(EMPRESA_STORAGE_KEY)
    localStorage.removeItem(SUCURSAL_STORAGE_KEY)
    setEmpresa(null)
    setSucursal(null)
    setResolviendoEmpresa(true)
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(EMPRESA_STORAGE_KEY)
    localStorage.removeItem(SUCURSAL_STORAGE_KEY)
    setResolviendoEmpresa(true)
    setToken(null)
    setUsuario(null)
    setEmpresa(null)
    setSucursal(null)
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          token ? (
            <Navigate to="/contabilidad/plan-cuentas" replace />
          ) : (
            <LoginPage onLoginSuccess={handleLoginSuccess} />
          )
        }
      />
      <Route
        path="/seleccionar-empresa"
        element={
          !token ? (
            <Navigate to="/login" replace />
          ) : empresa ? (
            <Navigate to="/contabilidad/plan-cuentas" replace />
          ) : (
            <SeleccionarEmpresaPage token={token} onSeleccionado={handleSeleccionEmpresa} />
          )
        }
      />
      <Route
        element={
          !token ? (
            <Navigate to="/login" replace />
          ) : checking || !usuario || resolviendoEmpresa ? (
            <div className="flex min-h-svh items-center justify-center">
              <p className="text-muted-foreground">Verificando sesión…</p>
            </div>
          ) : !empresa ? (
            <Navigate to="/seleccionar-empresa" replace />
          ) : (
            <AppShell
              usuario={usuario}
              empresa={empresa}
              sucursal={sucursal}
              onLogout={handleLogout}
              onCambiarEmpresa={handleCambiarEmpresa}
            />
          )
        }
      >
        <Route path="/" element={<Navigate to="/contabilidad/plan-cuentas" replace />} />
        <Route path="/contabilidad" element={<Navigate to="/contabilidad/plan-cuentas" replace />} />
        <Route path="/contabilidad/plan-cuentas" element={token && <PlanCuentasPage token={token} />} />
        <Route path="/nomina" element={<Navigate to="/nomina/empleados" replace />} />
        <Route path="/facturacion" element={<Navigate to="/facturacion/clientes" replace />} />
        <Route path="/inventario" element={<Navigate to="/inventario/almacenes" replace />} />
        <Route path="/configuracion" element={<Navigate to="/configuracion/empresas" replace />} />
        <Route
          path="/configuracion/empresas"
          element={token && <ConfiguracionEmpresasPage token={token} />}
        />
        {PLACEHOLDERS.map(({ path, titulo, descripcion }) => (
          <Route key={path} path={path} element={<SeccionPlaceholder titulo={titulo} descripcion={descripcion} />} />
        ))}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
