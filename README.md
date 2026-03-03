# AI 赋能的创作工具 (AutoSubtitles)

AutoSubtitles 是一个 AI 字幕处理与内容辅助创作项目，支持视频/音频转写、字幕润色、笔记生成与下载。

## 核心能力
- 自动提取音频并进行语音识别
- 使用 Whisper 生成带时间轴的 SRT 字幕
- 可选接入 LLM 做字幕润色、摘要和笔记生成
- 提供本地 Web 界面，支持上传、处理、下载全流程

## 快速开始

### 1) 准备环境
- Python 3.10+
- ffmpeg

在 macOS 上安装 ffmpeg：

```bash
brew install ffmpeg
```

### 2) 安装依赖

```bash
cd /Volumes/T7/编程项目/Projects/Studio/AutoSubtitles
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) 启动 Web 服务

```bash
bash run.sh
```

浏览器打开：

```text
http://localhost:8000
```

## 开源与协作

本项目使用 MIT 协议开源，详见 [LICENSE](./LICENSE)。

你可以：
- Fork 项目后自行修改
- 提交 Issue 反馈问题
- 提交 Pull Request 贡献代码

## GitHub Pages 前端展示

本仓库已配置 GitHub Pages 自动部署静态前端演示页（通过 GitHub Actions）。

注意：
- GitHub Pages 只能托管静态页面
- 上传/处理/下载等能力依赖 Python 后端，Pages 上仅用于 UI 展示

如果你要让他人在线“完整使用”上传与处理能力，建议把后端部署到 Render / Railway / Fly.io / 云服务器，并把前端请求地址指向后端公网 API。

## 发布你的开源仓库

1. 将仓库设置为 Public  
   GitHub 仓库页面 → Settings → General → Danger Zone / Change visibility

2. 启用 Pages  
   GitHub 仓库页面 → Settings → Pages → Build and deployment  
   Source 选择 `GitHub Actions`

3. 推送代码触发部署  

```bash
git add .
git commit -m "chore: enable open-source docs and pages"
git push origin main
```

部署成功后可在：

```text
https://<你的用户名>.github.io/<仓库名>/
```

查看前端演示。
