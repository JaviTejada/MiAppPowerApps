from pathlib import Path

import cv2
import numpy as np

from src.video_keymoments import Segment, highlight_element, select_key_moments


def test_select_key_moments_detects_keywords():
    segments = [
        Segment(0.0, 1.0, "Hola y bienvenidos"),
        Segment(1.0, 2.0, "Mediante este icono podéis buscar el cliente"),
    ]

    selected = select_key_moments(segments)

    assert len(selected) == 1
    assert "buscar" in selected[0].text.lower()


def test_highlight_element_marks_template(tmp_path: Path):
    frame = np.full((120, 160, 3), 255, dtype=np.uint8)
    cv2.rectangle(frame, (50, 40), (80, 70), (0, 0, 0), -1)
    template = frame[40:70, 50:80]

    frame_path = tmp_path / "frame.png"
    template_path = tmp_path / "template.png"
    out_path = tmp_path / "marked.png"

    cv2.imwrite(str(frame_path), frame)
    cv2.imwrite(str(template_path), template)

    x1, y1, x2, y2 = highlight_element(frame_path, template_path, out_path, threshold=0.8)

    assert out_path.exists()
    assert (x1, y1, x2, y2) == (50, 40, 80, 70)
