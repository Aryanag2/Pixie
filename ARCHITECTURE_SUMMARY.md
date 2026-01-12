# Pixie Architecture Summary

## Overview

Pixie is an AI-powered event video generation pipeline that transforms raw photos into polished videos through a 3-stage orchestrated workflow. The system uses a coordinator pattern where an **Orchestrator Agent** manages three specialized agents that work sequentially.

## Architecture Pattern

**Orchestrator Pattern**: A central orchestrator coordinates specialized agents that process data in stages, with each stage producing output for the next.

## System Components

### 1. Orchestrator Agent (Central Coordinator)
- **Role**: Pipeline coordination, error handling, workspace management
- **Responsibilities**:
  - Sets up workspace directories
  - Invokes agents in sequence
  - Manages intermediate files
  - Handles cleanup
  - Reports pipeline statistics
- **Dependencies**: None (pure coordination)

### 2. Photo Curator Agent (Stage 1)
- **Role**: Quality filtering using AI vision
- **Input**: Raw photos directory
- **Output**: Curated photos directory (filtered set)
- **Process**:
  1. Loads images from input directory
  2. Sends each photo to GPT-4o Vision API for quality analysis
  3. Filters out blurry, dark, or poorly composed photos
  4. Copies quality photos to curated directory
- **External Dependency**: OpenAI GPT-4o Vision API
- **Typical Result**: ~70% of photos kept (e.g., 35 out of 50)

### 3. Style Generator Agent (Stage 2)
- **Role**: Apply artistic transformations
- **Input**: Curated photos directory
- **Output**: Styled photos directory + metadata JSON
- **Process**:
  1. Loads curated photos
  2. Alternates styles for each photo (every 3rd photo):
     - Ghibli-style (anime aesthetic)
     - 1980s film (vintage cinematic)
     - Original (no modification)
  3. Uses GPT Image Edit API to apply styles
  4. Saves styled photos and style mapping metadata
- **External Dependency**: OpenAI Image Edit API
- **Output**: Same count as curated photos, with style variations

### 4. Video Generator Agent (Stage 3)
- **Two Modes**: Slideshow or AI-Generated Video

#### 4a. Slideshow Generator
- **Role**: Traditional video creation with transitions
- **Input**: Styled photos + audio file (optional)
- **Output**: MP4 slideshow video
- **Process**:
  1. Loads styled photos in order
  2. Creates video clips with transitions (crossfade)
  3. Adds background audio track
  4. Renders final MP4 video
- **External Dependency**: MoviePy, ffmpeg
- **Features**: Configurable FPS, duration per image, crossfade timing

#### 4b. Veo AI Generator
- **Role**: AI-powered video generation
- **Input**: Styled photos + text prompt
- **Output**: MP4 AI-generated video
- **Process**:
  1. Prepares styled photos as reference images
  2. Sends request to Google Veo 3.1 API with prompt
  3. Polls API for completion status
  4. Downloads generated video when ready
- **External Dependency**: Google Veo 3.1 API
- **Features**: Configurable duration, FPS, custom prompts

## Workflow Execution

### Pipeline Flow

```
Raw Photos → [Stage 1: Curation] → Curated Photos → [Stage 2: Styling] → Styled Photos → [Stage 3: Video] → Final Video
```

### Detailed Execution Steps

1. **Initialization**
   - Orchestrator creates workspace directory structure
   - Sets up: `curated_photos/`, `styled_photos/` subdirectories

2. **Stage 1: Photo Curation**
   - Orchestrator invokes Photo Curator Agent
   - Agent processes each photo through GPT-4o Vision
   - Quality photos copied to `curated_photos/`
   - Statistics: raw count → curated count

3. **Stage 2: Style Application**
   - Orchestrator invokes Style Generator Agent
   - Agent applies styles using rotation pattern (Ghibli/1980s/Original)
   - Styled photos saved to `styled_photos/`
   - Style metadata saved to `instructions.json`
   - Statistics: curated count → styled count (same)

4. **Stage 3: Video Generation**
   - **If Slideshow Mode**:
     - Orchestrator invokes Slideshow Generator
     - Generator creates MP4 with MoviePy
     - Adds audio track (if provided)
     - Saves to output path
   - **If Veo Mode**:
     - Orchestrator invokes Veo Generator
     - Generator sends API request with prompt
     - Polls for completion (typically 2-5 minutes)
     - Downloads and saves video to output path

5. **Cleanup & Summary**
   - Orchestrator prints pipeline statistics
   - Optionally cleans up workspace directory
   - Returns final video path to user

## State Machine

The system follows a linear state progression with error handling:

```
Idle → Setup → Curating → Styling → VideoGeneration → Cleanup → Complete
```

At each stage, failures transition to error states while preserving workspace for debugging (if cleanup disabled).

## Data Flow

- **Input**: Raw photos directory (user-provided)
- **Intermediate 1**: Curated photos (35% reduction typical)
- **Intermediate 2**: Styled photos (same count, transformed)
- **Output**: Final MP4 video file

## Error Handling

- Try-catch wrapper around entire pipeline
- Errors logged with context
- Workspace preserved if cleanup disabled (for debugging)
- Exceptions propagated to user with helpful messages
- Each stage validates input before proceeding

## Key Design Principles

1. **Separation of Concerns**: Each agent handles one specific task
2. **Sequential Processing**: Stages execute in order, each depends on previous output
3. **Stateless Agents**: Agents are pure functions, orchestration manages state
4. **Workspace Isolation**: All intermediate files in dedicated workspace directory
5. **Configurable Cleanup**: Option to preserve intermediate files for inspection
6. **Error Recovery**: Workspace preserved on failure when cleanup disabled

## External API Dependencies

| Agent | API Service | Purpose |
|-------|------------|---------|
| Photo Curator | OpenAI GPT-4o Vision | Quality assessment |
| Style Generator | OpenAI Image Edit API | Style transformation |
| Veo Generator | Google Veo 3.1 | AI video generation |
| Slideshow Generator | MoviePy (local) | Video rendering |

## Performance Characteristics

- **Photo Curation**: ~2-3 seconds per photo (API dependent)
- **Style Generation**: ~5-10 seconds per styled photo (API dependent)
- **Slideshow Generation**: Fast (local processing, depends on photo count)
- **Veo Generation**: 2-5 minutes (API queue dependent)

## Summary

Pixie uses an **orchestrator pattern** where a central coordinator manages three specialized AI agents that process event photos through curation, styling, and video generation stages. The system is designed for reliability with error handling, workspace management, and configurable cleanup options.

