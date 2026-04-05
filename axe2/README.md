# VerifyAI — Product Requirements Document

> **Hackathon Axis 2: Contextual Consistency**
> Version 1.0 · April 2026

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [System Architecture](#3-system-architecture)
4. [Full Pipeline — Stage by Stage](#4-full-pipeline--stage-by-stage)
   - 4.1 [Input Ingestion](#41-input-ingestion)
   - 4.2 [Preprocessing](#42-preprocessing)
   - 4.3 [CLIP Early Exit Gate](#43-clip-early-exit-gate)
   - 4.4 [Deep AI Analysis](#44-deep-ai-analysis)
   - 4.5 [Consistency Comparator](#45-consistency-comparator)
   - 4.6 [Evidence Search Layer](#46-evidence-search-layer--optional-bonus)
   - 4.7 [Output Generation](#47-output-generation)
5. [API Specification](#5-api-specification)
6. [Technology Stack](#6-technology-stack)
7. [Frontend — React UI](#7-frontend--react-ui)
8. [Output Bilan Format](#8-output-bilan-format)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Project Structure](#10-project-structure)
11. [Sprint Plan](#11-sprint-plan)
12. [Risks & Mitigations](#12-risks--mitigations)

---

## 1. Problem Statement

In the modern information ecosystem, the most dangerous form of misinformation is not the fabricated image — it is the **real image used in the wrong context**. A genuine protest photograph from Egypt in 2019 gets reposted as "breaking news from Tunisia today." A real flood from Bangladesh is captioned as a local disaster happening now. This form of manipulation — contextual misuse — is far more common than deepfakes and far harder to detect with traditional tools.

**Why traditional verification fails:**

- Manual fact-checking cannot keep up with the volume and velocity of social media content
- Metadata (timestamps, GPS) can be stripped or forged
- Centralized platforms create bottlenecks and are subject to bias
- AI deepfake detectors are designed for synthetic content — they pass real-but-reused images as authentic

**The gap this project fills:**

> *Most tools ask "Is this image fake?" — VerifyAI asks "Is this image being used truthfully?"*

---

## 2. Solution Overview

**VerifyAI** is a multimodal AI verification pipeline that detects contextual inconsistencies between visual media (images, Instagram reels, short videos) and the textual claims made about them.

The system ingests a media file and a caption, then runs it through a layered pipeline:

1. A **fast semantic gate** (CLIP) that immediately rejects obvious mismatches
2. A **deep understanding layer** (BLIP + spaCy) that extracts meaning from both image and text
3. A **reasoning comparator** that cross-references all signals to identify specific inconsistency patterns
4. An optional **evidence search layer** (DuckDuckGo) that grounds the verdict in real-world sources

Every verdict is returned as a structured **output bilan**: a score (0–100), a verdict label, a list of detected flags, and a human-readable explanation — making results transparent and explainable to non-technical users.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                             │
│                                                                 │
│   [Image / Video / Reel]          [Caption / Claim Text]        │
│        (JPG, PNG, MP4)                (raw string)              │
└────────────────┬────────────────────────────┬───────────────────┘
                 │                            │
                 ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PREPROCESSING LAYER                        │
│                                                                 │
│   OpenCV frame extractor          spaCy early tokenization      │
│   (video → key frames)            (language detect, clean)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLIP EARLY EXIT GATE                         │
│                                                                 │
│   CLIP encodes image + caption → cosine similarity score        │
│                                                                 │
│   score < 0.18  ──────────────────► EARLY EXIT → MISMATCH      │
│   score ≥ 0.18  ──► continue to deep pipeline                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
┌──────────────────────┐     ┌─────────────────────────────────┐
│    BLIP CAPTIONER    │     │         spaCy NER               │
│                      │     │                                 │
│  image → text desc.  │     │  caption → entities             │
│  "a crowd gathered   │     │  LOC: Tunisia                   │
│   in a city street"  │     │  DATE: today                    │
│                      │     │  EVENT: protest                 │
└──────────┬───────────┘     └──────────────┬──────────────────┘
           │                                │
           └──────────────┬─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONSISTENCY COMPARATOR                        │
│                                                                 │
│   · CLIP score                  → semantic alignment            │
│   · BLIP description            → what is actually shown        │
│   · spaCy entities              → what the caption claims       │
│   · Cross-reference signals     → detect inconsistency patterns │
│   · Optional LLM synthesis      → generate explanation text     │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┴───────────────┐
            │   search_enabled = true?   │
            ▼                            ▼
┌───────────────────────┐    ┌───────────────────────────────────┐
│   EVIDENCE SEARCH     │    │         SKIP SEARCH               │
│   (DuckDuckGo)        │    │                                   │
│   query from entities │    │   proceed directly to output      │
│   → news results      │    │                                   │
└──────────┬────────────┘    └──────────────┬────────────────────┘
           │                                │
           └──────────────┬─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT BILAN                              │
│                                                                 │
│   score · verdict · flags · explanation · evidence              │
│                                                                 │
│   → FastAPI JSON response → React frontend display              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Full Pipeline — Stage by Stage

### 4.1 Input Ingestion

The system accepts a single HTTP POST request with two mandatory fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `media` | File | Yes | Image (JPG, PNG, WEBP) or video (MP4, MOV). Max 50MB. |
| `caption` | string | Yes | The claim, post description, or article headline to verify against. |
| `search_enabled` | boolean | No | Activate the DuckDuckGo evidence layer. Default: `false`. |

**Validation at ingestion:**
- Reject files that are not image or video MIME types
- Reject files over 50MB
- Reject empty or whitespace-only captions
- Return a `400 Bad Request` with a clear error message for any validation failure

---

### 4.2 Preprocessing

**For images:**
The image is loaded directly into memory and passed to the CLIP encoder as a PIL Image object. No resizing is done at this stage — CLIP handles its own preprocessing internally via its `CLIPProcessor`.

**For videos (MP4 / MOV / Instagram Reels):**
OpenCV is used to extract representative frames from the video before any AI model runs:

```
video file
    │
    ▼
cv2.VideoCapture
    │
    ├── total_frames / fps → compute frame positions
    │
    ├── extract N key frames (default: 5)
    │   strategy: evenly spaced + scene-change detection
    │
    └── return List[PIL.Image]
```

Key frame selection strategy:
- Compute total frame count and video duration
- Extract frames at positions: 10%, 25%, 50%, 75%, 90% of total duration
- Additionally, detect scene changes using frame difference scoring — if a frame differs significantly from the previous one (pixel diff > threshold), include it
- Cap at a maximum of 8 frames regardless of video length to control inference time

**For captions:**
The raw caption string passes through a lightweight spaCy pipeline at this stage for:
- Language detection (used later to select the correct NER model)
- Unicode normalization and whitespace cleaning
- No entity extraction yet — that happens in Stage 4 after CLIP passes

---

### 4.3 CLIP Early Exit Gate

CLIP (Contrastive Language–Image Pretraining) is the first and cheapest AI model in the pipeline. It computes a single cosine similarity score between the image embedding and the caption embedding, answering: *"How semantically related are these two things?"*

**Model:** `openai/clip-vit-base-patch32` via HuggingFace `transformers`

**Process:**

```
image (PIL)  ──► CLIPProcessor ──► image_features (tensor)
                                          │
                                          ▼
                                   cosine_similarity()  ──► score (0.0 – 1.0)
                                          ▲
caption (str) ──► CLIPTokenizer ──► text_features (tensor)
```

**For video inputs:**
CLIP runs once per extracted frame. The final CLIP score for the video is the **maximum score across all frames**. Rationale: one matching frame is enough to justify deeper analysis. Only if *every* frame scores below the threshold do we trigger early exit.

**Decision thresholds:**

| CLIP Score | Verdict | Action |
|---|---|---|
| `< 0.18` | `MISMATCH` | **Early exit** — skip BLIP and spaCy entirely. Return verdict immediately. |
| `0.18 – 0.28` | `SUSPICIOUS` | Continue to deep pipeline. Score indicates partial match at best. |
| `> 0.28` | `LIKELY MATCH` | Continue to deep pipeline. Entity-level checks still needed. |

> **Important:** These thresholds must be calibrated on a test set before the demo. The 0.18 value is a conservative starting point — adjust based on observed score distributions on your specific test cases.

**Why this gate saves time:**
CLIP inference on CPU takes ~100–300ms. BLIP captioning takes ~2–4s. spaCy NER takes ~200ms. If the image and caption are semantically worlds apart (a cat photo captioned as a political protest), there is no value in running the heavier models. The gate eliminates this waste and returns a result in under 1 second for obvious mismatches.

---

### 4.4 Deep AI Analysis

If the CLIP gate does not trigger early exit, two models run **in parallel** (using Python's `concurrent.futures.ThreadPoolExecutor`):

---

#### BLIP Image Captioner

**Model:** `Salesforce/blip-image-captioning-base` via HuggingFace `transformers`

**Purpose:** Convert the image into a natural language description that describes what is *actually* happening in the scene — independent of what the caption *claims*.

**Process:**

```
image (PIL)
    │
    ▼
BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    │
    ▼
BlipForConditionalGeneration.generate()
    │
    ▼
blip_description: str
    → "a large crowd of people gathered in an urban street during daytime"
    → "a flooded road with submerged vehicles and people wading through water"
    → "a group of people celebrating at a nighttime event with fireworks"
```

**For video inputs:** BLIP runs on the frame that produced the highest CLIP score. This is the most "relevant" frame to the caption and gives the most meaningful description.

**Output:** A single string — the generated image caption. This is stored in the response as `blip_description` and fed into the comparator.

---

#### spaCy Named Entity Recognition

**Model:** `en_core_web_sm` (English) / `xx_ent_wiki_sm` (multilingual fallback for Arabic/French)

**Purpose:** Extract structured claims from the raw caption — specifically the factual assertions that can be cross-referenced against the image.

**Entities extracted:**

| spaCy Label | Maps to | Example |
|---|---|---|
| `GPE` | Location claim | "Tunisia", "Paris", "Gaza" |
| `LOC` | Location claim | "the Mediterranean", "North Africa" |
| `DATE` | Temporal claim | "today", "this morning", "2019" |
| `TIME` | Temporal claim | "right now", "last night" |
| `EVENT` | Event claim | "the protest", "the earthquake" |
| `PERSON` | Person claim | "President X", named individuals |

**Temporal red-flag keywords** (checked independently of NER):
These words trigger a `temporal_claim_unverifiable` flag regardless of NER output, because they assert immediacy that an image cannot confirm:

```
["today", "right now", "breaking", "just in", "this morning",
 "tonight", "happening now", "live", "currently", "at this moment"]
```

**Output:** A structured `entities` object:

```json
{
  "locations": ["Tunisia"],
  "dates": ["today"],
  "events": ["protest"],
  "persons": [],
  "temporal_flags": ["today"]
}
```

---

### 4.5 Consistency Comparator

The comparator is the reasoning core of the system. It takes the four signals produced so far and cross-references them to identify specific, named inconsistency patterns.

**Inputs:**
- `clip_score` — from Stage 4.3
- `blip_description` — from Stage 4.4 (BLIP)
- `entities` — from Stage 4.4 (spaCy)
- `caption` — original raw caption string

**Inconsistency patterns checked:**

**Pattern 1 — Location mismatch:**
Caption claims a specific city or country (`entities.locations` is non-empty). BLIP description contains no corroborating visual location cues. No recognizable landmarks, flags, signs, or geographic indicators appear in the BLIP output.

→ Raises flag: `location_mismatch`

**Pattern 2 — Temporal claim unverifiable:**
Caption uses present-tense immediacy language (`entities.temporal_flags` is non-empty: "today", "breaking", "right now"). An image cannot prove when it was taken. Any such claim is inherently unverifiable from visual content alone.

→ Raises flag: `temporal_claim_unverifiable`

**Pattern 3 — Event type mismatch:**
Caption claims a specific type of event (protest, fire, earthquake, celebration). BLIP description suggests a different event type. Detection uses keyword matching between `entities.events` and the BLIP output.

```
caption claims:   "violent protest"
BLIP describes:   "people celebrating at a festival"
→ event_type_mismatch
```

→ Raises flag: `event_type_mismatch`

**Pattern 4 — Overclaiming specificity:**
Caption makes multiple specific, unverifiable claims simultaneously (location + date + named person) while BLIP describes a generic scene with no specific identifiers.

→ Raises flag: `overclaiming_specificity`

**Score calculation:**

The final consistency score (0–100) is computed from a weighted combination:

```
base_score = clip_score × 100           # maps 0.0–1.0 to 0–100

penalties:
  location_mismatch             → −25
  temporal_claim_unverifiable   → −15
  event_type_mismatch           → −30
  overclaiming_specificity      → −10

final_score = max(0, base_score − sum(penalties))
```

**Verdict mapping:**

| Score | Verdict |
|---|---|
| `70 – 100` | `CONSISTENT` |
| `35 – 69` | `SUSPICIOUS` |
| `0 – 34` | `MISMATCH` |

**Optional LLM synthesis layer:**
If an LLM API key is configured, a final call synthesizes all signals into the `explanation` field. The prompt provides CLIP score, BLIP description, extracted entities, and detected flags, and asks the model to produce one clear paragraph explaining the verdict in plain language. If no LLM is available, a rule-based template fills the explanation field instead.

---

### 4.6 Evidence Search Layer *(Optional Bonus)*

Activated when `search_enabled=true` in the request.

**Tool:** `duckduckgo-search` Python library (no API key required)

**Purpose:** Ground the verdict in real-world evidence by checking whether the claimed event actually appears in news sources.

**Query construction:**
The search query is built from `entities.locations` + `entities.events` + the current year:

```python
query = f"{' '.join(entities['events'])} {' '.join(entities['locations'])} {current_year}"
# → "protest Tunisia 2026"
```

**Process:**

```
entities (locations + events)
    │
    ▼
construct search query
    │
    ▼
DuckDuckGoSearchResults.run(query, max_results=5)
    │
    ▼
parse results → List[{title, url, snippet}]
    │
    ▼
relevance filter: keep results whose snippet contains
                  at least one entity from the caption
    │
    ▼
evidence: List[{title, url, snippet, relevance_score}]
```

**How evidence affects the final score:**
- If 2+ relevant results confirm the event in the claimed location → `+10` score bonus
- If 0 relevant results found for a very specific claim → `−10` score penalty
- If results contradict the claim (different date or location for the same event) → `−15` score penalty and adds `evidence_contradicts_claim` flag

**Failure handling:**
DuckDuckGo can rate-limit or fail. The evidence layer is wrapped in a `try/except` with a 5-second timeout. On failure, the system proceeds without evidence and sets `evidence: null` in the response — the main verdict is never blocked by search availability.

---

### 4.7 Output Generation

All signals are assembled into the final **output bilan** — a consistent JSON structure returned by the API regardless of which path through the pipeline was taken (early exit or full pipeline).

**Early exit bilan** (CLIP score < 0.18):

```json
{
  "score": 8,
  "verdict": "MISMATCH",
  "early_exit": true,
  "clip_score": 0.09,
  "flags": ["semantic_mismatch"],
  "blip_description": null,
  "entities": null,
  "explanation": "The image and caption are semantically unrelated (CLIP similarity: 0.09). The visual content has no meaningful connection to the claim being made. No further analysis was necessary.",
  "evidence": null,
  "processing_time_ms": 312
}
```

**Full pipeline bilan** (deep analysis ran):

```json
{
  "score": 28,
  "verdict": "SUSPICIOUS",
  "early_exit": false,
  "clip_score": 0.22,
  "flags": [
    "location_mismatch",
    "temporal_claim_unverifiable"
  ],
  "blip_description": "a large crowd of people gathered in an urban street during daytime",
  "entities": {
    "locations": ["Tunisia"],
    "dates": ["today"],
    "events": ["protest"],
    "persons": [],
    "temporal_flags": ["today"]
  },
  "explanation": "The caption claims a protest occurring in Tunisia today. The image shows a generic urban crowd scene with no visual indicators confirming the location or time. The word 'today' makes a temporal claim that cannot be verified from visual content alone. This pattern is consistent with real content being reused in a misleading context.",
  "evidence": [
    {
      "title": "Protests in Tunisia — Al Jazeera",
      "url": "https://...",
      "snippet": "Protests erupted in Tunis in January 2021...",
      "relevance_score": 0.6
    }
  ],
  "processing_time_ms": 5840
}
```

---

## 5. API Specification

### Endpoint

```
POST /verify
Content-Type: multipart/form-data
```

### Input fields

| Field | Type | Required | Constraints |
|---|---|---|---|
| `media` | File | Yes | image/jpeg, image/png, image/webp, video/mp4, video/quicktime. Max 50MB. |
| `caption` | string | Yes | 1–2000 characters. Must not be empty. |
| `search_enabled` | boolean | No | Default: `false`. Set `true` to activate DuckDuckGo evidence layer. |

### Response fields

| Field | Type | Description |
|---|---|---|
| `score` | integer 0–100 | Final consistency score. Higher = more consistent. |
| `verdict` | string | `CONSISTENT` / `SUSPICIOUS` / `MISMATCH` |
| `early_exit` | boolean | `true` if the CLIP gate triggered and the deep pipeline was skipped. |
| `clip_score` | float | Raw CLIP cosine similarity score (0.0–1.0). |
| `flags` | string[] | List of detected inconsistency flags. Empty array if none. |
| `blip_description` | string \| null | BLIP-generated image caption. `null` if early exit. |
| `entities` | object \| null | Extracted entities from caption. `null` if early exit. |
| `explanation` | string | Human-readable explanation of the verdict. Always present. |
| `evidence` | object[] \| null | Search results. `null` if `search_enabled=false` or search failed. |
| `processing_time_ms` | integer | Total processing time in milliseconds. |

### Error responses

| HTTP Code | Condition |
|---|---|
| `400` | Invalid file type, file too large, empty caption |
| `422` | Missing required fields |
| `500` | Internal model inference error |
| `503` | Model not loaded / service unavailable |

### Additional endpoints

```
GET  /health     → { "status": "ok", "models_loaded": true }
GET  /docs       → Swagger UI (auto-generated by FastAPI)
```

---

## 6. Technology Stack

| Component | Library / Model | Version | Role |
|---|---|---|---|
| **CLIP** | `openai/clip-vit-base-patch32` | HuggingFace | Semantic similarity gate (Stage 3) |
| **BLIP** | `Salesforce/blip-image-captioning-base` | HuggingFace | Image-to-text captioning (Stage 4) |
| **spaCy** | `en_core_web_sm` / `xx_ent_wiki_sm` | spaCy 3.x | Named entity extraction (Stage 4) |
| **OpenCV** | `cv2` | 4.x | Video frame extraction (Stage 2) |
| **DuckDuckGo** | `duckduckgo-search` | latest | Evidence search (Stage 6) |
| **FastAPI** | `fastapi` + `uvicorn` | 0.110+ | REST API backend |
| **Transformers** | `transformers` | 4.x | HuggingFace model runner |
| **Pillow** | `PIL` | 10.x | Image loading and preprocessing |
| **React** | React 18 + Vite | 18.x | Frontend upload UI and results display |

### Python dependencies

```
fastapi
uvicorn
transformers
torch
Pillow
opencv-python
spacy
duckduckgo-search
python-multipart
```

### Model preloading

All three AI models (CLIP, BLIP, spaCy) are loaded **once at server startup** into memory. This avoids cold-start latency on the first request and is critical for demo performance.

```python
# At startup — not per-request
clip_model, clip_processor = load_clip()
blip_model, blip_processor = load_blip()
nlp = spacy.load("en_core_web_sm")
```

---

## 7. Frontend — React UI

### Upload screen

- Drag-and-drop zone or click-to-browse for image or video file
- Accepted formats shown clearly: JPG, PNG, WEBP, MP4, MOV
- Text area for caption / claim input (placeholder: *"Paste the post caption or claim here..."*)
- Toggle switch: **Enable evidence search** (DuckDuckGo)
- Submit button — disabled until both fields are filled
- File preview: thumbnail shown after selection

### Loading state

- Animated progress indicator
- Stage label that updates: *"Running CLIP gate..."* → *"Analysing image..."* → *"Extracting entities..."* → *"Building verdict..."*
- If early exit triggers, loading completes in under 1 second

### Results screen — the output bilan

The results screen is the product's most important surface. It is structured in clear sections:

**Section 1 — Verdict header**
Large score gauge (0–100) with color coding:
- Green (70–100): CONSISTENT
- Amber (35–69): SUSPICIOUS
- Red (0–34): MISMATCH

Verdict badge displayed prominently next to the score.

Early exit indicator (if applicable): *"Verdict reached at screening stage — image and caption are semantically unrelated."*

**Section 2 — Flags**
Each detected flag rendered as a labeled chip with an icon and a short plain-language description:

| Flag | Display label |
|---|---|
| `location_mismatch` | Location could not be confirmed in image |
| `temporal_claim_unverifiable` | Caption makes a time claim that cannot be verified visually |
| `event_type_mismatch` | Event type in caption does not match what the image shows |
| `overclaiming_specificity` | Caption makes multiple specific claims unsupported by the image |
| `evidence_contradicts_claim` | Search results suggest the claim is inaccurate |

**Section 3 — Explanation**
Card containing the `explanation` field. Always present. Written in plain, non-technical language.

**Section 4 — Image analysis detail** *(collapsible)*
- CLIP score displayed as a progress bar with label
- BLIP description: *"What the AI saw in this image"*
- Extracted entities table: locations, dates, events found in the caption

**Section 5 — Evidence** *(shown only if search was enabled)*
List of search result cards, each with title, source URL, and snippet. Labeled clearly as: *"Web sources found for this claim."*

---

## 8. Output Bilan Format

The output bilan is the structured deliverable that every request produces. It is designed to be immediately readable by both developers (via JSON) and end users (via the React UI rendering).

### Score interpretation

| Score | Verdict | Meaning |
|---|---|---|
| 70–100 | **CONSISTENT** | No significant inconsistencies detected. The image and caption are semantically aligned. Claims are not contradicted by visual evidence. |
| 35–69 | **SUSPICIOUS** | Partial inconsistencies detected. The image may be real but context claims are unverifiable or weakly supported. Human review recommended. |
| 0–34 | **MISMATCH** | Strong inconsistencies detected. High probability of contextual misuse — real image, misleading caption. |

### Flag reference

| Flag | Triggered by | Penalty |
|---|---|---|
| `semantic_mismatch` | CLIP score < 0.18 (early exit) | −80 (direct to low score) |
| `location_mismatch` | spaCy GPE entity + no visual confirmation in BLIP | −25 |
| `temporal_claim_unverifiable` | Temporal keywords in caption | −15 |
| `event_type_mismatch` | Event entity in caption contradicts BLIP description | −30 |
| `overclaiming_specificity` | 3+ specific unverifiable claims simultaneously | −10 |
| `evidence_contradicts_claim` | Search results conflict with caption claims | −15 |

---

## 9. Non-Functional Requirements

| Requirement | Target |
|---|---|
| CLIP-only early exit response time | < 1 second |
| Full pipeline response time (image) | < 8 seconds on CPU |
| Full pipeline response time (video) | < 15 seconds on CPU (5 frames) |
| Maximum file size | 50 MB |
| Maximum video frames processed | 8 frames |
| Maximum caption length | 2000 characters |
| API JSON schema consistency | Identical structure for early exit and full pipeline responses |
| Frontend mobile responsiveness | Fully usable on 375px viewport width |
| Model availability at startup | All models loaded before first request accepted |
| Search layer fault tolerance | Verdict never blocked by search failure — graceful fallback to `evidence: null` |

---

## 10. Project Structure

```
verifyai/
│
├── backend/
│   ├── main.py                  # FastAPI app, routes, startup model loading
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingest.py            # Input validation, file handling
│   │   ├── preprocess.py        # OpenCV frame extraction, image loading
│   │   ├── clip_gate.py         # CLIP similarity computation + threshold logic
│   │   ├── blip_captioner.py    # BLIP image-to-text
│   │   ├── ner_extractor.py     # spaCy NER + temporal keyword detection
│   │   ├── comparator.py        # Consistency comparator, flag detection, scoring
│   │   ├── evidence_search.py   # DuckDuckGo search layer
│   │   └── output_builder.py    # Assemble final bilan JSON
│   ├── models/
│   │   └── loader.py            # Singleton model loader (called at startup)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadForm.jsx   # Drag-drop upload + caption input
│   │   │   ├── LoadingState.jsx # Stage-aware loading indicator
│   │   │   ├── VerdictHeader.jsx# Score gauge + verdict badge
│   │   │   ├── FlagChips.jsx    # Flag chips with labels
│   │   │   ├── Explanation.jsx  # Explanation card
│   │   │   ├── AnalysisDetail.jsx # Collapsible CLIP/BLIP/entities detail
│   │   │   └── Evidence.jsx     # Search result cards
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md                    # This file
```

---

## 11. Sprint Plan

| Sprint | Focus | Key deliverables |
|---|---|---|
| **Sprint 1** | Foundation | FastAPI scaffold, `/health` endpoint, CLIP model loading, CLIP gate logic with threshold, basic `/verify` endpoint accepting file + caption, minimal React upload form |
| **Sprint 2** | Deep pipeline | BLIP integration, spaCy NER + temporal keyword detection, consistency comparator with all 4 flag types, score calculation formula, full pipeline wired end-to-end |
| **Sprint 3** | Output + search | Output bilan assembly, explanation generation (rule-based + optional LLM), DuckDuckGo search layer, evidence scoring, full React results screen with all 5 sections |
| **Sprint 4** | Video + polish | OpenCV frame extraction for MP4/Reels, multi-frame CLIP max-score logic, BLIP on best frame, UI polish, edge case testing, demo preparation |

---

## 12. Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| CLIP threshold miscalibrated — legitimate matches flagged as mismatch | Medium | Run 20+ test pairs before demo; measure score distribution; start conservative at 0.18 and adjust upward if too many false positives |
| BLIP inference too slow on CPU during live demo | High | Pre-load at startup; use `blip-image-captioning-base` (not large variant); cap max_new_tokens at 50; cache results for repeated identical images |
| DuckDuckGo rate-limits during demo | Low | Wrap in try/except with 5s timeout; result is always optional; pre-cache search results for demo test cases |
| Video frame processing too slow for long reels | Medium | Hard cap at 8 frames; use evenly-spaced strategy (faster than scene detection); skip scene detection for videos under 30s |
| spaCy misses entities in French or Arabic captions | Medium | Use `xx_ent_wiki_sm` multilingual model as fallback when language detection returns non-English |
| React UI too complex to finish in time | Low | Prioritise the three core sections (verdict header, flags, explanation) first; evidence and detail sections are enhancement-only |

---

*VerifyAI — Built for the hackathon. Designed to last.*  

