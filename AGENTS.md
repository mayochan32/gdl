# AGENTS.md — GDLリポジトリの運用ルール

> このリポジトリで作業する**人とAIの両方**が従うルールの正本です。
> Claude Code・Codex・Cursor など、`AGENTS.md` / `CLAUDE.md` を自動で読むツールにはそのまま適用されます。
> ChatGPT や Gemini など自動で読まないAIに作業させるときは、最初にこのファイルを読ませてください。
> `research/` 配下の詳しいルールは [research/README.md](research/README.md) が正本です。

- 制定: 2026-10-10
- 最終更新: 2026-10-10

---

## 1. フォルダ構成

```
gdl/
├── README.md               # プロジェクト説明（人向けの入口）
├── AGENTS.md               # 運用ルール（このファイル）
├── CLAUDE.md               # Claude Code 用。AGENTS.md を読み込むだけ
├── HANDOFF.md              # 別のAIへの引き継ぎ資料
├── LICENSE
├── index.html  input.html  eval.html  ptt_guide.html  filelist.html   # GitHub Pages
├── images/                 # Pages 用の画像
│
├── schema/                 # 仕様の本体（マスタースキーマ・自動生成スキーマ・質問セット）
│   └── lang/               # 言語パック（英語・中国語）
├── prompts/                # LLMに貼るシステムプロンプト
│   ├── generator/          # GDL生成（GPTs・Gems）
│   └── text-analyzer/      # 文章からGDLを抽出
├── eval/                   # 忠実度評価
│   ├── keys/               # 被験者ごとの回答キー
│   ├── ptt/                # ペルソナ チューリングテスト
│   └── bigfive/            # 性格診断法（Big Five / IPIP-NEO-120）
├── research/               # 調査・検討（ルールは research/README.md）
├── docs/                   # スライドなどの資料
├── archive/                # 使わなくなった旧版
└── local/                  # 公開しないファイル（.gitignore 対象）
```

### 何をどこに置くか

| 置くもの | 場所 |
|---|---|
| スキーマ、質問セット、スキーマ生成スクリプト | `schema/` |
| スキーマの翻訳（言語パック） | `schema/lang/` |
| GPTs・Gems などに貼るプロンプトと、そのナレッジファイル | `prompts/<用途>/` |
| 評価の仕様・質問・採点スクリプト・結果データ | `eval/` |
| 論文の調査、設計の検討、実験の記録 | `research/<カテゴリ>/studies/` |
| 公開ページ（HTML） | ルート |
| 実名や個人を特定できる情報を含むファイル | `local/` |
| 置き換えられた旧版 | `archive/`（不要なら削除してよい。git の履歴には残る） |

迷ったときの目安は、**「作ったもの（動くもの・配るもの）」は機能別のフォルダ、「調べたこと・考えたこと」は `research/`** です。
`research/` で結論が出たら `schema/` や `eval/` に反映します。

---

## 2. 変えてはいけないもの

- **ルートの HTML 5本と `images/`**
  GitHub Pages（https://mayochan32.github.io/gdl/ ）の公開URLです。移動も改名もしないでください。
- **既存ファイルの名前**
  プロンプトや配布物がファイル名で参照しています（例: `PTT_prompt.txt` は `GDL_eval_pool.json` を名指ししている）。フォルダの移動はしてよいですが、改名はしないでください。
- **`research/` の検討フォルダ名と論点ID**
  一度作ったら変えないでください。リンクが切れます。
- **`schema/GDL_schema_lv1.json` / `lv2` / `lv3`**
  自動生成物なので、直接編集しないでください。`GDL_schema.json` を直してから `node schema/build_schemas.js` で再生成します。

---

## 3. 命名規則

| 対象 | 規則 | 例 |
|---|---|---|
| 仕様・ツールのファイル | `GDL_` で始め、英語の snake_case（既存に合わせる） | `GDL_eval_pool.json` |
| フォルダ | 英小文字。単語はハイフンでつなぐ | `text-analyzer` |
| research の検討フォルダ | `YYYY-MM-DD_english-slug_日本語の短い名前` | `2026-10-08_memoryforge_MemoryForge論文の解釈` |

すべての名前で、次のものは使わないでください。

- スペース（半角・全角とも）
- 記号 `/ \ : * ? " < > | # %`
- 全角英数字

---

## 4. ファイルを変更したら必ずやること

1. **`filelist.html` を更新する**
   ファイルを作成・削除したとき、内容を大きく変えたときは毎回更新し、同じコミットに含めます。
2. **フォルダ構成を変えたら、このファイルの §1 と `README.md` のファイル構成の節を更新する**
3. **移動・改名したら、古いパスを全文検索してリンク切れを直す**
   ```
   grep -rn "古いパス" --include=*.md --include=*.html --include=*.txt --include=*.py --include=*.js .
   ```
   特に `ptt_guide.html` の raw ダウンロードリンクは配布中のページなので、必ず確認してください。
4. **スキーマを変えたら影響範囲を追う**
   `build_schemas.js` で lv1〜lv3 を再生成し、言語パック・プロンプト群・入力フォームへの波及を確認します。

---

## 5. 公開範囲

- このリポジトリは**公開**です。`research/` を含め、コミットしたものはすべて公開されます。
- 実名や個人を特定できる情報を含むファイルは `local/` に置いてください（`.gitignore` 対象）。
- 論文の PDF はコミットしないでください。arXiv などへのリンクで参照します（`research/` 配下の PDF は `.gitignore` 対象）。
- 普及戦略やロードマップのような非公開の資料は、別の非公開リポジトリで扱います。ここには置きません。

---

## 6. git の扱い

- コミットと push は mayo の Mac から行います。
  このリポジトリは `core.precomposeunicode = true` に設定済みで、日本語の濁点が分解されてファイル名が崩れる問題を防いでいます。Mac 以外の環境からはコミットしないでください。
- 日本語のパスを読める形で表示するため、`git config core.quotepath false` を推奨します。
- ファイルの移動は `git mv` で行います。**移動だけのコミット**と**中身を直すコミット**を分けてください。GitHub が改名として認識し、`git log --follow` で履歴を追えるようになります。
- コミットメッセージは英語で、既存の形式（`Add ...`、`PTT: ...` など）に合わせます。

### AI向けの注意

- リモート環境（サンドボックスや VM）から `git status` / `git add` / `git commit` を実行しないでください。`.git/index.lock` が残り、mayo の手元の git がロックされます。読み取り専用の `git log` などは使ってかまいません。
- 作業を始める前に、このファイルと、作業するフォルダの README を読んでください。
- 置き場所や名前の判断に迷ったら、推測でファイルを作らずに確認してください。
