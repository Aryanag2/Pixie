# Event Video Generation Pipeline

An AI-powered orchestrator system that transforms raw event photos into polished videos using multiple specialized agents.

## Architecture

The system consists of three specialized agents coordinated by an orchestrator:

1. **Photo Curator Agent** (`src/photo/photo_curator.py`)
   - Uses GPT-4o vision to evaluate photo quality
   - Filters out blurry, dark, or irrelevant shots
   - Keeps only meaningful, well-composed photos

2. **Style Generator Agent** (`src/photo/styled_photo_generator.py`)
   - Applies artistic transformations using GPT image editing
   - Alternates between Ghibli-style, 1980s film, and original styles
   - Creates visually cohesive output

3. **Video Generator Agent** (`src/video_gen/`)
   - **Slideshow mode**: Creates smooth transitions with audio (MoviePy)
   - **Veo mode**: Generates AI video using Google's Veo 3.1 model

4. **Orchestrator** (`orchestrator.py`)
   - Coordinates all agents in sequence
   - Manages intermediate files and workspace
   - Provides progress tracking and error handling

## Setup

### Prerequisites

```bash
# Python 3.12+ recommended
python --version

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```bash
# Required for photo curation and styling
OPENAI_API_KEY=sk-...

# Required only for Veo video generation
GOOGLE_API_KEY=...
```

### Directory Structure

```
.
├── orchestrator.py           # Main orchestrator agent
├── src/
│   ├── photo/
│   │   ├── photo_curator.py         # Agent 1: Quality filtering
│   │   └── styled_photo_generator.py # Agent 2: Style application
│   └── video_gen/
│       ├── create_slideshow.py      # Agent 3a: Slideshow generator
│       └── generate_veo_video.py    # Agent 3b: AI video generator
├── raw_photos/              # Your input photos (you create this)
└── pipeline_work/           # Auto-generated workspace (cleaned after)
```

## Usage

### Quick Start

**Generate a slideshow with music:**
```bash
python orchestrator.py \
  --raw-photos ./raw_photos \
  --output final_video.mp4 \
  --mode slideshow \
  --audio music.mp3
```

**Generate an AI video with Veo:**
```bash
python orchestrator.py \
  --raw-photos ./raw_photos \
  --output ai_video.mp4 \
  --mode veo \
  --prompt "A heartwarming celebration of friendship and joy"
```

### Advanced Options

#### Slideshow Customization

```bash
python orchestrator.py \
  --raw-photos ./raw_photos \
  --output slideshow.mp4 \
  --mode slideshow \
  --audio background_music.mp3 \
  --fps 60 \
  --seconds-per-image 4.0 \
  --crossfade 0.6
```

Options:
- `--fps`: Frame rate (default: 30)
- `--seconds-per-image`: Duration per photo (default: 3.0)
- `--crossfade`: Transition duration (default: 0.4)

#### Veo Video Generation

```bash
python orchestrator.py \
  --raw-photos ./event_photos \
  --output veo_story.mp4 \
  --mode veo \
  --prompt "An epic journey through a magical evening, cinematic style" \
  --duration 12 \
  --veo-model veo-3.1-generate-preview
```

Options:
- `--prompt`: Required text description for video generation
- `--duration`: Video length in seconds (default: 8)
- `--veo-model`: Veo model to use (default: veo-3.1-generate-preview)
- `--veo-fps`: Frame rate for Vertex AI (default: 24)

#### Workspace Management

```bash
# Keep intermediate files for inspection
python orchestrator.py \
  --raw-photos ./raw_photos \
  --output video.mp4 \
  --mode slideshow \
  --no-cleanup \
  --work-dir ./my_workspace
```

This preserves:
- `my_workspace/curated_photos/` - Photos that passed quality check
- `my_workspace/styled_photos/` - Stylized versions
- `my_workspace/styled_photos/instructions.json` - Style mapping

## Pipeline Stages

### Stage 1: Photo Curation
```
[Curator Agent]
Raw Photos (50) → Quality Check → Curated Photos (35)
                     ↓
              Filters: blur, darkness, composition
```

### Stage 2: Style Application
```
[Stylist Agent]
Curated Photos → Style Rotation → Styled Photos
                      ↓
         Ghibli / 1980s Film / Original
```

### Stage 3: Video Generation
```
[Video Agent - Slideshow Mode]
Styled Photos + Audio → MoviePy → MP4 Video

[Video Agent - Veo Mode]
Styled Photos + Prompt → Veo API → AI-Generated Video
```

## Example Workflows

### Wedding Highlights

```bash
# 1. Place wedding photos in raw_photos/
# 2. Generate romantic slideshow
python orchestrator.py \
  --raw-photos ./raw_photos \
  --output wedding_highlights.mp4 \
  --mode slideshow \
  --audio romantic_song.mp3 \
  --seconds-per-image 5.0
```

### Event Recap Video

```bash
# Generate AI video with dynamic narrative
python orchestrator.py \
  --raw-photos ./conference_photos \
  --output conference_recap.mp4 \
  --mode veo \
  --prompt "Dynamic montage of an exciting tech conference, energetic and inspiring" \
  --duration 15
```

### Family Vacation

```bash
# Create nostalgic slideshow
python orchestrator.py \
  --raw-photos ./vacation_pics \
  --output vacation_memories.mp4 \
  --mode slideshow \
  --audio vacation_theme.mp3 \
  --seconds-per-image 4.0 \
  --crossfade 0.8
```

## Individual Agent Usage

You can also run agents independently:

### Photo Curator Only
```python
from src.photo.photo_curator import run
run("./raw_photos", "./curated_photos")
```

### Style Generator Only
```python
from src.photo.styled_photo_generator import run
run("./curated_photos", "./styled_photos")
```

### Slideshow Only
```bash
python src/video_gen/create_slideshow.py \
  --images-dir styled_photos \
  --audio music.mp3 \
  --out output.mp4 \
  --seconds-per-image 3
```

### Veo Only
```bash
python src/video_gen/generate_veo_video.py \
  --images styled_photos \
  --prompt "Your video description" \
  --output veo.mp4
```

## Output Examples

After running the orchestrator, you'll see:

```
============================================================
PIPELINE SUMMARY
============================================================
Raw photos processed:     50
Photos after curation:    35
Photos after styling:     35
Video generated:          ✓
Output location:          final_video.mp4
============================================================
```

## Troubleshooting

### No photos passed curation
- **Cause**: Photos may be too blurry or low quality
- **Solution**: Try with higher quality source photos

### Veo API errors
- **Cause**: Missing GOOGLE_API_KEY or quota limits
- **Solution**: Check environment variables and API quotas

### MoviePy errors
- **Cause**: Missing system dependencies for video encoding
- **Solution**: Install ffmpeg: `brew install ffmpeg` (Mac) or `apt-get install ffmpeg` (Linux)

### Out of memory
- **Cause**: Too many high-resolution photos
- **Solution**: Reduce source photo count or resolution

## Performance Notes

- **Photo Curation**: ~2-3 seconds per photo (GPT-4o API calls)
- **Style Generation**: ~5-10 seconds per styled photo (GPT image API)
- **Slideshow**: Fast, depends on photo count and length
- **Veo Generation**: 2-5 minutes (varies by complexity and queue)

## Cost Estimation

Approximate costs per 50 raw photos:

- Photo Curation: ~$0.50 (GPT-4o vision)
- Style Generation: ~$3.00 (GPT image edits)
- Veo Video: ~$0.20-0.40 per video

Total: ~$4-5 per complete pipeline run

## API References

- [OpenAI Image API](https://platform.openai.com/docs/guides/images)
- [Google Veo API](https://ai.google.dev/gemini-api/docs/video-generation)
- [MoviePy Documentation](https://zulko.github.io/moviepy/)

## License

MIT