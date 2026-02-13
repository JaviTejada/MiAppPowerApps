# MiAppPowerApps

Aplicación para generar capturas de momentos clave de un vídeo tutorial (con audio/transcripción) y remarcar el elemento visual importante (icono, botón, etc.) en cada captura.

## Arquitectura

- **Backend Python (Flask):** recibe archivos, ejecuta el pipeline y devuelve metadatos.
- **Pipeline OpenCV:** selecciona segmentos clave y marca elementos por template matching.
- **Frontend React (Vite):** interfaz para subir vídeo y ficheros necesarios.

## Qué hace el pipeline

1. Lee una transcripción segmentada con tiempos (`start`, `end`, `text`).
2. Detecta frases clave (por defecto: *icono, botón, buscar, cliente*, etc.).
3. Extrae una captura por cada momento clave.
4. Si hay una plantilla asociada al texto, localiza ese elemento y lo marca con un recuadro rojo.
5. Guarda cada captura individualmente y genera un `capturas.json` con metadatos.

## Estructura de salida

- `output/<job_id>/raw/momento_001.png`
- `output/<job_id>/marked/momento_001.png`
- `output/<job_id>/capturas.json`

## Instalación backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar backend

```bash
python src/api.py
```

Backend disponible en `http://localhost:8000`.

## Instalación frontend

```bash
cd web
npm install
npm run dev
```

Frontend disponible en `http://localhost:5173` (con proxy a `/api`).

## Formato de transcripción

`transcript.json`

```json
{
  "segments": [
    {"start": 5.2, "end": 8.1, "text": "Mediante este icono podéis buscar el cliente"}
  ]
}
```

## Mapa de plantillas

`template_map.json`

```json
{
  "buscar": "icono_buscar.png",
  "cliente": "icono_cliente.png"
}
```

> En la interfaz React puedes subir las imágenes de plantilla en el campo **Plantillas**.

## API principal

`POST /api/process` con `multipart/form-data`:

- `video`: archivo de vídeo
- `transcript`: JSON de segmentos
- `template_map`: JSON trigger->plantilla
- `templates`: (opcional, múltiple) imágenes de iconos/botones
- `threshold`: (opcional) umbral de matching, default `0.7`

## Notas

- Si no encuentra plantilla para un texto, se guarda la captura sin marcar.
- Este MVP usa `template matching`; para UI muy variable se recomienda evolucionar a un detector visual más robusto.
