#!/bin/bash

# 获取当前脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在检查环境..."

# 添加本地 bin 目录到 PATH
export PATH="$DIR/bin:$PATH"

# 检查 ffmpeg
if ! command -v ffmpeg &> /dev/null
then
    echo "警告: 未找到 ffmpeg。视频处理功能将无法使用。"
    echo "请尝试运行: brew install ffmpeg"
    # 不退出，继续运行 server
else
    echo "ffmpeg check passed."
fi

# 检查 Python 环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 运行 Web 服务 (FastAPI)
echo "正在启动 AutoSubtitles Web 服务..."
echo "访问地址: http://localhost:8000"
python server.py
