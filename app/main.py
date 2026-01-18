"""主程序入口"""
import uvicorn
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config
from app.api.routes import router
from app.workflow.summarizer import init_agentscope

os.makedirs("logs", exist_ok=True)
# 配置日志 - 同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('logs/app.log', encoding='utf-8')  # 输出到文件
    ]
)
logger = logging.getLogger(__name__)


# 初始化配置
config = Config()

# 初始化 AgentScope
init_agentscope()

# 创建 FastAPI 应用
app = FastAPI(
    title="精简报告生成服务",
    description="基于 AgentScope 的报告摘要生成服务",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=config.API_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "精简报告生成服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info(f"启动服务器: {config.HOST}:{config.PORT}")
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info",
        access_log=True,
    )