# GDL ペルソナ チューリングテスト — GPT 構築手順（v1.1 / 軸A）

> 旧ファイル名 `PTT_GPTs_prompt.md`。中身がプロンプト本体から構築手順書に変わったため 2026-08-17 に改名。

> **このファイルは Instructions に貼らない。**
> Instructions に貼るのは **`PTT_GPT_instructions.txt` の全文**（先頭から末尾まで、加工不要）。
> 本ファイルはGPTを作る側のための設定チェックリストと設計メモ。

---

## 1. GPT Builder での設定

| 項目 | 設定値 |
|---|---|
| **Name** | GDL Persona Turing Test |
| **Description** | 下記「1.1 説明欄に貼るテキスト」を参照（準備物・流れ・添付タイミングを含む） |
| **Instructions** | `PTT_GPT_instructions.txt` の**全文をそのまま貼る**（約6,300文字。上限8,000文字に収まる） |
| **Conversation starters** | `開始` / `再開`（2つだけ。余計な導線を作らない） |
| **Knowledge** | `GDL_eval_pool.json`（リポジトリ直下）<br>`ptt_scorer.py`（gpts/配下） |
| **Capabilities** | ✅ Code Interpreter & Data Analysis（**必須**）<br>❌ Web Search（不要）<br>❌ Canvas（不要）<br>❌ 画像生成（不要） |
| **Actions** | なし |
| **公開範囲** | リンクを知っている人のみ（被験者にURLを配布する運用） |

### 1.1 説明欄に貼るテキスト

説明欄は、被験者がまだ何も入力していない段階で目に入る唯一の場所。**「GDLを事前に用意する必要があること」と「最初は添付しないこと」の両方**をここで伝える。片方だけだと、手ぶらで来られるか、逆に開始前に添付されて汚染する。

```
GDLを読み込んだAIが、どれだけ「あなた」を再現できるかを定量測定します。
【準備】あなたのGDL（JSONファイル）を手元に用意してください。無い場合は先に「GDL Generator」で作成を。
【流れ】①「開始」と送る→②出題数を選ぶ（40問/80問）→③AIが先に回答→④求められたらGDLを添付→⑤あなたが1問ずつ回答→⑥結果レポート
⚠️GDLは④まで添付しないでください。先に添付すると測定が成立しません。
```

説明欄は表示スペースが限られ長文は省略されるため、収まらない場合は短縮版を使う（160文字）。

```
GDLを読み込んだAIが、どれだけ「あなた」を再現できるかを測定します。
【準備】GDLのJSONファイルを手元に（無ければ先にGDL Generatorで作成）。
【流れ】「開始」→出題数を選択→AIが先に回答→求められたらGDLを添付→あなたが1問ずつ回答→レポート
⚠️GDLは求められるまで添付しないでください。
```

なお **Instructions の Step 0 でも同じ内容を再度・より詳しく提示する**設計にしてある。説明欄を読み飛ばされても、最初の応答で全体像・準備物・添付タイミングが伝わる。GDLを持っていない被験者にはそこで作成を案内し、セッションを終了する。

### 設定時の注意

- **Code Interpreter が OFF だと動かない。** サンプリングも採点も Python 実行が前提。
- Knowledge にアップした2ファイルは、Code Interpreter 有効時に `/mnt/data/` 配下から読める。パスが違う環境もあるため、Instructions 側で探索するよう指示済み。
- Web Search を ON にすると、モデルが余計な検索をして進行が乱れる。OFF 推奨。
- 作成後、**公開URLを `ptt_guide.html` の `PTT_GPT_URL_HERE`（3箇所）に反映**すること。

---

## 2. 動作の骨格

- **A（床）** GDL無しの素のAI ／ **B** GDL有りのAI ／ **C（gold）** 人間本人
- 指標: `GDL Fidelity Score = (sim(B,C) − sim(A,C)) / (1 − sim(A,C))`
- 測定対象は **軸A（同一性）** のみ。軸B（人間かAIか）は未対応。
- 出題数は被験者が選択: **短縮版40問**（各軸1問） / **標準版80問**（各軸2問）

```
Step 0  モード選択（GDLはまだ添付させない）
Step 1  sample_subset で層化抽出（Code Interpreter 必須）
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

ChatGPTは**添付した瞬間にファイル内容をコンテキストへ展開する**。「添付するが開かない」では床(A)が汚れる。したがって **Aの生成が終わるまでGDLを会話に持ち込ませない**（後から添付させる）のが唯一の解。A→B→C の順序も厳守（Cを先に見るとBがカンニングになる）。

Aは事前固定せず、**実施のたびにその場の現行モデルで取り直す**。モデルが更新されると床も動くため、古いAを使い回すと比較が壊れる。

### 3.2 中断復帰（v1.1で追加）

Code Interpreter のセッションは長時間の対話中にリセットされ、変数が失われることがある。80問の一問一答は数十分かかるため、**A確定・B確定・C収集10問ごとに `ptt_state.json` を書き出す**。落ちたら被験者がこれを再添付して続きから再開できる。

`ptt_state.json` には**質問IDのみ**を保存し、質問本体と `axis_pos` は保存しない。被験者がファイルを開いても正解の配点が漏れないようにするため。採点時はIDでプールから引き直す。

### 3.3 出題数の選択（v1.1で追加）

各軸2問（80問）は測定が安定するが、被験者の負担が大きく途中離脱と惰性回答のリスクがある。各軸1問（40問）でも40軸すべてをカバーできるため、被験者に選ばせる。`sample_subset(pool, n_per_axis=1 or 2, seed)` で切り替わる。

### 3.4 axis_pos は絶対に見せない

選択肢の軸座標を被験者が見ると、C（gold）が「正解を狙った回答」になり測定が壊れる。表示は ID・質問文・選択肢ラベルのみ。

---

## 4. ファイル

| ファイル | 役割 |
|---|---|
| `PTT_GPT_instructions.txt` | **Instructions に貼る本体**（単一の正） |
| `PTT_GPT_SETUP.md` | 本ファイル。構築手順と設計メモ |
| `ptt_scorer.py` | 採点エンジン（Knowledgeに同梱、Code Interpreterで実行） |
| `README.md` | 運用手順（被験者フローの概要） |
| `../GDL_eval_pool.json` | 質問プール1000問（Knowledgeに同梱） |
| `../ptt_guide.html` | 被験者向けガイド（配布用） |

---

## 5. ローカル検証

```bash
# 出題サブセット作成（40問版）
python gpts/ptt_scorer.py sample --pool GDL_eval_pool.json --n 1 --seed 1234 --out subset.json --show

# A/B/C（各 {"answers":{"P0001":"A",...}} 形式）を用意して採点
python gpts/ptt_scorer.py score --subset subset.json --a A.json --b B.json --c C.json \
       --subject mayo --model gpt --date 2026-08-17 --out-json result.json --out-md report.md
```

---

## 6. 既知の限界（v1）

- 1回実施（A/B/C各1回）。揺らぎ低減には複数回平均が有効。
- 天井を1.0で近似（本来は人間のtest-retest自己一致）。Fidelityはやや低めに出る安全側。
- 軸B（人間かAIか＝ブレードランナー型）は未対応。v2で自由記述＋判定を追加予定。
- 選択式のみ。実際の文体・語りの癖は測っていない（「文体傾向」カテゴリは自己申告の選好）。
