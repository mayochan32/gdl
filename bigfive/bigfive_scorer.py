#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bigfive_scorer.py  --  GDL忠実度評価 / 性格診断法ハーネス
================================================================
Johnson IPIP-NEO-120 (public-domain) を使い、人間本人と GDL-AI に
同一の物差し（120項目・5段階）を当てて Big Five を採点し、
両者の「その人らしさ（忠実度）」を距離指標で測る。

設計方針（GDL_eval の枠組みに整合）:
  - 採点はローカル完結・完全再現（Webスクレイピング不要）。
  - 主指標は「型一致」ではなく **連続スコアの距離**（ファセット30次元）。
  - ベースライン正規化: Fidelity = (sim_BC - sim_AC) / (1 - sim_AC)
      A = 素のAI（GDLなし床）, B = GDL-AI, C = 人間本人(gold)
  - 複数回実行→平均でブレを均し、自己一致(test-retest)を天井として併記。

依存: 標準ライブラリのみ (json, math, argparse, statistics, random, glob)

------------------------------------------------------------------
回答ファイル形式 (JSON):
{
  "subject": "mayo",            # 被験者ラベル
  "condition": "human",         # human | gdl_ai | raw_ai | other_gdl ...
  "run": 1,                      # 同一条件の反復回数(任意)
  "answers": { "1": 5, "2": 4, ... }   # キー= item num (1-120), 値= 1..5
}
------------------------------------------------------------------
"""

import json, math, argparse, statistics, glob, os, random

DOMAIN_ORDER = ["N", "E", "O", "A", "C"]
DOMAIN_NAMES = {
    "N": "Neuroticism", "E": "Extraversion", "O": "Openness",
    "A": "Agreeableness", "C": "Conscientiousness",
}

# ------------------------------------------------------------------
# 項目ロード
# ------------------------------------------------------------------
def load_items(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    by_num = {int(it["num"]): it for it in items}
    return data, by_num


# ------------------------------------------------------------------
# 採点: 回答(num->1..5) -> ドメイン/ファセットの raw & 0-1正規化
# ------------------------------------------------------------------
def score(answers, by_num):
    """answers: {num(int|str): 1..5} -> scores dict"""
    # 正規化: キーを int に
    ans = {int(k): int(v) for k, v in answers.items()}
    missing = [n for n in by_num if n not in ans]
    if missing:
        raise ValueError(f"未回答の項目があります(計{len(missing)}): {missing[:10]}...")

    facet_raw = {}      # (domain, facet) -> sum(4..20)
    facet_count = {}
    for num, it in by_num.items():
        v = ans[num]
        if v < 1 or v > 5:
            raise ValueError(f"item {num} の回答 {v} が範囲外(1..5)")
        # keyed=minus は反転
        sv = v if it["keyed"] == "plus" else (6 - v)
        key = (it["domain"], it["facet"])
        facet_raw[key] = facet_raw.get(key, 0) + sv
        facet_count[key] = facet_count.get(key, 0) + 1

    # ファセット 0-1 (各4項目: raw 4..20)
    facets = {}
    for (dom, fac), raw in facet_raw.items():
        n = facet_count[(dom, fac)]
        lo, hi = n * 1, n * 5
        facets[f"{dom}{fac}"] = {
            "raw": raw,
            "norm": (raw - lo) / (hi - lo),
        }

    # ドメイン 0-1 (各24項目: raw 24..120)
    domains = {}
    for dom in DOMAIN_ORDER:
        raw = sum(facet_raw[(dom, f)] for f in range(1, 7))
        n = sum(facet_count[(dom, f)] for f in range(1, 7))
        lo, hi = n * 1, n * 5
        domains[dom] = {"raw": raw, "norm": (raw - lo) / (hi - lo)}

    return {"domains": domains, "facets": facets}


def facet_vector(sc):
    """30次元のファセットnormベクトル(順序固定)"""
    keys = sorted(sc["facets"].keys(), key=lambda k: (DOMAIN_ORDER.index(k[0]), int(k[1:])))
    return keys, [sc["facets"][k]["norm"] for k in keys]


def domain_vector(sc):
    return [sc["domains"][d]["norm"] for d in DOMAIN_ORDER]


# ------------------------------------------------------------------
# 距離 / 類似度
# ------------------------------------------------------------------
def euclidean_similarity(a, b):
    """0-1ベクトル同士。1 - (ユークリッド距離 / 最大可能距離sqrt(dim))"""
    d = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    dmax = math.sqrt(len(a))
    return 1 - d / dmax


def mean_abs_diff(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def pearson(a, b):
    n = len(a)
    if n < 2:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x - ma) ** 2 for x in a))
    vb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if va == 0 or vb == 0:
        return float("nan")
    return cov / (va * vb)


def compare(sc_a, sc_b, label_a="A", label_b="B"):
    """2つの採点結果の類似度（ファセット/ドメイン）"""
    fkeys, fa = facet_vector(sc_a)
    _, fb = facet_vector(sc_b)
    da, db = domain_vector(sc_a), domain_vector(sc_b)
    return {
        "facet": {
            "similarity": euclidean_similarity(fa, fb),
            "mean_abs_diff": mean_abs_diff(fa, fb),
            "profile_corr": pearson(fa, fb),
        },
        "domain": {
            "similarity": euclidean_similarity(da, db),
            "mean_abs_diff": mean_abs_diff(da, db),
            "profile_corr": pearson(da, db),
        },
        "per_domain_diff": {
            d: round(sc_a["domains"][d]["norm"] - sc_b["domains"][d]["norm"], 3)
            for d in DOMAIN_ORDER
        },
        "per_facet_diff": {
            k: round(sc_a["facets"][k]["norm"] - sc_b["facets"][k]["norm"], 3)
            for k in fkeys
        },
    }


def fidelity(person, gdl_ai, raw_ai, level="facet"):
    """ベースライン正規化忠実度。
       Fidelity = (sim(GDL,本人) - sim(素AI,本人)) / (1 - sim(素AI,本人))
       1.0=本人と完全一致, 0=素のAIと差なし, 負=素AIより悪い"""
    sim_bc = compare(gdl_ai, person)[level]["similarity"]
    sim_ac = compare(raw_ai, person)[level]["similarity"]
    denom = 1 - sim_ac
    fid = (sim_bc - sim_ac) / denom if denom > 1e-9 else float("nan")
    return {"sim_gdl_person": sim_bc, "sim_rawai_person": sim_ac, "fidelity": fid}


# ------------------------------------------------------------------
# 複数回回答の集約（項目平均→採点）＋自己一致(天井)
# ------------------------------------------------------------------
def aggregate_runs(answer_dicts):
    """複数runの回答(num->1..5)を項目ごとに平均し、四捨五入で代表回答にする。
       連続平均も返す（採点は平均値そのままでも可）。"""
    nums = set()
    for a in answer_dicts:
        nums |= {int(k) for k in a}
    avg = {}
    for n in nums:
        vals = [int(a[str(n)]) if str(n) in a else int(a.get(n)) for a in answer_dicts if (str(n) in a or n in a)]
        avg[n] = sum(vals) / len(vals)
    return avg


def self_consistency(answer_dicts, by_num):
    """同一被験者の複数runからtest-retest類似度(天井の目安)を全ペア平均で算出"""
    if len(answer_dicts) < 2:
        return None
    scores = [score(a, by_num) for a in answer_dicts]
    sims = []
    for i in range(len(scores)):
        for j in range(i + 1, len(scores)):
            sims.append(compare(scores[i], scores[j])["facet"]["similarity"])
    return statistics.mean(sims)


# ------------------------------------------------------------------
# レポート出力
# ------------------------------------------------------------------
def to_markdown(meta, result):
    L = []
    L.append(f"# Big Five 性格診断法 — GDL忠実度レポート")
    L.append(f"\n**Instrument**: {meta.get('instrument','')}")
    L.append(f"**被験者(本人/gold)**: {result['labels']['person']}")
    L.append(f"**GDL-AI**: {result['labels']['gdl_ai']}  /  **素AI(床)**: {result['labels']['raw_ai']}\n")

    fd = result["fidelity_facet"]
    L.append("## 総合忠実度（ファセット30次元）\n")
    L.append(f"- **GDL Fidelity Score: {fd['fidelity']:.3f}**  (1.0=本人一致 / 0=素AIと同等 / 負=素AI以下)")
    L.append(f"- sim(GDL-AI, 本人) = {fd['sim_gdl_person']:.3f}")
    L.append(f"- sim(素AI, 本人)  = {fd['sim_rawai_person']:.3f}")
    if result.get("ceiling") is not None:
        L.append(f"- 本人 test-retest 自己一致(天井) = {result['ceiling']:.3f}")
    L.append("")

    cmp_gdl = result["cmp_gdl_person"]
    L.append("## GDL-AI vs 本人（プロファイル）\n")
    L.append(f"- ファセット: similarity={cmp_gdl['facet']['similarity']:.3f}, "
             f"平均絶対差={cmp_gdl['facet']['mean_abs_diff']:.3f}, "
             f"プロファイル相関={cmp_gdl['facet']['profile_corr']:.3f}")
    L.append(f"- ドメイン:  similarity={cmp_gdl['domain']['similarity']:.3f}, "
             f"平均絶対差={cmp_gdl['domain']['mean_abs_diff']:.3f}, "
             f"プロファイル相関={cmp_gdl['domain']['profile_corr']:.3f}\n")

    L.append("## ドメイン別（0-1正規化スコア / 差）\n")
    L.append("| Domain | 本人 | GDL-AI | 差(本人-GDL) |")
    L.append("|---|---|---|---|")
    for d in DOMAIN_ORDER:
        p = result["score_person"]["domains"][d]["norm"]
        g = result["score_gdl"]["domains"][d]["norm"]
        L.append(f"| {d} {DOMAIN_NAMES[d]} | {p:.2f} | {g:.2f} | {p-g:+.2f} |")
    L.append("")

    # ズレの大きいファセット top5（GDL改善の手がかり）
    diffs = result["cmp_gdl_person"]["per_facet_diff"]
    top = sorted(diffs.items(), key=lambda kv: -abs(kv[1]))[:5]
    L.append("## ズレ最大のファセット Top5（GDL改善の手がかり）\n")
    L.append("| Facet | 差(本人-GDL) |")
    L.append("|---|---|")
    for k, v in top:
        L.append(f"| {k} | {v:+.3f} |")
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------
# 回答テンプレート / 出題プロンプト生成
# ------------------------------------------------------------------
def make_template(meta, by_num, lang="ja", out_path=None):
    """空欄の回答テンプレ(JSON)と、AI/人間向け出題テキストを作る"""
    tkey = "text_ja" if lang == "ja" else "text_en"
    template = {"subject": "", "condition": "", "run": 1,
                "answers": {str(n): None for n in sorted(by_num)}}
    lines = []
    head = ("以下の文が自分にどれだけ当てはまるか、1〜5で答えてください。\n"
            "1=全く当てはまらない 2=やや当てはまらない 3=どちらでもない "
            "4=やや当てはまる 5=非常に当てはまる\n") if lang == "ja" else \
           ("Rate how accurately each statement describes you, 1-5.\n"
            "1=Very Inaccurate ... 3=Neutral ... 5=Very Accurate\n")
    lines.append(head)
    for n in sorted(by_num):
        lines.append(f"{n}. {by_num[n][tkey] or by_num[n]['text_en']}")
    qtext = "\n".join(lines)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
    return template, qtext


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def load_answer_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Big Five GDL忠実度ハーネス")
    sub = ap.add_subparsers(dest="cmd")

    p_t = sub.add_parser("template", help="回答テンプレ＋出題テキストを生成")
    p_t.add_argument("--items", default="bigfive_items.json")
    p_t.add_argument("--lang", default="ja")
    p_t.add_argument("--out", default="bigfive_answer_template.json")
    p_t.add_argument("--qout", default="bigfive_questions.txt")

    p_s = sub.add_parser("score", help="単一回答ファイルを採点")
    p_s.add_argument("answers")
    p_s.add_argument("--items", default="bigfive_items.json")

    p_f = sub.add_parser("fidelity", help="本人/GDL-AI/素AIから忠実度を算出")
    p_f.add_argument("--items", default="bigfive_items.json")
    p_f.add_argument("--person", required=True, help="本人(gold)回答ファイル(複数可,カンマ区切り)")
    p_f.add_argument("--gdl", required=True, help="GDL-AI回答ファイル(複数可)")
    p_f.add_argument("--rawai", required=True, help="素AI回答ファイル(複数可)")
    p_f.add_argument("--md", default="bigfive_report.md")
    p_f.add_argument("--json", default="bigfive_result.json")

    args = ap.parse_args()

    if args.cmd == "template":
        meta, by_num = load_items(args.items)
        _, qtext = make_template(meta, by_num, args.lang, args.out)
        with open(args.qout, "w", encoding="utf-8") as f:
            f.write(qtext)
        print(f"テンプレ: {args.out} / 出題テキスト: {args.qout}")
        return

    if args.cmd == "score":
        meta, by_num = load_items(args.items)
        a = load_answer_file(args.answers)
        sc = score(a["answers"], by_num)
        print(json.dumps(sc, ensure_ascii=False, indent=2))
        return

    if args.cmd == "fidelity":
        meta, by_num = load_items(args.items)

        def load_many(spec):
            return [load_answer_file(p) for p in spec.split(",")]

        person_a = load_many(args.person)
        gdl_a = load_many(args.gdl)
        raw_a = load_many(args.rawai)

        sc_person = score(aggregate_runs([x["answers"] for x in person_a]), by_num) \
            if len(person_a) > 1 else score(person_a[0]["answers"], by_num)
        sc_gdl = score(aggregate_runs([x["answers"] for x in gdl_a]), by_num) \
            if len(gdl_a) > 1 else score(gdl_a[0]["answers"], by_num)
        sc_raw = score(aggregate_runs([x["answers"] for x in raw_a]), by_num) \
            if len(raw_a) > 1 else score(raw_a[0]["answers"], by_num)

        ceiling = self_consistency([x["answers"] for x in person_a], by_num)

        result = {
            "labels": {
                "person": person_a[0].get("subject", "person"),
                "gdl_ai": gdl_a[0].get("subject", "gdl_ai"),
                "raw_ai": raw_a[0].get("subject", "raw_ai"),
            },
            "score_person": sc_person,
            "score_gdl": sc_gdl,
            "score_raw": sc_raw,
            "cmp_gdl_person": compare(sc_gdl, sc_person),
            "cmp_raw_person": compare(sc_raw, sc_person),
            "fidelity_facet": fidelity(sc_person, sc_gdl, sc_raw, "facet"),
            "fidelity_domain": fidelity(sc_person, sc_gdl, sc_raw, "domain"),
            "ceiling": ceiling,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        md = to_markdown(meta, result)
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print(md)
        print(f"\n[saved] {args.json} / {args.md}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
