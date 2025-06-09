import re
from typing import List, Tuple, Dict, Any
from translation_api import TranslationAPI


class MarkdownTranslator:
    """Markdown文件翻译器"""
    
    def __init__(self, translator: TranslationAPI, source_lang: str, target_lang: str):
        """
        初始化Markdown翻译器
        :param translator: 翻译API接口
        :param source_lang: 源语言
        :param target_lang: 目标语言
        """
        self.translator = translator
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.in_code_block = False  # 用于跟踪是否在代码块内
    
    def translate_file(self, input_file: str, output_file: str) -> None:
        """
        翻译整个Markdown文件
        :param input_file: 输入文件路径
        :param output_file: 输出文件路径
        """
        # 读取原始文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 翻译内容
        translated_content = self.translate_markdown(content)
        
        # 保存翻译后的内容
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        print(f"翻译完成，已保存到 {output_file}")
    
    def translate_markdown(self, markdown_text: str) -> str:
        """
        翻译Markdown文本，保持原始布局
        :param markdown_text: 原始Markdown文本
        :return: 翻译后的Markdown文本
        """
        # 预处理：提取并保护数学公式
        protected_text, math_formulas = self._protect_math_formulas(markdown_text)
        
        # 预处理：保护代码块
        protected_text, code_blocks = self._protect_code_blocks(protected_text)
        
        # 将Markdown文本按行分割
        lines = protected_text.split('\n')
        translated_lines = []
        
        # 逐行处理
        for line in lines:
            # 检查是否为特殊行（图片、分隔符等）
            if self._is_special_line(line):
                translated_lines.append(line)
            else:
                # 翻译普通文本行，保持原始格式
                translated_line = self._translate_line(line)
                translated_lines.append(translated_line)
        
        # 重新组合为完整的Markdown文本
        translated_text = '\n'.join(translated_lines)
        
        # 恢复代码块
        translated_text = self._restore_code_blocks(translated_text, code_blocks)
        
        # 恢复数学公式
        final_text = self._restore_math_formulas(translated_text, math_formulas)
        
        return final_text
    
    def _protect_code_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        保护代码块，将其替换为占位符
        :param text: 原始文本
        :return: (替换后的文本, 代码块字典)
        """
        lines = text.split('\n')
        result_lines = []
        
        # 存储所有提取的代码块
        code_blocks = {}
        current_block = []
        in_code_block = False
        block_id = 0
        
        for line in lines:
            # 检测代码块开始或结束
            if line.strip().startswith("```"):
                if not in_code_block:  # 开始一个新代码块
                    in_code_block = True
                    current_block = [line]  # 包含开始行
                else:  # 结束当前代码块
                    current_block.append(line)  # 包含结束行
                    # 生成占位符并存储代码块
                    placeholder = f"__CODE_BLOCK_{block_id}__"
                    code_blocks[placeholder] = '\n'.join(current_block)
                    result_lines.append(placeholder)
                    in_code_block = False
                    block_id += 1
            else:
                if in_code_block:
                    current_block.append(line)
                else:
                    result_lines.append(line)
        
        # 处理文档末尾未关闭的代码块
        if in_code_block:
            placeholder = f"__CODE_BLOCK_{block_id}__"
            code_blocks[placeholder] = '\n'.join(current_block)
            result_lines.append(placeholder)
        
        return '\n'.join(result_lines), code_blocks
    
    def _restore_code_blocks(self, text: str, code_blocks: Dict[str, str]) -> str:
        """
        恢复被保护的代码块
        :param text: 带有占位符的文本
        :param code_blocks: 代码块字典
        :return: 恢复后的文本
        """
        result = text
        for placeholder, block in code_blocks.items():
            result = result.replace(placeholder, block)
        return result
    
    def _protect_math_formulas(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        保护数学公式，将其替换为占位符
        :param text: 原始文本
        :return: (替换后的文本, 公式字典)
        """
        # 行内数学公式模式: $...$
        inline_pattern = r'\$([^\$]+?)\$'
        # 块级数学公式模式: $$...$$
        block_pattern = r'\$\$([^\$]+?)\$\$'
        
        # 存储所有提取的公式
        formulas = {}
        placeholder_id = 0
        
        # 替换块级公式
        def replace_block_formula(match):
            nonlocal placeholder_id
            placeholder = f"__MATH_BLOCK_{placeholder_id}__"
            formulas[placeholder] = f"$${match.group(1)}$$"
            placeholder_id += 1
            return placeholder
        
        # 替换行内公式
        def replace_inline_formula(match):
            nonlocal placeholder_id
            placeholder = f"__MATH_INLINE_{placeholder_id}__"
            formulas[placeholder] = f"${match.group(1)}$"
            placeholder_id += 1
            return placeholder
        
        # 先替换块级公式，再替换行内公式
        protected_text = re.sub(block_pattern, replace_block_formula, text)
        protected_text = re.sub(inline_pattern, replace_inline_formula, protected_text)
        
        return protected_text, formulas
    
    def _restore_math_formulas(self, text: str, formulas: Dict[str, str]) -> str:
        """
        恢复被保护的数学公式
        :param text: 带有占位符的文本
        :param formulas: 公式字典
        :return: 恢复后的文本
        """
        result = text
        for placeholder, formula in formulas.items():
            # 使用SVG或图片表示数学公式，确保在最终PDF中正确渲染
            if placeholder.startswith("__MATH_BLOCK_"):
                # 对于块级公式，添加居中样式
                result = result.replace(placeholder, f'<div class="math-block">{formula}</div>')
            else:
                # 对于行内公式
                result = result.replace(placeholder, f'<span class="math-inline">{formula}</span>')
        return result
    
    def _is_special_line(self, line: str) -> bool:
        """
        判断是否为特殊行（不需要翻译的行）
        :param line: 行文本
        :return: 是否为特殊行
        """
        # 空行
        if not line.strip():
            return True
        
        # 图片行
        if re.match(r'!\[.*?\]\(.*?\)', line.strip()):
            return True
        
        # 数学公式占位符
        if "__MATH_" in line:
            return False  # 我们会在_translate_line中处理这些占位符
        
        # 代码块占位符
        if "__CODE_BLOCK_" in line:
            return True
        
        return False
    
    def _translate_line(self, line: str) -> str:
        """
        翻译单行文本，保持原始格式
        :param line: 原始行文本
        :return: 翻译后的行文本
        """
        # 提取行首的特殊格式（如标题的#、列表的-/*等）
        prefix_match = re.match(r'^(\s*(?:[#]+\s*|[-*+]\s*|[0-9]+\.\s*|>\s*|))', line)
        prefix = prefix_match.group(1) if prefix_match else ''
        
        # 提取行尾的特殊字符
        suffix_match = re.search(r'(\s+)$', line)
        suffix = suffix_match.group(1) if suffix_match else ''
        
        # 提取正文内容
        content = line[len(prefix):len(line)-len(suffix)] if suffix else line[len(prefix):]
        
        # 如果内容为空，直接返回原行
        if not content.strip():
            return line
        
        # 处理含有行内代码、链接等特殊元素的文本
        parts = self._split_special_elements(content)
        translated_parts = []
        
        for part, should_translate in parts:
            if should_translate:
                translated_part = self.translator.translate(part, self.source_lang, self.target_lang)
                translated_parts.append(translated_part)
            else:
                translated_parts.append(part)
        
        # 组合翻译后的内容
        translated_content = ''.join(translated_parts)
        
        # 返回完整的翻译后行，保持原始格式
        return f"{prefix}{translated_content}{suffix}"
    
    def _split_special_elements(self, text: str) -> List[Tuple[str, bool]]:
        """
        分割文本中的特殊元素（代码、链接等）与普通文本
        :param text: 要分割的文本
        :return: 分割后的部分列表，每个元素为(文本片段, 是否需要翻译)
        """
        # 定义需要识别的特殊元素模式
        patterns = [
            (r'`[^`]+`', False),  # 行内代码
            (r'\[([^\]]+)\]\(([^)]+)\)', True),  # 链接 - 只翻译显示文本
            (r'!\[([^\]]*)\]\(([^)]+)\)', True),  # 图片 - 只翻译alt文本
            (r'\*\*[^*]+\*\*', True),  # 粗体
            (r'\*[^*]+\*', True),  # 斜体
            (r'~~[^~]+~~', True),  # 删除线
            (r'__MATH_[A-Z]+_\d+__', False),  # 数学公式占位符
            (r'__CODE_BLOCK_\d+__', False),  # 代码块占位符
        ]
        
        # 将所有模式合并为一个正则表达式
        combined_pattern = '|'.join(f'({pattern})' for pattern, _ in patterns)
        
        # 找出所有特殊元素的位置
        matches = list(re.finditer(combined_pattern, text))
        result = []
        
        # 如果没有特殊元素，直接返回整个文本
        if not matches:
            return [(text, True)]
        
        # 分割文本
        last_end = 0
        for match in matches:
            start, end = match.span()
            
            # 添加特殊元素前的普通文本
            if start > last_end:
                result.append((text[last_end:start], True))
            
            # 找出匹配的是哪种特殊元素
            for i, (pattern, should_translate) in enumerate(patterns):
                if re.match(pattern, match.group(0)):
                    # 如果是链接，只翻译显示文本部分
                    if pattern == r'\[([^\]]+)\]\(([^)]+)\)':
                        link_match = re.match(pattern, match.group(0))
                        if link_match:
                            display_text = link_match.group(1)
                            url = link_match.group(2)
                            if should_translate:
                                # 只翻译显示文本，URL保持不变
                                translated_display = self.translator.translate(
                                    display_text, self.source_lang, self.target_lang
                                )
                                result.append((f"[{translated_display}]({url})", False))
                            else:
                                result.append((match.group(0), False))
                        break
                    # 图片处理 - 只翻译alt文本
                    elif pattern == r'!\[([^\]]*)\]\(([^)]+)\)':
                        img_match = re.match(pattern, match.group(0))
                        if img_match:
                            alt_text = img_match.group(1)
                            img_url = img_match.group(2)
                            if should_translate and alt_text.strip():
                                # 只翻译alt文本，URL保持不变
                                translated_alt = self.translator.translate(
                                    alt_text, self.source_lang, self.target_lang
                                )
                                result.append((f"![{translated_alt}]({img_url})", False))
                            else:
                                result.append((match.group(0), False))
                        break
                    else:
                        result.append((match.group(0), should_translate))
                        break
            
            last_end = end
        
        # 添加最后一个特殊元素后的普通文本
        if last_end < len(text):
            result.append((text[last_end:], True))
        
        return result 