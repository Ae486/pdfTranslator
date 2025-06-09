import abc
import hashlib
import random
import requests
import json
from typing import Dict, Any, List


class TranslationAPI(abc.ABC):
    """翻译API的抽象基类"""

    @abc.abstractmethod
    def translate(self, text: str, from_lang: str, to_lang: str) -> str:
        """
        翻译文本
        :param text: 要翻译的文本
        :param from_lang: 源语言
        :param to_lang: 目标语言
        :return: 翻译后的文本
        """
        pass
    
    @abc.abstractmethod
    def batch_translate(self, texts: List[str], from_lang: str, to_lang: str) -> List[str]:
        """
        批量翻译文本
        :param texts: 要翻译的文本列表
        :param from_lang: 源语言
        :param to_lang: 目标语言
        :return: 翻译后的文本列表
        """
        pass


class BaiduTranslationAPI(TranslationAPI):
    """百度翻译API实现"""
    
    def __init__(self, app_id: str, app_key: str):
        """
        初始化百度翻译API
        :param app_id: 百度翻译API的APP ID
        :param app_key: 百度翻译API的密钥
        """
        self.app_id = app_id
        self.app_key = app_key
        self.url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        
    def translate(self, text: str, from_lang: str = "en", to_lang: str = "zh") -> str:
        """
        翻译文本
        :param text: 要翻译的文本
        :param from_lang: 源语言，默认为英语
        :param to_lang: 目标语言，默认为中文
        :return: 翻译后的文本
        """
        if not text.strip():
            return text
            
        salt = str(random.randint(32768, 65536))
        sign = hashlib.md5((self.app_id + text + salt + self.app_key).encode()).hexdigest()
        
        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            response = requests.get(self.url, params=params)
            result = response.json()
            
            if 'trans_result' in result:
                return result['trans_result'][0]['dst']
            else:
                print(f"翻译错误: {result}")
                return text
        except Exception as e:
            print(f"翻译请求出错: {e}")
            return text
    
    def batch_translate(self, texts: List[str], from_lang: str = "en", to_lang: str = "zh") -> List[str]:
        """
        批量翻译文本
        :param texts: 要翻译的文本列表
        :param from_lang: 源语言，默认为英语
        :param to_lang: 目标语言，默认为中文
        :return: 翻译后的文本列表
        """
        # 百度翻译API限制了单次请求的字符数，需要将长文本切分
        # 由于字符限制，这里简单实现为单个翻译
        results = []
        for text in texts:
            results.append(self.translate(text, from_lang, to_lang))
        return results 