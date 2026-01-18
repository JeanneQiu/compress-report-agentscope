"""FastAPI 路由"""
import os
import json
import asyncio
import logging
import traceback
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.config import Config
from app.models.schemas import (
    ReportTypesListResponse,
    SummarizeResponse,
    SSEStatusEvent,
    SSEProgressEvent,
    SSEErrorEvent,
)
from app.workflow.summarizer import ReportSummarizer, init_agentscope

logger = logging.getLogger(__name__)


router = APIRouter()
config = Config()
summarizer = ReportSummarizer()


# 初始化上传目录
os.makedirs(config.UPLOAD_DIR, exist_ok=True)


@router.get("/report/types", response_model=ReportTypesListResponse)
async def get_report_types():
    """获取报告类型列表"""
    return ReportTypesListResponse(types=config.get_report_types())


@router.post("/report/summarize", response_model=SummarizeResponse)
async def summarize_report(
    report_type: str = Form(...),
    max_words: int = Form(config.DEFAULT_MAX_WORDS),
    max_paragraphs: int = Form(config.DEFAULT_MAX_PARAGRAPHS),
    requirements: str = Form(""),
    files: List[UploadFile] = File(...),
):
    """生成报告摘要（非流式）"""
    
    # 验证报告类型（去除前后空格）
    report_type = report_type.strip()
    valid_types = [rt["value"] for rt in config.get_report_types()]
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的报告类型: {report_type}")
    
    # 保存上传的文件
    file_paths = []
    try:
        for file in files:
            file_path = os.path.join(config.UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append((file_path, file.filename))
        
        # 生成摘要
        report_markdown, meta = await summarizer.summarize(
            report_type=report_type,
            file_paths=file_paths,
            max_words=max_words,
            max_paragraphs=max_paragraphs,
            requirements=requirements,
        )
        
        return SummarizeResponse(report_markdown=report_markdown, meta=meta)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 清理临时文件
        for file_path, _ in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)


async def _summarize_stream_generator(
    report_type: str,
    file_paths: List[tuple],
    max_words: int,
    max_paragraphs: int,
    requirements: str,
):
    """流式生成摘要的生成器 - 支持增量内容传输"""
    
    # 创建事件队列
    event_queue = asyncio.Queue()
    
    async def progress_callback(stage: str, status: str, message: str):
        """进度回调函数"""
        if stage == "progress":
            # 进度事件
            await event_queue.put({
                "event": "progress",
                "data": json.dumps({"message": message}, ensure_ascii=False)
            })
        else:
            # 状态事件
            await event_queue.put({
                "event": "status",
                "data": json.dumps({
                    "stage": stage,
                    "status": status,
                    "message": message
                }, ensure_ascii=False)
            })
    
    async def stream_callback(delta: str):
        """流式内容回调函数 - 接收增量内容"""
        await event_queue.put({
            "event": "content",
            "data": json.dumps({"delta": delta}, ensure_ascii=False)
        })
    
    # 创建摘要生成任务
    async def generate_summary():
        try:
            report_markdown, meta = await summarizer.summarize(
                report_type=report_type,
                file_paths=file_paths,
                max_words=max_words,
                max_paragraphs=max_paragraphs,
                requirements=requirements,
                progress_callback=progress_callback,
                stream_callback=stream_callback,
            )
            # 将结果放入队列
            await event_queue.put({
                "event": "result",
                "data": json.dumps({
                    "report_markdown": report_markdown,
                    "meta": meta.model_dump()
                }, ensure_ascii=False)
            })
        except Exception as e:
            # 记录完整的错误堆栈到日志
            logger.error(f"摘要生成失败: {str(e)}\n{traceback.format_exc()}")
            await event_queue.put({
                "event": "error",
                "data": json.dumps({
                    "message": str(e),
                    "trace_id": ""
                }, ensure_ascii=False)
            })
    
    # 启动摘要生成任务
    summary_task = asyncio.create_task(generate_summary())
    
    try:
        # 从队列中获取事件并 yield
        while True:
            event = await event_queue.get()
            yield event
            
            # 如果是结果或错误事件，结束生成
            if event["event"] in ("result", "error"):
                break
    
    except Exception as e:
        logger.error(f"流式生成器错误: {str(e)}\n{traceback.format_exc()}")
        yield {
            "event": "error",
            "data": json.dumps({
                "message": str(e),
                "trace_id": ""
            }, ensure_ascii=False)
        }


@router.post("/report/summarize/stream")
async def summarize_report_stream(
    report_type: str = Form(...),
    max_words: int = Form(config.DEFAULT_MAX_WORDS),
    max_paragraphs: int = Form(config.DEFAULT_MAX_PARAGRAPHS),
    requirements: str = Form(""),
    files: List[UploadFile] = File(...),
):
    """生成报告摘要（流式 SSE）"""
    # 验证报告类型（去除前后空格）
    report_type = report_type.strip()
    valid_types = [rt["value"] for rt in config.get_report_types()]
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的报告类型: {report_type}")
    
    # 保存上传的文件
    file_paths = []
    try:
        for file in files:
            file_path = os.path.join(config.UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append((file_path, file.filename))
        
        # 返回 SSE 流
        return EventSourceResponse(
            _summarize_stream_generator(
                report_type=report_type,
                file_paths=file_paths,
                max_words=max_words,
                max_paragraphs=max_paragraphs,
                requirements=requirements,
            )
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 清理临时文件（在后台任务中）
        async def cleanup():
            await asyncio.sleep(5)  # 等待流式传输完成
            for file_path, _ in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        asyncio.create_task(cleanup())
