---
name: science-video
description: Generate Chinese science explainer videos from a topic or markdown text. Bootstraps the full project, designs custom animations, produces TTS audio, subtitles, and rendered MP4 video.
trigger: /science-video
---

# /science-video

Generate a Chinese science explainer video from a topic description or markdown script. The pipeline: bootstrap project -> write episode content -> design custom animations -> TTS audio (Qwen3-TTS) -> subtitles -> video render (Remotion).

## Usage

```
/science-video <topic>                        # generate video from a topic (Claude writes the script)
/science-video --file <path.md>               # generate video from existing markdown file
/science-video <topic> --no-render            # generate audio + subtitles only, skip video render
/science-video <topic> --voice Bella           # use a different TTS voice (default: Cherry)
/science-video <topic> --subtitle whisper      # use Whisper ASR for subtitles instead of script timing
/science-video <topic> --segments 6            # target number of segments (default: 6-8)
/science-video <topic> --preview               # render only first 150 frames for quick preview
/science-video <topic> --project <path>        # specify project directory (default: ./science-video)
```

## Examples

```
/science-video Why is the sky blue
/science-video "Black hole formation" --segments 8
/science-video --file ./my_speech.md --no-render
/science-video "Quantum entanglement" --voice Ethan --preview
```

## How it works

### Step 0: Parse arguments

Parse the user's input to extract:
- `TOPIC`: free-text topic string (everything that is not a flag)
- `FILE`: path to an existing `.md` or `.json` file (mutually exclusive with TOPIC)
- `NO_RENDER`: if set, skip video rendering (default: false, i.e. render by default)
- `VOICE`: TTS voice name (default: `Cherry`; options: `Cherry`, `Bella`, `Ethan`, etc.)
- `SUBTITLE_SOURCE`: `script` (default) or `whisper`
- `SEGMENTS`: target segment count for generated scripts (default: 6-8)
- `PREVIEW`: if set, only render first 150 frames
- `PROJECT_DIR`: project directory path (default: `./science-video` under the current working directory)

If neither TOPIC nor FILE is provided, ask the user what topic they want.

Set `PROJECT_DIR` to the resolved absolute path. All subsequent steps use `PROJECT_DIR` as the root.

### Step 1: Bootstrap the project

Check if `PROJECT_DIR` already has the project structure by testing for `PROJECT_DIR/remotion/src/components/AnimationScene.tsx`.

**If the project does NOT exist:**

1. The scaffold template is bundled at `SKILL_BASE_DIR/scaffold/` (where `SKILL_BASE_DIR` is the directory containing this SKILL.md file). Copy the entire scaffold to `PROJECT_DIR`:

```bash
cp -r "SKILL_BASE_DIR/scaffold/." "PROJECT_DIR/"
```

This creates:
```
PROJECT_DIR/
  remotion/
    package.json
    tsconfig.json
    src/
      index.ts
      Root.tsx
      ScienceVideo.tsx
      data/script.json  (placeholder)
      components/
        AnimationScene.tsx  (base shell, no custom animations yet)
        Background.tsx
        ChartScene.tsx
        Subtitle.tsx
        TitleScene.tsx
    public/  (empty, will hold audio.mp3 and subtitles.srt)
  scripts/
    pipeline.py
    generate_audio.py
    generate_srt.py
    create_episode.py
  content/  (empty, will hold episode JSON/MD files)
  output/   (empty, will hold rendered video)
```

2. Install Node.js dependencies:
```bash
cd PROJECT_DIR/remotion && npm install
```

**If the project already exists:** skip this step. Only verify `node_modules` exists; if not, run `npm install`.

### Step 2: Prepare the episode content

**If FILE is provided:**
- If it's a `.json` file, use it directly.
- If it's a `.md` file, it will be converted automatically by the pipeline.
- Set `EPISODE_PATH` to the resolved path.

**If TOPIC is provided (no FILE):**
- Generate a Markdown speech script for the topic. The script MUST follow this format:

```markdown
# {Video Title}

## {Opening Section Title}
{Opening narration - introduce the topic, hook the viewer. 2-4 sentences.}

## {Content Section 1 Title} {animation=unique_id_1}
{Narration explaining the first key concept. 3-5 sentences.}

## {Content Section 2 Title} {animation=unique_id_2}
{Narration for the second concept. 3-5 sentences.}

...more sections as needed...

## {Closing Section Title}
{Summary and conclusion. 2-3 sentences.}
```

**Script writing guidelines:**
- Write in Chinese (Mandarin), conversational but informative tone
- Target audience: general public, no prior expertise assumed
- Each section narration should be 40-120 Chinese characters
- First section and last section become `title` type segments (intro/outro)
- Middle sections become `animation` type segments
- IMPORTANT: Every middle section MUST have a unique `{animation=xxx}` attribute. Use a short, descriptive snake_case ID that reflects the visual content (e.g., `{animation=atom_structure}`, `{animation=dna_helix}`, `{animation=solar_system}`). Do NOT use `default` — every segment gets its own custom animation.
- You may use `{type=chart, chart_type=skill_compounding}` for data-heavy segments.
- Total video should be 1-3 minutes (aim for 6-8 segments at ~10s each)

Save the generated markdown to `PROJECT_DIR/content/{slugified_topic}.md` and set `EPISODE_PATH` to that file.

**Show the generated script to the user and ask for confirmation before proceeding.** If the user wants changes, revise and re-confirm. Once confirmed, proceed to Step 3.

### Step 3: Design and implement custom animations

**This step is MANDATORY for every video generation.** Each `animation` type segment must have a purpose-built SVG animation that visually illustrates its specific content. Never reuse existing animations or fall back to `default`.

#### 3.1 Read the current AnimationScene.tsx

Read `PROJECT_DIR/remotion/src/components/AnimationScene.tsx` to understand the existing code structure.

#### 3.2 Design animations for each segment

For each middle segment (type=animation), design a custom SVG animation that:
- **Visually represents the narration content** — not just text, but diagrams, shapes, flows, or models
- Uses Remotion's `interpolate`, `spring`, `Easing` for smooth motion
- Follows the existing component pattern: `React.FC<{ frame: number; durationInFrames: number }>`
- Uses SVG with `viewBox="0 0 920 500"`
- Has entry animations (elements appearing/assembling over time)
- Has meaningful motion throughout the segment duration (not just static after entry)
- Includes a bottom caption summarizing the key insight
- Uses colors from the project palette: `#ff6b6b`, `#3ea6ff`, `#ffd166`, `#06d6a0`, `#f72585`, `#4cc9f0`, `#80ed99`
- Uses font `"Noto Sans SC", sans-serif` for Chinese text, `"Consolas, monospace"` for code/formulas

**Animation design patterns to use (pick what fits the content):**

| Pattern | When to use | Example |
|---------|-------------|---------|
| Node + arrow flow | Processes, cycles, cause-effect | Nodes appear sequentially, arrows connect them, a dot travels the path |
| Layered stack | Hierarchies, compositions | Bars/rects expand from center, stacking upward |
| Split comparison | A vs B concepts | Left/right panels fade in with contrasting content |
| Zoom/scale axis | Size comparisons, timelines | Markers appear along an axis, indicator dot moves |
| Orbital/circular | Relationships, systems | Elements orbit a center, connections pulse |
| Grid/matrix | Collections, taxonomies | Cells appear one by one with icons/labels |
| Growth curve | Accumulation, change over time | SVG path draws progressively, data points appear |
| Exploded view | Internal structure, decomposition | Object splits apart to reveal components |

#### 3.3 Implement the animations

Edit `PROJECT_DIR/remotion/src/components/AnimationScene.tsx`:

1. **Add new component functions** before the `DefaultAnimation` component. Each new animation is a `const` component:

```tsx
const MyCustomAnimation: React.FC<{ frame: number; durationInFrames: number }> = ({
  frame,
  durationInFrames,
}) => {
  // Use interpolate/spring for motion
  // Return <svg viewBox="0 0 920 500"> with animated elements
};
```

2. **Register each animation** in the main `AnimationScene` component's render block. Insert before the `{animationType === "default" ...}` line:

```tsx
{animationType === "my_custom_id" && (
  <MyCustomAnimation frame={frame} durationInFrames={durationInFrames} />
)}
```

3. **Do NOT remove or modify existing animations** — they may be used by previously generated episodes. Only add new ones.

#### 3.4 Verify the animation IDs match

Ensure every `{animation=xxx}` in the markdown file has a corresponding registered component in AnimationScene.tsx. If there's a mismatch, the segment will render empty.

### Step 4: Check prerequisites

Before running the pipeline, verify:

1. **Environment variable**: `DASHSCOPE_API_KEY` must be set. Check with:
   ```bash
   echo $DASHSCOPE_API_KEY
   ```
   If not set, tell the user to set it:
   - bash: `export DASHSCOPE_API_KEY="sk-xxx"`
   - PowerShell: `$env:DASHSCOPE_API_KEY = "sk-xxx"`
   The API key is obtained from the Alibaba Cloud DashScope platform (https://help.aliyun.com/zh/model-studio/get-api-key).

2. **Python dependencies**: `dashscope` and `requests` must be installed:
   ```bash
   python -c "import dashscope; import requests" 2>&1
   ```
   If missing: `pip install dashscope requests`

3. **FFmpeg**: Verify `ffmpeg` and `ffprobe` are on PATH:
   ```bash
   ffmpeg -version 2>/dev/null | head -1
   ffprobe -version 2>/dev/null | head -1
   ```

4. **Node.js dependencies**: Check if `PROJECT_DIR/remotion/node_modules` exists. If not, run:
   ```bash
   cd PROJECT_DIR/remotion && npm install
   ```

If any prerequisite is missing, tell the user clearly what to install and stop.

### Step 5: Run the pipeline

Execute the pipeline from the scripts directory:

```bash
cd PROJECT_DIR/scripts && python pipeline.py \
  --episode "EPISODE_PATH" \
  {--render if NO_RENDER is not set} \
  --subtitle-source {SUBTITLE_SOURCE}
```

**Important for Windows:** If there are encoding errors (GBK codec), prepend `PYTHONIOENCODING=utf-8` to the command.

If `PREVIEW` is set, instead of using `--render`, run the pipeline without `--render` first, then run:
```bash
cd PROJECT_DIR/remotion && npm run build:preview
```

The pipeline will:
1. Convert `.md` to episode JSON (if needed)
2. Generate TTS audio -> `remotion/public/audio.mp3`
3. Generate subtitles -> `remotion/public/subtitles.srt`
4. Generate script config -> `remotion/src/data/script.json`
5. (If rendering) Render video -> `output/video.mp4`

### Step 6: Report results

After the pipeline completes, report:
- Whether each step succeeded (bootstrap, script, animations, audio, subtitles, render)
- List every custom animation created and what it visualizes
- File locations of generated artifacts:
  - Episode: `PROJECT_DIR/content/{name}.json`
  - Audio: `PROJECT_DIR/remotion/public/audio.mp3`
  - Subtitles: `PROJECT_DIR/remotion/public/subtitles.srt`
  - Script config: `PROJECT_DIR/remotion/src/data/script.json`
  - Video (if rendered): `PROJECT_DIR/output/video.mp4`
- If rendering was skipped, remind the user they can:
  - Preview interactively: `cd PROJECT_DIR/remotion && npm start`
  - Render full video: `cd PROJECT_DIR/remotion && npm run build`

## Error handling

- If TTS generation fails, check `DASHSCOPE_API_KEY` and network connectivity
- If subtitle generation fails, try `--subtitle whisper` as fallback
- If Remotion render fails with a TypeScript error, it's likely a bug in the custom animation code — read the error, fix the component, and retry
- If Remotion render fails otherwise, check that Chrome/Chromium is installed and `node_modules` exists
- On Windows, if encoding errors appear, ensure `PYTHONIOENCODING=utf-8` is set
- For any pipeline error, show the full error output to the user
