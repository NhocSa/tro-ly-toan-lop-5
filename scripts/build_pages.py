#!/usr/bin/env python3
"""Build the static GitHub Pages frontend and point it at the Render API."""
import argparse
import json
import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_URL = "https://tro-ly-toan-lop-5.onrender.com"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=["site", "_site"], default="site")
    args = parser.parse_args()

    api_url = os.environ.get("RENDER_API_URL", DEFAULT_API_URL).strip().rstrip("/")
    parsed = urlsplit(api_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path:
        parser.error("RENDER_API_URL must be an HTTPS origin, e.g. https://example.onrender.com")

    output = ROOT / args.output
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "static", output)

    config = {
        "apiBase": api_url,
        "assetBase": ".",
        "homePath": "./index.html",
        "examPath": "./de-thi.html",
    }
    (output / "config.js").write_text(
        "window.MATHBOT_CONFIG = " + json.dumps(config, ensure_ascii=True) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
