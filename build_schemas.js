#!/usr/bin/env node
/**
 * GDL Schema Builder
 *
 * マスタースキーマ（GDL_schema.json）から、
 * Lv1 / Lv2 / Lv3 の3つのレベル別ファイルを自動生成する。
 *
 * 使い方:
 *   node build_schemas.js
 *
 * 出力:
 *   - GDL_schema_lv1.json  ... 各セクションの Lv1 キーのみ
 *   - GDL_schema_lv2.json  ... Lv1 + Lv2 キー
 *   - GDL_schema_lv3.json  ... Lv1 + Lv2 + Lv3 キー（マスターと同等）
 */

const fs = require('fs');
const path = require('path');

const MASTER_FILE = 'GDL_schema.json';

// ── セクション分類 ──────────────────────────────
// ネスト型: 各セクション内に Lv1/Lv2/Lv3 キーがある
const LEVELED_SECTIONS = [
  'identity', 'appearance', 'background', 'philosophy',
  'personality', 'knowledge', 'preferences', 'expression', 'relationships'
];

// フラット型: Lv1/Lv2/Lv3 ネストを持たない。最低出現レベルを指定
const FLAT_SECTIONS = {
  meta: 1,                      // 常に含める
  personality_assessments: 1,   // 個性の核なので Lv1 から
  episodes: 1                   // 個性の核なので Lv1 から
};

// ── ビルド本体 ──────────────────────────────────
function buildLevel(master, targetLevel) {
  const { _levels, _labels, gdl } = master;
  const result = { _levels, _labels, gdl: {} };

  // フラット型セクション
  for (const [section, minLevel] of Object.entries(FLAT_SECTIONS)) {
    if (gdl[section] && targetLevel >= minLevel) {
      result.gdl[section] = gdl[section];
    }
  }

  // ネスト型セクション: Lv1〜targetLevel のキーのみ含める
  for (const section of LEVELED_SECTIONS) {
    if (!gdl[section]) continue;
    const content = {};
    for (let lv = 1; lv <= targetLevel; lv++) {
      const key = `Lv${lv}`;
      if (gdl[section][key] !== undefined) {
        content[key] = gdl[section][key];
      }
    }
    result.gdl[section] = content;
  }

  // meta.detail_level を対象レベルに設定
  if (result.gdl.meta) {
    result.gdl.meta = { ...result.gdl.meta, detail_level: targetLevel };
  }

  return result;
}

// ── 実行 ────────────────────────────────────────
const masterPath = path.join(__dirname, MASTER_FILE);
const master = JSON.parse(fs.readFileSync(masterPath, 'utf8'));

for (const lv of [1, 2, 3]) {
  const data = buildLevel(master, lv);
  const outFile = `GDL_schema_lv${lv}.json`;
  const outPath = path.join(__dirname, outFile);
  fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  const size = (fs.statSync(outPath).size / 1024).toFixed(1);
  console.log(`✓ ${outFile}  (${size} KB)`);
}

console.log('\nDone. 3 schema files generated from master.');
