"""
WCAG 1.4.5 Images of Text Checker - HTML処理モジュール
==================================================

このモジュールは、ウェブページからHTMLを取得し、画像要素を抽出して分析のために
準備する機能を提供します。キャッシュ機能を活用して、パフォーマンスを向上させます。

主な機能:
-------
- ウェブページのHTMLコンテンツの取得とキャッシュ
- img要素の抽出とURL正規化
- 画像要素のXPATH生成
- キャッシュを活用した効率的な処理

使用方法:
-------
```python
from wcag_images_of_text_checker.utils.html_processor import HTMLProcessor
from wcag_images_of_text_checker.utils.cache_manager import CacheManager

# キャッシュマネージャーの初期化（オプション）
cache_manager = CacheManager('./cache')

# HTMLプロセッサの初期化
processor = HTMLProcessor(cache_manager)

# URLからHTMLを取得
url = 'https://example.com'
soup = processor.fetch_page_content(url)

# 画像を抽出
images = processor.extract_images(url, soup)

# 画像情報の処理
for img in images:
    # 画像のXPATHを取得
    xpath = processor.get_xpath(img)
    
    # 画像のURLを取得（相対パスを絶対パスに変換）
    src = img.get('src', '')
    absolute_url = processor.get_absolute_url(url, src)
    
    print(f"URL: {absolute_url}")
    print(f"XPATH: {xpath}")
    print(f"Alt Text: {img.get('alt', '')}")
```
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Any

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class HTMLProcessor:
    def __init__(self, cache_manager=None):
        """HTML処理クラスの初期化"""
        self.cache_manager = cache_manager
        self.use_cache = cache_manager is not None
    
    def is_absolute_url(self, url: str) -> bool:
        """URLが絶対パスかどうかを判定"""
        return bool(urlparse(url).netloc)
    
    def get_absolute_url(self, base_url: str, url: str) -> str:
        """相対URLを絶対URLに変換"""
        if self.is_absolute_url(url):
            return url
        return urljoin(base_url, url)
    
    def fetch_page_content(self, url: str) -> BeautifulSoup:
        """URLにアクセスしてHTMLを取得・パース（キャッシュ対応）"""
        # キャッシュが有効で、URLがキャッシュされている場合
        if self.use_cache and self.cache_manager.is_html_cached(url):
            logger.info(f"キャッシュからHTMLを使用: {url}")
            html_content = self.cache_manager.get_html(url)
            if html_content:
                return BeautifulSoup(html_content, 'html.parser')
        
        # キャッシュがない場合は通常通りアクセス
        logger.info(f"URLにアクセス中: {url}")
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # キャッシュが有効な場合はHTMLをキャッシュ
        if self.use_cache:
            self.cache_manager.cache_html(url, response.text)
        
        return BeautifulSoup(response.text, 'html.parser')
    
    def extract_images(self, url: str, soup: BeautifulSoup) -> List[Any]:
        """画像要素を抽出（キャッシュ対応）"""
        # キャッシュが有効で、URLがキャッシュされている場合
        if self.use_cache and self.cache_manager.is_images_cached(url):
            logger.info(f"キャッシュから画像リストを使用: {url}")
            images_data = self.cache_manager.get_images(url)
            if images_data:
                # 画像データをBeautifulSoup要素に変換
                images = []
                for img_data in images_data:
                    img_element = BeautifulSoup(img_data, 'html.parser').find('img')
                    if img_element:
                        images.append(img_element)
                
                return images
        
        # キャッシュがない場合は通常通り抽出
        images = []
        for img in soup.find_all('img'):
            if img.parent.name != 'picture':
                images.append(img)
            elif not any(i.get('src') == img.get('src') for i in images):
                images.append(img)
        
        # キャッシュが有効な場合は画像リストをキャッシュ
        if self.use_cache:
            # BeautifulSoup要素をシリアライズ可能な形式に変換
            images_data = [str(img) for img in images]
            self.cache_manager.cache_images(url, images_data)
        
        return images
    
    def get_xpath(self, element) -> str:
        """要素のXPATHを取得"""
        try:
            if element is None:
                return "unknown"
            
            components = []
            current = element
            
            while current and current.name != '[document]':
                if current.name == 'picture':
                    # picture要素の場合は、img要素のインデックスを使用
                    imgs = current.find_all('img', recursive=False)
                    if element.name == 'img':
                        index = imgs.index(element) + 1
                        components.append(f"{current.name}/img[{index}]")
                    else:
                        components.append(current.name)
                else:
                    # 通常の要素の場合
                    siblings = current.parent.find_all(current.name, recursive=False) if current.parent else []
                    if len(siblings) > 1:
                        index = siblings.index(current) + 1
                        components.append(f"{current.name}[{index}]")
                    else:
                        components.append(current.name)
                current = current.parent
            
            components.reverse()
            return '/' + '/'.join(components)
            
        except Exception as e:
            logger.error(f"XPATH生成エラー: {str(e)}")
            return "xpath_error"