#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDL Eval Harness — ペルソナ忠実度評価ハーネス

GDL_eval_questions.json（質問バンク）と GDL_eval_key_<subject>.json（回答）を使い、
本人とGDL-AIの「その人らしさ」をtrait_axis座標の距離で定量評価する。

依存: 標準ライブラリのみ（json, argparse, random, statistics, re, math）

サブコマンド:
  profile  ある回答keyの傾向プロファイル（カテゴリ別・軸別の平均axis_pos）を表示
  score    本人key vs AI key を採点（質問別類似度・プロファイル距離・全体スコア）
           --baseline で素のAI等を渡すと床↔天井正規化した GDL Fidelity Score も算出
  sample   層化ランダムサンプリングで出題サブセットを抽出（各カテゴリから固定数）
  style    open回答の簡易文体計量（文字数・平均文長・語彙多様度など）を本人vsAIで比較

採点式（GDL_eval.md §scoring）:
  選択肢類似度 = 1 − |axis_pos(本人) − axis_pos(AI)|
  「どれでもない(X)」は距離採点から除外し件数のみログ。
  集計はカテゴリ別/軸別平均と全体平均。プロファイル距離 = 1 − 平均|Δ(カテゴリ平均)|。
正規化:
  GDL Fidelity Score = (AIスコア − 床) / (天井 − 床)   （0=素のAI相当, 1=本人自己一致相当）
"""

import json
import argparse
import random
import re
import statistics
from collections import defaultdict


# ---------- I/O ----------

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_question_index(bank):
    """id -> question dict（choice）。axis_pos/カテゴリ/軸ラベルを引けるように。"""
    idx = {}
    for q in bank.get("choice_questions", []):
        idx[q["id"]] = q
    return idx


def opt_pos(question, key):
    """質問の選択肢keyからaxis_posを返す。X/不明はNone。"""
    for o in question["options"]:
        if o["key"] == key:
            return o.get("axis_pos")
    return None


def key_choice_map(key):
    """answer key の choice_answers を id->選択key の辞書に。"""
    return {a["id"]: a["answer"] for a in key.get("choice_answers", [])}


# ---------- プロファイル ----------

def build_profile(bank, key):
    """回答keyから傾向プロファイルを作る。
    返り値: {
      'by_category': {cat: mean_pos},
      'by_axis': {axis_label: mean_pos},
      'overall': float,
      'per_question': {id: pos},
      'none_count': int, 'answered': int
    }
    """
    qidx = build_question_index(bank)
    ans = key_choice_map(key)
    cat_pos = defaultdict(list)
    axis_pos = defaultdict(list)
    per_q = {}
    none_count = 0
    answered = 0
    for qid, a in ans.items():
        q = qidx.get(qid)
        if not q:
            continue
        p = opt_pos(q, a)
        if p is None:  # X どれでもない 等
            none_count += 1
            continue
        answered += 1
        per_q[qid] = p
        cat_pos[q["category"]].append(p)
        axis_pos[q.get("trait_axis", "?")].append(p)
    by_cat = {c: round(statistics.mean(v), 3) for c, v in cat_pos.items()}
    by_axis = {ax: round(statistics.mean(v), 3) for ax, v in axis_pos.items()}
    allv = [p for v in cat_pos.values() for p in v]
    overall = round(statistics.mean(allv), 3) if allv else None
    return {
        "by_category": by_cat,
        "by_axis": by_axis,
        "overall": overall,
        "per_question": per_q,
        "none_count": none_count,
        "answered": answered,
    }


# ---------- 採点 ----------

def score_pair(bank, person_key, ai_key):
    """本人 vs AI の採点。共通して回答のある選択式質問のみ対象。"""
    qidx = build_question_index(bank)
    pa = key_choice_map(person_key)
    aa = key_choice_map(ai_key)
    common = [qid for qid in pa if qid in aa and qid in qidx]
    sims = []
    per_q = {}
    skipped_none = 0
    cat_sims = defaultdict(list)
    for qid in common:
        q = qidx[qid]
        pp = opt_pos(q, pa[qid])
        ap = opt_pos(q, aa[qid])
        if pp is None or ap is None:
            skipped_none += 1
            continue
        sim = 1.0 - abs(pp - ap)
        sims.append(sim)
        per_q[qid] = round(sim, 3)
        cat_sims[q["category"]].append(sim)
    overall = round(statistics.mean(sims), 4) if sims else None
    by_cat = {c: round(statistics.mean(v), 3) for c, v in cat_sims.items()}

    # プロファイル距離（カテゴリ平均ベクトルの距離 → 類似度）
    p_prof = build_profile(bank, person_key)["by_category"]
    a_prof = build_profile(bank, ai_key)["by_category"]
    shared = [c for c in p_prof if c in a_prof]
    if shared:
        diffs = [abs(p_prof[c] - a_prof[c]) for c in shared]
        profile_sim = round(1.0 - statistics.mean(diffs), 4)
    else:
        profile_sim = None

    return {
        "n_scored": len(sims),
        "n_skipped_none": skipped_none,
        "overall_similarity": overall,
        "by_category": by_cat,
        "profile_similarity": profile_sim,
        "per_question": per_q,
    }


def normalize(ai_score, floor_score, ceil_score):
    """床↔天井で正規化。GDL Fidelity Score。"""
    if ceil_score is None or floor_score is None or ai_score is None:
        return None
    denom = ceil_score - floor_score
    if abs(denom) < 1e-9:
        return None
    return round((ai_score - floor_score) / denom, 4)


# ---------- 層化サンプリング ----------

def stratified_sample(bank, per_category, seed=None, include_open=0):
    """各カテゴリから per_category 問を抽出。open_questions から include_open 問を追加。"""
    rng = random.Random(seed)
    by_cat = defaultdict(list)
    for q in bank.get("choice_questions", []):
        by_cat[q["category"]].append(q["id"])
    chosen = []
    for cat, ids in by_cat.items():
        ids = ids[:]
        rng.shuffle(ids)
        chosen.extend(ids[:per_category])
    open_ids = [q["id"] for q in bank.get("open_questions", [])]
    rng.shuffle(open_ids)
    chosen_open = open_ids[:include_open]
    return chosen, chosen_open


def shuffle_options(question, seed=None):
    """選択肢をランタイムでシャッフルし、A-Dを振り直す（Xは末尾固定）。axis_posは保持。"""
    rng = random.Random(seed)
    opts = [dict(o) for o in question["options"]]
    nonx = [o for o in opts if o["key"] != "X"]
    x = [o for o in opts if o["key"] == "X"]
    rng.shuffle(nonx)
    for i, o in enumerate(nonx):
        o["key"] = chr(65 + i)
    return nonx + x


# ---------- 文体計量（open） ----------

def stylometry(text):
    if not text:
        return None
    chars = len(text)
    sentences = [s for s in re.split(r"[。．.!?！？\n]", text) if s.strip()]
    n_sent = max(1, len(sentences))
    avg_sent = round(chars / n_sent, 1)
    tokens = re.findall(r"\w+", text)
    uniq = len(set(tokens))
    ttr = round(uniq / len(tokens), 3) if tokens else 0.0
    # 日本語は空白区切りがないため語TTRは当てにならない。文字bigram多様度を併記。
    compact = re.sub(r"\s+", "", text)
    bigrams = [compact[i:i + 2] for i in range(len(compact) - 1)]
    bigram_ttr = round(len(set(bigrams)) / len(bigrams), 3) if bigrams else 0.0
    return {
        "chars": chars,
        "sentences": len(sentences),
        "avg_sentence_chars": avg_sent,
        "type_token_ratio": ttr,
        "char_bigram_ttr": bigram_ttr,
    }


def style_compare(person_key, ai_key):
    pa = {a["id"]: a["answer"] for a in person_key.get("open_answers", [])}
    aa = {a["id"]: a["answer"] for a in ai_key.get("open_answers", [])}
    rows = {}
    for qid in pa:
        if qid in aa:
            rows[qid] = {"person": stylometry(pa[qid]), "ai": stylometry(aa[qid])}
    return rows


# ---------- 出力 ----------

def cmd_profile(args):
    bank = load_json(args.bank)
    key = load_json(args.key)
    prof = build_profile(bank, key)
    print(f"# プロファイル: {args.key}")
    print(f"  回答数: {prof['answered']}  (どれでもない: {prof['none_count']})")
    print(f"  全体平均 axis_pos: {prof['overall']}")
    print("  カテゴリ別:")
    for c, v in sorted(prof["by_category"].items(), key=lambda x: -x[1]):
        bar = "█" * int(round(v * 20))
        print(f"    {v:.2f} {bar:<20} {c}")


def cmd_score(args):
    bank = load_json(args.bank)
    person = load_json(args.person)
    ai = load_json(args.ai)
    r = score_pair(bank, person, ai)
    print(f"# 採点: 本人={args.person}  AI={args.ai}")
    print(f"  採点質問数: {r['n_scored']}  (X除外: {r['n_skipped_none']})")
    print(f"  質問別平均類似度: {r['overall_similarity']}")
    print(f"  プロファイル類似度: {r['profile_similarity']}")
    print("  カテゴリ別類似度:")
    for c, v in sorted(r["by_category"].items(), key=lambda x: x[1]):
        bar = "█" * int(round(v * 20))
        print(f"    {v:.2f} {bar:<20} {c}")
    if args.baseline:
        base = load_json(args.baseline)
        rb = score_pair(bank, person, base)
        floor = rb["overall_similarity"]
        ceil = 1.0 if args.ceiling is None else args.ceiling
        norm = normalize(r["overall_similarity"], floor, ceil)
        print(f"\n  床(素のAI等)スコア: {floor}   天井: {ceil}")
        print(f"  GDL Fidelity Score (正規化): {norm}")
        print("    0=素のAI相当 / 1=本人自己一致(天井)相当")


def cmd_sample(args):
    bank = load_json(args.bank)
    ids, open_ids = stratified_sample(bank, args.per_category, args.seed, args.open)
    qidx = build_question_index(bank)
    print(f"# 層化サンプリング: 各カテゴリ{args.per_category}問  seed={args.seed}")
    for qid in ids:
        q = qidx[qid]
        opts = shuffle_options(q, seed=args.seed) if args.shuffle else q["options"]
        print(f"\n[{qid}] ({q['category']}) {q['question_ja']}")
        for o in opts:
            print(f"   {o['key']}. {o['label']}")
    if open_ids:
        print("\n# 自由記述:")
        omap = {q["id"]: q for q in bank.get("open_questions", [])}
        for oid in open_ids:
            print(f"[{oid}] {omap[oid]['question_ja']}")


def cmd_style(args):
    person = load_json(args.person)
    ai = load_json(args.ai)
    rows = style_compare(person, ai)
    print(f"# 文体計量: 本人={args.person}  AI={args.ai}")
    for qid, r in rows.items():
        print(f"\n[{qid}]")
        print(f"   person: {r['person']}")
        print(f"   ai    : {r['ai']}")


def main():
    p = argparse.ArgumentParser(description="GDL Eval Harness")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("profile", help="傾向プロファイル表示")
    sp.add_argument("--bank", required=True)
    sp.add_argument("--key", required=True)
    sp.set_defaults(func=cmd_profile)

    ss = sub.add_parser("score", help="本人 vs AI 採点")
    ss.add_argument("--bank", required=True)
    ss.add_argument("--person", required=True)
    ss.add_argument("--ai", required=True)
    ss.add_argument("--baseline", help="床ベースライン（素のAI等）のkey")
    ss.add_argument("--ceiling", type=float, help="天井スコア（本人test-retest）。省略時1.0")
    ss.set_defaults(func=cmd_score)

    sm = sub.add_parser("sample", help="層化サンプリング出題")
    sm.add_argument("--bank", required=True)
    sm.add_argument("--per-category", type=int, default=2, dest="per_category")
    sm.add_argument("--open", type=int, default=0, help="追加するopen問数")
    sm.add_argument("--seed", type=int, default=None)
    sm.add_argument("--shuffle", action="store_true", help="選択肢順をランタイムでシャッフル")
    sm.set_defaults(func=cmd_sample)

    st = sub.add_parser("style", help="open回答の文体計量比較")
    st.add_argument("--person", required=True)
    st.add_argument("--ai", required=True)
    st.set_defaults(func=cmd_style)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
