# GDL ペルソナ チューリングテスト — GPTs 運用手順（v1 / 軸A）

GDLを組み込んだAIが本人をどれだけ再現できるかを、1つのGPTで A/B/C 比較により定量測定する。

- **A（床）**: GDL無しの素のAI　**B**: GDL有りのAI　**C（gold）**: 人間本人
- 指標: `GDL Fidelity Score = (sim(B,C) − sim(A,C)) / (1 − sim(A,C))`（1に近いほどGDLが効いている）
- 測定対象は **軸A（同一性）** のみ（軸B＝人間性は今後）。

## 構成ファイル

| ファイル | 役割 |
|---|---|
| `PTT_GPTs_prompt.md` | GPTのInstructionsに貼るシステムプロンプト全文 |
| `ptt_scorer.py` | 採点エンジン（Knowledgeに同梱、Code Interpreterで実行） |
| `../GDL_eval_pool.json` | 質問プール1000問（Knowledgeに同梱） |

## GPTの作り方（OpenAI GPTs）

1. GPTを新規作成し、名前を「GDL Persona Turing Test」に。
2. **Instructions** に `PTT_GPTs_prompt.md` の「システムプロンプト本体」セクションを貼る。
3. **Capabilities**: Code Interpreter & Data Analysis を **ON**（必須）。
4. **Knowledge** に2ファイルをアップロード: `GDL_eval_pool.json`、`ptt_scorer.py`。
5. 公開範囲を設定して保存。

## 被験者の使い方

1. まず別GPT「GDL Generator」で自分のGDL（JSON）を作る。
2. このGPTを開き、**GDLをファイルで添付**（本文に貼らない）。
3. 「開始」と入力。GPTが自動で進める:
   - 80問の出題サブセットを抽出（各軸2問）
   - A（素のAI）を生成 → GDL読込 → B（本人として）を生成
   - 同じ80問に**あなた自身が回答**（C）
   - 採点 → レポート表示＋ `ptt_result.json` ＋ `ptt_report.md` をダウンロード

## 汚染防止（設計の肝）

- GDLは**ファイル添付のみ**。Code Interpreterではファイルはディスクに置かれ、開くまで文脈に入らない。
- GPTは **Bフェーズまでファイルを開かない** → Aはクリーンな床になる。
- **A→B→C の順**を厳守（Cを先に見るとBがカンニングになる）。
- GDLを本文に貼った場合は汚染するため、GPTがやり直しを促す。

## 既知の限界（v1）

- 1回実施（A/B/C各1回）。揺らぎ低減には複数回平均が有効。
- 天井を1.0で近似（本来は人間のtest-retest自己一致）。Fidelityはやや低めに出る安全側。
- 軸B（人間かAIか＝ブレードランナー型）は未対応。v2で自由記述＋判定を追加予定。

## ローカル検証（手元のPythonでも実行可）

```bash
# 出題サブセット作成
python gpts/ptt_scorer.py sample --pool GDL_eval_pool.json --n 2 --seed 1234 --out subset.json --show

# A/B/C（各 {"answers":{"C0001":"A",...}} 形式）を用意して採点
python gpts/ptt_scorer.py score --subset subset.json --a A.json --b B.json --c C.json \
       --subject mayo --model gpt --date 2026-06-01 --out-json result.json --out-md report.md
```
