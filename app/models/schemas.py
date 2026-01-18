"""数据模型和请求/响应 schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ReportTypeRequest(BaseModel):
    """报告类型请求"""
    report_type: str = Field(..., description="报告类型")
    max_words: int = Field(8196, description="最大字数", ge=1)
    max_paragraphs: int = Field(100, description="最大段落数", ge=1)
    requirements: str = Field("", description="特定要求")


class ReportTypeResponse(BaseModel):
    """报告类型响应"""
    value: str
    description: str


class ReportTypesListResponse(BaseModel):
    """报告类型列表响应"""
    types: List[ReportTypeResponse]


class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str
    filename: str
    text_md: str
    warnings: List[str] = []


class DocumentSummary(BaseModel):
    """文档摘要"""
    doc_id: str
    summary_md: str


class MetaInfo(BaseModel):
    """元数据信息"""
    used_files: List[str]
    hash: str
    model: str
    base_url: str
    temperature: float
    total_duration_ms: float
    stage_durations_ms: dict
    trace_id: str
    warnings: List[str] = []


class SummarizeResponse(BaseModel):
    """摘要响应"""
    report_markdown: str
    meta: MetaInfo


class SSEEvent(BaseModel):
    """SSE 事件"""
    event: str
    data: dict


class SSEStatusEvent(BaseModel):
    """SSE 状态事件"""
    stage: str
    status: str  # "start" or "end"
    message: str


class SSEProgressEvent(BaseModel):
    """SSE 进度事件"""
    current: int
    total: int
    filename: str


class SSEErrorEvent(BaseModel):
    """SSE 错误事件"""
    message: str
    trace_id: str