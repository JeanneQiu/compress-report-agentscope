"""核心工作流 - 报告摘要生成"""
import time
import uuid
import re
from typing import List, Optional, AsyncGenerator
import agentscope
from agentscope.model import OpenAIChatModel
from app.config import Config, ReportType
from app.models.schemas import DocumentInfo, DocumentSummary, MetaInfo
from app.prompts.templates import PromptTemplates
from app.utils.document_parser import DocumentParser


class ReportSummarizer:
    """报告摘要生成器"""
    
    def __init__(self):
        self.config = Config()
        self.parser = DocumentParser()
        self.prompts = PromptTemplates()
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM 模型"""
        self.llm = OpenAIChatModel(
            model_name=self.config.LLM_MODEL,
            api_key=self.config.LLM_API_KEY,
            client_kwargs={
                "base_url": self.config.LLM_BASE_URL,
                "max_retries": 0,  # 禁用重试
                "timeout": 120.0,  # 设置超时时间
            },
            generate_kwargs={
                "temperature": self.config.LLM_TEMPERATURE,
                "max_tokens": 8196,  
            },
        )
    
    def _split_text_by_headers(self, text: str, max_chars: int = 6000) -> List[str]:
        """根据标题拆分文本，确保每个部分不超过最大字符数
        
        Args:
            text: 原始文本
            max_chars: 最大字符数（默认 6000，约为 4000 tokens）
            
        Returns:
            List[str]: 拆分后的文本列表
        """
        # 递归拆分函数
        def split_recursive(text_to_split: str, max_len: int) -> List[str]:
            if len(text_to_split) <= max_len:
                return [text_to_split]
            
            # 找到所有标题位置（# 开头的行）
            lines = text_to_split.split('\n')
            header_positions = []
            current_pos = 0
            
            for i, line in enumerate(lines):
                line_length = len(line) + 1  # +1 for \n
                if line.strip().startswith('#'):
                    header_positions.append((current_pos, i, line))
                current_pos += line_length
            
            # 如果没有标题，直接按中间拆分
            if not header_positions:
                mid = len(text_to_split) // 2
                part1 = text_to_split[:mid]
                part2 = text_to_split[mid:]
                return split_recursive(part1, max_len) + split_recursive(part2, max_len)
            
            # 找到最佳拆分点（使两部分字数差异最小）
            best_split_idx = -1
            min_diff = float('inf')
            
            for pos, line_idx, line in header_positions:
                # 计算拆分后的两部分长度
                part1_len = pos
                part2_len = len(text_to_split) - pos
                diff = abs(part1_len - part2_len)
                
                # 确保两部分都不超过 max_len
                if part1_len <= max_len and part2_len <= max_len:
                    if diff < min_diff:
                        min_diff = diff
                        best_split_idx = line_idx
            
            # 如果找不到合适的拆分点，按中间拆分
            if best_split_idx == -1:
                mid = len(text_to_split) // 2
                part1 = text_to_split[:mid]
                part2 = text_to_split[mid:]
                return split_recursive(part1, max_len) + split_recursive(part2, max_len)
            
            # 在最佳拆分点拆分
            part1_lines = lines[:best_split_idx]
            part2_lines = lines[best_split_idx:]
            
            part1 = '\n'.join(part1_lines)
            part2 = '\n'.join(part2_lines)
            
            # 递归拆分
            return split_recursive(part1, max_len) + split_recursive(part2, max_len)
        
        return split_recursive(text, max_chars)
    
    def _count_words(self, text: str) -> int:
        """统计字数"""
        return len(text)
    
    def _count_paragraphs(self, text: str) -> int:
        """统计段落数（按空行分割，排除标题）"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        # 排除只包含标题的段落（以 # 开头的行）
        non_title_paragraphs = []
        for p in paragraphs:
            lines = p.split('\n')
            # 检查段落中是否所有行都是标题行
            is_all_titles = all(line.strip().startswith('#') for line in lines if line.strip())
            if not is_all_titles:
                non_title_paragraphs.append(p)
        return len(non_title_paragraphs)
    
    def _get_report_type_enum(self, report_type: str) -> ReportType:
        """获取报告类型枚举"""
        for rt in ReportType:
            if rt.value == report_type:
                return rt
        raise ValueError(f"未知的报告类型: {report_type}")
    
    async def _call_llm(self, prompt: str, trace_id: str, stage: str, stream_callback: Optional[callable] = None) -> str:
        """调用 LLM 并记录日志
        
        Args:
            prompt: 提示词
            trace_id: 追踪ID
            stage: 阶段名称
            stream_callback: 流式回调函数，接收增量内容（只在验证阶段使用）
            
        Returns:
            str: 完整响应文本
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[{trace_id}] 开始调用 LLM - 阶段: {stage}, prompt 长度: {len(prompt)}")
        
        response = await self.llm(
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "repetition_penalty": 1.05,
                "chat_template_kwargs": {"enable_thinking": False}
            },
            stream=True  # 启用流式输出
        )
        
        # 流式处理：提取增量内容
        full_text = ""
        chunk_count = 0
        prev_text = ""
        
        async for chunk in response:
            chunk_count += 1
            if hasattr(chunk, 'content'):
                # 获取当前chunk的完整文本
                current_text = ""
                for item in chunk.content:
                    if isinstance(item, dict) and 'text' in item:
                        current_text += item['text']
                
                # 提取增量内容
                if current_text.startswith(prev_text):
                    delta = current_text[len(prev_text):]
                    if delta:  # 如果有增量内容
                        full_text = current_text
                        # 只在验证阶段调用流式回调
                        if stream_callback and stage == "validate":
                            await stream_callback(delta)
                        prev_text = current_text
                else:
                    # 如果不是增量，直接使用当前文本
                    full_text = current_text
                    prev_text = current_text
        
        logger.info(f"[{trace_id}] LLM 调用完成 - 阶段: {stage}, chunk 数量: {chunk_count}, 响应长度: {len(full_text)}")
        return full_text
    
    async def summarize(
        self,
        report_type: str,
        file_paths: List[tuple],
        max_words: int,
        max_paragraphs: int,
        requirements: str,
        progress_callback: Optional[callable] = None,
        stream_callback: Optional[callable] = None,
    ) -> tuple[str, MetaInfo]:
        """生成报告摘要
        
        Args:
            report_type: 报告类型
            file_paths: (file_path, filename) 元组列表
            max_words: 最大字数
            max_paragraphs: 最大段落数
            requirements: 特定要求
            progress_callback: 进度回调函数
            
        Returns:
            tuple: (report_markdown, meta_info)
        """
        trace_id = str(uuid.uuid4())
        stage_durations = {}
        warnings = []
        start_time = time.time()
        
        # 获取报告类型枚举
        rt_enum = self._get_report_type_enum(report_type)
        
        # 阶段 1: 解析文件
        stage_start = time.time()
        if progress_callback:
            await progress_callback("parse", "start", "开始解析文件")
        
        documents = self.parser.parse_files(file_paths)
        used_files = [fn for _, fn in file_paths]
        
        if progress_callback:
            await progress_callback("parse", "end", f"解析完成，共 {len(documents)} 份文件")
        
        stage_durations["parse"] = (time.time() - stage_start) * 1000
        
        # 阶段 2: 逐文档压缩
        stage_start = time.time()
        if progress_callback:
            await progress_callback("doc_compress", "start", "开始逐文档压缩")
        
        import logging
        logger = logging.getLogger(__name__)
        summaries = []
        for i, doc in enumerate(documents):
            if progress_callback:
                await progress_callback("progress", "", f"处理文档 {i+1}/{len(documents)}: {doc.filename}")
            
            logger.info(f"文档 {i+1}/{len(documents)}: {doc.filename}, 原始长度: {len(doc.text_md)}")
            
            # 检查文档是否解析成功
            if not doc.text_md or len(doc.text_md) < 10:
                logger.warning(f"文档 {doc.filename} 解析失败或内容过短，跳过处理")
                warnings.append(f"文档 {doc.filename} 解析失败或内容过短")
                continue
            
            # 根据标题拆分文档内容
            text_parts = self._split_text_by_headers(doc.text_md)
            logger.info(f"文档 {i+1} 拆分后部分数量: {len(text_parts)}")
            
            # 如果文档被拆分成多个部分，分别压缩后再合并
            if len(text_parts) > 1:
                part_summaries = []
                for j, part in enumerate(text_parts):
                    prompt = self.prompts.DOC_COMPRESS_TEMPLATES[rt_enum].format(
                        text_md=part
                    )
                    part_summary = await self._call_llm(prompt, trace_id, f"doc_compress_{doc.doc_id}_part{j}", stream_callback)
                    part_summaries.append(part_summary)
                
                # 合并所有部分的摘要
                summary_md = "\n\n---\n\n".join(part_summaries)
            else:
                prompt = self.prompts.DOC_COMPRESS_TEMPLATES[rt_enum].format(
                    text_md=text_parts[0]
                )
                summary_md = await self._call_llm(prompt, trace_id, f"doc_compress_{doc.doc_id}", stream_callback)
            
            summaries.append(DocumentSummary(doc_id=doc.doc_id, summary_md=summary_md))
        
        if progress_callback:
            await progress_callback("doc_compress", "end", "逐文档压缩完成")
        
        stage_durations["doc_compress"] = (time.time() - stage_start) * 1000
        
        # 阶段 3: 总体压缩
        stage_start = time.time()
        if progress_callback:
            await progress_callback("global_compress", "start", "开始总体压缩")
        
        # 准备约束条件块
        requirements_block = f"- 特定要求：{requirements}" if requirements else ""
        
        # 合并所有摘要
        summaries_text = "\n\n---\n\n".join([s.summary_md for s in summaries])
        
        import logging
        logger = logging.getLogger(__name__)
        paragraph_count = len([p for p in summaries_text.split('\n\n') if p.strip()])
        logger.info(f"合并后的摘要文本长度: {len(summaries_text)}, 段落数: {paragraph_count}")
        
        # 如果摘要文本仍然太长，继续拆分处理
        summary_parts = self._split_text_by_headers(summaries_text, max_chars=5000)
        logger.info(f"拆分后的部分数量: {len(summary_parts)}")
        
        # 打印前5个部分的内容（用于调试）
        for i, part in enumerate(summary_parts[:5]):
            logger.info(f"部分 {i+1} 长度: {len(part)}, 内容预览: {part[:200]}")
        
        if len(summary_parts) > 1:
            # 分多次压缩
            compressed_parts = []
            import logging
            logger = logging.getLogger(__name__)
            
            for j, part in enumerate(summary_parts):
                logger.info(f"处理第 {j+1}/{len(summary_parts)} 部分, 长度: {len(part)}")
                prompt = self.prompts.GLOBAL_COMPRESS_TEMPLATES[rt_enum].format(
                    max_words=max_words // len(summary_parts),
                    max_paragraphs=max_paragraphs // len(summary_parts),
                    requirements_block=requirements_block,
                    summaries=part
                )
                compressed_part = await self._call_llm(prompt, trace_id, f"global_compress_part{j}", stream_callback)
                compressed_parts.append(compressed_part)
            
            # 合并压缩后的部分
            report_markdown_draft = "\n\n---\n\n".join(compressed_parts)
        else:
            prompt = self.prompts.GLOBAL_COMPRESS_TEMPLATES[rt_enum].format(
                max_words=max_words,
                max_paragraphs=max_paragraphs,
                requirements_block=requirements_block,
                summaries=summary_parts[0]
            )
            report_markdown_draft = await self._call_llm(prompt, trace_id, "global_compress", stream_callback)
        
        if progress_callback:
            await progress_callback("global_compress", "end", "总体压缩完成")
        
        stage_durations["global_compress"] = (time.time() - stage_start) * 1000
        
        # 阶段 4: validate_and_refine
        stage_start = time.time()
        if progress_callback:
            await progress_callback("validate", "start", "开始验证和修订")
        
        current_words = self._count_words(report_markdown_draft)
        current_paragraphs = self._count_paragraphs(report_markdown_draft)
        
        prompt = self.prompts.VALIDATE_TEMPLATES[rt_enum].format(
            max_words=max_words,
            max_paragraphs=max_paragraphs,
            requirements=requirements if requirements else "无",
            current_words=current_words,
            current_paragraphs=current_paragraphs,
            report_markdown=report_markdown_draft
        )
        
        report_markdown = await self._call_llm(prompt, trace_id, "validate", stream_callback)
        
        # 检查最终结果
        final_words = self._count_words(report_markdown)
        final_paragraphs = self._count_paragraphs(report_markdown)
        
        if final_words > max_words:
            warnings.append(f"最终报告字数 ({final_words}) 超过约束 ({max_words})")
        if final_paragraphs > max_paragraphs:
            warnings.append(f"最终报告段落数 ({final_paragraphs}) 超过约束 ({max_paragraphs})")
        
        if progress_callback:
            await progress_callback("validate", "end", "验证和修订完成")
        
        stage_durations["validate"] = (time.time() - stage_start) * 1000
        
        # 计算总耗时
        total_duration = (time.time() - start_time) * 1000
        
        # 计算哈希
        hash_value = DocumentParser.calculate_hash(report_markdown)
        
        # 构建元数据
        meta = MetaInfo(
            used_files=used_files,
            hash=hash_value,
            model=self.config.LLM_MODEL,
            base_url=self.config.LLM_BASE_URL,
            temperature=self.config.LLM_TEMPERATURE,
            total_duration_ms=total_duration,
            stage_durations_ms=stage_durations,
            trace_id=trace_id,
            warnings=warnings
        )
        
        return report_markdown, meta


def init_agentscope():
    """初始化 AgentScope"""
    agentscope.init(
        project="compress_report",
        name="report_summarizer",
        logging_path="./logs/agentscope.log",
        logging_level="DEBUG",
    )
