import { useState } from 'react'

const initial = {
  video: null,
  transcript: null,
  template_map: null,
  templates: []
}

export default function App() {
  const [files, setFiles] = useState(initial)
  const [threshold, setThreshold] = useState(0.7)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onFile = (key) => (event) => {
    const value = key === 'templates' ? Array.from(event.target.files || []) : event.target.files?.[0] ?? null
    setFiles((prev) => ({ ...prev, [key]: value }))
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setResult(null)

    if (!files.video || !files.transcript || !files.template_map) {
      setError('Debes subir vídeo, transcript y template_map.')
      return
    }

    const form = new FormData()
    form.append('video', files.video)
    form.append('transcript', files.transcript)
    form.append('template_map', files.template_map)
    form.append('threshold', String(threshold))
    files.templates.forEach((tpl) => form.append('templates', tpl))

    try {
      setLoading(true)
      const response = await fetch('/api/process', { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'No se pudo procesar')
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>Capturas clave de vídeo</h1>
      <p>Sube el vídeo y los archivos de configuración para generar capturas individuales con marcado.</p>

      <form onSubmit={onSubmit} className="card">
        <label>
          Vídeo
          <input type="file" accept="video/*" onChange={onFile('video')} required />
        </label>

        <label>
          Transcripción (JSON)
          <input type="file" accept="application/json" onChange={onFile('transcript')} required />
        </label>

        <label>
          Template map (JSON)
          <input type="file" accept="application/json" onChange={onFile('template_map')} required />
        </label>

        <label>
          Plantillas (opcional, múltiples PNG/JPG)
          <input type="file" accept="image/*" multiple onChange={onFile('templates')} />
        </label>

        <label>
          Umbral: {threshold}
          <input
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
        </label>

        <button type="submit" disabled={loading}>{loading ? 'Procesando...' : 'Procesar vídeo'}</button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="card">
          <h2>Resultado</h2>
          <p>Job: <strong>{result.job_id}</strong></p>
          <p>Capturas generadas: <strong>{result.captures.length}</strong></p>
          <ul>
            {result.captures.map((item) => (
              <li key={item.id}>
                t={item.timestamp}s — {item.text}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  )
}
