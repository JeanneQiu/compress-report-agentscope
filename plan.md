# 精简报告生成后端（FastAPI + AgentScope + MarkItDown）需求与方案（修正版）

## 1. 目标
用户选择报告类型并上传多份既有报告，后端完成：
1) 文档解析为统一 Markdown  
2) **逐文档压缩（初步）**：每份报告先提炼并压缩到“可融合”的短文本  
3) **总体压缩（强约束）**：融合多份初步结果，按 max_words / max_paragraphs / requirements 输出精简报告  
4) **validate_and_refine（最多 1 次）**：自检约束与要求，必要时修订一次  
同时输出可追溯日志（含 LLM 输出日志、阶段耗时、trace_id），便于审计与迭代。

---

## 2. 功能需求

### 2.1 输入
- report_type（enum）
  - 用电需求预测报告
  - 迎峰度冬(夏)分析报告
  - 特定专题分析报告
  - 临时性分析报告
  - 常态化分析报告
- files（多文件上传）：pdf/docx/md/txt（MVP 优先 pdf + docx）
- max_words: int（最大字数；默认：8196）
- max_paragraphs: int（最大段落数；默认：100）
- requirements: str（特定要求：必须包含/禁止包含/写作风格/结构要求等；默认为空）

### 2.2 输出
- report_markdown：精简报告（Markdown）
- meta：溯源信息（用于审计/调试）
  - used_files（文件名列表）、hash（请求或文件摘要）、模型信息（model/base_url/temperature）
  - token用量（若可获取）、运行耗时（总耗时与各阶段耗时）、trace_id
  - warnings（如约束过紧导致信息删减）

---

## 3. 环境变量（部署配置）
- API_PREFIX=/v1
- HOST=0.0.0.0
- PORT=6060
- MAX_UPLOAD_SIZE=104857600
- UPLOAD_DIR=uploads
- LLM_MODEL=qwen3-4b
- LLM_BASE_URL=http://0.0.0.0:10010/v1
- LLM_API_KEY=""
- LLM_TEMPERATURE=0.3

---

## 4. API 设计（FastAPI）

### 4.1 基础接口
- `GET {API_PREFIX}/report/types`
  - 返回 report_type 列表与说明（含“输出结构/关注点”简介）
- `POST {API_PREFIX}/report/summarize`（multipart/form-data）
  - fields：report_type, max_words, max_paragraphs, requirements, files[]
  - resp：{report_markdown, meta}

### 4.2 SSE 流式输出
- `POST {API_PREFIX}/report/summarize/stream`（multipart/form-data + text/event-stream）
  - 输入同上
  - 事件流输出生成过程与最终结果，适配长任务与更好的用户体验

建议事件：
- `status`：阶段开始/结束（parse/doc_compress/global_compress/validate）
- `progress`：当前处理文档名/序号
- `delta`：精简报告 Markdown 增量输出（可选）
- `result`：最终 {report_markdown, meta}
- `error`：错误信息（含 message + trace_id）

---

## 5. 文档解析与标准化（MarkItDown）
统一使用现成的 MarkItDown 将 PDF / Word 转为 Markdown，作为后续压缩输入。

解析产出字段（内部使用）：
- doc_id：内部唯一 id
- filename：原始文件名
- text_md：Markdown 正文
- warnings：解析噪声/疑似空文本等
---

## 6. 核心工作流（固定流程，强约束写进提示词）
工作流严格为：
1) 解析文件（parse）
2) 逐文档压缩（doc_compress，逐个文件）
3) 总体压缩（global_compress，融合后再强约束压缩）
4) validate_and_refine（自检修订，最多 1 次）

### 6.1 逐文档压缩（doc_compress）
目标：把每份报告压缩为短文本，便于后续融合。

输入：
- report_type
- 单份 text_md
- prompt：根据重点进行信息提取和压缩

输出：
- doc_summary_md：该文档的压缩版

### 6.2 总体压缩（global_compress）
目标：融合多份 doc_summary_md，生成最终 report_markdown，并满足约束。

输入：
- report_type
- summaries[]（每份 doc_summary_md）
- constraints（写入提示词）：
  - max_words
  - max_paragraphs
  - requirements（如果有）

输出：
- report_markdown_draft（接近最终的 Markdown）

### 6.3 validate_and_refine（最多 1 次）
目标：对 draft 做清单式自检，若不满足约束或 requirements，则修订一次。

检查项（写进提示词）：
- 字数 <= max_words
- 段落数 <= max_paragraphs（按空行/Markdown 段落计数规则）
- requirements
- 是否存在明显重复、语义冲突

输出：
- report_markdown（最终）
- log

---

## 7. 报告类型 Prompt 体系（约束写进 Prompt）
要求：
- 每个 report_type 对应独立 prompt 集合（逐文档压缩 + 总体压缩 + validate）
- 所有 prompt 必须显式包含：
  - max_words / max_paragraphs / requirements

建议提供的 Prompt 集合（逻辑层面）：
- PROMPT_DOC_COMPRESS_{TYPE}
- PROMPT_GLOBAL_COMPRESS_{TYPE}
- PROMPT_VALIDATE_{TYPE}

Prompt 内容先简短设计即可，后续根据需求迭代优化

---

## 8. AgentScope 集成（日志 + LLM 输出日志）
目标：代码简洁，同时必须能记录 LLM 输出日志与关键阶段日志。

### 8.1 AgentScope 初始化与内置日志
- 启动时调用 `agentscope.init(...)` 启用内置 logging

### 8.2 LLM 客户端配置
- 基于环境变量 LLM_MODEL/LLM_BASE_URL/LLM_API_KEY/LLM_TEMPERATURE 初始化模型调用
- 在 AgentScope 的 agent / model wrapper 中统一注入：
  - trace_id
  - report_type
  - doc_id（逐文档阶段）
以便日志可关联与回放。

---

## 9. 失败处理与降级策略（保证一晚可交付）
- LLM 输出不符合 Markdown 或明显超限：
  - validate_and_refine 强制修订一次
  - 若仍失败：返回最终版本，不强行要求符合约束

---

## 10. 环境与部署（内网离线）
- 使用 conda 管理依赖
- 通过 **conda-pack** 将环境打包为离线可部署产物：
  - 构建机生成 env 包（tar.gz）
  - 内网解压部署并执行 `conda-unpack` 修复路径
