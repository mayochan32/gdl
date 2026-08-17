# GDL ペルソナ チューリングテスト — 運用手順（v1.1 / 軸A）

GDLを組み込んだAIが本人をどれだけ再現できるかを、1つのGPTで A/B/C 比較により定量測定する。

- **A（床）**: GDL無しの素のAI　**B**: GDL有りのAI　**C（gold）**: 人間本人
- 指標: `GDL Fidelity Score = (sim(B,C) − sim(A,C)) / (1 − sim(A,C))`（1に近いほどGDLが効いている）
- 測定対象は **軸A（同一性）** のみ（軸B＝人間性は今後）。
- 出題数は被験者が選択：**短縮版40問**（各軸1問）／**標準版80問**（各軸2問）

## 構成ファイル

| ファイル | 役割 | 読む人 |
|---|---|---|
| `PTT_GPT_instructions.txt` | GPTのInstructionsに貼る本体（全文をそのまま貼る） | GPT作成者 |
| `PTT_GPT_SETUP.md` | GPT構築手順・設定チェックリスト（説明欄の文面を含む）・設計メモ | GPT作成者 |
| `ptt_scorer.py` | 採点エンジン（Knowledgeに同梱、Code Interpreterで実行） | — |
| `../GDL_eval_pool.json` | 質問プール1000問（Knowledgeに同梱） | — |
| `../ptt_guide.html` | 被験者向けガイド（これ1枚を配れば受験できる） | 被験者 |
| `../eval.html` | 評価フレームワークの設計思想 | 興味のある人 |

## GPTの作り方

設定値の一覧は `PTT_GPT_SETUP.md` の「1. GPT Builder での設定」を参照。要点だけ：

1. GPTを新規作成し、名前を「GDL Persona Turing Test」に。
2. **Instructions** に `PTT_GPT_instructions.txt` の**全文**を貼る（加工不要）。
3. **Capabilities**: Code Interpreter & Data Analysis を **ON**（必須）。Web Searchは **OFF** 推奨。
4. **Knowledge** に2ファイルをアップロード: `GDL_eval_pool.json`、`ptt_scorer.py`。
5. 公開範囲を「リンクを知っている人のみ」にして保存。
6. 発行された公開URLを `../ptt_guide.html` の `PTT_GPT_URL_HERE`（3箇所）に反映する。

## 被験者の使い方

被験者に渡すのは `../ptt_guide.html`（またはそのGitHub PagesのURL）。以下はその要約：

1. まず別GPT「GDL Generator」で自分のGDL（JSON）を作り、`.json` ファイルとして保存する。
2. このGPTを開き、**まだGDLは添付せず**「開始」と入力する。
   - ※ChatGPTは添付した瞬間に中身を読み込むため、先に添付すると床(A)が汚染される。**GDLはGPTから求められてから**ファイルで添付（本文に貼らない）。
3. 出題数（40問 or 80問）を選ぶ。
4. GPTが自動で進める:
   - 出題サブセットを層化抽出（各軸1問 or 2問）
   - A（素のAI）を生成（GDL不在のクリーンな床）→ **「GDLを添付してください」と依頼** → 添付 → B（本人として）を生成
   - 同じ問題に**被験者自身が回答**（C）。**1問ずつ提示され、記号1文字（A/B/C/D/X）を送るだけ**で次へ進む。
   - 採点 → レポート表示＋ `ptt_result.json` ＋ `ptt_report.md` をダウンロード

> 注：ChatGPTのGPTではチャット内にクリック可能なボタンは出せない（仕様）。回答は記号1文字の送信で行う。本物のボタンUIが必要な場合は、GPTsではなく別途Webフォーム（`input.html` 系）の用意が必要。

## 汚染防止（設計の肝）

- GDLは**ファイル添付のみ**、かつ **Aの生成が終わってから**添付させる。
- **A→B→C の順**を厳守（Cを先に見るとBがカンニングになる）。
- GDLを本文に貼った場合は汚染するため、GPTがやり直しを促す。
- 選択肢の軸座標 `axis_pos` は被験者に一切見せない（見えると狙って答えられてしまう）。

## 中断復帰（v1.1）

Code Interpreter のセッションは長時間の対話でリセットされ、変数が消えることがある。対策として **A確定時・B確定時・C収集10問ごと**に `ptt_state.json` を書き出す。落ちた場合は被験者が新しい会話で「再開」と送り、このファイルを添付すれば続きから再開できる。

`ptt_state.json` には**質問IDのみ**を保存し、質問本体と `axis_pos` は含めない（被験者が開いても答えが漏れないため）。採点時はIDでプールから引き直す。

## 既知の限界（v1）

- 1回実施（A/B/C各1回）。揺らぎ低減には複数回平均が有効。
- 天井を1.0で近似（本来は人間のtest-retest自己一致）。Fidelityはやや低めに出る安全側。
- 軸B（人間かAIか＝ブレードランナー型）は未対応。v2で自由記述＋判定を追加予定。
- 選択式のみ。実際の文体は測っていない。

## ローカル検証（手元のPythonでも実行可）

```bash
# 出題サブセット作成（--n は 1=40問 / 2=80問）
python gpts/ptt_scorer.py sample --pool GDL_eval_pool.json --n 1 --seed 1234 --out subset.json --show

# A/B/C（各 {"answers":{"P0001":"A",...}} 形式）を用意して採点
python gpts/ptt_scorer.py score --subset subset.json --a A.json --b B.json --c C.json \
       --subject mayo --model gpt --date 2026-08-17 --out-json result.json --out-md report.md
```
