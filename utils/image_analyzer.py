"""
WCAG 1.4.5 Images of Text Checker - 画像分析モジュール
==================================================

このモジュールは、OpenAI Vision APIを使用して画像を分析し、WCAG 1.4.5基準に基づいて
テキストが含まれているかどうかを判定します。非同期処理を使用して、複数の画像を
効率的に処理します。

主な機能:
-------
- OpenAI Vision APIを使用した画像分析
- 非同期処理による並列実行
- バッチ処理による効率化
- キャッシュ機能によるパフォーマンス向上

使用方法:
-------
```python
from wcag_images_of_text_checker.utils.image_analyzer import ImageAnalyzer

# 画像分析クラスの初期化
analyzer = ImageAnalyzer(
    api_key='your_openai_api_key',
    model='gpt-4o-mini'
)

# 単一画像の分析（同期版）
result = analyzer.analyze_image(
    image_url='https://example.com/image.jpg',
    count=1,
    total=1,
    cache_manager=None  # オプション: キャッシュマネージャー
)

# 単一画像の分析（非同期版）
result = await analyzer.analyze_image_async(
    image_url='https://example.com/image.jpg',
    count=1,
    total=1,
    cache_manager=None  # オプション: キャッシュマネージャー
)

# 複数画像のバッチ処理（非同期）
image_tasks = [
    ('https://example.com/image1.jpg', 1, 3, cache_manager),
    ('https://example.com/image2.jpg', 2, 3, cache_manager),
    ('https://example.com/image3.jpg', 3, 3, cache_manager)
]
results = await analyzer.analyze_images_batch(image_tasks)
```
"""

import json
import logging
import re
import asyncio
from typing import Dict, List, Tuple, Any
from openai import AsyncOpenAI

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self, api_key, model):
        """画像分析クラスの初期化"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.batch_size = 10  # 一度に処理するバッチサイズ
    
    async def analyze_image_async(self, image_url: str, count: int, total: int, cache_manager=None, max_retries: int = 3) -> Dict:
        """Vision APIを使用して画像を非同期分析（キャッシュ対応）"""
        # キャッシュが有効で、画像分析結果がキャッシュされている場合
        if cache_manager and cache_manager.is_analysis_cached(image_url):
            logger.info(f"キャッシュから分析結果を使用 ({count}/{total}): {image_url}")
            cached_analysis = cache_manager.get_analysis(image_url)
            if cached_analysis:
                return cached_analysis
        
        logger.info(f"画像を分析中 ({count}/{total}): {image_url}")
        
        for retry in range(max_retries):
            try:
                if retry > 0:
                    logger.info(f"リトライ {retry}/{max_retries-1} ({count}/{total}): {image_url}")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
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
                            if cache_manager:
                                cache_manager.cache_analysis(image_url, result)
                                
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
                            if cache_manager:
                                cache_manager.cache_analysis(image_url, result)
                                
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
                            if cache_manager:
                                cache_manager.cache_analysis(image_url, result)
                                
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
    
    def analyze_image(self, image_url: str, count: int, total: int, cache_manager=None, max_retries: int = 3) -> Dict:
        """同期版の画像分析メソッド（後方互換性のため）"""
        return asyncio.run(self.analyze_image_async(image_url, count, total, cache_manager, max_retries))
    
    async def analyze_images_batch(self, image_tasks: List[Tuple[str, int, int, Any]], max_retries: int = 3) -> List[Dict]:
        """複数の画像を非同期でバッチ処理"""
        tasks = []
        for image_url, count, total, cache_manager in image_tasks:
            task = self.analyze_image_async(image_url, count, total, cache_manager, max_retries)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)

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