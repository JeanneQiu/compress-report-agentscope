# 精简报告生成服务

基于 FastAPI + AgentScope + MarkItDown 的报告摘要生成服务。

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
