import base64
import json
import os
import shutil
from pathlib import Path
from typing import List

from openai import OpenAI

IMAGE_EXTS = (".jpg", ".jpeg", ".png")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def list_images(folder: str) -> List[Path]:
    return sorted([
        f for f in Path(folder).iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ])


def call_image_edit(image_path: Path, prompt: str, out_path: Path):
    with open(image_path, "rb") as f:
        result = client.images.edit(
            model="gpt-image-1",
            image=f,
            prompt=prompt,
            size="1024x1024"
        )

    out_path.write_bytes(base64.b64decode(result.data[0].b64_json))


def run_style(folder2: str, folder3: str):
    Path(folder3).mkdir(exist_ok=True)

    styles = {
        0: "Ghibli-inspired anime style, soft watercolor, warm colors, cinematic lighting",
        1: "1980s film photography, warm tones, subtle grain, vintage look"
    }

    instructions = []

    images = list_images(folder2)

    for index, img in enumerate(images):
        mode = index % 3
        print(f"[Stylist] {img.name} -> mode {mode}")

        if mode == 2:
            shutil.copy2(img, Path(folder3) / img.name)
            instructions.append({
                "input": img.name,
                "output": img.name,
                "style": "none"
            })
            continue

        prompt = (
            f"Transform this photo into: {styles[mode]}. "
            "Keep same subject and framing. No text."
        )

        out_name = f"{img.stem}__styled.png"
        out_path = Path(folder3) / out_name

        call_image_edit(img, prompt, out_path)

        instructions.append({
            "input": img.name,
            "output": out_name,
            "style": "ghibli" if mode == 0 else "1980s"
        })

    with open(Path(folder3) / "instructions.json", "w") as f:
        json.dump(instructions, f, indent=2)


if __name__ == "__main__":
    run_style("./curated_photos", "./styled_photos")
