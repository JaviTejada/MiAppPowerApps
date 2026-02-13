from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from src.video_keymoments import run_pipeline

app = Flask(__name__)
BASE_OUTPUT_DIR = Path("output")
BASE_OUTPUT_DIR.mkdir(exist_ok=True)


def _save_upload(file_storage, directory: Path) -> Path:
    filename = secure_filename(file_storage.filename or "file")
    destination = directory / filename
    file_storage.save(destination)
    return destination


@app.post("/api/process")
def process_video():
    if "video" not in request.files or "transcript" not in request.files or "template_map" not in request.files:
        return jsonify({"error": "Se requieren video, transcript y template_map"}), 400

    threshold = float(request.form.get("threshold", 0.7))

    with tempfile.TemporaryDirectory(prefix="miapp_upload_") as temp_dir:
        temp_path = Path(temp_dir)
        video_path = _save_upload(request.files["video"], temp_path)
        transcript_path = _save_upload(request.files["transcript"], temp_path)
        template_map_path = _save_upload(request.files["template_map"], temp_path)

        template_dir = temp_path / "templates"
        template_dir.mkdir(exist_ok=True)

        uploaded_templates = request.files.getlist("templates")
        template_name_to_path: dict[str, str] = {}
        for tpl in uploaded_templates:
            if not tpl.filename:
                continue
            saved = _save_upload(tpl, template_dir)
            template_name_to_path[saved.name] = str(saved)

        template_map = json.loads(template_map_path.read_text(encoding="utf-8"))
        normalized_template_map: dict[str, str] = {}
        for trigger, template_ref in template_map.items():
            ref_name = Path(str(template_ref)).name
            if ref_name in template_name_to_path:
                normalized_template_map[trigger] = template_name_to_path[ref_name]
            else:
                normalized_template_map[trigger] = str((template_dir / ref_name).resolve())

        template_map_path.write_text(
            json.dumps(normalized_template_map, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        job_id = video_path.stem.replace(" ", "_")
        output_dir = BASE_OUTPUT_DIR / job_id
        if output_dir.exists():
            shutil.rmtree(output_dir)

        metadata = run_pipeline(
            video_path=video_path,
            transcript_path=transcript_path,
            template_map_path=template_map_path,
            output_dir=output_dir,
            threshold=threshold,
        )

    return jsonify(
        {
            "job_id": job_id,
            "captures": metadata,
            "captures_json": f"/api/output/{job_id}/capturas.json",
        }
    )


@app.get("/api/output/<job_id>/<path:filename>")
def get_output_file(job_id: str, filename: str):
    return send_from_directory(BASE_OUTPUT_DIR / job_id, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
