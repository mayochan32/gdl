# GDL スキーマ拡張設計 — personality のファセット粒度化（Big Five 30ファセット）

## 背景（なぜ拡張するか）

性格診断法による評価で、松永サンプルGDLのズレが **再現性をもって** E（外向性）と A（協調性）に局在することが判明した。
本人像は「1対1では親しみやすい（E1高）が大人数は苦手（E2低）」「頼まれると断れない（compliance高）が利他（A3）・主張（E3）は強くない・自己評価は低くない（modesty低）」。

ところが現行 Lv1 は **1ドメイン＝1スカラー**（extraversion_level=4 等）。微調整実験で決定的なことが分かった:

| 設定 | Fidelity |
|---|---|
| extraversion を 4→2 一律補正 | 0.272 |
| extraversion を 2→3 一律 | **0.194（悪化）** |
| E1=3・E2=1・E3=2（実像の凹凸） | 0.282 |

ドメインの数値を本人に合わせても（E domain 0.50≈本人0.47）Fidelityはむしろ下がる。
**忠実度を運んでいるのはドメインのスカラーではなくファセットの形（凹凸）**であり、それは単一スカラーでは原理的に表現できない。→ ファセット粒度のスキーマが必要。

## 設計

`personality` に Big Five 5ドメイン × 6ファセット = **30ファセット（IPIP-NEO-PI-R 準拠）** の層を追加する。

### レベル設計（既存の detail_level 思想を踏襲）

- **Lv1**: 既存のドメイン5スカラー。**後方互換のため残す**（粗いユースケース・既存資産用）。
- **Lv2**: 30ファセットに `value`(1–5)。本命。
- **Lv3**: 30ファセット `value` + `confidence` + `note`（凹凸の根拠を自由記述）。

### 値の規約

- `value` は **high-pole 基準の 1–5**（5＝高極が強く該当、1＝低極）。各ファセットに `low_pole`/`high_pole` の説明を併記して方向を一意化。
- `label` は該当時の意味（value から自動 or 手書き）。

### 構造（抜粋）

```json
"big_five_facets": {
  "E_extraversion": {
    "_domain": "E 外向性 (extraversion)",
    "facets": {
      "E1_friendliness":   { "ipip_code":"E1", "name_ja":"親しみやすさ", "value":4, "label":"誰とでもすぐ打ち解ける" },
      "E2_gregariousness": { "ipip_code":"E2", "name_ja":"集団志向",   "value":1, "label":"少人数・一人を好む" },
      "E3_assertiveness":  { "ipip_code":"E3", "name_ja":"主張性",     "value":2, "label":"控えめで主導しない" }
      // E4..E6
    }
  }
  // N / O / A / C も同形
}
```

### 評価系との直接結合（この設計の最大の利点）

各 facet の `ipip_code`（E1, A5 …）は `bigfive_items.json` の domain+facet と **1:1 対応**する。
つまり **GDLが宣言したファセット値と、性格診断法が実測したファセットを直接照合できる**。
これまで「GDL-AIに受験させて間接的に測る」しかなかったのが、**GDLの記述そのものを答え合わせ**できるようになる（記述の予測妥当性を facet 単位で検証）。

## 効果（実測）

mayoの確認済み定性知識から30ファセット値を起こし（120回答の転記ではない）、GDL-AIを再受験:

| GDL形式 | Fidelity | facet相関 |
|---|---|---|
| 初期（誤ったLv1スカラー） | 0.159 | 0.601 |
| Lv1スカラー補正（ext/assert 4→2） | 0.276 | 0.727 |
| **Lv2 ファセット粒度（本設計）** | **0.344** | **0.830** |

ドメイン差は全5領域で ≤0.09 に収束。残ズレは E1・A1・C6・N2・N4 など**単一ファセットに分散**（＝もはや構造的欠陥ではなくチューニング領域）。

## 移行方針

1. `GDL_schema.json`（マスター）に `personality.Lv2.big_five_facets` を追加し、`build_schemas.js` で lv2/lv3 に展開。
2. Lv1 は温存（後方互換）。Lv1↔Lv2 の整合は「ドメイン値 ≈ 6ファセット平均」で検算可能。
3. GDL入力フォーム（GDL_input.html）に30ファセットの任意入力を追加（未入力はLv1から推定で補完）。
4. 評価ハーネスに「GDL宣言ファセット vs 実測ファセット」の直接照合モードを追加。

## 成果物

- `GDL_personality_facets_schema.json` — 30ファセット定義テンプレート（ipip_code・name_ja・low/high_pole・担当item番号・空のvalue）。
- `GDL_matsunaga_facet.json` — 松永への適用例（personality.Lv2, v2.0）。
