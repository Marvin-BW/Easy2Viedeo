# Science Video Generator

📖 **[中文版本](./README_zh.md)** | **English** ⚡

**One-click Generation of High-Quality Science Explainer Videos - Claude Code Skill** ⚡

A powerful Chinese science explainer video generation tool. Automatically generate high-quality videos with custom animations, TTS voiceover, and synchronized subtitles by simply inputting a topic or Markdown script.

## 🎯 Features

- **Automatic Script Generation**: Generate science explanation scripts from topics (Chinese)
- **Custom Animations**: Design unique SVG animations for each scene
- **TTS Voice Synthesis**: Integrated Alibaba Cloud DashScope TTS with multiple voices
- **Auto Subtitles**: Script-synchronized or Whisper ASR subtitles
- **Video Rendering**: Generate high-quality MP4 videos using the Remotion framework
- **Complete Pipeline**: One-click generation from script to finished video

## 🚀 Quick Start

### Basic Usage

```bash
/science-video Why is the sky blue
/science-video Black hole formation --segments 8
/science-video --file ./my_script.md
/science-video Quantum entanglement --voice Ethan --preview
```

### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file <path.md>` | Use existing Markdown file | - |
| `--no-render` | Skip video rendering, audio & subtitles only | false |
| `--voice <name>` | TTS voice (Cherry, Bella, Ethan, etc.) | Cherry |
| `--subtitle <source>` | Subtitle source (`script` or `whisper`) | script |
| `--segments <n>` | Target segment count | 6-8 |
| `--preview` | Render first 150 frames only | false |
| `--project <path>` | Project directory | ./science-video |

## 📋 Project Structure

```
science-video/
├── scaffold/
│   ├── remotion/              # Remotion video rendering project
│   │   ├── src/
│   │   │   ├── components/    # Animation components (AnimationScene.tsx, etc.)
│   │   │   ├── Root.tsx       # Main video component
│   │   │   └── data/          # Script data
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── scripts/               # Python processing scripts
│       ├── pipeline.py        # Main processing pipeline
│       ├── generate_audio.py  # TTS audio generation
│       └── generate_srt.py    # Subtitle generation
├── SKILL.md                   # Technical documentation
└── README.md                  # This file
```

## 🔧 Environment Setup

### Required Environment Variables

```bash
# Set DashScope API Key (for TTS)
export DASHSCOPE_API_KEY="sk-xxx"
```

Get your API Key from [Alibaba Cloud DashScope Console](https://help.aliyun.com/en/model-studio/get-api-key).

### Dependencies

- **Node.js** (v16+): For Remotion video rendering
- **Python** (3.8+): For script processing
  - `dashscope`: TTS audio generation
  - `requests`: HTTP requests
- **FFmpeg** & **FFprobe**: Audio/video processing
- **Chrome/Chromium**: Required for Remotion rendering

### Install Dependencies

```bash
# Python dependencies
pip install dashscope requests

# Node.js dependencies (auto-installed on first run)
cd science-video/remotion
npm install
```

## 📹 Example Output

**Input Topic:** `What is the smallest unit in physics`

**Output:** `video.mp4` - Auto-generated high-quality science explainer video (with custom animations, TTS voiceover, and synchronized subtitles)

This video is completely auto-generated. Users provide just one topic, and the tool will:
- Auto-generate a science script
- Design multiple unique SVG animations
- Generate Chinese voice narration
- Add synchronized Chinese subtitles
- Render the final MP4 video

## 💡 Usage Examples

### Example 1: Generate Video from Topic

```bash
/science-video Wave-particle duality of light
```

The tool will:
1. Generate a science script (3-5 segments)
2. Request your confirmation of the script
3. Design custom animations for each segment
4. Generate TTS audio
5. Generate synchronized subtitles
6. Render final video → `output/video.mp4`

### Example 2: Audio & Subtitles Only

```bash
/science-video Cell division --no-render
```

Skip video rendering and quickly generate audio and subtitles. Later, manually render:

```bash
cd science-video/remotion
npm run build
```

### Example 3: Use Existing Script

Create `my_script.md`:

```markdown
# DNA Double Helix Structure

## Opening
DNA is the instruction manual of life, found in the nucleus of every cell...

## DNA Discovery {animation=dna_discovery}
In 1953, Watson and Crick first revealed DNA's double helix structure...

## Double Helix Model {animation=dna_helix}
DNA is composed of four bases: adenine, thymine, guanine, and cytosine...

## Genetic Code {animation=genetic_code}
DNA sequences contain the complete instructions for building proteins...

## Conclusion
DNA is the most complex and elegant molecule on Earth...
```

Then run:

```bash
/science-video --file ./my_script.md
```

## 🎨 Animation Design

Each video segment requires a custom SVG animation. The framework provides 7 common animation patterns:

| Pattern | Use Case | Example |
|---------|----------|---------|
| Node Flow | Processes, cycles, cause-effect | Flowchart, matter cycle |
| Layered Stack | Hierarchies, compositions | Geological layers, data structures |
| Split Comparison | A vs B concepts | DNA vs RNA, light vs sound |
| Zoom/Scale Axis | Size comparisons, timelines | Galaxy sizes, evolution timeline |
| Orbital/Circular | Relationships, systems | Solar system, atomic structure |
| Grid/Matrix | Collections, taxonomies | Periodic table, species classification |
| Growth Curve | Accumulation, change over time | Population growth, temperature rise |

### Custom Animation Example

All animations are defined in `remotion/src/components/AnimationScene.tsx`. Each animation is a React component:

```tsx
const DnaHelix: React.FC<{ frame: number; durationInFrames: number }> = ({
  frame,
  durationInFrames,
}) => {
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    easing: Easing.inOut(Easing.ease),
  });

  return (
    <svg viewBox="0 0 920 500">
      {/* Animation content */}
    </svg>
  );
};
```

## 🐛 Troubleshooting

### TTS Generation Fails

```bash
# Check API Key
echo $DASHSCOPE_API_KEY

# Check network and Python dependencies
python -c "import dashscope; import requests"
```

### Subtitle Generation Fails

Use Whisper ASR as fallback:

```bash
/science-video your-topic --subtitle whisper
```

### Video Rendering Fails

1. Ensure Chrome/Chromium is installed
2. Check that `remotion/node_modules` exists
3. Look for TypeScript errors in logs (usually animation component issues)

### Windows Encoding Errors

Set environment variable before running the pipeline:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

## 📚 Tech Stack

- **Video Rendering**: [Remotion](https://www.remotion.dev/) (React video framework)
- **TTS Voice**: [Alibaba Cloud DashScope](https://help.aliyun.com/en/model-studio)
- **Subtitle Generation**: Script-synchronized or [Whisper](https://openai.com/research/whisper)
- **Animation**: SVG + React + Remotion API
- **Processing Pipeline**: Python 3.8+

## 📄 License

MIT

## 🤝 Contributing

Issues and Pull Requests welcome!

---

**Quick Links**
- [SKILL.md](./SKILL.md) - Complete technical documentation
- [DashScope API Docs](https://help.aliyun.com/en/model-studio)
- [Remotion Official Docs](https://www.remotion.dev/docs)
