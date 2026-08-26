import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import type { Seccion } from '@/components/layout/Sidebar'
import { getEmpresas, getMe, getSucursales, type Empresa, type Sucursal, type Usuario } from '@/lib/api'
import { LoginPage } from '@/pages/LoginPage'
import { SeccionPlaceholder } from '@/pages/SeccionPlaceholder'
import { SeleccionarEmpresaPage } from '@/pages/SeleccionarEmpresaPage'

const TOKEN_STORAGE_KEY = 'sistema-af.token'
const EMPRESA_STORAGE_KEY = 'sistema-af.empresaId'
const SUCURSAL_STORAGE_KEY = 'sistema-af.sucursalId'

const PLACEHOLDERS: Record<Seccion, { titulo: string; descripcion: string }> = {
  contabilidad: {
    titulo: 'Contabilidad',
    descripcion:
      'El motor de asientos está diseñado pero bloqueado hasta cerrar las preguntas pendientes con el contador (ver docs/designs/nucleo-contabilidad-nomina.md).',
  },
  nomina: {
    titulo: 'Nómina',
    descripcion:
      'Bloqueado por el mismo gate que contabilidad: nómina compartida/separada y las tablas de ISR/TSS aún no están confirmadas.',
  },
  facturacion: {
    titulo: 'Facturación',
    descripcion:
      'Diseño nuevo — Soluflex nunca tuvo esto en uso real. Pendiente confirmar si e-CF es obligación legal activa para Agrocasa.',
  },
  inventario: {
    titulo: 'Inventario',
    descripcion: 'Diseño nuevo por finca/lote de cosecha. Sin datos históricos que migrar.',
  },
}

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
          token ? <Navigate to="/contabilidad" replace /> : <LoginPage onLoginSuccess={handleLoginSuccess} />
        }
      />
      <Route
        path="/seleccionar-empresa"
        element={
          !token ? (
            <Navigate to="/login" replace />
          ) : empresa ? (
            <Navigate to="/contabilidad" replace />
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
        <Route path="/" element={<Navigate to="/contabilidad" replace />} />
        <Route path="/contabilidad" element={<SeccionPlaceholder {...PLACEHOLDERS.contabilidad} />} />
        <Route path="/nomina" element={<SeccionPlaceholder {...PLACEHOLDERS.nomina} />} />
        <Route path="/facturacion" element={<SeccionPlaceholder {...PLACEHOLDERS.facturacion} />} />
        <Route path="/inventario" element={<SeccionPlaceholder {...PLACEHOLDERS.inventario} />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
