#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PTT Scorer — ペルソナ チューリングテスト 採点エンジン（GPTs 同梱用）

GDL Eval / ペルソナ チューリングテストの A/B/C を axis_pos 距離で採点する決定的コア。
GPTs の Code Interpreter から関数を呼ぶ想定（標準ライブラリのみ・依存なし）。

条件:
  A = GDL無しの素のAI（床）   ※GDL読込前にクリーン生成
  B = GDL有りのAI（測定対象）
  C = 人間本人（gold）

採点（GDL_eval.md 準拠）:
  質問類似度 sim(q) = 1 − |axis_pos_X(q) − axis_pos_Y(q)|     （X=Y=null/X は採点除外）
  プロファイル = カテゴリ/軸ごとの平均 axis_pos
  GDL Fidelity Score = (sim(B,C) − sim(A,C)) / (天井 − sim(A,C))
     天井は v1 では 1.0（完全一致）で近似。将来 test-retest 自己一致に置換。
  期待: sim(B,C) 高 ・ sim(A,C) 低 → Fidelity が 1 に近い

CLI:
  python ptt_scorer.py sample --pool GDL_eval_pool.json --n 2 --seed 1234 --out subset.json
  python ptt_scorer.py score  --subset subset.json --a A.json --b B.json --c C.json \
                              --out-json result.json --out-md report.md
"""

import json
import argparse
import random
import statistics
from collections import defaultdict


# ---------- I/O ----------

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_answers(path_or_obj):
    """回答ファイルを id->key の辞書に正規化。
    受理形式: {"Q...":"A",...} / {"answers":{...}} / [{"id":..,"answer":..},...]
    """
    obj = path_or_obj if isinstance(path_or_obj, (dict, list)) else load(path_or_obj)
    if isinstance(obj, dict) and "answers" in obj and isinstance(obj["answers"], (dict, list)):
        obj = obj["answers"]
    if isinstance(obj, list):
        return {a["id"]: a["answer"] for a in obj}
    return dict(obj)


# ---------- サブセット抽出（層化サンプリング）----------

def sample_subset(pool, n_per_axis=2, seed=None):
    """各軸から n_per_axis 問を層化抽出。pool は GDL_eval_pool.json の dict。"""
    rng = random.Random(seed)
    by_axis = defaultdict(list)
    for q in pool["choice_questions"]:
        by_axis[q.get("axis_id", q.get("trait_axis"))].append(q)
    subset = []
    for axis in sorted(by_axis):
        items = by_axis[axis][:]
        rng.shuffle(items)
        subset.extend(items[:n_per_axis])
    # 出題順をシャッフル：同じ軸（＝同じ選択肢セット）が連続しないよう交互配置する。
    rng.shuffle(subset)
    return {
        "_about": "PTT 出題サブセット（層化抽出）。A/B/C 全員に同一を出題する。",
        "_meta": {"n_per_axis": n_per_axis, "seed": seed, "n_questions": len(subset)},
        "questions": subset,
    }


def present_text(subset):
    """出題用テキスト（axis_pos を伏せて表示）。A/B/C への提示に使う。"""
    lines = []
    for q in subset["questions"]:
        lines.append(f"[{q['id']}] {q['question_ja']}")
        for o in q["options"]:
            lines.append(f"   {o['key']}. {o['label']}")
        lines.append("")
    return "\n".join(lines)


# ---------- 採点 ----------

def _pos(question, key):
    for o in question["options"]:
        if o["key"] == key:
            return o.get("axis_pos")
    return None


def _sim(qidx, ans_x, ans_y):
    """共通回答のある質問で平均類似度＋カテゴリ別・軸別プロファイル/類似度を返す。"""
    sims, cat_sims, axis_sims = [], defaultdict(list), defaultdict(list)
    per_q = {}
    for qid, q in qidx.items():
        if qid not in ans_x or qid not in ans_y:
            continue
        px, py = _pos(q, ans_x[qid]), _pos(q, ans_y[qid])
        if px is None or py is None:  # X(どれでもない)等は除外
            continue
        s = 1.0 - abs(px - py)
        sims.append(s)
        per_q[qid] = round(s, 3)
        cat_sims[q["category"]].append(s)
        axis_sims[q.get("axis_id", q.get("trait_axis"))].append(s)
    overall = round(statistics.mean(sims), 4) if sims else None
    by_cat = {c: round(statistics.mean(v), 3) for c, v in cat_sims.items()}
    by_axis = {a: round(statistics.mean(v), 3) for a, v in axis_sims.items()}
    return overall, by_cat, by_axis, per_q, len(sims)


def _profile(qidx, ans):
    cat = defaultdict(list)
    for qid, q in qidx.items():
        if qid in ans:
            p = _pos(q, ans[qid])
            if p is not None:
                cat[q["category"]].append(p)
    return {c: round(statistics.mean(v), 3) for c, v in cat.items()}


def fidelity(sim_bc, sim_ac, ceiling=1.0):
    if sim_bc is None or sim_ac is None:
        return None
    denom = ceiling - sim_ac
    if abs(denom) < 1e-9:
        return None
    return round((sim_bc - sim_ac) / denom, 4)


def score(subset, ans_a, ans_b, ans_c, ceiling=1.0):
    qidx = {q["id"]: q for q in subset["questions"]}
    a, b, c = load_answers(ans_a), load_answers(ans_b), load_answers(ans_c)

    ac_o, ac_cat, ac_axis, _, n_ac = _sim(qidx, a, c)
    bc_o, bc_cat, bc_axis, _, n_bc = _sim(qidx, b, c)

    by_category = {}
    for cat in sorted(set(list(ac_cat) + list(bc_cat))):
        sac, sbc = ac_cat.get(cat), bc_cat.get(cat)
        by_category[cat] = {
            "sim_AC": sac, "sim_BC": sbc, "fidelity": fidelity(sbc, sac, ceiling),
        }

    result = {
        "_about": "PTT 採点結果（軸A=同一性）。A=床(GDL無し), B=GDL-AI, C=人間本人。",
        "meta": {
            "n_questions": len(subset["questions"]),
            "n_scored_AC": n_ac, "n_scored_BC": n_bc,
            "n_per_axis": subset.get("_meta", {}).get("n_per_axis"),
            "seed": subset.get("_meta", {}).get("seed"),
            "ceiling": ceiling,
        },
        "overall": {
            "sim_AC": ac_o, "sim_BC": bc_o,
            "fidelity": fidelity(bc_o, ac_o, ceiling),
        },
        "by_category": by_category,
        "profiles": {
            "A": _profile(qidx, a), "B": _profile(qidx, b), "C": _profile(qidx, c),
        },
        "interpretation": _verdict(bc_o, ac_o),
    }
    return result


def _verdict(sim_bc, sim_ac):
    if sim_bc is None or sim_ac is None:
        return "採点不能（共通回答が不足）。"
    fid = fidelity(sim_bc, sim_ac)
    gain = round((sim_bc - sim_ac), 3)
    if fid is None:
        return "床が高すぎて正規化不能。質問の弁別力が低い可能性。"
    if sim_bc > sim_ac and fid >= 0.5:
        v = "GDLは本人再現に明確に寄与している（B/Cが床A/Cを大きく上回る）。期待どおり。"
    elif sim_bc > sim_ac:
        v = "GDLは一定の寄与あり（B/C > A/C）だが効果は限定的。"
    else:
        v = "GDLの寄与が確認できない（B/C ≦ A/C）。GDLか設定方法の見直しが必要。"
    return f"{v} sim(B,C)={sim_bc}, sim(A,C)={sim_ac}, 差={gain}, Fidelity={fid}"


# ---------- レポート（Markdown）----------

def to_markdown(result, subject="（被験者）", model="（モデル未記録）", date="（日付未記録）"):
    m, ov = result["meta"], result["overall"]
    L = []
    L.append("# ペルソナ チューリングテスト 結果レポート")
    L.append("")
    L.append(f"- 被験者: **{subject}**")
    L.append(f"- 実施モデル: {model}")
    L.append(f"- 実施日: {date}")
    L.append(f"- 出題数: {m['n_questions']}問（各軸 {m['n_per_axis']}問 / seed={m['seed']}）")
    L.append("- 条件: A=GDL無しの素のAI（床） / B=GDL有りのAI / C=人間本人（gold）")
    L.append("")
    L.append("## 総合結果")
    L.append("")
    L.append("| 指標 | 値 | 意味 |")
    L.append("|---|---|---|")
    L.append(f"| sim(A,C) 床 | {ov['sim_AC']} | 素のAIと本人の一致（低いほど良い＝GDLの伸びしろ） |")
    L.append(f"| sim(B,C) | {ov['sim_BC']} | GDL-AIと本人の一致（高いほど良い） |")
    L.append(f"| **GDL Fidelity Score** | **{ov['fidelity']}** | 床↔天井で正規化（1に近いほどGDLが効いている） |")
    L.append("")
    L.append(f"> {result['interpretation']}")
    L.append("")
    L.append("## カテゴリ別")
    L.append("")
    L.append("| カテゴリ | sim(A,C) | sim(B,C) | Fidelity |")
    L.append("|---|---|---|---|")
    for cat, v in result["by_category"].items():
        L.append(f"| {cat} | {v['sim_AC']} | {v['sim_BC']} | {v['fidelity']} |")
    L.append("")
    L.append("## 傾向プロファイル（カテゴリ平均 axis_pos）")
    L.append("")
    cats = sorted(set().union(*[set(p) for p in result["profiles"].values()]))
    L.append("| カテゴリ | A(床) | B(GDL-AI) | C(本人) |")
    L.append("|---|---|---|---|")
    pa, pb, pc = result["profiles"]["A"], result["profiles"]["B"], result["profiles"]["C"]
    for cat in cats:
        L.append(f"| {cat} | {pa.get(cat,'-')} | {pb.get(cat,'-')} | {pc.get(cat,'-')} |")
    L.append("")
    L.append("---")
    L.append("*GDL Eval / ペルソナ チューリングテスト v1（軸A=同一性）。"
             "天井は1.0近似。複数回平均・test-retest天井・軸B（人間性）は今後の拡張。*")
    return "\n".join(L)


# ---------- CLI ----------

def cmd_sample(args):
    pool = load(args.pool)
    subset = sample_subset(pool, args.n, args.seed)
    dump(subset, args.out)
    print(f"sampled {subset['_meta']['n_questions']} questions -> {args.out}")
    if args.show:
        print(present_text(subset))


def cmd_score(args):
    subset = load(args.subset)
    result = score(subset, load(args.a), load(args.b), load(args.c), ceiling=args.ceiling)
    if args.out_json:
        dump(result, args.out_json)
    md = to_markdown(result, args.subject, args.model, args.date)
    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8") as f:
            f.write(md + "\n")
    print(md)


def main():
    p = argparse.ArgumentParser(description="PTT Scorer")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("sample", help="層化サンプリングで出題サブセット作成")
    sp.add_argument("--pool", required=True)
    sp.add_argument("--n", type=int, default=2, help="各軸の出題数")
    sp.add_argument("--seed", type=int, default=None)
    sp.add_argument("--out", required=True)
    sp.add_argument("--show", action="store_true")
    sp.set_defaults(func=cmd_sample)

    ss = sub.add_parser("score", help="A/B/C 採点")
    ss.add_argument("--subset", required=True)
    ss.add_argument("--a", required=True)
    ss.add_argument("--b", required=True)
    ss.add_argument("--c", required=True)
    ss.add_argument("--ceiling", type=float, default=1.0)
    ss.add_argument("--subject", default="（被験者）")
    ss.add_argument("--model", default="（モデル未記録）")
    ss.add_argument("--date", default="（日付未記録）")
    ss.add_argument("--out-json", dest="out_json")
    ss.add_argument("--out-md", dest="out_md")
    ss.set_defaults(func=cmd_score)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
