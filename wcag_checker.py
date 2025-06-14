"""
WCAG 1.4.5 Images of Text Checker - メインチェッカークラス
======================================================

このファイルは、WCAG 1.4.5基準に基づいてウェブページ内の画像テキストをチェックするメインクラスを定義しています。
非同期処理とバッチ処理を使用して、複数の画像を効率的に処理します。

主な機能:
-------
- ウェブページからの画像抽出
- OpenAI Vision APIを使用した画像分析
- 非同期処理によるバッチ処理
- キャッシュ機能によるパフォーマンス向上

使用方法:
-------
このクラスは通常、main.pyから呼び出されます。直接使用する場合は以下のようにします：

```python
from wcag_images_of_text_checker.wcag_checker import WCAGImagesOfTextChecker

# チェッカーの初期化
checker = WCAGImagesOfTextChecker(
    config_path='config.yaml',  # 設定ファイルのパス
    max_images=10,              # 処理する画像の最大数
    use_cache=True,             # キャッシュを使用するかどうか
    batch_size=5                # バッチサイズ
)

# URLをチェック
checker.check_url('https://example.com')

# 結果を表示
checker.print_results()

# 結果を取得
results = checker.get_results()
```
"""

import os
import yaml
import logging
import asyncio
from typing import List, Dict, Optional, Set, Any, Tuple
from bs4 import BeautifulSoup

# 内部からの実行のみをサポート
from utils.cache_manager import CacheManager
from utils.image_analyzer import ImageAnalyzer
from utils.html_processor import HTMLProcessor

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class WCAGImagesOfTextChecker:
    def __init__(self, config_path: str = 'config.yaml', max_images: int = None, use_cache: bool = True, batch_size: int = 10):
        """初期化"""
        logger.info("WCAGImagesOfTextCheckerを初期化中...")
        self.config = self.load_config(config_path)
        self.results = []
        self.checked_urls = set()
        self.checked_images = set()  # 重複チェック防止用
        self.max_images = max_images
        self.use_cache = use_cache
        self.batch_size = batch_size  # バッチサイズ
        
        # キャッシュマネージャーの初期化
        if self.use_cache:
            cache_dir = self.config.get('cache', {}).get('directory', 'cache')
            cache_expiry = self.config.get('cache', {}).get('expiry_days', 7)
            self.cache_manager = CacheManager(cache_dir, cache_expiry)
        else:
            self.cache_manager = None
        
        # 画像分析クラスの初期化
        self.image_analyzer = ImageAnalyzer(
            api_key=self.config['openai']['api_key'],
            model=self.config['openai']['model']
        )
        
        # HTML処理クラスの初期化
        self.html_processor = HTMLProcessor(self.cache_manager if self.use_cache else None)
        
        logger.info("初期化完了")

    def load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        logger.info(f"設定ファイルを読み込み中: {config_path}")
        
        # モジュールディレクトリを取得
        module_dir = os.path.dirname(os.path.abspath(__file__))
        
        # デフォルト設定
        default_config = {
            'openai': {
                'api_key': os.environ.get('OPENAI_API_KEY', ''),
                'model': 'gpt-4-vision-preview'
            },
            'cache': {
                'enabled': True,
                'directory': os.path.join(module_dir, 'cache'),  # モジュールディレクトリ内のcacheディレクトリを指定
                'expiry_days': 7
            }
        }
        
        # 相対パスの場合、モジュールのディレクトリからの相対パスとして解釈
        if not os.path.isabs(config_path):
            module_config_path = os.path.join(module_dir, config_path)
            
            if os.path.exists(module_config_path):
                config_path = module_config_path
                logger.info(f"モジュールディレクトリ内の設定ファイルを使用: {config_path}")
        
        # 設定ファイルが存在する場合は読み込む
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info("設定ファイルの読み込みが完了")
            except Exception as e:
                logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}")
                logger.info("デフォルト設定を使用します")
                config = default_config
        else:
            logger.warning(f"設定ファイル {config_path} が見つかりません")
            logger.info("デフォルト設定を使用します")
            config = default_config
            
        # キャッシュ設定がなければデフォルト値を設定
        if 'cache' not in config:
            config['cache'] = default_config['cache']
        elif 'directory' in config['cache'] and not os.path.isabs(config['cache']['directory']):
            # キャッシュディレクトリが相対パスの場合、モジュールディレクトリからの相対パスに変換
            config['cache']['directory'] = os.path.join(module_dir, config['cache']['directory'])
            
        # OpenAI設定がなければデフォルト値を設定
        if 'openai' not in config:
            config['openai'] = default_config['openai']
            
        logger.info(f"キャッシュディレクトリ: {config['cache']['directory']}")
        return config

    async def check_image_async(self, img: BeautifulSoup, base_url: str, count: int, total: int) -> Optional[Dict]:
        """画像要素を非同期でチェック（キャッシュ対応）"""
        try:
            src = img.get('src')
            if not src:
                logger.warning(f"src属性が見つかりません ({count}/{total})")
                return None
                
            # 画像URLを絶対パスに変換
            image_url = self.html_processor.get_absolute_url(base_url, src)
            
            # 重複チェック
            if image_url in self.checked_images:
                logger.info(f"画像は既にチェック済み: {image_url}")
                return None
            self.checked_images.add(image_url)
            
            alt = img.get('alt', '')
            xpath = self.html_processor.get_xpath(img)
            
            # Vision APIで画像を分析（キャッシュ対応）
            analysis = await self.image_analyzer.analyze_image_async(
                image_url,
                count,
                total,
                self.cache_manager if self.use_cache else None
            )
            
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
    
    def check_image(self, img: BeautifulSoup, base_url: str, count: int, total: int) -> Optional[Dict]:
        """画像要素をチェック（同期版、後方互換性のため）"""
        return asyncio.run(self.check_image_async(img, base_url, count, total))

    async def check_url_async(self, url: str):
        """URLを非同期でチェック（キャッシュ対応）"""
        if url in self.checked_urls:
            logger.info(f"URLは既にチェック済み: {url}")
            return
        self.checked_urls.add(url)
        
        try:
            # 1. ページコンテンツを取得（キャッシュがあれば再利用）
            soup = self.html_processor.fetch_page_content(url)
            
            # 2. 画像要素を抽出（キャッシュがあれば再利用）
            images = self.html_processor.extract_images(url, soup)
            
            # 3. 画像を分析
            total_images = len(images) if self.max_images is None else min(len(images), self.max_images)
            logger.info(f"画像要素を {len(images)} 個検出" + (f"（処理上限: {self.max_images}個）" if self.max_images is not None else ""))
            
            # 処理対象の画像
            target_images = images if self.max_images is None else images[:self.max_images]
            
            # バッチ処理
            results = []
            for i in range(0, len(target_images), self.batch_size):
                batch = target_images[i:i+self.batch_size]
                batch_tasks = []
                
                logger.info(f"バッチ処理開始: {i+1}～{min(i+self.batch_size, len(target_images))}/{len(target_images)}")
                
                # 各画像の処理タスクを作成
                for j, img in enumerate(batch, 1):
                    count = i + j
                    task = self.check_image_async(img, url, count, total_images)
                    batch_tasks.append(task)
                
                # バッチ内のタスクを並列実行
                batch_results = await asyncio.gather(*batch_tasks)
                
                # 結果を追加
                for result in batch_results:
                    if result:
                        results.append(result)
                
                logger.info(f"バッチ処理完了: {i+1}～{min(i+self.batch_size, len(target_images))}/{len(target_images)}")
            
            # 結果を保存
            self.results.extend(results)
                    
        except Exception as e:
            logger.error(f"URLのチェック中にエラーが発生: {str(e)}")
            self.results.append({
                "url": url,
                "error": f"URLのチェック中にエラーが発生: {str(e)}"
            })
    
    def check_url(self, url: str):
        """URLをチェック（同期版、後方互換性のため）"""
        asyncio.run(self.check_url_async(url))

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