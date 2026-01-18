"""配置管理模块"""
import os
from typing import List
from enum import Enum


class ReportType(str, Enum):
    """报告类型枚举"""
    ELECTRICITY_DEMAND = "用电需求预测报告"
    PEAK_SUMMER_WINTER = "迎峰度冬(夏)分析报告"
    SPECIAL_TOPIC = "特定专题分析报告"
    TEMPORARY = "临时性分析报告"
    REGULAR = "常态化分析报告"


REPORT_TYPE_DESCRIPTIONS = {
    ReportType.ELECTRICITY_DEMAND: "主体是针对特定时间节点的负荷或电量进行预测的报告",
    ReportType.PEAK_SUMMER_WINTER: "针对迎峰度冬/度夏期间最大负荷进行复盘分析的报告",
    ReportType.SPECIAL_TOPIC: "针对不同主题（特殊事件、热点方向）对用电影响进行分析研判的报告",
    ReportType.TEMPORARY: "针对某一时间段的电力电量特殊变化进行分析的报告",
    ReportType.REGULAR: "日/周/旬/月/年用电监测分析报告",
}


class Config:
    """应用配置类"""
    
    # API 配置
    API_PREFIX: str = os.getenv("API_PREFIX", "/v1")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "6060"))
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))  # 100MB
    
    # 文件上传配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # LLM 配置
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3-4b")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://0.0.0.0:10010/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    
    # 默认约束
    DEFAULT_MAX_WORDS: int = 8196
    DEFAULT_MAX_PARAGRAPHS: int = 100
    
    @classmethod
    def get_report_types(cls) -> List[dict]:
        """获取报告类型列表"""
        return [
            {
                "value": rt.value,
                "description": REPORT_TYPE_DESCRIPTIONS.get(rt, "")
            }
            for rt in ReportType
        ]


# 全局配置实例
config = Config()