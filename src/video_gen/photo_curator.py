import base64
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


def get_media_type(path: Path) -> str:
    return "image/jpeg" if path.suffix.lower() != ".png" else "image/png"


def is_interesting(image_path: Path) -> bool:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    prompt = (
        "Is this a good event photo worth keeping for a highlight video?\n\n"
        "Answer Yes ONLY if:\n"
        "- The subject is clear and in focus\n"
        "- Faces or key event elements are visible\n"
        "- The moment feels meaningful or memorable\n"
        "- Lighting and composition are acceptable\n\n"
        "Answer No if ANY of the following:\n"
        "- Blurry or out of focus\n"
        "- Too dark, too bright, or washed out\n"
        "- Accidental or irrelevant shot (floor, wall, hand, random object)\n"
        "- Duplicate or near-duplicate\n"
        "- Poor expressions (eyes closed, awkward pose)\n\n"
        "Reply with ONLY one word:\n"
        "Yes or No"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{get_media_type(image_path)};base64,{image_data}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        max_tokens=5
    )

    text = (response.choices[0].message.content or "").strip().lower()

    # Robust decision
    if text.startswith("yes"):
        return True
    if text.startswith("no"):
        return False
    if "yes" in text and "no" not in text:
        return True
    return False


def run_curate(folder1: str, folder2: str):
    Path(folder2).mkdir(exist_ok=True)

    for img in list_images(folder1):
        print("[Curator] checking:", img.name)
        if is_interesting(img):
            shutil.copy2(img, Path(folder2) / img.name)


if __name__ == "__main__":
    run_curate("./raw_photos", "./curated_photos")
