import { useState, useEffect } from 'react'

const STEPS = [
  'Enviando pregunta en lenguaje natural',
  'Generando embedding vectorial',
  'Comparación semántica con contexto',
  'Recuperando esquema relevante (RAG)',
  'Construyendo prompt enriquecido',
  'Generando SQL con LLM',
  'Pasando guardrails de seguridad',
  'Ejecutando consulta en base de datos',
  'Formateando respuesta en lenguaje natural',
]

function ThinkingDots() {
  return (
    <span style={{ display: 'inline-flex', gap: 3, alignItems: 'center', marginLeft: 4 }}>
      {(['dot1', 'dot2', 'dot3'] as const).map((anim, i) => (
        <span key={i} style={{
          width: 4, height: 4, borderRadius: '50%',
          background: 'currentColor', display: 'inline-block',
          animation: `${anim} 1.2s ease-in-out infinite`,
        }} />
      ))}
    </span>
  )
}

function ThinkingBlob({ active }: { active: boolean }) {
  const color = 'var(--purple)'
  return (
    <div style={{
      width: 34, height: 34, flexShrink: 0,
      position: 'relative', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        position: 'absolute', inset: -4, borderRadius: '50%',
        background: `radial-gradient(circle, rgba(124,58,237,0.16) 0%, transparent 70%)`,
        animation: active ? 'breathe 2s ease-in-out infinite' : 'none',
      }} />
      <div style={{
        width: 34, height: 34,
        background: `radial-gradient(135deg, ${color} 0%, rgba(124,58,237,0.53) 60%, rgba(124,58,237,0.2) 100%)`,
        animation: active
          ? 'blob-drift 3s ease-in-out infinite, breathe 2s ease-in-out infinite'
          : 'none',
        opacity: active ? 1 : 0.55,
        transition: 'opacity 0.5s',
        boxShadow: active ? '0 0 18px rgba(124,58,237,0.33)' : 'none',
      }} />
    </div>
  )
}

interface PipelineLoaderProps {
  active: boolean
}

export function PipelineLoader({ active }: PipelineLoaderProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [exiting, setExiting] = useState(false)

  useEffect(() => {
    if (!active) { setCurrentStep(0); setExiting(false); return }
    const interval = setInterval(() => {
      setExiting(true)
      setTimeout(() => {
        setCurrentStep(s => (s + 1) % STEPS.length)
        setExiting(false)
      }, 250)
    }, 900)
    return () => clearInterval(interval)
  }, [active])

  return (
    <div style={{
      margin: '20px 0',
      background: 'var(--surface)',
      border: `1px solid ${active ? 'rgba(124,58,237,0.19)' : 'rgba(34,197,94,0.2)'}`,
      borderRadius: 14,
      padding: '16px 20px',
      display: 'flex', alignItems: 'center', gap: 16,
      animation: 'glow-in 0.35s ease',
      transition: 'border-color 0.6s',
    }}>
      <ThinkingBlob active={active} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13.5,
          fontFamily: 'var(--font-body)',
          fontWeight: 400,
          color: active ? 'var(--text-dim)' : '#4ade80',
          display: 'flex', alignItems: 'center', flexWrap: 'wrap' as const,
          animation: exiting ? 'word-out 0.25s ease forwards' : 'word-in 0.35s ease forwards',
          transition: 'color 0.5s',
          minHeight: 22,
        }}>
          {active ? (
            <><span>{STEPS[currentStep]}</span><ThinkingDots /></>
          ) : (
            <span style={{ color: '#4ade80', fontWeight: 500 }}>Respuesta lista ✓</span>
          )}
        </div>
      </div>
    </div>
  )
}
