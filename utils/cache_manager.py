"""
WCAG 1.4.5 Images of Text Checker - キャッシュ管理モジュール
==================================================

このモジュールは、HTMLコンテンツ、画像リスト、分析結果などのデータをキャッシュし、
アプリケーションのパフォーマンスを向上させる機能を提供します。

主な機能:
-------
- HTMLコンテンツのキャッシュと取得
- 画像リストのキャッシュと取得
- 画像分析結果のキャッシュと取得
- キャッシュの有効期限管理
- メタデータの管理

使用方法:
-------
```python
from wcag_images_of_text_checker.utils.cache_manager import CacheManager

# キャッシュマネージャーの初期化
cache_manager = CacheManager(
    cache_dir='./cache',  # キャッシュディレクトリのパス
    cache_expiry_days=7   # キャッシュの有効期限（日数）
)

# HTMLをキャッシュ
url = 'https://example.com'
html_content = '<html>...</html>'
cache_manager.cache_html(url, html_content)

# キャッシュからHTMLを取得
cached_html = cache_manager.get_html(url)

# 画像分析結果をキャッシュ
image_url = 'https://example.com/image.jpg'
analysis_data = {'has_text': True, 'confidence': 0.95}
cache_manager.cache_analysis(image_url, analysis_data)

# キャッシュから分析結果を取得
cached_analysis = cache_manager.get_analysis(image_url)

# キャッシュをクリア（特定のURLまたはすべて）
cache_manager.clear_cache(url)  # 特定のURLのキャッシュをクリア
cache_manager.clear_cache()     # すべてのキャッシュをクリア
```
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir='cache', cache_expiry_days=7):
        """キャッシュマネージャーの初期化"""
        self.cache_dir = cache_dir
        self.html_cache_dir = os.path.join(cache_dir, 'html')
        self.images_cache_dir = os.path.join(cache_dir, 'images')
        self.analysis_cache_dir = os.path.join(cache_dir, 'analysis')
        self.metadata_file = os.path.join(cache_dir, 'metadata.json')
        self.cache_expiry = timedelta(days=cache_expiry_days)
        
        # キャッシュディレクトリの作成
        os.makedirs(self.html_cache_dir, exist_ok=True)
        os.makedirs(self.images_cache_dir, exist_ok=True)
        os.makedirs(self.analysis_cache_dir, exist_ok=True)
        
        # メタデータの読み込み
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """メタデータの読み込み"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"メタデータの読み込みに失敗しました: {str(e)}")
                return {}
        return {}
    
    def _save_metadata(self):
        """メタデータの保存"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"メタデータの保存に失敗しました: {str(e)}")
    
    def _get_url_hash(self, url):
        """URLからハッシュ値を生成"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _get_image_hash(self, image_url):
        """画像URLからハッシュ値を生成"""
        return hashlib.md5(image_url.encode('utf-8')).hexdigest()
    
    def is_html_cached(self, url):
        """URLのHTMLがキャッシュされているか確認"""
        url_hash = self._get_url_hash(url)
        
        # メタデータに存在するか確認
        if url_hash not in self.metadata:
            return False
        
        # キャッシュファイルが存在するか確認
        html_cache_path = os.path.join(self.html_cache_dir, f"{url_hash}.html")
        
        if not os.path.exists(html_cache_path):
            return False
        
        # キャッシュの有効期限を確認
        cache_time = datetime.fromisoformat(self.metadata[url_hash]['timestamp'])
        if datetime.now() - cache_time > self.cache_expiry:
            logger.info(f"HTMLキャッシュの有効期限切れ: {url}")
            return False
        
        return True
    
    def is_images_cached(self, url):
        """URLの画像リストがキャッシュされているか確認"""
        url_hash = self._get_url_hash(url)
        
        # メタデータに存在するか確認
        if url_hash not in self.metadata:
            return False
        
        # キャッシュファイルが存在するか確認
        images_cache_path = os.path.join(self.images_cache_dir, f"{url_hash}.json")
        
        if not os.path.exists(images_cache_path):
            return False
        
        # キャッシュの有効期限を確認
        cache_time = datetime.fromisoformat(self.metadata[url_hash]['timestamp'])
        if datetime.now() - cache_time > self.cache_expiry:
            logger.info(f"画像リストキャッシュの有効期限切れ: {url}")
            return False
        
        return True
    
    def is_analysis_cached(self, image_url):
        """画像分析結果がキャッシュされているか確認"""
        image_hash = self._get_image_hash(image_url)
        
        # メタデータに存在するか確認
        key = f"analysis_{image_hash}"
        if key not in self.metadata:
            return False
        
        # キャッシュファイルが存在するか確認
        analysis_cache_path = os.path.join(self.analysis_cache_dir, f"{image_hash}.json")
        
        if not os.path.exists(analysis_cache_path):
            return False
        
        # キャッシュの有効期限を確認
        cache_time = datetime.fromisoformat(self.metadata[key]['timestamp'])
        if datetime.now() - cache_time > self.cache_expiry:
            logger.info(f"分析結果キャッシュの有効期限切れ: {image_url}")
            return False
        
        return True
    
    def cache_html(self, url, html_content):
        """HTMLコンテンツをキャッシュ"""
        url_hash = self._get_url_hash(url)
        html_cache_path = os.path.join(self.html_cache_dir, f"{url_hash}.html")
        
        try:
            with open(html_cache_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # メタデータを更新
            self.metadata[url_hash] = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'type': 'html'
            }
            self._save_metadata()
            
            logger.info(f"HTMLをキャッシュしました: {url}")
            return True
        except Exception as e:
            logger.error(f"HTMLのキャッシュに失敗しました: {str(e)}")
            return False
    
    def cache_images(self, url, images_data):
        """画像要素リストをキャッシュ"""
        url_hash = self._get_url_hash(url)
        images_cache_path = os.path.join(self.images_cache_dir, f"{url_hash}.json")
        
        try:
            with open(images_cache_path, 'w', encoding='utf-8') as f:
                json.dump(images_data, f, ensure_ascii=False, indent=2)
            
            # メタデータを更新（既に存在する場合は上書き）
            if url_hash in self.metadata:
                self.metadata[url_hash]['timestamp'] = datetime.now().isoformat()
            else:
                self.metadata[url_hash] = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'images'
                }
            self._save_metadata()
            
            logger.info(f"画像リストをキャッシュしました: {url}")
            return True
        except Exception as e:
            logger.error(f"画像リストのキャッシュに失敗しました: {str(e)}")
            return False
    
    def cache_analysis(self, image_url, analysis_data):
        """画像分析結果をキャッシュ"""
        image_hash = self._get_image_hash(image_url)
        analysis_cache_path = os.path.join(self.analysis_cache_dir, f"{image_hash}.json")
        
        try:
            with open(analysis_cache_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            
            # メタデータを更新
            key = f"analysis_{image_hash}"
            self.metadata[key] = {
                'url': image_url,
                'timestamp': datetime.now().isoformat(),
                'type': 'analysis'
            }
            self._save_metadata()
            
            logger.info(f"分析結果をキャッシュしました: {image_url}")
            return True
        except Exception as e:
            logger.error(f"分析結果のキャッシュに失敗しました: {str(e)}")
            return False
    
    def get_html(self, url):
        """キャッシュからHTMLを取得"""
        if not self.is_html_cached(url):
            return None
        
        url_hash = self._get_url_hash(url)
        html_cache_path = os.path.join(self.html_cache_dir, f"{url_hash}.html")
        
        try:
            with open(html_cache_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"キャッシュからHTMLを読み込みました: {url}")
            return html_content
        except Exception as e:
            logger.error(f"キャッシュからのHTML読み込みに失敗しました: {str(e)}")
            return None
    
    def get_images(self, url):
        """キャッシュから画像リストを取得"""
        if not self.is_images_cached(url):
            return None
        
        url_hash = self._get_url_hash(url)
        images_cache_path = os.path.join(self.images_cache_dir, f"{url_hash}.json")
        
        try:
            with open(images_cache_path, 'r', encoding='utf-8') as f:
                images_data = json.load(f)
            
            logger.info(f"キャッシュから画像リストを読み込みました: {url}")
            return images_data
        except Exception as e:
            logger.error(f"キャッシュからの画像リスト読み込みに失敗しました: {str(e)}")
            return None
    
    def get_analysis(self, image_url):
        """キャッシュから画像分析結果を取得"""
        if not self.is_analysis_cached(image_url):
            return None
        
        image_hash = self._get_image_hash(image_url)
        analysis_cache_path = os.path.join(self.analysis_cache_dir, f"{image_hash}.json")
        
        try:
            with open(analysis_cache_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            logger.info(f"キャッシュから分析結果を読み込みました: {image_url}")
            return analysis_data
        except Exception as e:
            logger.error(f"キャッシュからの分析結果読み込みに失敗しました: {str(e)}")
            return None
    
    def clear_cache(self, url=None):
        """キャッシュをクリア"""
        if url:
            # 特定のURLのキャッシュをクリア
            url_hash = self._get_url_hash(url)
            html_cache_path = os.path.join(self.html_cache_dir, f"{url_hash}.html")
            images_cache_path = os.path.join(self.images_cache_dir, f"{url_hash}.json")
            
            if os.path.exists(html_cache_path):
                os.remove(html_cache_path)
            if os.path.exists(images_cache_path):
                os.remove(images_cache_path)
            
            if url_hash in self.metadata:
                del self.metadata[url_hash]
                self._save_metadata()
            
            logger.info(f"キャッシュをクリアしました: {url}")
        else:
            # すべてのキャッシュをクリア
            for filename in os.listdir(self.html_cache_dir):
                os.remove(os.path.join(self.html_cache_dir, filename))
            for filename in os.listdir(self.images_cache_dir):
                os.remove(os.path.join(self.images_cache_dir, filename))
            for filename in os.listdir(self.analysis_cache_dir):
                os.remove(os.path.join(self.analysis_cache_dir, filename))
            
            self.metadata = {}
            self._save_metadata()
            
            logger.info("すべてのキャッシュをクリアしました")