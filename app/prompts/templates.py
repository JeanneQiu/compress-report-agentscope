"""Prompt 模板系统"""
from typing import Dict
from app.config import ReportType


class PromptTemplates:
    """Prompt 模板类"""
    
    # 逐文档压缩 Prompt
    DOC_COMPRESS_TEMPLATES: Dict[ReportType, str] = {
        ReportType.ELECTRICITY_DEMAND: """你是一位专业的电力需求分析专家。请对以下报告进行精炼和压缩，提取关键信息。

要求：
1. 保留核心数据、趋势分析和结论
2. 去除冗余描述和无关内容
3. 输出简洁的 Markdown 格式
4. 重点保留：历史数据、预测方法、预测结果、关键影响因素

原始报告内容：
{text_md}

请输出压缩后的报告摘要：""",

        ReportType.PEAK_SUMMER_WINTER: """你是一位专业的电力供需分析专家。请对以下迎峰度冬/夏分析报告进行精炼和压缩。

要求：
1. 保留供需平衡分析、负荷预测、保供措施等核心内容
2. 去除冗余描述和无关内容
3. 输出简洁的 Markdown 格式
4. 重点保留：负荷情况、供需缺口、应对措施、风险点

原始报告内容：
{text_md}

请输出压缩后的报告摘要：""",

        ReportType.SPECIAL_TOPIC: """你是一位专业的专题分析专家。请对以下专题分析报告进行精炼和压缩。

要求：
1. 保留专题的核心观点、分析方法和结论
2. 去除冗余描述和无关内容
3. 输出简洁的 Markdown 格式
4. 重点保留：问题背景、分析过程、关键发现、建议措施

原始报告内容：
{text_md}

请输出压缩后的报告摘要：""",

        ReportType.TEMPORARY: """你是一位专业的分析报告专家。请对以下临时性分析报告进行精炼和压缩。

要求：
1. 保留分析目的、关键数据和结论
2. 去除冗余描述和无关内容
3. 输出简洁的 Markdown 格式
4. 重点保留：分析背景、核心发现、主要结论

原始报告内容：
{text_md}

请输出压缩后的报告摘要：""",

        ReportType.REGULAR: """你是一位专业的常态化分析专家。请对以下常态化分析报告进行精炼和压缩。

要求：
1. 保留定期分析的关键指标、趋势和异常情况
2. 去除冗余描述和无关内容
3. 输出简洁的 Markdown 格式
4. 重点保留：关键指标、趋势变化、异常分析、工作建议

原始报告内容：
{text_md}

请输出压缩后的报告摘要：""",
    }
    
    # 总体压缩 Prompt
    GLOBAL_COMPRESS_TEMPLATES: Dict[ReportType, str] = {
        ReportType.ELECTRICITY_DEMAND: """你是一位专业的电力需求分析专家。请将以下多份报告摘要融合，生成一份精简的综合报告。

约束条件：
- 最大字数：{max_words}
- 最大段落数：{max_paragraphs}
{requirements_block}

要求：
1. 融合多份报告的核心信息，避免重复
2. 保持逻辑清晰，结构完整
3. 输出标准的 Markdown 格式
4. 确保满足上述约束条件

多份报告摘要：
{summaries}

请输出精简的综合报告：""",

        ReportType.PEAK_SUMMER_WINTER: """你是一位专业的电力供需分析专家。请将以下多份迎峰度冬/夏报告摘要融合，生成一份精简的综合报告。

约束条件：
- 最大字数：{max_words}
- 最大段落数：{max_paragraphs}
{requirements_block}

要求：
1. 融合多份报告的核心信息，避免重复
2. 保持逻辑清晰，结构完整
3. 输出标准的 Markdown 格式
4. 确保满足上述约束条件

多份报告摘要：
{summaries}

请输出精简的综合报告：""",

        ReportType.SPECIAL_TOPIC: """你是一位专业的专题分析专家。请将以下多份专题报告摘要融合，生成一份精简的综合报告。

约束条件：
- 最大字数：{max_words}
- 最大段落数：{max_paragraphs}
{requirements_block}

要求：
1. 融合多份报告的核心信息，避免重复
2. 保持逻辑清晰，结构完整
3. 输出标准的 Markdown 格式
4. 确保满足上述约束条件

多份报告摘要：
{summaries}

请输出精简的综合报告：""",

        ReportType.TEMPORARY: """你是一位专业的分析报告专家。请将以下多份临时性报告摘要融合，生成一份精简的综合报告。

约束条件：
- 最大字数：{max_words}
- 最大段落数：{max_paragraphs}
{requirements_block}

要求：
1. 融合多份报告的核心信息，避免重复
2. 保持逻辑清晰，结构完整
3. 输出标准的 Markdown 格式
4. 确保满足上述约束条件

多份报告摘要：
{summaries}

请输出精简的综合报告：""",

        ReportType.REGULAR: """你是一位专业的常态化分析专家。请将以下多份常态化报告摘要融合，生成一份精简的综合报告。

约束条件：
- 最大字数：{max_words}
- 最大段落数：{max_paragraphs}
{requirements_block}

要求：
1. 融合多份报告的核心信息，避免重复
2. 保持逻辑清晰，结构完整
3. 输出标准的 Markdown 格式
4. 确保满足上述约束条件

多份报告摘要：
{summaries}

请输出精简的综合报告：""",
    }
    
    # 验证和修订 Prompt
    VALIDATE_TEMPLATES: Dict[ReportType, str] = {
        ReportType.ELECTRICITY_DEMAND: """你是一位专业的报告审核专家。请对以下报告进行自检和必要的修订。

检查清单：
1. 字数是否 <= {max_words}（当前字数：{current_words}）
2. 段落数是否 <= {max_paragraphs}（当前段落数：{current_paragraphs}）
3. 是否满足特定要求：{requirements}
4. 是否存在明显重复内容
5. 是否存在语义冲突

如果报告满足所有约束条件，直接返回原报告。
如果报告不满足约束条件，请修订一次，使其满足所有条件。

待审核报告：
{report_markdown}

请输出最终报告：""",

        ReportType.PEAK_SUMMER_WINTER: """你是一位专业的报告审核专家。请对以下报告进行自检和必要的修订。

检查清单：
1. 字数是否 <= {max_words}（当前字数：{current_words}）
2. 段落数是否 <= {max_paragraphs}（当前段落数：{current_paragraphs}）
3. 是否满足特定要求：{requirements}
4. 是否存在明显重复内容
5. 是否存在语义冲突

如果报告满足所有约束条件，直接返回原报告。
如果报告不满足约束条件，请修订一次，使其满足所有条件。

待审核报告：
{report_markdown}

请输出最终报告：""",

        ReportType.SPECIAL_TOPIC: """你是一位专业的报告审核专家。请对以下报告进行自检和必要的修订。

检查清单：
1. 字数是否 <= {max_words}（当前字数：{current_words}）
2. 段落数是否 <= {max_paragraphs}（当前段落数：{current_paragraphs}）
3. 是否满足特定要求：{requirements}
4. 是否存在明显重复内容
5. 是否存在语义冲突

如果报告满足所有约束条件，直接返回原报告。
如果报告不满足约束条件，请修订一次，使其满足所有条件。

待审核报告：
{report_markdown}

请输出最终报告：""",

        ReportType.TEMPORARY: """你是一位专业的报告审核专家。请对以下报告进行自检和必要的修订。

检查清单：
1. 字数是否 <= {max_words}（当前字数：{current_words}）
2. 段落数是否 <= {max_paragraphs}（当前段落数：{current_paragraphs}）
3. 是否满足特定要求：{requirements}
4. 是否存在明显重复内容
5. 是否存在语义冲突

如果报告满足所有约束条件，直接返回原报告。
如果报告不满足约束条件，请修订一次，使其满足所有条件。

待审核报告：
{report_markdown}

请输出最终报告：""",

        ReportType.REGULAR: """你是一位专业的报告审核专家。请对以下报告进行自检和必要的修订。

检查清单：
1. 字数是否 <= {max_words}（当前字数：{current_words}）
2. 段落数是否 <= {max_paragraphs}（当前段落数：{current_paragraphs}）
3. 是否满足特定要求：{requirements}
4. 是否存在明显重复内容
5. 是否存在语义冲突

如果报告满足所有约束条件，直接返回原报告。
如果报告不满足约束条件，请修订一次，使其满足所有条件。

待审核报告：
{report_markdown}

请输出最终报告：""",
    }


def get_prompt_templates() -> PromptTemplates:
    """获取 Prompt 模板实例"""
    return PromptTemplates()