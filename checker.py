import os
import sys
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
from typing import List, Dict, Optional, Set, Any
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
import re

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

class WCAGImagesOfTextChecker:
    def __init__(self, config_path: str = 'config.yaml', max_images: int = None, use_cache: bool = True):
        """初期化"""
        logger.info("WCAGImagesOfTextCheckerを初期化中...")
        self.config = self.load_config(config_path)
        self.client = OpenAI(api_key=self.config['openai']['api_key'])
        self.results = []
        self.checked_urls = set()
        self.checked_images = set()  # 重複チェック防止用
        self.max_images = max_images
        self.use_cache = use_cache
        
        # キャッシュマネージャーの初期化
        if self.use_cache:
            cache_dir = self.config.get('cache', {}).get('directory', 'cache')
            cache_expiry = self.config.get('cache', {}).get('expiry_days', 7)
            self.cache_manager = CacheManager(cache_dir, cache_expiry)
        
        logger.info("初期化完了")

    def load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        logger.info(f"設定ファイルを読み込み中: {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # キャッシュ設定がなければデフォルト値を設定
        if 'cache' not in config:
            config['cache'] = {
                'enabled': True,
                'directory': 'cache',
                'expiry_days': 7
            }
            
        logger.info("設定ファイルの読み込みが完了")
        return config

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

    def analyze_image(self, image_url: str, count: int, total: int, max_retries: int = 3) -> Dict:
        """Vision APIを使用して画像を分析（キャッシュ対応）"""
        # キャッシュが有効で、画像分析結果がキャッシュされている場合
        if self.use_cache and self.cache_manager.is_analysis_cached(image_url):
            logger.info(f"キャッシュから分析結果を使用 ({count}/{total}): {image_url}")
            cached_analysis = self.cache_manager.get_analysis(image_url)
            if cached_analysis:
                return cached_analysis
        
        logger.info(f"画像を分析中 ({count}/{total}): {image_url}")
        
        for retry in range(max_retries):
            try:
                if retry > 0:
                    logger.info(f"リトライ {retry}/{max_retries-1} ({count}/{total}): {image_url}")
                
                response = self.client.chat.completions.create(
                    model=self.config['openai']['model'],
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """
                                    この画像をWCAG 1.4.5（Images of Text）の観点から詳細に分析し、以下の形式でJSON応答してください：
                                    {
                                        "contains_text": true/false,
                                        "detected_text": "検出されたテキスト",
                                        "text_purpose": "テキストの目的（ロゴ、ナビゲーション、見出し、本文など）",
                                        "has_significant_visual_content": true/false,
                                        "visual_content_description": "重要な視覚的コンテンツの説明（存在する場合）",
                                        "is_logo": true/false,
                                        "is_essential": true/false,
                                        "essential_reason": "本質的と判断した理由（is_essentialがtrueの場合）",
                                        "is_customizable": true/false,
                                        "can_be_html_css": true/false,
                                        "has_text_alternative": true/false,
                                        "wcag_145_compliant": true/false,
                                        "reason": "準拠/非準拠の詳細な理由",
                                        "recommendations": ["改善提案1", "改善提案2"]
                                    }
                                    
                                    判断基準：
                                    1. has_significant_visual_content:
                                       - グラフ、スクリーンショット、図表など、テキスト以外の重要な視覚的情報を含むか
                                       - 含む場合、そのコンテンツの説明を提供

                                    2. is_logo:
                                       - 企業・組織のロゴまたはブランド名の一部か
                                       - ブランドアイデンティティとして不可欠な表現か

                                    3. is_essential:
                                       - フォントサンプル、歴史的文書の表現など、特定の表示が情報伝達に不可欠か
                                       - 「B」（太字）、「I」（斜体）などのシンボリックな表現か
                                       - なぜその表現が本質的なのか、理由を説明

                                    4. is_customizable:
                                       - ユーザーがフォントサイズ、色、間隔などをカスタマイズできるか
                                       - カスタマイズ可能な場合、その方法を説明

                                    5. has_text_alternative:
                                       - 同じ情報がテキストでも提供されているか
                                       - テキストと画像が併用されている場合、基準を満たす

                                    6. wcag_145_compliant: 以下のいずれかを満たすか
                                       - ロゴ/ブランド名である
                                       - カスタマイズ可能である
                                       - 特定の表現が本質的である
                                       - テキストで同じ情報が提供されている
                                       - 重要な他の視覚的コンテンツの一部である
                                    
                                    必ず有効なJSONフォーマットで回答してください。
                                    """
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_url
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content.strip()
                
                # JSONの抽出を改善
                try:
                    # 方法1: 最初の { から最後の } までを抽出
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        try:
                            result = json.loads(json_str)
                            logger.info(f"画像分析が完了 ({count}/{total})")
                            
                            # キャッシュが有効な場合は分析結果をキャッシュ
                            if self.use_cache:
                                self.cache_manager.cache_analysis(image_url, result)
                                
                            return result
                        except json.JSONDecodeError:
                            # 最初の方法が失敗した場合、別の方法を試す
                            pass
                    
                    # 方法2: 正規表現でJSONを抽出
                    json_pattern = re.compile(r'(\{.*\})', re.DOTALL)
                    match = json_pattern.search(content)
                    
                    if match:
                        json_str = match.group(1)
                        try:
                            result = json.loads(json_str)
                            logger.info(f"画像分析が完了 ({count}/{total}) - 正規表現で抽出")
                            
                            # キャッシュが有効な場合は分析結果をキャッシュ
                            if self.use_cache:
                                self.cache_manager.cache_analysis(image_url, result)
                                
                            return result
                        except json.JSONDecodeError:
                            # 両方の方法が失敗した場合
                            pass
                    
                    # 方法3: 行ごとに処理して { で始まり } で終わる部分を見つける
                    lines = content.split('\n')
                    json_lines = []
                    in_json = False
                    
                    for line in lines:
                        line = line.strip()
                        if not in_json and '{' in line:
                            in_json = True
                            json_lines.append(line[line.find('{'):])
                        elif in_json and '}' in line:
                            json_lines.append(line[:line.rfind('}')+1])
                            in_json = False
                            break
                        elif in_json:
                            json_lines.append(line)
                    
                    if json_lines:
                        json_str = ''.join(json_lines)
                        try:
                            result = json.loads(json_str)
                            logger.info(f"画像分析が完了 ({count}/{total}) - 行分割で抽出")
                            
                            # キャッシュが有効な場合は分析結果をキャッシュ
                            if self.use_cache:
                                self.cache_manager.cache_analysis(image_url, result)
                                
                            return result
                        except json.JSONDecodeError:
                            # すべての方法が失敗した場合
                            if retry < max_retries - 1:
                                logger.warning(f"JSON抽出に失敗、リトライします ({count}/{total})")
                                continue
                            else:
                                logger.error(f"JSON解析エラー ({count}/{total}): JSONを抽出できませんでした\nResponse: {content}")
                                return self._create_error_response(f"JSON解析エラー: JSONを抽出できませんでした")
                    
                    # すべての抽出方法が失敗した場合
                    if retry < max_retries - 1:
                        logger.warning(f"JSON not found in response、リトライします ({count}/{total})")
                        continue
                    else:
                        logger.error(f"JSON not found in response ({count}/{total})\nResponse: {content}")
                        return self._create_error_response("JSON not found in response")
                    
                except Exception as e:
                    if retry < max_retries - 1:
                        logger.warning(f"JSON処理中にエラー、リトライします ({count}/{total}): {str(e)}")
                        continue
                    else:
                        logger.error(f"JSON処理中にエラー ({count}/{total}): {str(e)}\nResponse: {content}")
                        return self._create_error_response(f"JSON処理エラー: {str(e)}")
                    
            except Exception as e:
                if retry < max_retries - 1:
                    logger.warning(f"API呼び出しエラー、リトライします ({count}/{total}): {str(e)}")
                    continue
                else:
                    logger.error(f"画像分析中にエラーが発生 ({count}/{total}): {str(e)}")
                    return self._create_error_response(f"画像分析エラー: {str(e)}")
        
        # すべてのリトライが失敗した場合
        return self._create_error_response("最大リトライ回数を超えました")

    def _create_error_response(self, error_message: str) -> Dict:
        """エラーレスポンスを生成"""
        return {
            "error": error_message,
            "contains_text": False,
            "detected_text": "",
            "is_logo": False,
            "is_essential": False,
            "is_customizable": False,
            "can_be_html_css": False,
            "wcag_145_compliant": False,
            "reason": error_message,
            "recommendations": []
        }

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

    def check_image(self, img: BeautifulSoup, base_url: str, count: int, total: int) -> Optional[Dict]:
        """画像要素をチェック（キャッシュ対応）"""
        try:
            src = img.get('src')
            if not src:
                logger.warning(f"src属性が見つかりません ({count}/{total})")
                return None
                
            # 画像URLを絶対パスに変換
            image_url = self.get_absolute_url(base_url, src)
            
            # 重複チェック
            if image_url in self.checked_images:
                logger.info(f"画像は既にチェック済み: {image_url}")
                return None
            self.checked_images.add(image_url)
            
            alt = img.get('alt', '')
            xpath = self.get_xpath(img)
            
            # Vision APIで画像を分析（キャッシュ対応）
            analysis = self.analyze_image(image_url, count, total)
            
            if "error" in analysis:
                logger.error(f"画像分析でエラー ({count}/{total}): {analysis['error']}")
                return {
                    "url": base_url,
                    "image_url": image_url,
                    "element": str(img),
                    "xpath": xpath,
                    "alt_text": alt,
                    "error": analysis["error"]
                }
                
            logger.info(f"画像チェック完了 ({count}/{total}): {image_url}")
            return {
                "url": base_url,
                "image_url": image_url,
                "element": str(img),
                "xpath": xpath,
                "alt_text": alt,
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"画像チェック中にエラー ({count}/{total}): {str(e)}")
            return None

    def check_url(self, url: str):
        """URLをチェック（キャッシュ対応）"""
        if url in self.checked_urls:
            logger.info(f"URLは既にチェック済み: {url}")
            return
        self.checked_urls.add(url)
        
        try:
            # 1. ページコンテンツを取得（キャッシュがあれば再利用）
            soup = self.fetch_page_content(url)
            
            # 2. 画像要素を抽出（キャッシュがあれば再利用）
            images = self.extract_images(url, soup)
            
            # 3. 画像を分析
            total_images = len(images) if self.max_images is None else min(len(images), self.max_images)
            logger.info(f"画像要素を {len(images)} 個検出" + (f"（処理上限: {self.max_images}個）" if self.max_images is not None else ""))
            
            for i, img in enumerate(images if self.max_images is None else images[:self.max_images], 1):
                result = self.check_image(img, url, i, total_images)
                if result:
                    self.results.append(result)
                    
        except Exception as e:
            logger.error(f"URLのチェック中にエラーが発生: {str(e)}")
            self.results.append({
                "url": url,
                "error": f"URLのチェック中にエラーが発生: {str(e)}"
            })

    def get_results(self) -> List[Dict]:
        """チェック結果を取得"""
        return self.results

    def print_results(self):
        """チェック結果を表示"""
        print("\nWCAG 1.4.5 Images of Text チェック結果:")
        print("=" * 80)
        
        if not self.results:
            print("問題は検出されませんでした。")
            return
            
        for result in self.results:
            print(f"\nURL: {result['url']}")
            if 'error' in result:
                print(f"エラー: {result['error']}")
                continue
                
            print(f"画像URL: {result['image_url']}")
            print(f"XPATH: {result['xpath']}")
            print(f"要素: {result['element']}")
            print(f"代替テキスト: {result['alt_text']}")
            
            analysis = result.get('analysis', {})
            if analysis:
                print("\nWCAG 1.4.5判定:")
                print(f"テキスト検出: {'あり' if analysis.get('contains_text') else 'なし'}")
                if analysis.get('contains_text'):
                    print(f"検出テキスト: {analysis.get('detected_text', '不明')}")
                    print(f"テキストの目的: {analysis.get('text_purpose', '不明')}")
                    
                    print("\n視覚的コンテンツ:")
                    print(f"重要な視覚的コンテンツを含む: {'はい' if analysis.get('has_significant_visual_content') else 'いいえ'}")
                    if analysis.get('has_significant_visual_content'):
                        print(f"視覚的コンテンツの説明: {analysis.get('visual_content_description', '不明')}")
                    
                    print("\nWCAG 1.4.5基準:")
                    print(f"ロゴ/ブランド: {'はい' if analysis.get('is_logo') else 'いいえ'}")
                    print(f"本質的な表現: {'はい' if analysis.get('is_essential') else 'いいえ'}")
                    if analysis.get('is_essential'):
                        print(f"本質的と判断した理由: {analysis.get('essential_reason', '不明')}")
                    print(f"カスタマイズ可能: {'はい' if analysis.get('is_customizable') else 'いいえ'}")
                    print(f"HTML/CSS実装可能: {'はい' if analysis.get('can_be_html_css') else 'いいえ'}")
                    print(f"テキストでも提供: {'はい' if analysis.get('has_text_alternative') else 'いいえ'}")
                    
                    print(f"\nWCAG 1.4.5準拠: {'はい' if analysis.get('wcag_145_compliant') else 'いいえ'}")
                    print(f"判定理由: {analysis.get('reason', '不明')}")
                
                if analysis.get('recommendations'):
                    print("\n改善提案:")
                    for rec in analysis['recommendations']:
                        print(f"- {rec}")
                        
            print("-" * 80)

def check_wcag_1_4_5(url: str, config_path: str = 'config.yaml', max_images: int = None, use_cache: bool = True):
    """WCAG 1.4.5チェックを実行（キャッシュ対応）"""
    logger.info(f"WCAG 1.4.5チェックを開始: {url}")
    checker = WCAGImagesOfTextChecker(config_path, max_images, use_cache)
    checker.check_url(url)
    checker.print_results()
    logger.info("チェックが完了しました")
    return checker.get_results()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        check_wcag_1_4_5(url)
    else:
        print("使用方法: python checker.py <URL> [--no-cache]")
        print("オプション:")
        print("  --no-cache: キャッシュを使用しない")