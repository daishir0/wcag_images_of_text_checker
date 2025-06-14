# WCAG Images of Text Checker

## Overview
This tool checks images on web pages to determine if they contain text and verifies if the alternative text matches the text content within the image. It helps ensure compliance with WCAG 1.4.5 (Images of Text) and 1.1.1 (Non-text Content) guidelines. The tool uses OpenAI Vision API for image analysis and implements asynchronous processing and batch operations for improved performance.

## Features
- Asynchronous processing for faster analysis
- Batch processing of multiple images in parallel
- Caching mechanism to reduce API calls and improve performance
- Modular code structure for better maintainability
- Detailed documentation and usage examples

## Installation
1. Clone the repository:
```bash
git clone https://github.com/daishir0/wcag_images_of_text_checker.git
cd wcag_images_of_text_checker
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the settings:
   - Copy `config.yaml.sample` to `config.yaml`
   - Add your OpenAI API key to `config.yaml`

## Usage
1. Run the checker with a URL:
```bash
python main.py <URL> [options]
```

### Command Line Options
- `--max-images <number>`: Limit the number of images to process
- `--batch-size <number>`: Set the number of images to process in parallel (default: 10)
- `--no-cache`: Disable caching and always perform fresh analysis
- `--config <file_path>`: Specify a custom configuration file path

### Examples
```bash
# Basic usage
python main.py https://example.com

# Process maximum 5 images
python main.py https://example.com --max-images 5

# Set batch size to 3
python main.py https://example.com --batch-size 3

# Disable caching
python main.py https://example.com --no-cache

# Combine multiple options
python main.py https://example.com --max-images 20 --batch-size 5 --no-cache
```

### Example Output
```
2025-05-23 14:22:44 - INFO - Starting WCAG 1.4.5 check: https://example.com/page
2025-05-23 14:22:44 - INFO - Initializing WCAGImagesOfTextChecker...
2025-05-23 14:22:44 - INFO - Loading config file: config.yaml
2025-05-23 14:22:44 - INFO - Config file loaded
2025-05-23 14:22:44 - INFO - Initialization complete
2025-05-23 14:22:44 - INFO - Accessing URL: https://example.com/page
2025-05-23 14:22:45 - INFO - Detected 50 image elements (processing limit: 10)
2025-05-23 14:22:45 - INFO - Processing images in batches of 10...

[... Processing logs omitted for brevity ...]

WCAG 1.4.5 Images of Text Check Results:
================================================================================

URL: https://example.com/page
Image URL: https://example.com/images/header.jpg
XPATH: /html/body/div/header/img
Element: <img alt="Company Project Initiative" src="/images/header.jpg"/>
Alt Text: Company Project Initiative

WCAG 1.4.5 Assessment:
Text Detection: Yes
Detected Text: "Company Project Initiative"
Text Purpose: Header, Project Introduction

Visual Content:
Contains Significant Visual Content: Yes
Visual Content Description: Colorful design elements with brand imagery

WCAG 1.4.5 Criteria:
Logo/Brand: Yes
Essential Presentation: Yes
Essential Reason: Brand identity and recognition
Customizable: No
HTML/CSS Implementation Possible: Yes
Text Alternative Provided: No

WCAG 1.4.5 Compliant: Yes
Reason: Contains essential brand elements and logo that are exempt from the requirement

Recommendations:
- Consider providing text alternatives where possible
- Enhance visual contrast for better readability

[... Additional results omitted for brevity ...]
```

## Module Structure
- `wcag_checker.py`: Main checker class implementing WCAG 1.4.5 checks
- `utils/`:
  - `cache_manager.py`: Caching functionality for HTML, images, and analysis results
  - `html_processor.py`: HTML fetching and image extraction
  - `image_analyzer.py`: OpenAI Vision API integration for image analysis

## Programmatic Usage
You can also use the tool programmatically in your Python code:

```python
from wcag_images_of_text_checker import check_wcag_1_4_5

# Basic usage
results = check_wcag_1_4_5('https://example.com')

# With options
results = check_wcag_1_4_5(
    url='https://example.com',
    config_path='custom_config.yaml',
    max_images=20,
    use_cache=True,
    batch_size=5
)
```

## Notes
- The tool requires an OpenAI API key with access to Vision API
- Performance is significantly improved with asynchronous and batch processing
- Caching reduces API calls and speeds up repeated analyses
- Some complex text layouts might not be accurately detected
- Performance may vary depending on image quality and text complexity

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# WCAG 文字画像チェッカー

## 概要
このツールは、ウェブページ上の画像をチェックし、テキストを含むかどうかを判定し、代替テキストが画像内のテキストと一致しているかを検証します。WCAG 1.4.5（文字画像）と1.1.1（非テキストコンテンツ）のガイドラインへの準拠を確認するのに役立ちます。OpenAI Vision APIを使用して画像分析を行い、非同期処理とバッチ処理を実装してパフォーマンスを向上させています。

## 機能
- 非同期処理による高速な分析
- 複数画像の並列バッチ処理
- API呼び出しを削減し、パフォーマンスを向上させるキャッシュ機構
- 保守性を高めるモジュール構造
- 詳細なドキュメントと使用例

## インストール方法
1. リポジトリをクローン:
```bash
git clone https://github.com/daishir0/wcag_images_of_text_checker.git
cd wcag_images_of_text_checker
```

2. 必要な依存関係をインストール:
```bash
pip install -r requirements.txt
```

3. 設定:
   - `config.yaml.sample`を`config.yaml`にコピー
   - `config.yaml`にOpenAI APIキーを追加

## 使い方
1. URLを指定してチェッカーを実行:
```bash
python main.py <URL> [オプション]
```

### コマンドラインオプション
- `--max-images <数値>`: 処理する画像の最大数を指定
- `--batch-size <数値>`: 並列処理する画像の数を指定（デフォルト: 10）
- `--no-cache`: キャッシュを無効にして常に新しい分析を実行
- `--config <ファイルパス>`: カスタム設定ファイルのパスを指定

### 実行例
```bash
# 基本的な使用方法
python main.py https://example.com

# 最大5枚の画像を処理
python main.py https://example.com --max-images 5

# バッチサイズを3に設定
python main.py https://example.com --batch-size 3

# キャッシュを無効化
python main.py https://example.com --no-cache

# 複数のオプションを組み合わせ
python main.py https://example.com --max-images 20 --batch-size 5 --no-cache
```

### 実行例
```
2025-05-23 14:22:44 - INFO - WCAG 1.4.5チェックを開始: https://example.com/page
2025-05-23 14:22:44 - INFO - WCAGImagesOfTextCheckerを初期化中...
2025-05-23 14:22:44 - INFO - 設定ファイルを読み込み中: config.yaml
2025-05-23 14:22:44 - INFO - 設定ファイルの読み込みが完了
2025-05-23 14:22:44 - INFO - 初期化完了
2025-05-23 14:22:44 - INFO - URLにアクセス中: https://example.com/page
2025-05-23 14:22:45 - INFO - 画像要素を 50 個検出（処理上限: 10個）
2025-05-23 14:22:45 - INFO - 画像をバッチ処理中（バッチサイズ: 10）...

[... 処理ログ省略 ...]

WCAG 1.4.5 Images of Text チェック結果:
================================================================================

URL: https://example.com/page
画像URL: https://example.com/images/header.jpg
XPATH: /html/body/div/header/img
要素: <img alt="企業プロジェクト施策" src="/images/header.jpg"/>
代替テキスト: 企業プロジェクト施策

WCAG 1.4.5判定:
テキスト検出: あり
検出テキスト: "企業プロジェクト施策"
テキストの目的: 見出し、プロジェクト紹介

視覚的コンテンツ:
重要な視覚的コンテンツを含む: はい
視覚的コンテンツの説明: ブランドイメージを含むカラフルなデザイン要素

WCAG 1.4.5基準:
ロゴ/ブランド: はい
本質的な表現: はい
本質的と判断した理由: ブランドアイデンティティと認知のため
カスタマイズ可能: いいえ
HTML/CSS実装可能: はい
テキストでも提供: いいえ

WCAG 1.4.5準拠: はい
判定理由: 必須のブランド要素とロゴを含むため、要件の例外に該当

改善提案:
- 可能な箇所でテキストによる代替を検討
- 視認性向上のためコントラストを強化

[... 以下、結果省略 ...]
```

## モジュール構造
- `wcag_checker.py`: WCAG 1.4.5チェックを実装するメインクラス
- `utils/`:
  - `cache_manager.py`: HTML、画像、分析結果のキャッシュ機能
  - `html_processor.py`: HTMLの取得と画像抽出
  - `image_analyzer.py`: OpenAI Vision APIを使用した画像分析

## プログラムからの使用
Pythonコードから直接ツールを使用することもできます：

```python
from wcag_images_of_text_checker import check_wcag_1_4_5

# 基本的な使用方法
results = check_wcag_1_4_5('https://example.com')

# オプションを指定
results = check_wcag_1_4_5(
    url='https://example.com',
    config_path='custom_config.yaml',
    max_images=20,
    use_cache=True,
    batch_size=5
)
```

## 注意点
- このツールはVision APIにアクセスできるOpenAI APIキーが必要です
- 非同期処理とバッチ処理によりパフォーマンスが大幅に向上します
- キャッシュによりAPI呼び出しが削減され、繰り返し分析が高速化されます
- 複雑なテキストレイアウトは正確に検出できない場合があります
- 画像の品質やテキストの複雑さによって性能が変動する可能性があります

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。