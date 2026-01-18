# 精简报告生成服务

基于 FastAPI + AgentScope + MarkItDown 的报告摘要生成服务。

## 代码阅读指南

### 推荐阅读顺序

建议按照以下顺序阅读代码，从入口到核心逻辑：

1. **[`app/main.py`](app/main.py)** - 程序入口
   - FastAPI 应用初始化
   - 路由注册
   - AgentScope 初始化

2. **[`app/config.py`](app/config.py)** - 配置管理
   - 报告类型枚举定义
   - 环境变量配置
   - 全局配置实例

3. **[`app/models/schemas.py`](app/models/schemas.py)** - 数据模型
   - 请求/响应数据结构
   - Pydantic 模型定义

4. **[`app/prompts/templates.py`](app/prompts/templates.py)** - Prompt 模板
   - 5种报告类型的 Prompt 模板
   - 三阶段 Prompt（逐文档压缩、总体压缩、验证修订）

5. **[`app/utils/document_parser.py`](app/utils/document_parser.py)** - 文档解析
   - MarkItDown 文档解析器
   - 文件转 Markdown 功能

6. **[`app/workflow/summarizer.py`](app/workflow/summarizer.py)** - 核心工作流
   - 四阶段处理流程
   - LLM 调用与日志记录

7. **[`app/api/routes.py`](app/api/routes.py)** - API 路由
   - FastAPI 接口定义
   - 文件上传处理
   - SSE 流式输出

### 各文件功能详解

#### [`app/main.py`](app/main.py) - 程序入口
- **功能**：FastAPI 应用的启动入口
- **核心内容**：
  - 初始化 AgentScope 日志系统
  - 创建 FastAPI 应用实例
  - 配置 CORS 中间件
  - 注册 API 路由
  - 提供根路径和健康检查接口

#### [`app/config.py`](app/config.py) - 配置管理
- **功能**：统一管理应用配置
- **核心内容**：
  - `ReportType` 枚举：定义 5 种报告类型
  - `Config` 类：从环境变量读取配置
  - 配置项：API 前缀、端口、LLM 配置、上传目录等

#### [`app/models/schemas.py`](app/models/schemas.py) - 数据模型
- **功能**：定义 API 请求和响应的数据结构
- **核心内容**：
  - `ReportTypeRequest`：报告摘要请求参数
  - `SummarizeResponse`：报告摘要响应结果
  - `DocumentInfo`：解析后的文档信息
  - `MetaInfo`：元数据（trace_id、耗时、警告等）
  - SSE 事件模型（状态、进度、错误）

#### [`app/prompts/templates.py`](app/prompts/templates.py) - Prompt 模板
- **功能**：为不同报告类型和工作流阶段提供 Prompt 模板
- **核心内容**：
  - `DOC_COMPRESS_TEMPLATES`：逐文档压缩 Prompt（5种类型）
  - `GLOBAL_COMPRESS_TEMPLATES`：总体压缩 Prompt（5种类型）
  - `VALIDATE_TEMPLATES`：验证修订 Prompt（5种类型）
  - 每个模板都包含约束条件和格式要求

#### [`app/utils/document_parser.py`](app/utils/document_parser.py) - 文档解析
- **功能**：将上传的文件转换为 Markdown 格式
- **核心内容**：
  - `DocumentParser` 类：封装 MarkItDown 解析器
  - `parse_file()`：解析单个文件
  - `parse_files()`：批量解析文件
  - `calculate_hash()`：计算内容哈希值

#### [`app/workflow/summarizer.py`](app/workflow/summarizer.py) - 核心工作流
- **功能**：实现报告摘要生成的四阶段工作流
- **核心内容**：
  - `ReportSummarizer` 类：核心业务逻辑
  - 四阶段流程：
    1. **parse**：解析文件为 Markdown
    2. **doc_compress**：逐文档压缩
    3. **global_compress**：总体压缩（融合多份摘要）
    4. **validate**：验证约束并修订
  - LLM 调用与 AgentScope 日志记录
  - 字数/段落数统计

#### [`app/api/routes.py`](app/api/routes.py) - API 路由
- **功能**：定义 FastAPI 接口端点
- **核心内容**：
  - `GET /v1/report/types`：获取报告类型列表
  - `POST /v1/report/summarize`：非流式摘要生成
  - `POST /v1/report/summarize/stream`：流式 SSE 摘要生成
  - 文件上传与临时文件管理
  - SSE 事件流生成器

### 数据流向

```
用户请求 (FastAPI)
    ↓
routes.py (接收请求、保存文件)
    ↓
summarizer.py (四阶段工作流)
    ├─→ document_parser.py (解析文件)
    ├─→ templates.py (获取 Prompt)
    └─→ LLM 调用 (AgentScope)
    ↓
返回结果 (JSON / SSE)
```

### 关键概念

1. **报告类型**：5 种预定义的报告类型，每种有独立的 Prompt 模板
2. **四阶段工作流**：parse → doc_compress → global_compress → validate
3. **约束条件**：max_words、max_paragraphs、requirements
4. **日志追踪**：trace_id 关联所有 LLM 调用和阶段日志
5. **流式输出**：SSE 实时推送处理进度

## 目录说明

- `uploads/` - 文件上传临时目录（处理完成后自动删除）
- `logs/` - AgentScope 日志目录（包含 LLM 输出日志、阶段耗时、trace_id）

## 功能特性

- 支持多种报告类型（用电需求预测、迎峰度冬/夏、特定专题、临时性、常态化）
- 支持多文件上传（PDF/DOCX/MD/TXT）
- 逐文档压缩 + 总体压缩 + 验证修订的三阶段工作流
- 支持流式 SSE 输出
- 完整的日志追踪（trace_id、阶段耗时、LLM 输出日志）

## 环境要求

- Python 3.10+
- conda 环境

## 创建 conda 环境

```bash
# 创建新的 conda 环境
conda create -n compress python=3.10 -y

# 激活环境
conda activate compress

# 安装依赖
pip install -r requirements.txt
```

## 打包 conda 环境（用于离线部署）

```bash
# 确保已安装 conda-pack
pip install conda-pack

# 打包当前环境
conda pack -n compress_report_env -o compress_report_env.tar.gz
```

## 离线部署

```bash
# 解压环境包
tar -xzf compress_report_env.tar.gz

# 激活环境并修复路径
source bin/activate
conda-unpack

# 启动服务
python -m app.main
```

## 配置环境变量

编辑 `.env` 文件：

```env
API_PREFIX=/v1
HOST=0.0.0.0
PORT=6060
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=uploads
LLM_MODEL=qwen3-4b
LLM_BASE_URL=http://0.0.0.0:10010/v1
LLM_API_KEY=
LLM_TEMPERATURE=0.3
```

## 启动服务

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 6060
```

## API 接口

### 获取报告类型列表

```
GET /v1/report/types
```

### 生成报告摘要（非流式）

```
POST /v1/report/summarize
Content-Type: multipart/form-data

report_type: 用电需求预测报告
max_words: 8196
max_paragraphs: 100
requirements: 必须包含数据来源
files: [file1.pdf, file2.docx]
```

### 生成报告摘要（流式 SSE）

```
POST /v1/report/summarize/stream
Content-Type: multipart/form-data
Accept: text/event-stream

参数同上
```

## API 测试

### 使用 Swagger UI（推荐）

启动服务后，访问以下地址查看自动生成的 API 文档并进行交互式测试：

- Swagger UI: http://localhost:6060/docs
- ReDoc: http://localhost:6060/redoc

在 Swagger UI 中可以直接：
1. 查看所有 API 接口
2. 填写参数并上传文件
3. 点击 "Execute" 执行请求
4. 查看响应结果

### 使用 curl 测试

#### 获取报告类型列表

```bash
curl -X GET "http://localhost:6060/v1/report/types"
```

#### 生成报告摘要（非流式）

```bash
curl -X POST "http://localhost:6060/v1/report/summarize" \
  -F "report_type=用电需求预测报告" \
  -F "max_words=8196" \
  -F "max_paragraphs=100" \
  -F "requirements=" \
  -F "files=@/path/to/file1.pdf" \
  -F "files=@/path/to/file2.docx"
```

#### 生成报告摘要（流式 SSE）

```bash
curl -X POST "http://localhost:6060/v1/report/summarize/stream" \
  -F "report_type=用电需求预测报告" \
  -F "max_words=8196" \
  -F "max_paragraphs=100" \
  -F "requirements=" \
  -F "files=@/path/to/file1.pdf" \
  -F "files=@/path/to/file2.docx" \
  -H "Accept: text/event-stream"
```

### 使用 Python requests 测试

```python
import requests

# 获取报告类型列表
response = requests.get("http://localhost:6060/v1/report/types")
print(response.json())

# 生成报告摘要
url = "http://localhost:6060/v1/report/summarize"
files = [
    ("files", open("file1.pdf", "rb")),
    ("files", open("file2.docx", "rb")),
]
data = {
    "report_type": "用电需求预测报告",
    "max_words": 8196,
    "max_paragraphs": 100,
    "requirements": "",
}
response = requests.post(url, files=files, data=data)
print(response.json())
```

## 项目结构

```
compress_report_agentscope/
├── app/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── config.py            # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # 数据模型
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py     # Prompt 模板
│   ├── utils/
│   │   ├── __init__.py
│   │   └── document_parser.py  # 文档解析
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── summarizer.py    # 核心工作流
│   └── api/
│       ├── __init__.py
│       └── routes.py        # API 路由
├── uploads/                 # 文件上传临时目录
├── logs/                    # AgentScope 日志目录
├── .env                     # 环境变量
├── requirements.txt         # 依赖列表
├── plan.md                  # 项目计划
└── README.md                # 项目说明