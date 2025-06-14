"""
WCAG 1.4.5 Images of Text Checker
=================================

このパッケージは、ウェブページ内の画像テキストをWCAG 1.4.5基準に基づいてチェックするツールを提供します。
OpenAI Vision APIを使用して画像を分析し、テキストが含まれているかどうかを判定します。

主な機能:
-------
- ウェブページからの画像抽出
- OpenAI Vision APIを使用した画像分析
- 非同期処理とバッチ処理による効率的な実行
- キャッシュ機能によるパフォーマンス向上

使用方法:
-------
```python
from wcag_images_of_text_checker import check_wcag_1_4_5

# 基本的な使用方法
results = check_wcag_1_4_5('https://example.com')

# オプションを指定して使用
results = check_wcag_1_4_5(
    url='https://example.com',
    config_path='custom_config.yaml',
    max_images=20,
    use_cache=True,
    batch_size=5
)
```

コマンドラインからの使用:
---------------------
```bash
python -m wcag_images_of_text_checker.main https://example.com
```
"""

# wcag_images_of_text_checker パッケージの初期化
from .main import check_wcag_1_4_5

__all__ = ['check_wcag_1_4_5']