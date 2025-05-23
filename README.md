# WCAG Images of Text Checker

## Overview
This tool checks images on web pages to determine if they contain text and verifies if the alternative text matches the text content within the image. It helps ensure compliance with WCAG 1.4.5 (Images of Text) and 1.1.1 (Non-text Content) guidelines.

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

## Usage
1. Configure the settings in `config.yaml`
2. Run the checker with a URL:
```bash
python checker.py <URL>
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

The tool will:
- Detect if an image contains text
- Verify if the alternative text matches the text in the image
- Identify exceptions (logos, decorative text, font samples, brand text)
- Generate separate reports for WCAG 1.1.1 and 1.4.5 compliance

## Notes
- The tool requires proper image processing capabilities
- Some complex text layouts might not be accurately detected
- Performance may vary depending on image quality and text complexity

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# WCAG 文字画像チェッカー

## 概要
このツールは、ウェブページ上の画像をチェックし、テキストを含むかどうかを判定し、代替テキストが画像内のテキストと一致しているかを検証します。WCAG 1.4.5（文字画像）と1.1.1（非テキストコンテンツ）のガイドラインへの準拠を確認するのに役立ちます。

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

## 使い方
1. `config.yaml`で設定を行います
2. URLを指定してチェッカーを実行:
```bash
python checker.py <URL>
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

このツールは以下の機能を提供します：
- 画像内のテキスト検出
- 代替テキストと画像内テキストの一致確認
- 例外事項（ロゴ、装飾文字、フォントサンプル、ブランド文字）の識別
- WCAG 1.1.1と1.4.5の準拠状況の個別レポート生成

## 注意点
- 適切な画像処理機能が必要です
- 複雑なテキストレイアウトは正確に検出できない場合があります
- 画像の品質やテキストの複雑さによって性能が変動する可能性があります

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。