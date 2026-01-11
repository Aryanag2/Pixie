from __future__ import annotations

import argparse
from pathlib import Path


def _import_moviepy_components():
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, afx  # type: ignore
        return AudioFileClip, ImageClip, concatenate_videoclips, afx
    except Exception:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, afx  # type: ignore
        return AudioFileClip, ImageClip, concatenate_videoclips, afx


def create_slideshow(
    *,
    images_dir: Path,
    audio_path: str | None,
    out_path: str,
    fps: int,
    seconds_per_image: float,
    crossfade: float,
) -> str:
    AudioFileClip, ImageClip, concatenate_videoclips, afx = _import_moviepy_components()
    image_files = sorted(
        [
            p
            for p in images_dir.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
    )
    if not image_files:
        raise ValueError(f"No images found in {images_dir}")

    clips = []
    for f in image_files:
        clip = ImageClip(str(f))
        if hasattr(clip, "with_duration"):
            clip = clip.with_duration(seconds_per_image)
        else:
            clip = clip.set_duration(seconds_per_image)
        clips.append(clip)

    try:
        import inspect

        concat_sig = inspect.signature(concatenate_videoclips)
        concat_params = concat_sig.parameters
    except Exception:
        concat_params = {}

    concat_kwargs = {"method": "compose"}
    if "padding" in concat_params:
        concat_kwargs["padding"] = -crossfade
    video = concatenate_videoclips(clips, **concat_kwargs)

    audio = None
    if audio_path:
        audio = AudioFileClip(audio_path)
        if audio.duration >= video.duration:
            if hasattr(audio, "subclipped"):
                audio = audio.subclipped(0, video.duration)
            else:
                audio = audio.subclip(0, video.duration)
        else:
            audio = afx.audio_loop(audio, duration=video.duration)
        if hasattr(video, "with_audio"):
            video = video.with_audio(audio)
        else:
            video = video.set_audio(audio)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import inspect

        sig = inspect.signature(video.write_videofile)  # type: ignore[attr-defined]
        params = sig.parameters
        if "verbose" in params or "logger" in params:
            video.write_videofile(
                str(out),
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
            )
        else:
            video.write_videofile(
                str(out),
                fps=fps,
                codec="libx264",
                audio_codec="aac",
            )
    except Exception:
        video.write_videofile(
            str(out),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
        )
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        try:
            video.close()
        except Exception:
            pass
        if audio:
            try:
                audio.close()
            except Exception:
                pass
    return str(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a photo slideshow video with optional audio."
    )
    parser.add_argument(
        "--images-dir",
        default="photos",
        help="Folder with .jpg/.png images (default: photos).",
    )
    parser.add_argument(
        "--audio",
        default="music.mp3",
        help="Audio file (default: music.mp3). Use empty string to disable.",
    )
    parser.add_argument(
        "--out",
        default="slideshow.mp4",
        help="Output path (default: slideshow.mp4).",
    )
    parser.add_argument("--fps", type=int, default=30, help="Frames per second.")
    parser.add_argument(
        "--seconds-per-image",
        type=float,
        default=20.0,
        help="Seconds each photo is shown.",
    )
    parser.add_argument(
        "--crossfade",
        type=float,
        default=0.4,
        help="Crossfade duration in seconds.",
    )
    args = parser.parse_args()

    audio_path = args.audio or None
    out = create_slideshow(
        images_dir=Path(args.images_dir),
        audio_path=audio_path,
        out_path=args.out,
        fps=args.fps,
        seconds_per_image=args.seconds_per_image,
        crossfade=args.crossfade,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
