#!/usr/bin/env python3
"""
Orchestrator Agent for Event Video Generation Pipeline

This orchestrator coordinates multiple agents to create a polished event video:
1. Photo Curator: Filters raw photos to keep only quality shots
2. Style Generator: Applies artistic styles to curated photos
3. Video Generator: Creates either a slideshow or AI-generated video

Usage:
    python orchestrator.py --raw-photos ./raw_photos --output-video final.mp4 --mode slideshow
    python orchestrator.py --raw-photos ./raw_photos --output-video final.mp4 --mode veo --prompt "A heartwarming journey through the event"
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Literal

# Import the agent modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from photo.photo_curator import run as run_curator
from photo.styled_photo_generator import run as run_stylist
from video_gen.create_slideshow import create_slideshow
from video_gen.generate_veo_video import (
    iter_images,
    load_reference_images,
    save_video_bytes,
)


class EventVideoOrchestrator:
    """Orchestrates the complete event video generation pipeline."""

    def __init__(
        self,
        raw_photos_dir: str,
        output_video: str,
        work_dir: str = "./pipeline_work",
        audio_path: str | None = None,
        cleanup: bool = True,
    ):
        self.raw_photos_dir = Path(raw_photos_dir)
        self.output_video = Path(output_video)
        self.work_dir = Path(work_dir)
        self.audio_path = audio_path
        self.cleanup = cleanup

        # Define working directories
        self.curated_dir = self.work_dir / "curated_photos"
        self.styled_dir = self.work_dir / "styled_photos"

        self.stats = {
            "raw_count": 0,
            "curated_count": 0,
            "styled_count": 0,
            "video_generated": False,
        }

    def setup_workspace(self):
        """Create necessary directories."""
        print("\n[Orchestrator] Setting up workspace...")
        self.work_dir.mkdir(exist_ok=True)
        self.curated_dir.mkdir(exist_ok=True)
        self.styled_dir.mkdir(exist_ok=True)

    def run_curation_agent(self):
        """Execute the photo curator agent."""
        print("\n" + "=" * 60)
        print("[Orchestrator] Stage 1: Running Photo Curator Agent")
        print("=" * 60)

        if not self.raw_photos_dir.exists():
            raise FileNotFoundError(
                f"Raw photos directory not found: {self.raw_photos_dir}"
            )

        raw_images = (
            list(self.raw_photos_dir.glob("*.[jJ][pP][gG]"))
            + list(self.raw_photos_dir.glob("*.[jJ][pP][eE][gG]"))
            + list(self.raw_photos_dir.glob("*.[pP][nN][gG]"))
        )

        self.stats["raw_count"] = len(raw_images)
        print(f"[Orchestrator] Found {self.stats['raw_count']} raw photos")

        if self.stats["raw_count"] == 0:
            raise ValueError("No images found in raw photos directory")

        run_curator(str(self.raw_photos_dir), str(self.curated_dir))

        curated_images = (
            list(self.curated_dir.glob("*.jpg"))
            + list(self.curated_dir.glob("*.jpeg"))
            + list(self.curated_dir.glob("*.png"))
        )
        self.stats["curated_count"] = len(curated_images)

        print(
            f"[Orchestrator] ✓ Curation complete: {self.stats['curated_count']}/{self.stats['raw_count']} photos kept"
        )

        if self.stats["curated_count"] == 0:
            raise ValueError(
                "No photos passed curation. Try with different/better quality photos."
            )

    def run_styling_agent(self):
        """Execute the style generator agent."""
        print("\n" + "=" * 60)
        print("[Orchestrator] Stage 2: Running Style Generator Agent")
        print("=" * 60)

        run_stylist(str(self.curated_dir), str(self.styled_dir))

        styled_images = (
            list(self.styled_dir.glob("*.jpg"))
            + list(self.styled_dir.glob("*.jpeg"))
            + list(self.styled_dir.glob("*.png"))
        )
        self.stats["styled_count"] = len(styled_images)

        print(
            f"[Orchestrator] ✓ Styling complete: {self.stats['styled_count']} photos ready"
        )

        # Load and display styling summary
        instructions_file = self.styled_dir / "instructions.json"
        if instructions_file.exists():
            with open(instructions_file) as f:
                instructions = json.load(f)
            style_counts = {}
            for item in instructions:
                style = item.get("style", "unknown")
                style_counts[style] = style_counts.get(style, 0) + 1
            print(f"[Orchestrator] Style breakdown: {style_counts}")

    def run_slideshow_generator(
        self,
        fps: int = 30,
        seconds_per_image: float = 3.0,
        crossfade: float = 0.4,
    ):
        """Generate a slideshow video from styled photos."""
        print("\n" + "=" * 60)
        print("[Orchestrator] Stage 3: Generating Slideshow Video")
        print("=" * 60)

        output = create_slideshow(
            images_dir=self.styled_dir,
            audio_path=self.audio_path,
            out_path=str(self.output_video),
            fps=fps,
            seconds_per_image=seconds_per_image,
            crossfade=crossfade,
        )

        self.stats["video_generated"] = True
        print(f"[Orchestrator] ✓ Slideshow generated: {output}")

    def run_veo_generator(
        self,
        prompt: str,
        model: str = "veo-3.1-generate-preview",
        duration: int = 8,
        fps: int = 24,
    ):
        """Generate an AI video using Veo with styled photos as references."""
        print("\n" + "=" * 60)
        print("[Orchestrator] Stage 3: Generating Veo AI Video")
        print("=" * 60)

        import os
        import time

        from dotenv import load_dotenv
        from google import genai
        from google.genai import types

        load_dotenv()
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise SystemExit("Missing GOOGLE_API_KEY in environment.")

        # Use styled photos as reference images
        image_paths = iter_images(self.styled_dir)
        if not image_paths:
            raise ValueError("No styled images available for Veo generation")

        print(f"[Orchestrator] Using {len(image_paths)} styled photos as references")

        reference_images = load_reference_images(image_paths)

        client = genai.Client(api_key=api_key)

        config = types.GenerateVideosConfig(
            duration_seconds=duration,
            reference_images=reference_images,
        )

        if getattr(client, "_api_client", None) and getattr(
            client._api_client, "vertexai", False
        ):
            config.fps = fps
        elif fps != 24:
            print("[Orchestrator] Warning: fps not supported in Gemini API")

        print(f"[Orchestrator] Prompt: {prompt}")
        print(
            f"[Orchestrator] Requesting video generation (this may take several minutes)..."
        )

        operation = client.models.generate_videos(
            model=model,
            source=types.GenerateVideosSource(prompt=prompt),
            config=config,
        )

        # Poll for completion
        dots = 0
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation)
            dots = (dots + 1) % 4
            print(
                f"\r[Orchestrator] Generating video{'.' * dots}   ", end="", flush=True
            )

        print()  # New line after progress

        if operation.error:
            raise RuntimeError(f"Video generation failed: {operation.error}")

        result = operation.result or operation.response
        save_video_bytes(result, self.output_video, client)

        self.stats["video_generated"] = True
        print(f"[Orchestrator] ✓ Veo video generated: {self.output_video}")

    def cleanup_workspace(self):
        """Remove intermediate files if cleanup is enabled."""
        if not self.cleanup:
            print(f"[Orchestrator] Workspace preserved at: {self.work_dir}")
            return

        print("\n[Orchestrator] Cleaning up workspace...")
        try:
            shutil.rmtree(self.work_dir)
            print("[Orchestrator] ✓ Workspace cleaned")
        except Exception as e:
            print(f"[Orchestrator] Warning: Could not clean workspace: {e}")

    def print_summary(self):
        """Print pipeline execution summary."""
        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Raw photos processed:     {self.stats['raw_count']}")
        print(f"Photos after curation:    {self.stats['curated_count']}")
        print(f"Photos after styling:     {self.stats['styled_count']}")
        print(
            f"Video generated:          {'✓' if self.stats['video_generated'] else '✗'}"
        )
        if self.stats["video_generated"]:
            print(f"Output location:          {self.output_video}")
        print("=" * 60)

    def run_pipeline(
        self,
        mode: Literal["slideshow", "veo"],
        veo_prompt: str | None = None,
        slideshow_config: dict | None = None,
        veo_config: dict | None = None,
    ):
        """Execute the complete pipeline."""
        try:
            self.setup_workspace()
            self.run_curation_agent()
            self.run_styling_agent()

            if mode == "slideshow":
                config = slideshow_config or {}
                self.run_slideshow_generator(**config)
            elif mode == "veo":
                if not veo_prompt:
                    raise ValueError("Veo mode requires a prompt")
                config = veo_config or {}
                self.run_veo_generator(prompt=veo_prompt, **config)
            else:
                raise ValueError(f"Unknown mode: {mode}")

            self.print_summary()

        except Exception as e:
            print(f"\n[Orchestrator] ✗ Pipeline failed: {e}")
            raise
        finally:
            if self.cleanup:
                self.cleanup_workspace()


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate event video generation from raw photos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a slideshow with music
  python orchestrator.py --raw-photos ./raw_photos --output final.mp4 --mode slideshow --audio music.mp3

  # Generate an AI video with Veo
  python orchestrator.py --raw-photos ./raw_photos --output final.mp4 --mode veo --prompt "A beautiful celebration"

  # Custom slideshow settings
  python orchestrator.py --raw-photos ./raw_photos --output final.mp4 --mode slideshow --seconds-per-image 4 --fps 60

  # Keep intermediate files
  python orchestrator.py --raw-photos ./raw_photos --output final.mp4 --mode slideshow --no-cleanup
        """,
    )

    # Required arguments
    parser.add_argument(
        "--raw-photos",
        required=True,
        help="Directory containing raw event photos",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output video path (e.g., final.mp4)",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["slideshow", "veo"],
        help="Video generation mode: slideshow or veo (AI-generated)",
    )

    # Optional arguments
    parser.add_argument(
        "--work-dir",
        default="./pipeline_work",
        help="Working directory for intermediate files (default: ./pipeline_work)",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep intermediate files after completion",
    )

    # Slideshow-specific arguments
    slideshow_group = parser.add_argument_group("slideshow options")
    slideshow_group.add_argument(
        "--audio",
        help="Audio file for slideshow (e.g., music.mp3)",
    )
    slideshow_group.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second for slideshow (default: 30)",
    )
    slideshow_group.add_argument(
        "--seconds-per-image",
        type=float,
        default=3.0,
        help="Duration each photo is shown (default: 3.0)",
    )
    slideshow_group.add_argument(
        "--crossfade",
        type=float,
        default=0.4,
        help="Crossfade duration between photos (default: 0.4)",
    )

    # Veo-specific arguments
    veo_group = parser.add_argument_group("veo options")
    veo_group.add_argument(
        "--prompt",
        help="Text prompt for Veo video generation (required for veo mode)",
    )
    veo_group.add_argument(
        "--veo-model",
        default="veo-3.1-generate-preview",
        help="Veo model name (default: veo-3.1-generate-preview)",
    )
    veo_group.add_argument(
        "--duration",
        type=int,
        default=8,
        help="Veo video duration in seconds (default: 8)",
    )
    veo_group.add_argument(
        "--veo-fps",
        type=int,
        default=24,
        help="Veo FPS (Vertex AI only, default: 24)",
    )

    args = parser.parse_args()

    # Validate mode-specific requirements
    if args.mode == "veo" and not args.prompt:
        parser.error("--prompt is required when using --mode veo")

    # Create orchestrator
    orchestrator = EventVideoOrchestrator(
        raw_photos_dir=args.raw_photos,
        output_video=args.output,
        work_dir=args.work_dir,
        audio_path=args.audio,
        cleanup=not args.no_cleanup,
    )

    # Prepare configs
    slideshow_config = {
        "fps": args.fps,
        "seconds_per_image": args.seconds_per_image,
        "crossfade": args.crossfade,
    }

    veo_config = {
        "model": args.veo_model,
        "duration": args.duration,
        "fps": args.veo_fps,
    }

    # Run pipeline
    orchestrator.run_pipeline(
        mode=args.mode,
        veo_prompt=args.prompt,
        slideshow_config=slideshow_config,
        veo_config=veo_config,
    )


if __name__ == "__main__":
    main()
