import os
from pathlib import Path
from uuid import uuid4
import aiofiles
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

from services.task_manager import task_manager
from services.workflow import run_simple_pipeline
from config import Config

app = FastAPI(title="Simple AI Subtitles")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path("static")
UPLOAD_DIR = Config.UPLOAD_DIR
ASSETS_DIR = Config.ASSETS_DIR

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Models
class ProcessRequest(BaseModel):
    task_id: str
    model_size: Literal["tiny", "base", "small", "medium", "large"] = Config.DEFAULT_MODEL_SIZE
    use_llm: bool = False
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    humor_level: Literal["none", "moderate", "high"] = "none"
    generate_note: bool = False


class UploadResponse(BaseModel):
    task_id: str
    message: str


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str


DOWNLOAD_FILE_TYPES: Dict[str, str] = {
    "audio": "audio_file",
    "srt": "srt_file",
    "optimized_srt": "optimized_srt_file",
    "note": "note_file"
}


def build_error_detail(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def raise_api_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail=build_error_detail(code, message))


def get_task_or_404(task_id: str) -> Dict[str, Any]:
    task = task_manager.get_task(task_id)
    if not task:
        raise_api_error(404, "TASK_NOT_FOUND", "任务不存在")
    return task


def resolve_download_path(file_path: str) -> Path:
    resolved = Path(file_path).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if resolved != upload_root and upload_root not in resolved.parents:
        raise_api_error(404, "FILE_NOT_FOUND", "文件不存在")
    return resolved


async def save_upload_file(file: UploadFile) -> Path:
    if not file.filename:
        raise_api_error(400, "INVALID_FILENAME", "文件名无效")
    safe_name = Path(file.filename).name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in Config.ALLOWED_EXTENSIONS:
        raise_api_error(400, "UNSUPPORTED_FILE_TYPE", "不支持的文件类型")

    target_path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    total_size = 0
    chunk_size = 1024 * 1024
    async with aiofiles.open(target_path, "wb") as f:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > Config.MAX_FILE_SIZE:
                await file.close()
                target_path.unlink(missing_ok=True)
                raise_api_error(400, "FILE_TOO_LARGE", "文件过大")
            await f.write(chunk)
    await file.close()
    return target_path

# --- Endpoints ---

@app.get("/")
async def read_root():
    return FileResponse(ASSETS_DIR / "app_ui.html")

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_path = await save_upload_file(file)
    task_id = task_manager.create_task(str(file_path.resolve()))
    return UploadResponse(task_id=task_id, message="上传成功")

@app.post("/process", response_model=MessageResponse)
async def start_process(request: ProcessRequest, background_tasks: BackgroundTasks):
    get_task_or_404(request.task_id)
    background_tasks.add_task(run_simple_pipeline, request.task_id, request.model_dump())
    return MessageResponse(message="任务已启动")

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    return get_task_or_404(task_id)

@app.get("/download/{task_id}/{file_type}")
async def download_file(task_id: str, file_type: Literal["audio", "srt", "optimized_srt", "note"]):
    task = get_task_or_404(task_id)
    data_key = DOWNLOAD_FILE_TYPES.get(file_type)
    if not data_key:
        raise_api_error(404, "FILE_NOT_FOUND", "文件不存在")
    file_path = task.get(data_key)
    if not file_path:
        raise_api_error(404, "FILE_NOT_FOUND", "文件不存在")

    resolved = resolve_download_path(file_path)
    if not resolved.exists():
        raise_api_error(404, "FILE_NOT_FOUND", "文件不存在")
    return FileResponse(str(resolved), filename=resolved.name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
