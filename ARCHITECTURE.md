# Orchestrator Architecture

## System Flow Diagram

```mermaid
graph TB
    Start([User: Raw Photos]) --> Orch[Orchestrator Agent]
    
    Orch --> Stage1{Stage 1: Curation}
    Stage1 --> Curator[Photo Curator Agent]
    Curator --> |GPT-4o Vision| QCheck[Quality Check]
    QCheck --> |Filters: blur, dark, composition| Curated[(Curated Photos)]
    
    Curated --> Stage2{Stage 2: Styling}
    Stage2 --> Stylist[Style Generator Agent]
    Stylist --> |GPT Image Edit API| Style1[Ghibli Style]
    Stylist --> Style2[1980s Film]
    Stylist --> Style3[Original]
    Style1 --> Styled[(Styled Photos)]
    Style2 --> Styled
    Style3 --> Styled
    
    Styled --> Stage3{Stage 3: Video Gen}
    Stage3 --> |Mode: Slideshow| VidAgent1[Slideshow Generator]
    Stage3 --> |Mode: Veo| VidAgent2[Veo AI Generator]
    
    VidAgent1 --> |MoviePy| Audio[Audio Track]
    Audio --> Slideshow[MP4 Slideshow]
    
    VidAgent2 --> |Google Veo 3.1| AIVideo[AI-Generated MP4]
    
    Slideshow --> Output([Final Video])
    AIVideo --> Output
    
    Orch --> |Cleanup| Cleanup[Remove Workspace]
    Cleanup --> Summary[Pipeline Summary]
    
    style Orch fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style Curator fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    style Stylist fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    style VidAgent1 fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    style VidAgent2 fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    style Output fill:#F44336,stroke:#C62828,stroke-width:3px,color:#fff
```

## Agent Communication Pattern

```mermaid
sequenceDiagram
    participant User
    participant Orch as Orchestrator
    participant Curator as Photo Curator
    participant Stylist as Style Generator
    participant VidGen as Video Generator
    participant APIs as External APIs
    
    User->>Orch: Raw photos + config
    Orch->>Orch: Setup workspace
    
    Note over Orch,Curator: Stage 1: Curation
    Orch->>Curator: Process raw photos
    loop Each Photo
        Curator->>APIs: GPT-4o vision check
        APIs-->>Curator: Quality score
        Curator->>Curator: Filter decision
    end
    Curator-->>Orch: Curated photos
    
    Note over Orch,Stylist: Stage 2: Styling
    Orch->>Stylist: Process curated photos
    loop Each Photo (every 3rd)
        Stylist->>APIs: GPT image edit
        APIs-->>Stylist: Styled image
    end
    Stylist-->>Orch: Styled photos + metadata
    
    Note over Orch,VidGen: Stage 3: Video Generation
    
    alt Mode: Slideshow
        Orch->>VidGen: Generate slideshow
        VidGen->>VidGen: MoviePy processing
        VidGen-->>Orch: MP4 video
    else Mode: Veo
        Orch->>VidGen: Generate AI video
        VidGen->>APIs: Veo 3.1 request
        loop Polling
            VidGen->>APIs: Check status
            APIs-->>VidGen: Progress update
        end
        APIs-->>VidGen: Generated video
        VidGen-->>Orch: MP4 video
    end
    
    Orch->>Orch: Cleanup workspace
    Orch->>User: Final video + summary
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph Input
        Raw[Raw Photos<br/>50 images]
    end
    
    subgraph Agent1[Photo Curator Agent]
        A1[Load Images]
        A2[Vision Analysis]
        A3[Filter Logic]
        A1 --> A2 --> A3
    end
    
    subgraph Workspace1[Curated Storage]
        W1[(35 quality photos)]
    end
    
    subgraph Agent2[Style Generator Agent]
        B1[Load Curated]
        B2[Apply Styles]
        B3[Save Results]
        B1 --> B2 --> B3
    end
    
    subgraph Workspace2[Styled Storage]
        W2[(35 styled photos<br/>+ metadata)]
    end
    
    subgraph Agent3A[Slideshow Generator]
        C1[Load Styled]
        C2[Create Transitions]
        C3[Add Audio]
        C4[Render MP4]
        C1 --> C2 --> C3 --> C4
    end
    
    subgraph Agent3B[Veo Generator]
        D1[Load Styled]
        D2[Prepare References]
        D3[API Request]
        D4[Poll & Retrieve]
        D1 --> D2 --> D3 --> D4
    end
    
    subgraph Output
        Out[Final Video<br/>MP4]
    end
    
    Raw --> Agent1
    Agent1 --> W1
    W1 --> Agent2
    Agent2 --> W2
    W2 --> Agent3A
    W2 --> Agent3B
    Agent3A --> Out
    Agent3B --> Out
    
    style Raw fill:#E3F2FD
    style Agent1 fill:#BBDEFB
    style Agent2 fill:#FFE0B2
    style Agent3A fill:#E1BEE7
    style Agent3B fill:#E1BEE7
    style Out fill:#FFCDD2
```

## State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Setup: run_pipeline()
    Setup --> Curating: workspace ready
    
    Curating --> CurationFailed: no photos kept
    Curating --> Styling: photos curated
    
    Styling --> StylingFailed: API error
    Styling --> VideoGeneration: photos styled
    
    VideoGeneration --> SlideshowMode: mode=slideshow
    VideoGeneration --> VeoMode: mode=veo
    
    SlideshowMode --> RenderingSlideshow
    RenderingSlideshow --> SlideshowFailed: render error
    RenderingSlideshow --> Cleanup: video ready
    
    VeoMode --> RequestingVeo
    RequestingVeo --> VeoFailed: API error
    RequestingVeo --> PollingVeo: request sent
    PollingVeo --> PollingVeo: waiting...
    PollingVeo --> Cleanup: video ready
    
    Cleanup --> Complete: cleanup=true
    Cleanup --> PreserveWorkspace: cleanup=false
    
    Complete --> [*]
    PreserveWorkspace --> [*]
    
    CurationFailed --> [*]
    StylingFailed --> [*]
    SlideshowFailed --> [*]
    VeoFailed --> [*]
```

## Component Responsibilities

| Component | Responsibility | Input | Output | External Deps |
|-----------|---------------|-------|--------|---------------|
| **Orchestrator** | Pipeline coordination, error handling, workspace management | Raw photos, config | Final video, stats | None |
| **Photo Curator** | Quality filtering using vision AI | Raw photos | Curated photos | OpenAI GPT-4o |
| **Style Generator** | Artistic style application | Curated photos | Styled photos | OpenAI Image API |
| **Slideshow Generator** | Traditional video creation | Styled photos, audio | MP4 video | MoviePy, ffmpeg |
| **Veo Generator** | AI-powered video generation | Styled photos, prompt | MP4 video | Google Veo 3.1 |

## Error Handling Flow

```mermaid
graph TD
    Start[Pipeline Start] --> Try{Try}
    Try --> |Success| Stage1[Stage 1]
    Try --> |Error| Catch[Catch Exception]
    
    Stage1 --> |Success| Stage2[Stage 2]
    Stage1 --> |Error| Catch
    
    Stage2 --> |Success| Stage3[Stage 3]
    Stage2 --> |Error| Catch
    
    Stage3 --> |Success| Success[Print Summary]
    Stage3 --> |Error| Catch
    
    Catch --> Log[Log Error]
    Log --> CheckCleanup{cleanup=true?}
    CheckCleanup --> |Yes| Remove[Remove Workspace]
    CheckCleanup --> |No| Preserve[Keep Files for Debug]
    
    Remove --> Reraise[Reraise Exception]
    Preserve --> Reraise
    
    Success --> FinalCleanup{cleanup=true?}
    FinalCleanup --> |Yes| RemoveSuccess[Remove Workspace]
    FinalCleanup --> |No| End[End]
    
    RemoveSuccess --> End
    Reraise --> UserError[User Sees Error]
    
    style Success fill:#4CAF50,color:#fff
    style Catch fill:#F44336,color:#fff
    style UserError fill:#FF5722,color:#fff
```