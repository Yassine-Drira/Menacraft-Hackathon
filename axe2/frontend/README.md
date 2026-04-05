# VerifyAI Frontend

React frontend for the VerifyAI multimodal context verification system.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` and proxy API requests to `http://localhost:8000`.

## Components

- **UploadForm** - File upload and caption input
- **LoadingState** - Animated loading with stage updates
- **VerdictHeader** - Score gauge and verdict badge
- **FlagChips** - Detected inconsistency flags
- **Explanation** - Human-readable explanation
- **AnalysisDetail** - CLIP score, BLIP description, extracted entities
- **Evidence** - Search results (when enabled)

## Features

- Drag-and-drop file upload
- Real-time caption validation
- Responsive design for mobile
- Color-coded score visualization
- Expandable analysis details
- Evidence search toggle