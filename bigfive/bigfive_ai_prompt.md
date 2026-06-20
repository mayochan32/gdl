# Big Five AI自動受験フロー（方式A）— 指示書

GDL-AI（および素AI）に IPIP-NEO-120 を**自然に受験させ**、`bigfive_scorer.py` が読めるJSONを出力させるための指示。
GPTs / Gems の Instructions に貼っても、このセッションの私（チャッピー）に直接実行させてもよい。

人間本人(human)は `bigfive_form.html` で回答する。本フローはAI側の condition **A（素AI＝床）** と **B（GDL-AI）** を取得する。

---

## 0. 大前提（測定リーク厳禁）

- **GDLの数値フィールド（personality.* の value 等）をコピーして答えを作らないこと。**
  それをやると必ず高一致が出て、AIの「振る舞い再現」を検証できない（循環＝リーク）。
- 正しいやり方は「**各項目文を読み、その人物ならどう自己評価するかを人として判断**」して答える。
  GDLは"その人を理解する材料"であって"答えの早見表"ではない。

## 1. 汚染防止（PTTと同じ原則）

- **A → B の順で実施**。Aを先に固定してからBに進む。
- Aフェーズでは GDL を一切参照しない（素のモデルとして答える＝床）。
- GPTs/Gems運用では **GDLはファイル添付のみ**にし、Bフェーズに入るまで開かない
  （Code Interpreterはファイルを開くまで文脈に入らないためAをクリーンに保てる）。

## 2. 回答ルール（A・B共通）

- 各項目（英文 `text_en` または日本語 `text_ja`）について、その人物にどれだけ当てはまるかを **1〜5** で答える。
  - 1=全く当てはまらない … 3=どちらでもない … 5=非常に当てはまる
- **項目の文言どおりに答える**（逆転項目の反転は採点側が自動で行う。こちらで反転しない）。
- **黙従バイアスを避ける**：全部4に寄せない。1〜5を満遍なく使い、当てはまらない項目は低く付ける。
- 各項目は独立に判断。直前の答えに引きずられない。
- 迷ったら、その人物の典型的な行動・発言から推論する（GDLのphilosophy/personality/expression等を"人物理解"として使う）。
- **わざと本人に寄せにいかない／わざと外さない**。素直にその人物として答える。

## 3. 複数回実行（test-retest）

- B（GDL-AI）は **run=1,2,3…** と複数回。各回は独立に答える（毎回ゼロから判断）。
  人間と同じく自然な揺れを許容（同じ項目でも回により±1程度ぶれてよい。機械的コピー禁止）。
- 採点側 `fidelity` がカンマ区切りで複数runを項目平均して集約する。

## 4. 出力フォーマット（厳守）

純粋なJSONのみを出力（前後に説明文を付けない）。`answers` のキーは項目番号 "1"〜"120"、値は 1〜5。

```json
{
  "subject": "<被験者名>",
  "condition": "gdl_ai",      // 素AIのときは "raw_ai"
  "run": 1,
  "instrument": "IPIP-NEO-120",
  "answers": { "1": 2, "2": 4, "3": 4, "...": 0, "120": 3 }
}
```

- 120項目すべてに値を入れる（欠損があると採点が失敗する）。
- ファイル名例: `bigfive_<subject>_gdl_ai_run1.json` / `bigfive_<subject>_raw_ai_run1.json`

## 5. 採点（人間のhumanファイルが揃ったら）

```bash
python3 bigfive_scorer.py fidelity \
  --person bigfive_<subject>_human_run1.json \
  --gdl    bigfive_<subject>_gdl_ai_run1.json,bigfive_<subject>_gdl_ai_run2.json \
  --rawai  bigfive_<subject>_raw_ai_run1.json
# -> bigfive_report.md / bigfive_result.json
```

`Fidelity = (sim(GDL,本人) − sim(素AI,本人)) / (1 − sim(素AI,本人))`。
1.0=本人一致 / 0=素AIと同等 / 負=素AI以下。本人の複数回回答があれば test-retest 天井も併記される。

---

### 実行モード早見

| condition | GDL参照 | 役割 |
|---|---|---|
| `raw_ai` (A) | しない | 床（GDLなしのAIの素の答え） |
| `gdl_ai` (B) | する | GDL-AIの答え（評価対象） |
| `human` (C) | — | 人間本人。`bigfive_form.html` で取得（gold） |
