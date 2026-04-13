# Science Video Generator

**一键生成高质量科学解释视频的 Claude Code Skill** ⚡

一个强大的中文科学解释视频生成工具。通过输入主题或 Markdown 脚本，自动生成包含自定义动画、TTS 语音和字幕的高质量视频。

## 🎯 功能特性

- **自动脚本生成**：从主题自动生成科学解释脚本（中文）
- **自定义动画**：为每个场景设计独特的 SVG 动画
- **TTS 语音合成**：集成阿里云 DashScope TTS，支持多种声音
- **自动字幕**：脚本同步或 Whisper ASR 字幕
- **视频渲染**：使用 Remotion 框架生成高质量 MP4 视频
- **完整管道**：一键生成从脚本到视频的全流程

## 🚀 快速开始

### 基本用法

```bash
/science-video 为什么天空是蓝色的
/science-video 黑洞形成 --segments 8
/science-video --file ./my_script.md
/science-video 量子纠缠 --voice Ethan --preview
```

### 命令选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--file <path.md>` | 使用现有 Markdown 文件 | - |
| `--no-render` | 仅生成音频和字幕，跳过视频渲染 | false |
| `--voice <name>` | TTS 语音（Cherry, Bella, Ethan 等） | Cherry |
| `--subtitle <source>` | 字幕源 (`script` 或 `whisper`) | script |
| `--segments <n>` | 目标段数 | 6-8 |
| `--preview` | 仅渲染前 150 帧作为预览 | false |
| `--project <path>` | 项目目录 | ./science-video |

## 📋 项目结构

```
science-video/
├── scaffold/
│   ├── remotion/              # Remotion 视频渲染项目
│   │   ├── src/
│   │   │   ├── components/    # 动画组件（AnimationScene.tsx 等）
│   │   │   ├── Root.tsx       # 主视频组件
│   │   │   └── data/          # 脚本数据
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── scripts/               # Python 处理脚本
│       ├── pipeline.py        # 主处理管道
│       ├── generate_audio.py  # TTS 音频生成
│       └── generate_srt.py    # 字幕生成
├── SKILL.md                   # 技术文档
└── README.md                  # 本文件
```

## 🔧 环境需求

### 必需环境变量

```bash
# 设置 DashScope API Key（用于 TTS）
export DASHSCOPE_API_KEY="sk-xxx"
```

在 [阿里云 DashScope 控制台](https://help.aliyun.com/zh/model-studio/get-api-key) 获取 API Key。

### 依赖项

- **Node.js** (v16+)：用于 Remotion 视频渲染
- **Python** (3.8+)：用于脚本处理
  - `dashscope`：TTS 音频生成
  - `requests`：HTTP 请求
- **FFmpeg** & **FFprobe**：音视频处理
- **Chrome/Chromium**：Remotion 渲染需要

### 安装依赖

```bash
# Python 依赖
pip install dashscope requests

# Node.js 依赖（首次运行时自动安装）
cd science-video/remotion
npm install
```

## 📹 示例输出

**输入主题：** `什么是物理学中的最小单位`

<video width="100%" controls style="max-width: 800px; margin: 20px 0; border-radius: 8px;">
  <source src="video.mp4" type="video/mp4">
  您的浏览器不支持视频标签。请升级浏览器或直接下载视频文件。
</video>

**输出：** `video.mp4` - 自动生成的高质量科学解释视频（包含自定义动画、TTS 语音配音和同步字幕）

这个视频完全由工具自动生成，用户只需提供一句话主题，工具就会：
- 自动生成科学脚本
- 设计多个独特的 SVG 动画
- 生成中文语音配音
- 添加同步中文字幕
- 渲染最终的 MP4 视频

## 💡 使用示例

### 示例 1：从主题生成视频

```bash
/science-video 光的波粒二象性
```

工具将：
1. 生成中文科学脚本（3-5 段）
2. 请求你确认脚本内容
3. 设计每段的自定义动画
4. 生成 TTS 音频
5. 生成同步字幕
6. 渲染最终视频 → `output/video.mp4`

### 示例 2：仅生成音频和字幕

```bash
/science-video 细胞分裂 --no-render
```

跳过视频渲染，快速生成音频和字幕。之后可以手动渲染：

```bash
cd science-video/remotion
npm run build
```

### 示例 3：使用现有脚本

创建 `my_script.md`：

```markdown
# DNA 双螺旋结构

## 开场
DNA 是生命的指令，它存在于我们每个细胞核中...

## DNA 的发现 {animation=dna_discovery}
1953 年，沃特森和克里克首次揭示了 DNA 的双螺旋结构...

## 双螺旋模型 {animation=dna_helix}
DNA 由四种碱基组成：腺嘌呤、胸腺嘧啶、鸟嘌呤和胞嘧啶...

## 遗传密码 {animation=genetic_code}
DNA 序列包含了制造蛋白质的完整指令...

## 总结
DNA 是地球上最复杂、最优雅的分子...
```

然后运行：

```bash
/science-video --file ./my_script.md
```

## 🎨 动画设计

每个视频段都需要一个自定义的 SVG 动画。框架提供了 7 种常见动画模式：

| 模式 | 应用场景 | 例子 |
|------|--------|------|
| 节点流 | 过程、循环、因果关系 | 流程图、物质循环 |
| 分层堆叠 | 层次、组合关系 | 地质分层、数据结构 |
| 分割对比 | A vs B 概念对比 | DNA vs RNA、光 vs 声 |
| 缩放轴线 | 大小比较、时间线 | 星系大小、演化时间 |
| 轨道圆形 | 系统关系、连接 | 太阳系、原子结构 |
| 网格矩阵 | 集合、分类 | 元素周期表、物种分类 |
| 增长曲线 | 积累、变化 | 种群增长、温度上升 |

### 自定义动画示例

所有动画都在 `remotion/src/components/AnimationScene.tsx` 中定义。每个动画是一个 React 组件：

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
      {/* 动画内容 */}
    </svg>
  );
};
```

## 🐛 故障排除

### TTS 生成失败

```bash
# 检查 API Key
echo $DASHSCOPE_API_KEY

# 检查网络连接和 Python 依赖
python -c "import dashscope; import requests"
```

### 字幕生成失败

使用 Whisper ASR 作为备选：

```bash
/science-video 你的主题 --subtitle whisper
```

### 视频渲染失败

1. 确保 Chrome/Chromium 已安装
2. 检查 `remotion/node_modules` 存在
3. 查看错误日志中的 TypeScript 错误（通常是动画组件问题）

### Windows 编码错误

在运行管道前设置环境变量：

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

## 📚 技术栈

- **视频渲染**：[Remotion](https://www.remotion.dev/) (React 视频框架)
- **TTS 语音**：[阿里云 DashScope](https://help.aliyun.com/zh/model-studio)
- **字幕生成**：脚本同步或 [Whisper](https://openai.com/research/whisper)
- **动画**：SVG + React + Remotion API
- **处理管道**：Python 3.8+

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**快速链接**
- [SKILL.md](./SKILL.md) - 完整技术文档
- [DashScope API 文档](https://help.aliyun.com/zh/model-studio)
- [Remotion 官方文档](https://www.remotion.dev/docs)
