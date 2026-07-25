# GDL Project — Handoff Document

> このドキュメントは、GDLプロジェクトの作業を別のAI（LLM）に引き継ぐための情報をまとめたものです。
> 新しいLLMにこのファイルを読み込ませることで、プロジェクトのコンテキストを効率的に引き継げます。

---

## 1. プロジェクト概要

**GDL（Ghost Description Language）** は、人間の個性・思想・行動パターン・価値観を JSON 形式で構造化記述するための仕様。「攻殻機動隊」の「ゴースト」概念に着想を得ている。

- **リポジトリ**: https://github.com/mayochan32/gdl
- **作者**: mayo（AI共創アーキテクト / AIとメタバース専門エンジニア）
- **ライセンス**: MIT
- **GDLバージョン**: 1.0
- **スキーマバージョン**: 1.2
- **対応言語**: 日本語（JA）、英語（EN）、簡体字中国語（ZH）

### 主な用途
- AIパーソナライズ（LLMに読み込ませて"その人らしい"AIを作る）
- デジタルツイン（メタバースのアバター個性定義）
- 自己理解・記録（自分の価値観を整理して残す）
- 没後継承（本人の個性をAIが語り継ぐ）

---

## 2. アーキテクチャ & 設計原則

### 2.1 Single Source of Truth

`GDL_schema.json` がマスタースキーマ。全ファイルはこのスキーマとの整合性を保つ必要がある。

```
GDL_schema.json（マスター）
  ├── build_schemas.js → GDL_schema_lv1/lv2/lv3.json（自動生成）
  ├── GDL_questions.json（質問はスキーマのフィールドにマッピング）
  ├── GDL_TextAnalyzer_knowledge.json（スキーマ構造 + 推論ガイド）
  ├── GDL_lang_en.json / GDL_lang_zh.json（スキーマの多言語翻訳）
  └── GPTsプロンプト群（スキーマの出力形式に準拠）
```

### 2.2 3段階の詳細度レベル

| レベル | 観点 | AIが再現できること |
|--------|------|-------------------|
| **Lv1** | Who — 属性・表層 | 話し方・口調・基本的な好み |
| **Lv2** | How — 思考・判断 | 判断・推論パターン、価値観に基づく行動 |
| **Lv3** | Why — 深層心理・形成史 | 人生の文脈・矛盾・葛藤を含む深い人格 |

上位レベルは下位を包含する。スキーマは11セクション × 3レベルで642項目以上。

### 2.3 v1.2 出力形式の必須ルール

GDL JSON出力には以下が**必須**：

1. **`_preamble`** — AIがGDLを読み込む際の解釈ガイド。省略不可
2. **各セクションに `_description`** — セクションの意味説明
3. **スケール値に `label`** — `{ "value": 数値, "label": "意味" }` 形式
4. **`confidence_convention`** — テキスト分析時のみ。_preamble内に含める

### 2.4 _confidence 仕様

テキスト分析など間接的方法でGDLを生成する場合に使用：

| レベル | 意味 | AI指示 |
|--------|------|--------|
| high | 明示的記述あり | 強く反映 |
| medium | 複数間接証拠から推論 | 基本反映、矛盾時は調整 |
| low | 弱い手がかりからの推測 | 参考のみ |
| user_confirmed | 本人確認済み | high以上に信頼 |
| user_provided | 本人直接提供 | 最も信頼 |

---

## 3. ファイル構成

全ファイルの詳細は `filelist.html` を参照。以下は構造の概要：

### スキーマ & データ
| ファイル | 役割 |
|---------|------|
| `GDL_schema.json` | マスタースキーマ（SSOT） |
| `GDL_schema_lv1/lv2/lv3.json` | レベル別スキーマ（自動生成） |
| `GDL_questions.json` | インタビュー質問56問（JA/EN/ZH） |
| `GDL_TextAnalyzer_knowledge.json` | Text Analyzer用ナレッジ |

### 言語パック
| ファイル | 言語 | リーフ値 |
|---------|------|---------|
| `GDL_lang_en.json` | English | 2,341 |
| `GDL_lang_zh.json` | 简体中文 | 2,341 |

（日本語はマスタースキーマ内の `_labels` に含まれる）

### GPTsプロンプト（各3言語）
| エージェント | JA | EN | ZH |
|-------------|----|----|-----|
| Interview Agent | `GDL_GPTs_prompt.md` | `_en.md` | `_zh.md` |
| Text Analyzer | `GDL_TextAnalyzer_GPTs_prompt.md` | `_en.md` | `_zh.md` |
| Gems (Google) | `GDL_Gems_prompt.md` | — | — |

### Web UI
| ファイル | 役割 |
|---------|------|
| `index.html` | ランディングページ（3言語・GitHub Pages） |
| `input.html` | GDL入力フォーム（Lv1・3言語） |
| `GDL_input.html` | 旧版入力フォーム（参考用） |

### その他
| ファイル | 役割 |
|---------|------|
| `build_schemas.js` | レベル別スキーマ自動生成 |
| `README.md` | プロジェクト説明 |
| `GDL_concept_v2.pptx` | コンセプトプレゼン |
| `filelist.html` | リポジトリファイル一覧ページ |

---

## 4. 整合性ルール（最重要）

ファイル間の整合性は過去に複数回の不整合修正を経て確立されたもの。以下を厳守すること：

### 4.1 統一済みの仕様

| 項目 | 統一ルール |
|------|-----------|
| `gdl_version` | 全ファイルで `"1.0"`（GDL 1.0 凍結バージョン。旧 `schema_version` は廃止し `gdl_version` に一本化） |
| セクション `_description` | 各セクションのdescription表現は全ファイルで統一 |
| `_levels` キー名 | `Lv1`, `Lv2`, `Lv3`（大文字L、小文字v） |
| `_confidence` キー名 | `high`, `medium`, `low`, `user_confirmed`, `user_provided` |
| meta フィールド構成 | `gdl_version`, `created_at`, `updated_at`, `subject_id`, `detail_level`, `generation_method`, `source_type`, `source_summary`, `target_person`, `speakers_detected` |
| `_preamble` | スキーマに定義済み。出力時に必須 |

### 4.2 ファイル変更時のチェックリスト

スキーマを変更した場合：
- [ ] `GDL_schema.json` を更新
- [ ] `node build_schemas.js` でlv1/lv2/lv3を再生成
- [ ] `GDL_TextAnalyzer_knowledge.json` の対応箇所を更新
- [ ] `GDL_questions.json` の対応箇所を更新（該当する場合）
- [ ] `GDL_lang_en.json` / `GDL_lang_zh.json` の対応箇所を更新
- [ ] GPTsプロンプト群（JA/EN/ZH）の対応箇所を更新
- [ ] `filelist.html` を更新（ファイル追加/削除/大きな変更時）

---

## 5. 永続ルール

### 5.1 filelist.html のメンテナンス

`filelist.html` はリポジトリ内全ファイルの一覧ページ。**ファイルの作成・更新（大きな変更）・削除が発生した場合、必ず同時に更新すること。** コミットにも含める。

ファイルは以下の6カテゴリで分類：
1. スキーマ & データ定義
2. 言語パック（i18n）
3. GPTs システムプロンプト
4. Web UI
5. ツール & 設定
6. ドキュメント & プレゼン

---

## 6. 開発環境 & ツール

- **ホスティング**: GitHub Pages（index.html がランディングページ）
- **ビルドツール**: Node.js（`build_schemas.js`）
- **Git管理**: GitHub（https://github.com/mayochan32/gdl）
- **認証**: HTTPSリモート（push時にローカル環境で認証が必要）

---

## 7. 今後の検討事項・未着手タスク

- Lv2/Lv3対応の入力フォーム（現在input.htmlはLv1のみ）
- GDL_Gems_prompt.md の英語版・中国語版（現在日本語のみ）
- README.md の多言語化
- GDL_TextAnalyzer_knowledge.json の英語版・中国語版
- filelist.html 自体の多言語化

---

## 8. コミュニケーションスタイル

mayoとの作業時の注意点：
- 日本語で会話（技術用語は英語OK）
- 会話調の自然なスタイルを好む（箇条書きは「分析的に回答して」と指示された時のみ）
- 批判的思考を歓迎（同意よりも反対意見を求める）
- 事実ベースで正確な回答を重視
- 推測する場合はその旨を明示

---

*Generated: 2026-05-30 by Chappy (Claude)*
