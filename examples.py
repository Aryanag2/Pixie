#!/usr/bin/env python3
"""
Example: Using the Orchestrator Programmatically

This demonstrates how to use the EventVideoOrchestrator class
directly in your Python code instead of via command line.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import EventVideoOrchestrator


def example_1_basic_slideshow():
    """Create a simple slideshow from raw photos."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Slideshow")
    print("=" * 60)

    orchestrator = EventVideoOrchestrator(
        raw_photos_dir="./raw_photos",
        output_video="./output/basic_slideshow.mp4",
        work_dir="./work",
        cleanup=False,  # Keep files to inspect
    )

    orchestrator.run_pipeline(
        mode="slideshow",
        slideshow_config={
            "fps": 30,
            "seconds_per_image": 3.0,
            "crossfade": 0.4,
        },
    )


def example_2_slideshow_with_audio():
    """Create a slideshow with custom audio and timing."""
    print("\n" + "=" * 60)
    print("Example 2: Slideshow with Audio")
    print("=" * 60)

    orchestrator = EventVideoOrchestrator(
        raw_photos_dir="./raw_photos",
        output_video="./output/slideshow_with_music.mp4",
        work_dir="./work_music",
        audio_path="./music.mp3",  # Add your music file
        cleanup=True,
    )

    orchestrator.run_pipeline(
        mode="slideshow",
        slideshow_config={
            "fps": 60,
            "seconds_per_image": 4.0,
            "crossfade": 0.8,
        },
    )


def example_3_veo_video():
    """Generate an AI video using Veo."""
    print("\n" + "=" * 60)
    print("Example 3: Veo AI Video")
    print("=" * 60)

    orchestrator = EventVideoOrchestrator(
        raw_photos_dir="./raw_photos",
        output_video="./output/veo_video.mp4",
        work_dir="./work_veo",
        cleanup=True,
    )

    orchestrator.run_pipeline(
        mode="veo",
        veo_prompt="A heartwarming celebration of friendship and joy, cinematic style with warm lighting",
        veo_config={
            "model": "veo-3.1-generate-preview",
            "duration": 10,
            "fps": 24,
        },
    )


def example_4_custom_workflow():
    """Run individual stages with custom logic between them."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Multi-Stage Workflow")
    print("=" * 60)

    orchestrator = EventVideoOrchestrator(
        raw_photos_dir="./raw_photos",
        output_video="./output/custom_video.mp4",
        work_dir="./work_custom",
        cleanup=False,
    )

    # Run stages individually
    orchestrator.setup_workspace()

    print("\n➤ Running curation...")
    orchestrator.run_curation_agent()

    # Custom logic: Check if we have enough photos
    if orchestrator.stats["curated_count"] < 10:
        print("\n⚠️  Warning: Less than 10 photos passed curation")
        print("    Consider adjusting curation criteria or using more photos")

    print("\n➤ Running styling...")
    orchestrator.run_styling_agent()

    # Custom logic: Inspect styling results
    import json

    instructions_file = orchestrator.styled_dir / "instructions.json"
    if instructions_file.exists():
        with open(instructions_file) as f:
            instructions = json.load(f)
        print(f"\n📊 Applied {len(instructions)} style transformations")

    print("\n➤ Generating video...")
    orchestrator.run_slideshow_generator(
        fps=30,
        seconds_per_image=3.5,
        crossfade=0.5,
    )

    orchestrator.print_summary()


def example_5_batch_processing():
    """Process multiple event folders in batch."""
    print("\n" + "=" * 60)
    print("Example 5: Batch Processing Multiple Events")
    print("=" * 60)

    events = [
        ("./event1_photos", "Birthday Party"),
        ("./event2_photos", "Wedding Reception"),
        ("./event3_photos", "Corporate Event"),
    ]

    for photo_dir, event_name in events:
        print(f"\n{'='*60}")
        print(f"Processing: {event_name}")
        print(f"{'='*60}")

        # Skip if directory doesn't exist
        if not Path(photo_dir).exists():
            print(f"⚠️  Skipping {event_name} - directory not found")
            continue

        # Create safe filename
        safe_name = event_name.lower().replace(" ", "_")

        try:
            orchestrator = EventVideoOrchestrator(
                raw_photos_dir=photo_dir,
                output_video=f"./output/{safe_name}_video.mp4",
                work_dir=f"./work_{safe_name}",
                cleanup=True,
            )

            orchestrator.run_pipeline(
                mode="slideshow",
                slideshow_config={
                    "fps": 30,
                    "seconds_per_image": 3.0,
                    "crossfade": 0.4,
                },
            )

            print(f"✓ Successfully processed: {event_name}")

        except Exception as e:
            print(f"✗ Failed to process {event_name}: {e}")
            continue


def example_6_error_handling():
    """Demonstrate error handling and recovery."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    orchestrator = EventVideoOrchestrator(
        raw_photos_dir="./raw_photos",
        output_video="./output/safe_video.mp4",
        work_dir="./work_safe",
        cleanup=False,  # Keep files on error
    )

    try:
        orchestrator.setup_workspace()
        orchestrator.run_curation_agent()

        # Check if we have any photos after curation
        if orchestrator.stats["curated_count"] == 0:
            raise ValueError("No photos passed curation - check photo quality")

        orchestrator.run_styling_agent()
        orchestrator.run_slideshow_generator()
        orchestrator.print_summary()

        print("\n✓ Pipeline completed successfully")

    except FileNotFoundError as e:
        print(f"\n✗ Directory not found: {e}")
        print("💡 Tip: Create the raw_photos directory and add images")

    except ValueError as e:
        print(f"\n✗ Validation error: {e}")
        print("💡 Tip: Ensure photos are high quality and properly formatted")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print(f"💡 Intermediate files saved in: {orchestrator.work_dir}")
        print("   You can inspect these to debug the issue")
        raise


def main():
    """Run examples based on command line argument."""
    import sys

    examples = {
        "1": ("Basic Slideshow", example_1_basic_slideshow),
        "2": ("Slideshow with Audio", example_2_slideshow_with_audio),
        "3": ("Veo AI Video", example_3_veo_video),
        "4": ("Custom Workflow", example_4_custom_workflow),
        "5": ("Batch Processing", example_5_batch_processing),
        "6": ("Error Handling", example_6_error_handling),
    }

    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in examples:
            _, func = examples[choice]
            func()
        else:
            print(f"Unknown example: {choice}")
            print_menu(examples)
    else:
        print_menu(examples)


def print_menu(examples):
    """Print available examples."""
    print("\nAvailable Examples:")
    print("=" * 60)
    for num, (desc, _) in examples.items():
        print(f"  {num}. {desc}")
    print("=" * 60)
    print("\nUsage: python examples.py <number>")
    print("Example: python examples.py 1")


if __name__ == "__main__":
    main()
