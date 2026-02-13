from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2


@dataclass
class Segment:
    start: float
    end: float
    text: str


KEYWORDS = [
    "icono",
    "botón",
    "menu",
    "menú",
    "busca",
    "buscar",
    "cliente",
    "configuración",
    "ajustes",
]


def load_segments(transcript_path: Path) -> list[Segment]:
    """Load transcript segments from JSON.

    Expected format:
    {
      "segments": [
        {"start": 0.1, "end": 1.2, "text": "..."}
      ]
    }
    """
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    segments = []
    for item in data.get("segments", []):
        segments.append(Segment(float(item["start"]), float(item["end"]), str(item["text"])))
    return segments


def select_key_moments(segments: Iterable[Segment], keywords: Iterable[str] = KEYWORDS) -> list[Segment]:
    patterns = [re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE) for keyword in keywords]
    key_segments: list[Segment] = []
    for segment in segments:
        if any(pattern.search(segment.text) for pattern in patterns):
            key_segments.append(segment)
    return key_segments


def capture_frame(video_path: Path, timestamp_s: float, output_path: Path) -> Path:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el vídeo: {video_path}")

    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        raise RuntimeError(f"No se pudo capturar frame en t={timestamp_s:.2f}s")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)
    return output_path


def _match_template(frame, template, threshold: float):
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None
    h, w = template.shape[:2]
    x1, y1 = max_loc
    return x1, y1, x1 + w, y1 + h, max_val


def highlight_element(frame_path: Path, template_path: Path, output_path: Path, threshold: float = 0.7) -> tuple[int, int, int, int]:
    frame = cv2.imread(str(frame_path))
    template = cv2.imread(str(template_path))

    if frame is None:
        raise RuntimeError(f"No se pudo cargar la captura: {frame_path}")
    if template is None:
        raise RuntimeError(f"No se pudo cargar plantilla: {template_path}")

    match = _match_template(frame, template, threshold)
    if match is None:
        raise RuntimeError(
            f"No se encontró el elemento de {template_path.name} (threshold={threshold})"
        )

    x1, y1, x2, y2, _ = match
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)
    return x1, y1, x2, y2


def run_pipeline(
    video_path: Path,
    transcript_path: Path,
    template_map_path: Path,
    output_dir: Path,
    threshold: float,
) -> list[dict]:
    segments = load_segments(transcript_path)
    key_segments = select_key_moments(segments)

    template_map = json.loads(template_map_path.read_text(encoding="utf-8"))
    # Ejemplo: {"cliente": "templates/icono_cliente.png", "buscar": "templates/icono_buscar.png"}

    metadata: list[dict] = []
    for idx, segment in enumerate(key_segments, start=1):
        timestamp = (segment.start + segment.end) / 2
        raw_path = output_dir / "raw" / f"momento_{idx:03d}.png"
        marked_path = output_dir / "marked" / f"momento_{idx:03d}.png"

        capture_frame(video_path, timestamp, raw_path)

        selected_template = None
        for trigger, template_file in template_map.items():
            if re.search(rf"\b{re.escape(trigger)}\b", segment.text, flags=re.IGNORECASE):
                selected_template = Path(template_file)
                break

        bbox = None
        if selected_template and selected_template.exists():
            try:
                bbox = highlight_element(raw_path, selected_template, marked_path, threshold=threshold)
            except RuntimeError:
                marked_path = raw_path
        else:
            marked_path = raw_path

        metadata.append(
            {
                "id": idx,
                "timestamp": round(timestamp, 3),
                "text": segment.text,
                "raw_capture": str(raw_path),
                "marked_capture": str(marked_path),
                "bbox": bbox,
            }
        )

    meta_path = output_dir / "capturas.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrae capturas clave de un vídeo y marca elementos de interés en cada captura."
    )
    parser.add_argument("--video", required=True, type=Path, help="Ruta al vídeo de entrada")
    parser.add_argument("--transcript", required=True, type=Path, help="JSON con segmentos de transcripción")
    parser.add_argument(
        "--template-map",
        required=True,
        type=Path,
        help="JSON trigger->template para localizar iconos/botones",
    )
    parser.add_argument("--output", required=True, type=Path, help="Carpeta de salida")
    parser.add_argument("--threshold", type=float, default=0.7, help="Umbral de matching [0-1]")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    metadata = run_pipeline(
        video_path=args.video,
        transcript_path=args.transcript,
        template_map_path=args.template_map,
        output_dir=args.output,
        threshold=args.threshold,
    )
    print(f"Capturas generadas: {len(metadata)}")
    print(f"Metadatos: {args.output / 'capturas.json'}")


if __name__ == "__main__":
    main()
