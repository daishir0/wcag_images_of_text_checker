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
2. Run the checker:
```bash
python checker.py
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
2. チェッカーを実行:
```bash
python checker.py
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