#!/usr/bin/env python3
"""
Wrapper Orchestrator

Flow:
1) rclone sync remote BrunoShots -> local
2) agent1: curate
3) agent2: style
4) agent3: slideshow
5) agent4: highlight
6) rclone sync local -> remote
"""

# ---------- MUST BE FIRST ----------
from dotenv import load_dotenv

from src.video_gen.create_slideshow import run_create_slideshow

load_dotenv()  # <-- FIX: load env BEFORE any OpenAI client is created
# ----------------------------------

import os
import subprocess
from pathlib import Path

# ---------- rclone config ----------
RCLONE_REMOTE = os.environ.get("RCLONE_REMOTE", "grive_full")
RCLONE_BIN = os.environ.get("RCLONE_BIN", "rclone")
REMOTE_ROOT = os.environ.get("REMOTE_ROOT", "BrunoShots")
LOCAL_ROOT = Path(os.environ.get("LOCAL_ROOT", "./BrunoShots"))
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")


# ---------- folders ----------
CURATED_DIR = LOCAL_ROOT / "curated_photos"
STYLED_DIR = LOCAL_ROOT / "styled_photos"
VIDEOS_DIR = LOCAL_ROOT / "generated_videos"

# ---------- NOW import agents ----------
from src.video_gen.photo_curator import run_curate
from src.video_gen.styled_photo_generator import run_style
# from src.video_gen.create_slideshow import run_create_slideshow
from src.video_gen.generate_veo_video import run_generate_video


def run_cmd(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            f"Command failed:\n{' '.join(cmd)}\n\nSTDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}"
        )


def sync_remote_to_local() -> None:
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    run_cmd([
        RCLONE_BIN, "sync",
        f"{RCLONE_REMOTE}:{REMOTE_ROOT}",
        str(LOCAL_ROOT),
        "--progress"
    ])


def sync_local_to_remote() -> None:
    run_cmd([
        RCLONE_BIN, "sync",
        str(LOCAL_ROOT),
        f"{RCLONE_REMOTE}:{REMOTE_ROOT}",
        "--progress"
    ])


def ensure_dirs() -> None:
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    STYLED_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("[1] rclone remote → local")
    sync_remote_to_local()
    ensure_dirs()

    # print("[2] Agent1: Curator")
    # run_curate(str(LOCAL_ROOT), str(CURATED_DIR))
    #
    # print("[3] Agent2: Stylist")
    # run_style(str(CURATED_DIR), str(STYLED_DIR))
    #
    print("[4] Agent3: Slideshow")
    # run_create_slideshow(
    #     curated_photos_dir=str(CURATED_DIR),
    #     generated_videos_dir=str(VIDEOS_DIR),
    #     output_name="slideshow.mp4",
    #     seconds_per_image=2.0,
    # )
    #
    # print("[5] Agent4: Highlight video")
    # run_generate_video(str(STYLED_DIR), str(VIDEOS_DIR))
    # run_generate_video(
    #     images_dir=str(STYLED_DIR),
    #     generated_videos_dir=str(VIDEOS_DIR),
    #     output_name="highlight.mp4",
    # )

    print("[6] rclone local → remote")
    sync_local_to_remote()

    print("[DONE]")


if __name__ == "__main__":
    main()
