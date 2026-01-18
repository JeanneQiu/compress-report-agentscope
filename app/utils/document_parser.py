"""文档解析工具 - 使用 MarkItDown"""
import os
import hashlib
import uuid
from typing import List
from markitdown import MarkItDown
from app.models.schemas import DocumentInfo


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        self.markitdown = MarkItDown()
    
    def parse_file(self, file_path: str, filename: str) -> DocumentInfo:
        """解析单个文件为 Markdown
        
        Args:
            file_path: 文件路径
            filename: 原始文件名
            
        Returns:
            DocumentInfo: 解析后的文档信息
        """
        doc_id = str(uuid.uuid4())
        warnings = []
        
        try:
            result = self.markitdown.convert(file_path)
            text_md = result.text_content
            
            # 检查文本是否为空或过短
            if not text_md or len(text_md.strip()) < 10:
                warnings.append("解析结果文本过短，可能解析失败")
            
            return DocumentInfo(
                doc_id=doc_id,
                filename=filename,
                text_md=text_md,
                warnings=warnings
            )
        except Exception as e:
            warnings.append(f"解析失败: {str(e)}")
            return DocumentInfo(
                doc_id=doc_id,
                filename=filename,
                text_md="",
                warnings=warnings
            )
    
    def parse_files(self, file_paths: List[tuple]) -> List[DocumentInfo]:
        """解析多个文件
        
        Args:
            file_paths: (file_path, filename) 元组列表
            
        Returns:
            List[DocumentInfo]: 解析后的文档信息列表
        """
        return [self.parse_file(fp, fn) for fp, fn in file_paths]
    
    @staticmethod
    def calculate_hash(content: str) -> str:
        """计算内容哈希值
        
        Args:
            content: 文本内容
            
        Returns:
            str: SHA256 哈希值
        """
        return hashlib.sha256(content.encode()).hexdigest()