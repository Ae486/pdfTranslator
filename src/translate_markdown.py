#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的Markdown文件翻译测试脚本
"""

import os
import sys
import argparse
import re # Import the re module
from translation_api import BaiduTranslationAPI
from markdown_translator import MarkdownTranslator
import config


def process_translation(input_file, output_file=None, from_lang=None, to_lang=None, app_id=None, app_key=None):
    """
    翻译指定的Markdown文件
    
    :param input_file: 输入文件路径
    :param output_file: 输出文件路径 (可选)
    :param from_lang: 源语言 (可选)
    :param to_lang: 目标语言 (可选)
    :param app_id: 百度翻译APP ID
    :param app_key: 百度翻译密钥
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return None, "输入文件不存在"
    
    # 如果未指定输出文件，则自动生成
    if not output_file:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_translated{ext}"
    
    print(f"开始翻译Markdown文件: {input_file}")
    print(f"翻译结果将保存到: {output_file}")
    
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义HTML表格的正则表达式和占位符
    html_table_pattern = re.compile(r'<html>.*?</table>', re.DOTALL)
    placeholder_prefix = "HTML_TABLE_PLACEHOLDER_"
    
    # 查找所有HTML表格并替换为占位符
    tables = html_table_pattern.findall(content)
    content_with_placeholders = content
    placeholders_map = {}
    for i, table in enumerate(tables):
        placeholder = f"{placeholder_prefix}{i}__"
        content_with_placeholders = content_with_placeholders.replace(table, placeholder, 1)
        placeholders_map[placeholder] = table

    # 获取翻译参数
    source_lang = from_lang or config.SOURCE_LANG
    target_lang = to_lang or config.TARGET_LANG
    
    # 检查API密钥是否提供
    if not app_id or not app_key:
        error_msg = "错误：必须提供百度翻译API的APP ID和密钥"
        print(error_msg)
        return None, error_msg
    
    # 创建翻译API实例
    translator = BaiduTranslationAPI(app_id=app_id, app_key=app_key)
    
    # 创建Markdown翻译器
    md_translator = MarkdownTranslator(
        translator=translator,
        source_lang=source_lang,
        target_lang=target_lang
    )
    
    # 调用翻译函数进行翻译
    try:
        # 翻译包含占位符的Markdown内容
        result_with_placeholders = md_translator.translate_markdown(content_with_placeholders)
        
        # 将占位符替换回原始HTML表格内容
        translated_result = result_with_placeholders
        for placeholder, original_table in placeholders_map.items():
            translated_result = translated_result.replace(placeholder, original_table, 1)

        # 保存翻译结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_result)
        
        print(f"翻译完成！结果已保存到: {output_file}")
        return output_file, None
        
    except Exception as e:
        error_msg = f"翻译过程中出错: {e}"
        print(error_msg)
        return None, error_msg

def main():
    """测试翻译Markdown文件的主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Markdown文件翻译工具")
    parser.add_argument("input_file", help="输入的Markdown文件路径")
    parser.add_argument("-o", "--output", help="输出的翻译结果文件路径")
    parser.add_argument("--from-lang", help="源语言，默认为英语(en)")
    parser.add_argument("--to-lang", help="目标语言，默认为中文(zh)")
    
    args = parser.parse_args()
    
    # 注意：从命令行独立运行时，你需要确保config.py中有密钥，或通过其他方式传入
    process_translation(
        args.input_file, 
        args.output, 
        args.from_lang, 
        args.to_lang,
        config.BAIDU_TRANSLATE_APP_ID,
        config.BAIDU_TRANSLATE_APP_KEY
    )


if __name__ == "__main__":
    main() 