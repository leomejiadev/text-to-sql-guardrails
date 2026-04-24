import { useState } from 'react'

const DB_SECTIONS = [
  { icon: '👥', label: 'Clientes',    detail: '200 clientes · 26 ciudades · 12 países · membresías standard, silver, gold + puntos de fidelidad' },
  { icon: '🛒', label: 'Ventas',      detail: '500 órdenes entre ene 2024 – mar 2025 · detalle de productos, descuentos y métodos de pago' },
  { icon: '🪴', label: 'Sucursales',  detail: '30 locales activos en 5 continentes, cada uno con su gerente asignado' },
  { icon: '👔', label: 'Empleados',   detail: '100 empleados con roles, salarios y departamentos' },
  { icon: '☕', label: 'Productos',   detail: '30 ítems del menú – bebidas calientes, frías, comida, merchandise – con precio y costo' },
  { icon: '📦', label: 'Inventario',  detail: 'Stock por producto por sucursal en tiempo real' },
]

export function DBContext() {
  const [open, setOpen] = useState(false)

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      overflow: 'hidden',
      marginBottom: 18,
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', background: 'transparent', border: 'none',
          padding: '13px 18px', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          fontFamily: 'var(--font-body)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 18, lineHeight: 1 }}>☕</span>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
              StarBrew Coffee · base de datos demo
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 1 }}>
              13 tablas · cadena de cafeterías global · datos sintéticos realistas
            </div>
          </div>
        </div>
        <span style={{
          fontSize: 11, color: 'var(--text-muted)',
          transition: 'transform 0.25s',
          transform: open ? 'rotate(180deg)' : 'none',
          marginLeft: 12, flexShrink: 0,
        }}>▾</span>
      </button>

      {open && (
        <div style={{
          borderTop: '1px solid var(--border)',
          animation: 'slide-down 0.3s ease',
          overflow: 'hidden',
        }}>
          <div style={{ padding: '16px 18px 16px' }}>
            <div style={{
              fontSize: 10.5, fontWeight: 700, letterSpacing: '0.1em',
              textTransform: 'uppercase' as const, color: 'var(--text-muted)', marginBottom: 10,
            }}>
              Lo que podés consultar
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: 8,
            }}>
              {DB_SECTIONS.map(s => (
                <div key={s.label} style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border)',
                  borderRadius: 8, padding: '10px 12px',
                  display: 'flex', gap: 10, alignItems: 'flex-start',
                }}>
                  <span style={{ fontSize: 15, lineHeight: 1.3, flexShrink: 0 }}>{s.icon}</span>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>
                      {s.label}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      {s.detail}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
