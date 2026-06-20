# 性格診断法 — Big Five (IPIP-NEO-120) による GDL忠実度評価

既存の自作質問バンク（PTT / GDL_eval）に対する **外部・第三者ものさしによる収束的妥当性チェック**。
世の中で確立された性格診断を「人間本人」と「GDL-AI」の両方に当て、同じ性格に出るかで本人らしさを測る。

## なぜ Big Five / IPIP-NEO-120 を選ぶか

- **連続スコア**で測れる（MBTI/16Personalitiesの4文字型は境界付近でフリップし test-retest 信頼性が低い→忠実度指標に不向き）。
- **項目文・採点が public domain**（ipip.ori.org）。Webスクレイピング不要で**ローカル完全再現**できる。
- 5ドメイン × 6ファセット = **30次元**の細かいプロファイルで弁別力が高い。

項目ソース: `@alheimsins/b5-johnson-120-ipip-neo-pi-r`（bigfive-test.com / rubynor・Alheimsins 系の公開実装）。

## ファイル

| ファイル | 内容 |
|---|---|
| `bigfive_items.json` | 120項目（英語＋日本語）／domain・facet・keyed(plus/minus)・5段階選択肢 |
| `bigfive_scorer.py` | 採点＋忠実度ハーネス（標準ライブラリのみ） |
| `bigfive_form.html` | **人間(human)専用GUI回答フォーム**（ブラウザで開きマウスで5択→結果JSONを書き出し） |
| `bigfive_ai_prompt.md` | **AI自動受験フロー（方式A）指示書**（GDL-AI/素AIに自然受験させる） |
| `bigfive_sample_gdl_ai.json` | GDL-AI回答の出力サンプル（方式A実走例） |
| `bigfive_questions.txt` / `_en.txt` | 出題テキスト（AI回答用にそのまま提示） |
| `bigfive_answer_template.json` | 空欄の回答テンプレ（手編集用） |

## 3者の役割と取得方法

| condition | 誰 | 取得方法 |
|---|---|---|
| `human` (C, gold) | 人間本人 | `bigfive_form.html` をブラウザで開き回答 |
| `gdl_ai` (B, 評価対象) | GDL-AI | `bigfive_ai_prompt.md` に従い自然受験（複数run推奨） |
| `raw_ai` (A, 床) | 素AI | 同指示でGDLなしで受験 |

> **測定リーク厳禁**: AIは GDL の数値フィールドをコピーして答えを作らない。各項目文を読み「その人物としてどう自己評価するか」を判断する。詳細は `bigfive_ai_prompt.md`。

## 採点ロジック

各項目を5段階（1=全く当てはまらない 〜 5=非常に当てはまる）で回答。
`keyed=minus` の項目は反転（6−score）。ファセット=4項目和(4–20)、ドメイン=24項目和(24–120)を 0–1 に正規化。

## 忠実度の出し方（ベースライン正規化）

PTT と同じ式に統一:

```
Fidelity = (sim(GDL-AI, 本人) − sim(素AI, 本人)) / (1 − sim(素AI, 本人))
```

- **A=素AI（GDLなし・床）/ B=GDL-AI / C=人間本人（gold）**
- 類似度はファセット30次元の正規化ユークリッド類似度（`1 − 距離/√dim`）。
- 1.0=本人と完全一致、0=素AIと差なし、負=素AI以下。
- 本人に複数回受けさせると **test-retest 自己一致（天井）** を併記。

## 使い方

```bash
# 1) 出題テキストと回答テンプレを生成
python3 bigfive_scorer.py template --lang ja

# 2) 回答を集める（JSON: {"subject","condition","run","answers":{"1":5,...}}）
#    - 人間mayo : bigfive_form.html をブラウザで開きマウスで5択→「結果JSONをダウンロード」
#                （回答は自動保存。途中で閉じても再開可。JA/EN切替あり）
#    - GDL-AI   : 同じ出題(bigfive_questions.txt)をGDLペルソナで回答（複数回推奨）
#    - 素AI     : GDLなしのAIで回答（床）

# 3) 単体採点を確認
python3 bigfive_scorer.py score answers_mayo.json

# 4) 忠実度レポート（複数runはカンマ区切り→項目平均で集約）
python3 bigfive_scorer.py fidelity \
  --person mayo_r1.json,mayo_r2.json \
  --gdl gdl_r1.json,gdl_r2.json \
  --rawai raw_r1.json
# -> bigfive_report.md / bigfive_result.json
```

## AI自動受験の2方式

- **方式A（本命・採用）**: 採点が公開されているので Web を触らず、GDL-AIに120項目を回答させ→このスクリプトでローカル採点。完全再現・堅牢。
- **方式B（補助）**: 16Personalities 等、採点非公開サイトはブラウザ自動操作で実走（DOM変更に弱い）。本ハーネスは方式A用。

## 運用上の注意

- 黙従バイアス対策として逆転項目が効いているか確認（採点側で自動反転済み）。
- GDL-AI回答は**複数回平均**でブレを均す。本人の自己一致を超える一致は出ない（天井）。
- ズレ最大のファセット Top5 を GDL本体の改善手がかりにフィードバックする。

> 位置づけ: これ単独で忠実度を主張しない。性格診断は人格の薄いスライスのみを測るため、
> 既存PTT（思想・価値観・文体）と**併用**してこそ意味がある。
