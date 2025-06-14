"""
WCAG 1.4.5 Images of Text Checker
=================================

このプログラムは、ウェブページ内の画像テキストをWCAG 1.4.5基準に基づいてチェックします。
OpenAI Vision APIを使用して画像を分析し、テキストが含まれているかどうかを判定します。
非同期処理とバッチ処理を使用して、複数の画像を効率的に処理します。

使い方:
------
```bash
python -m wcag_images_of_text_checker.main <URL> [オプション]
```

オプション:
---------
--max-images <数値>  : 処理する画像の最大数を指定します
--batch-size <数値>  : 同時に処理する画像の数を指定します（デフォルト: 10）
--no-cache          : キャッシュを使用せずに常に新しい分析を行います
--config <ファイルパス> : 設定ファイルのパスを指定します

コマンド例:
---------
# 基本的な使用方法
python -m wcag_images_of_text_checker.main https://example.com

# 最大5枚の画像を処理
python -m wcag_images_of_text_checker.main https://example.com --max-images 5

# バッチサイズを3に設定して処理
python -m wcag_images_of_text_checker.main https://example.com --batch-size 3

# キャッシュを使用せずに処理
python -m wcag_images_of_text_checker.main https://example.com --no-cache

# 複数のオプションを組み合わせて使用
python -m wcag_images_of_text_checker.main https://example.com --max-images 20 --batch-size 5 --no-cache
"""

import sys
import logging
import asyncio

# 内部からの実行のみをサポート
from wcag_checker import WCAGImagesOfTextChecker

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def check_wcag_1_4_5_async(url: str, config_path: str = 'config.yaml', max_images: int = None, use_cache: bool = True, batch_size: int = 10):
    """WCAG 1.4.5チェックを非同期で実行（キャッシュ対応）"""
    logger.info(f"WCAG 1.4.5チェックを開始: {url}")
    checker = WCAGImagesOfTextChecker(config_path, max_images, use_cache, batch_size)
    await checker.check_url_async(url)
    checker.print_results()
    logger.info("チェックが完了しました")
    return checker.get_results()

def check_wcag_1_4_5(url: str, config_path: str = 'config.yaml', max_images: int = None, use_cache: bool = True, batch_size: int = 10):
    """WCAG 1.4.5チェックを実行（キャッシュ対応）"""
    return asyncio.run(check_wcag_1_4_5_async(url, config_path, max_images, use_cache, batch_size))

def main():
    """メイン実行関数"""
    # コマンドライン引数の処理
    use_cache = True
    if '--no-cache' in sys.argv:
        use_cache = False
        sys.argv.remove('--no-cache')
    
    max_images = None
    for i, arg in enumerate(sys.argv):
        if arg == '--max-images' and i + 1 < len(sys.argv):
            try:
                max_images = int(sys.argv[i + 1])
                sys.argv.pop(i)
                sys.argv.pop(i)
                break
            except ValueError:
                pass
    
    config_path = 'config.yaml'
    for i, arg in enumerate(sys.argv):
        if arg == '--config' and i + 1 < len(sys.argv):
            config_path = sys.argv[i + 1]
            sys.argv.pop(i)
            sys.argv.pop(i)
            break
    
    batch_size = 10  # デフォルトのバッチサイズ
    for i, arg in enumerate(sys.argv):
        if arg == '--batch-size' and i + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[i + 1])
                sys.argv.pop(i)
                sys.argv.pop(i)
                break
            except ValueError:
                pass
    
    if '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) <= 1:
        print("使用方法: python -m wcag_images_of_text_checker.main <URL> [オプション]")
        print("オプション:")
        print("  --no-cache: キャッシュを使用しない")
        print("  --max-images <数値>: 処理する画像の最大数")
        print("  --config <ファイルパス>: 設定ファイルのパス")
        print("  --batch-size <数値>: 同時に処理する画像の数（デフォルト: 10）")
        print("  --help, -h: このヘルプメッセージを表示")
    elif len(sys.argv) > 1:
        url = sys.argv[1]
        check_wcag_1_4_5(url, config_path, max_images, use_cache, batch_size)

if __name__ == "__main__":
    main()