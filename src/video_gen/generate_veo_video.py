#!/usr/bin/env python3
"""Generate a video with Veo using a folder of reference images."""

import argparse
import os
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def iter_images(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return sorted(files)


def load_reference_images(
    image_paths: list[Path],
) -> list[types.VideoGenerationReferenceImage]:
    references: list[types.VideoGenerationReferenceImage] = []
    if len(image_paths) > 3:
        print("Warning: Veo supports up to 3 asset reference images; using the first 3.")
        image_paths = image_paths[:3]
    for path in image_paths:
        image = types.Image.from_file(location=str(path))
        references.append(
            types.VideoGenerationReferenceImage(
                image=image,
                reference_type=types.VideoGenerationReferenceType.ASSET,
            )
        )
    return references


def save_video_bytes(result, output_path: Path, client: genai.Client) -> None:
    # The SDK response shape varies by version; handle common fields.
    videos = None
    if hasattr(result, "generated_videos"):
        videos = result.generated_videos
    elif hasattr(result, "videos"):
        videos = result.videos

    if not videos:
        raise RuntimeError("No video content returned from Veo.")

    video_entry = videos[0]
    video = getattr(video_entry, "video", None) or getattr(video_entry, "data", None)
    if not video:
        raise RuntimeError("Video payload missing in Veo response.")

    if getattr(video, "video_bytes", None):
        output_path.write_bytes(video.video_bytes)
        return

    if getattr(client, "_api_client", None) and not client._api_client.vertexai:
        client.files.download(file=video)
        video.save(str(output_path))
        return

    uri = getattr(video, "uri", None)
    if not uri:
        raise RuntimeError("Video payload missing bytes and uri.")

    if uri.startswith("http://") or uri.startswith("https://"):
        urllib.request.urlretrieve(uri, output_path)
        return

    raise RuntimeError(f"Video is stored remotely at {uri}. Download manually.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Veo video from reference images.")
    parser.add_argument("--images", required=True, help="Folder with reference images")
    parser.add_argument("--prompt", required=True, help="Text prompt for the video")
    parser.add_argument("--output", default="veo_output.mp4", help="Output mp4 path")
    parser.add_argument("--model", default="veo-3.1-generate-preview", help="Veo model name")
    parser.add_argument("--duration", type=int, default=8, help="Video duration in seconds")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second (Vertex AI only)")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Missing GOOGLE_API_KEY in environment.")

    image_dir = Path(args.images)
    if not image_dir.is_dir():
        raise SystemExit(f"Image folder not found: {image_dir}")

    image_paths = iter_images(image_dir)
    if not image_paths:
        raise SystemExit("No images found in the folder.")

    reference_images = load_reference_images(image_paths)

    client = genai.Client(api_key=api_key)

    config = types.GenerateVideosConfig(
        duration_seconds=args.duration,
        reference_images=reference_images,
    )
    if getattr(client, "_api_client", None) and getattr(client._api_client, "vertexai", False):
        config.fps = args.fps
    elif args.fps != 24:
        print("Warning: fps is not supported in Gemini API; ignoring --fps.")

    operation = client.models.generate_videos(
        model=args.model,
        source=types.GenerateVideosSource(prompt=args.prompt),
        config=config,
    )

    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)

    if operation.error:
        raise RuntimeError(f"Video generation failed: {operation.error}")

    result = operation.result or operation.response
    save_video_bytes(result, Path(args.output), client)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
