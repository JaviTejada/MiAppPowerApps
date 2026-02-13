# MiAppPowerApps

MVP para generar capturas de momentos clave de un vídeo tutorial (con audio/transcripción) y remarcar el elemento visual importante (icono, botón, etc.) en cada captura.

## Qué hace

1. Lee una transcripción segmentada con tiempos (`start`, `end`, `text`).
2. Detecta frases clave (por defecto: *icono, botón, buscar, cliente*, etc.).
3. Extrae una captura por cada momento clave.
4. Si hay una plantilla asociada al texto (template de icono/botón), localiza ese elemento y lo marca con un recuadro rojo.
5. Guarda cada captura individualmente y genera un `capturas.json` con metadatos.

## Estructura de salida

- `output/raw/momento_001.png` ...
- `output/marked/momento_001.png` ...
- `output/capturas.json`

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
  "buscar": "templates/icono_buscar.png",
  "cliente": "templates/icono_cliente.png"
}
```

## Uso

```bash
python src/video_keymoments.py \
  --video demo.mp4 \
  --transcript transcript.json \
  --template-map template_map.json \
  --output output \
  --threshold 0.7
```

## Notas

- Para mayor precisión, recorta plantillas limpias (sin fondos extra) del icono/botón.
- Si no encuentra plantilla para un texto, se guarda la captura sin marcar.
- Este MVP usa `template matching`; para UI muy variable se recomienda evolucionar a un detector visual más robusto.
