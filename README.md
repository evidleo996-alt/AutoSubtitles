# AI赋能的创作工具

这是一个简单的 AI 工具，用于自动提取视频的音频文件，生成 SRT 字幕文件以及md文档，提升视频或文案创作。

## 功能
- 自动提取视频中的音频
- 使用 OpenAI Whisper 模型进行高精度语音转写（可选择模型大小）
- 生成标准的 SRT 字幕文件 (带时间轴)
- 生成小红书风格的md文档用于发布于小红书等平台
- 支持配置LLM以提升整体创作质量与效率

## 安装与使用

### 1. 前置要求 (重要)
本工具依赖 **ffmpeg** 来处理视频文件。请确保您的 Mac 上已安装 ffmpeg。

**安装 ffmpeg (推荐使用 Homebrew):**
1. 打开终端 (Terminal)。
2. 运行以下命令：
   ```bash
   brew install ffmpeg
   ```
   (如果没有安装 Homebrew，请先访问 [brew.sh](https://brew.sh) 安装)

### 2. 运行工具
1. 打开终端，进入项目目录：
   ```bash
   cd Projects/Studio/AutoSubtitles
   ```
2. 激活虚拟环境并安装依赖 (首次运行需要)：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. 启动程序：
   ```bash
   python main.py
   ```

## 使用说明
1. **选择视频文件**：点击“选择文件”按钮，选取您要处理的视频 (mp4, mov, avi 等)。
2. **选择模型**：
   - `tiny`/`base`: 速度快，精度一般。
   - `small`/`medium`: 平衡速度与精度 (推荐)。
   - `large`: 精度最高，但速度较慢。
   - 注意：首次使用某个模型时，会自动下载模型文件，请耐心等待。
3. **生成字幕**：点击“生成字幕”按钮。程序会自动在视频同目录下生成同名的 `.srt` 文件。
4. **查看结果**：使用视频播放器 (如 IINA, VLC) 打开视频，通常会自动加载同名字幕文件。

## 注意事项
- 处理长视频可能需要较长时间，请保持程序运行。
- 程序界面会显示当前进度。
