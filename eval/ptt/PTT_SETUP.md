# ペルソナ チューリングテスト — 実施方法と設計メモ（v1.2 / 軸A）

> 旧ファイル名 `gpts/PTT_GPTs_prompt.md` → `gpts/PTT_GPT_SETUP.md` → 本ファイル。
> 2026-08-17、OpenAIが個人アカウントでのGPTs新規作成を停止したため、実行形態を「専用GPT」から「プロンプト貼り付け」に変更した。

---

## 1. 実行形態

**PTT_prompt.txt を、コード実行が使えるAIチャットに貼り付けて実施する。**

OpenAIヘルプセンターの記載（2026-08時点）:

> New GPT creation and publishing are not available on personal ChatGPT accounts, including Free, Go, Plus, and Pro.
> Existing GPTs remain usable and can still be edited if existing plan and permission requirements are met.

新規GPTを作れるのは Business / Enterprise / Edu ワークスペースのみ。既存のGPT（GDL Generator など）は引き続き動作し、共有リンクも有効。

### 1.1 貼り付け方式（標準）

被験者は次の3点を用意し、**新規の会話に1通のメッセージとしてまとめて送る**。

| 用意するもの | 場所 |
|---|---|
| `GDL_eval_pool.json` | リポジトリ直下（約894KB） |
| `ptt_scorer.py` | `ptt/` 配下（約11KB） |
| `PTT_prompt.txt` の全文 | `ptt/` 配下（約6,300文字） |

- 前2つは**添付**、プロンプトは**本文に貼り付け**。
- 被験者向けの案内は `../ptt_guide.html` に全部書いてある。ファイルのダウンロードリンクとプロンプトのコピーボタンも設置済みなので、**配るのはこのページのURL1つで足りる**。
- **必須要件**: コード実行（Code Interpreter / データ分析）。採点はLLMの暗算ではなく実際にPythonを走らせる設計なので、これが無いと成立しない。

### 1.2 GPTs方式（Business等のワークスペースがある場合のみ）

`PTT_prompt.txt` はそのままGPTのInstructionsにも使える（約6,300文字、上限8,000文字に収まる）。プロンプト側で「添付されているか、Knowledgeとして与えられているか」を問わない書き方にしてあるため、変更不要。

| 項目 | 設定値 |
|---|---|
| Name | GDL Persona Turing Test |
| Conversation starters | `開始` / `再開` |
| Knowledge | `eval/GDL_eval_pool.json`、`eval/ptt/ptt_scorer.py` |
| Capabilities | Code Interpreter **ON（必須）**、Web Search OFF推奨 |
| 説明欄 | 下記 1.3 |

### 1.3 説明欄・案内文に使うテキスト

被験者が何も入力する前に読む場所には、**「GDLを事前に用意する必要があること」と「最初は添付しないこと」の両方**を書く。片方だけだと、手ぶらで来られるか、逆に開始前に添付されて汚染する。

```
GDLを読み込んだAIが、どれだけ「あなた」を再現できるかを定量測定します。
【準備】あなたのGDL（JSONファイル）を手元に用意してください。無い場合は先に「GDL Generator」で作成を。
【流れ】①「開始」と送る→②出題数を選ぶ（40問/80問）→③AIが先に回答→④求められたらGDLを添付→⑤あなたが1問ずつ回答→⑥結果レポート
⚠️GDLは④まで添付しないでください。先に添付すると測定が成立しません。
```

なお `PTT_prompt.txt` の Step 0 でも同じ内容をより詳しく提示する。案内文を読み飛ばされても、最初の応答で全体像・準備物・添付タイミングが伝わる。

---

## 2. 動作の骨格

- **A（床）** GDL無しの素のAI ／ **B** GDL有りのAI ／ **C（gold）** 人間本人
- 指標: `GDL Fidelity Score = (sim(B,C) − sim(A,C)) / (1 − sim(A,C))`
- 測定対象は **軸A（同一性）** のみ。軸B（人間かAIか）は未対応。
- 出題数は被験者が選択: **短縮版40問**（各軸1問） / **標準版80問**（各軸2問）

```
Step 0  モード選択（GDLはまだ添付させない）
Step 1  sample_subset で層化抽出（コード実行必須）
Step 2  A（床）生成
Step 2.5 ptt_state.json 書き出し ← 中断対策
Step 3  GDL添付依頼 → B 生成 → state 更新
Step 4  C を一問一答で収集（10問ごとに state 更新）
Step 5  採点（state の question_ids からプールを引き直して subset 復元）
Step 6  レポート + ptt_result.json + ptt_report.md
```

---

## 3. 設計の肝

### 3.1 汚染防止

LLMは**添付した瞬間にファイル内容をコンテキストへ展開する**。「添付するが開かない」では床(A)が汚れる。したがって **Aの生成が終わるまでGDLを会話に持ち込ませない**（後から添付させる）のが唯一の解。A→B→C の順序も厳守（Cを先に見るとBがカンニングになる）。

貼り付け方式では開始時に2ファイルを添付するため、**「添付があれば汚染」ではなく「GDLの添付があれば汚染」**と判定する必要がある。プロンプト側に判別の目安（`meta.gdl_version` や `_preamble` を持つ人格記述JSONがGDL、質問プールと採点コードは違う）を明記してある。

Aは事前固定せず、**実施のたびにその場の現行モデルで取り直す**。モデルが更新されると床も動くため、古いAを使い回すと比較が壊れる。

### 3.2 中断復帰

コード実行環境のセッションは長時間の対話中にリセットされ、変数が失われることがある。80問の一問一答は数十分かかるため、**A確定・B確定・C収集10問ごとに `ptt_state.json` を書き出す**。落ちたら被験者が新しい会話でプロンプトを貼り直し、`ptt_state.json` を再添付して続きから再開できる。

`ptt_state.json` には**質問IDのみ**を保存し、質問本体と `axis_pos` は保存しない。被験者がファイルを開いても正解の配点が漏れないようにするため。採点時はIDでプールから引き直す。

### 3.3 出題数の選択

各軸2問（80問）は測定が安定するが、被験者の負担が大きく途中離脱と惰性回答のリスクがある。各軸1問（40問）でも40軸すべてをカバーできるため、被験者に選ばせる。`sample_subset(pool, n_per_axis=1 or 2, seed)` で切り替わる。

### 3.4 axis_pos は絶対に見せない

選択肢の軸座標を被験者が見ると、C（gold）が「正解を狙った回答」になり測定が壊れる。表示は ID・質問文・選択肢ラベルのみ。

---

## 4. ファイル

| ファイル | 役割 |
|---|---|
| `PTT_prompt.txt` | **貼り付ける本体**（単一の正。GPTのInstructionsにも流用可） |
| `PTT_SETUP.md` | 本ファイル。実施方法と設計メモ |
| `ptt_scorer.py` | 採点エンジン（被験者が添付、またはKnowledgeに同梱） |
| `README.md` | 運用手順の入口 |
| `../GDL_eval_pool.json` | 質問プール1000問 |
| `../ptt_guide.html` | 被験者向けガイド（**配布するのはこれ1つ**） |

---

## 5. ローカル検証

```bash
# 出題サブセット作成（--n は 1=40問 / 2=80問）
python eval/ptt/ptt_scorer.py sample --pool eval/GDL_eval_pool.json --n 1 --seed 1234 --out subset.json --show

# A/B/C（各 {"answers":{"P0001":"A",...}} 形式）を用意して採点
python eval/ptt/ptt_scorer.py score --subset subset.json --a A.json --b B.json --c C.json \
       --subject mayo --model gpt --date 2026-08-17 --out-json result.json --out-md report.md
```

---

## 6. 既知の限界（v1）

- 1回実施（A/B/C各1回）。揺らぎ低減には複数回平均が有効。
- 天井を1.0で近似（本来は人間のtest-retest自己一致）。Fidelityはやや低めに出る安全側。
- 軸B（人間かAIか＝ブレードランナー型）は未対応。v2で自由記述＋判定を追加予定。
- 選択式のみ。実際の文体・語りの癖は測っていない（「文体傾向」カテゴリは自己申告の選好）。
- 実行環境によって床(A)が変わるため、**異なるAIサービス・異なる時期の結果を直接比較しない**こと。
