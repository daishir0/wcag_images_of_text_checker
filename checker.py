import os
import sys
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
from typing import List, Dict, Optional, Set
import json
import logging

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class WCAGImagesOfTextChecker:
    def __init__(self, config_path: str = 'config.yaml', max_images: int = 10):
        """初期化"""
        logger.info("WCAGImagesOfTextCheckerを初期化中...")
        self.config = self.load_config(config_path)
        self.client = OpenAI(api_key=self.config['openai']['api_key'])
        self.results = []
        self.checked_urls = set()
        self.checked_images = set()  # 重複チェック防止用
        self.max_images = max_images
        logger.info("初期化完了")

    def load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        logger.info(f"設定ファイルを読み込み中: {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
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

    def analyze_image(self, image_url: str, count: int, total: int) -> Dict:
        """Vision APIを使用して画像を分析"""
        logger.info(f"画像を分析中 ({count}/{total}): {image_url}")
        try:
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
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                else:
                    raise ValueError("JSON not found in response")
                
                logger.info(f"画像分析が完了 ({count}/{total})")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析エラー ({count}/{total}): {str(e)}\nResponse: {content}")
                return self._create_error_response(f"JSON解析エラー: {str(e)}")
                
        except Exception as e:
            logger.error(f"画像分析中にエラーが発生 ({count}/{total}): {str(e)}")
            return self._create_error_response(f"画像分析エラー: {str(e)}")

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

    def check_image(self, img: BeautifulSoup, base_url: str, count: int, total: int) -> Optional[Dict]:
        """画像要素をチェック"""
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
            
            # Vision APIで画像を分析
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
        """URLをチェック"""
        if url in self.checked_urls:
            logger.info(f"URLは既にチェック済み: {url}")
            return
        self.checked_urls.add(url)
        
        try:
            logger.info(f"URLにアクセス中: {url}")
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # すべての画像要素を取得
            images = []
            for img in soup.find_all('img'):
                if img.parent.name != 'picture':
                    images.append(img)
                elif not any(i.get('src') == img.get('src') for i in images):
                    images.append(img)
            
            total_images = min(len(images), self.max_images)
            logger.info(f"画像要素を {len(images)} 個検出（処理上限: {self.max_images}個）")
            
            # 各画像をチェック
            for i, img in enumerate(images[:self.max_images], 1):
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

def check_wcag_1_4_5(url: str, config_path: str = 'config.yaml', max_images: int = 10):
    """WCAG 1.4.5チェックを実行"""
    logger.info(f"WCAG 1.4.5チェックを開始: {url}")
    checker = WCAGImagesOfTextChecker(config_path, max_images)
    checker.check_url(url)
    checker.print_results()
    logger.info("チェックが完了しました")
    return checker.get_results()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        check_wcag_1_4_5(url)
    else:
        print("使用方法: python checker.py <URL>")