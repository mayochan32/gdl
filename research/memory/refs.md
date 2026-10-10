# GDL 記憶設計 — 参考文献リスト

> [README.md](README.md)（論点マップ）の検討に使う先行研究のリスト。分類は論点マップの論点（MEM-01〜07）に対応させてある。
> ★ = 要旨を実際に取得して内容を確認済み。無印 = 検索結果のタイトル・arXiv ID を記載（未読）。
>
> - 作成: 2026-09-21
> - 最終更新: 2026-10-10

---

## 1. まず全体像を掴むためのサーベイ

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 1-1 ★ | A Survey of Agent Memory in the Second Half: Towards Self-Evolving and Long-Horizon Agents | [2602.06052](https://arxiv.org/abs/2602.06052) | 記憶を「基盤（パラメトリック/外部）×認知機構（感覚・作業・エピソード・意味・手続き）×主体（ユーザー向け/エージェント向け）」の3軸で整理。GDLの記憶セクションをどの軸に置くかの座標系として使える。**主体の軸が特に重要** — GDLはユーザー向け記憶に属する |
| 1-2 ★ | From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms | [2605.06716](https://arxiv.org/abs/2605.06716) | 記憶機構の発展を Storage → Reflection → Experience の3段階で捉える進化フレーム。現在のGDL `episodes` は最初期のStorage段階に留まっている、と位置づけられる |
| 1-3 | From Human Memory to AI Memory: A Survey on Memory Mechanisms in the Era of LLMs | [2504.15965](https://arxiv.org/abs/2504.15965) | 人間の記憶研究とAIの記憶実装を対応づけたサーベイ。GDLが人間の記憶概念を借りるときの用語統一に使える |
| 1-4 | A Survey on the Memory Mechanism of Large Language Model based Agents | [2404.13501](https://arxiv.org/abs/2404.13501) | この分野の初期サーベイ。定番の引用先 |
| 1-5 | Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers | [2603.07670](https://arxiv.org/abs/2603.07670) | 機構・評価・今後の論点を一続きで扱う。評価の節がMEM-06の下敷きになりそう |

---

## 2. アーキテクチャの定番（GDLの「外部化」判断を相対化する）

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 2-1 | Generative Agents: Interactive Simulacra of Human Behavior | [2304.03442](https://arxiv.org/abs/2304.03442) | memory stream + retrieval（recency/importance/relevance の重み付け）+ reflection。**「重要度」で想起を重み付けする発想は、想起バイアスの最も単純な原型**。ここを本人固有にできないか |
| 2-2 | MemGPT: Towards LLMs as Operating Systems | [2310.08560](https://arxiv.org/abs/2310.08560) | 記憶を仮想メモリ的に階層管理。GDLが「記憶ミドルウェアの設定ファイル」になる構図（MEM-05）の実装イメージ |
| 2-3 | A-MEM: Agentic Memory for LLM Agents | [2502.12110](https://arxiv.org/abs/2502.12110) | Zettelkasten風に記憶同士をエージェント自身がリンクさせ、記憶構造が自己組織化する。固定スキーマで記憶を書くGDLとは逆方向の設計で、**対比すると論点が立つ** |
| 2-4 | Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory | [2504.19413](https://arxiv.org/abs/2504.19413) | 実運用寄り。抽出・更新・削除のパイプライン設計が具体的 |

---

## 3. エピソード記憶

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 3-1 | Position: Episodic Memory is the Missing Piece for Long-Term LLM Agents | [2502.06975](https://arxiv.org/abs/2502.06975) | エピソード記憶が欠けていることを正面から主張するポジションペーパー。GDLの `episodes` 未設計問題とまったく同じ問題意識 |
| 3-2 | Human-like Episodic Memory for Infinite Context LLMs (EM-LLM) | [2407.09450](https://arxiv.org/abs/2407.09450) | サプライズ量でトークン列をイベント境界に分割し、エピソードとして扱う。**「何を1つの出来事として切り出すか」の自動化**。定型エピソード抽出（MEM-04）に直結 |
| 3-3 | AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents | [2407.04363](https://arxiv.org/abs/2407.04363) | エピソード記憶と意味記憶をグラフで統合。GDLの人格記述（意味記憶的）とepisodes（エピソード的）の接続に参考 |
| 3-4 | Episodic Memories Generation and Evaluation Benchmark for LLMs | [2501.13121](https://arxiv.org/abs/2501.13121) | エピソード記憶を測るベンチマーク。MEM-06の評価設計に |
| 3-5 | E-mem: Multi-Agent Based Episodic Context Reconstruction for LLM Agent Memory | [2601.21714](https://arxiv.org/abs/2601.21714) | 想起時にエピソードの文脈を再構成する。**人間の想起が「再生」ではなく「再構成」であることの実装** — 想起バイアスの核心に近い |

---

## 4. 忘却・固定化（MEM-05「忘却の設計」用）

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 4-1 ★ | FSFM: A Biologically-Inspired Framework for Selective Forgetting of Agent Memory | [2604.20300](https://arxiv.org/abs/2604.20300) | 海馬的インデックス、エビングハウス忘却曲線、シナプス刈り込み、**記憶の再固定化（retrieval時にmemoryがlabileになり書き換わる）**の4機構を実装。336万件の実インタラクションで検証。GDLの「忘却の設計」に最も近い先行研究 |
| 4-2 | FadeMem: Biologically-Inspired Forgetting for Efficient Agent Memory | [2601.18642](https://arxiv.org/abs/2601.18642) | 忘却を効率化手段として扱う。減衰パラメータを本人ごとに変える余地がある |
| 4-3 | Learning to Forget: Sleep-Inspired Memory Consolidation for Resolving Proactive Interference in LLMs | [2603.14517](https://arxiv.org/abs/2603.14517) | 睡眠中の記憶固定化に着想。古い記憶が新しい記憶を妨害する順向干渉の解決 |
| 4-4 | SCM: Sleep-Consolidated Memory with Algorithmic Forgetting for LLMs | [2604.20943](https://arxiv.org/abs/2604.20943) | 同上、アルゴリズム的忘却の実装 |
| 4-5 | Selective Forgetting: A Graph-Based Memory Framework for Long-Term LLM Agents | [2608.28978](https://arxiv.org/abs/2608.28978) | グラフ構造上での選択的忘却 |
| 4-6 | Human-Like Remembering and Forgetting in LLM Agents: An ACT-R-Inspired Memory Architecture | [ACM HAI 2025](https://dl.acm.org/doi/10.1145/3765766.3765803) | 認知アーキテクチャACT-Rの活性化式を記憶に適用。**ACT-Rは活性化のパラメータが個人差として解釈できる**ので、想起バイアスを数値で持つGDLの表現方法として有望 |

---

## 5. 人格・パーソナライズと記憶（MEM-04「定型エピソード」用）

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 5-1 ★ | MemoryForge: Synthesize Lifelong Memory for Human-Like LLM Agents | [2608.00007](https://arxiv.org/abs/2608.00007) | **最重要**。静的なペルソナ記述を捨て、目標とする人格から逆算して生涯の自伝的記憶を合成し、それを検索させることで人格を発現させる（memory-based conditioning）。多解像度（生涯要約／一般的出来事／エピソード）の階層は、GDLの定型エピソード設計にほぼそのまま使える（MEM-04 の結論として採用済み）。**精読の結果、当初「GDLへの対抗仮説」と評したのは誤りと判明**（批判対象は薄いペルソナカード群であり、GDLは比較対象に入っていない）。ただし「全文静的注入」という提示方式への批判は成立する（→ MEM-05）。精読メモ → [MemoryForge論文の解釈](studies/2026-10-08_memoryforge_MemoryForge論文の解釈/) |
| 5-2 | PersonaAgent: Bridging Memory and Action for Personalized LLM Agents | [2506.06254](https://arxiv.org/abs/2506.06254) | 記憶と行動を人格で橋渡しする |
| 5-3 | Enabling Personalized Long-term Interactions in LLM-based Agents through Persistent Memory and User Profiles | [2510.07925](https://arxiv.org/abs/2510.07925) | **永続記憶とユーザープロファイルの併用** — GDL（プロファイル）+ RAG（記憶）という構成そのもの。先行実装として必読 |
| 5-4 | PersonaVLM: Long-Term Personalized Multimodal LLMs | [2604.13074](https://arxiv.org/abs/2604.13074) | マルチモーダルへの拡張。写真メタデータを `episodes.sources` に含めているGDLの将来方向 |

---

## 6. 想起バイアス・人間らしさの再現（MEM-03用）

| # | 論文 | arXiv / DOI | なぜGDLに効くか |
|---|---|---|---|
| 6-1 ★ | Simulating Human Memory with Language Models（Wang, Tomlin, Hu, Dillon, Linzen — NYU/UMass） | [2605.25680](https://arxiv.org/abs/2605.25680) | 心理学由来の10タスクでLLMが人間の記憶限界を模倣できるか検証。**結論はネガティブ** — フロンティアLLMは人間より記憶が良く、プロンプトでは人間的な忘却を誘導できない。4スロット作業記憶を持つcompactorで量的劣化は再現できるが、**誤りの「種類」は人間と違う**。GDLが想起バイアスを記述しても、それがLLM上で再現される保証はない、という重要な警告 |
| 6-2 ★ | What might we learn about autobiographical narrative processing from Artificial Intelligence?（Mansfield, Bauer, Booker, Grysman, Singer, Fivush — Humanities and Social Sciences Communications, 2026-02-04） | [s41599-025-06426-y](https://www.nature.com/articles/s41599-025-06426-y) | **決定的に重要**。人はAI生成の自伝的ナラティブを見分けられ、不自然だと感じる。ChatGPTは元の話にそれが無くても「贖罪型（redemptive）」の成長・解決の枠を押しつける傾向がある。訓練データが文化的に優勢な米国型ナラティブ鋳型に偏っているため。→ **GDLに定型エピソードを入れても、LLMが語り直す段階でこの鋳型に汚染される。**「語り口の鋳型」もGDLが明示的に指定しないと個性が消える |
| 6-3 | Integrating Dynamic Human-like Memory Recall and Forgetting | [2404.00573](https://arxiv.org/abs/2404.00573) | 人間的な想起と忘却の動的統合 |
| 6-4 | Conversational AI Powered by LLMs Amplifies False Memories in Witness Interviews | [2408.04681](https://arxiv.org/abs/2408.04681) | 対話AIが人間側に偽記憶を植えつける方向の研究。**没後継承ユースケースの倫理リスク**として押さえておく価値がある |

---

## 7. 評価（MEM-06「GDL_evalへの影響」用）

| # | 論文 | arXiv | なぜGDLに効くか |
|---|---|---|---|
| 7-1 ★ | LoCoMo-Plus: Beyond-Factual Cognitive Memory Evaluation Framework for LLM Agents | [2602.10715](https://arxiv.org/abs/2602.10715) | **GDL_eval再設計の直接の下敷き**。Level-1（事実想起）と Level-2（認知的記憶）を分離し、後者を causal / state-based / goal-oriented / value-based の4型で測る。さらに **文字列一致メトリクスが「記憶の忠実度」と「生成スタイル」を混同して評価を歪めることを指摘** — GDL_evalの4層分解（Content/Reasoning/Style/Values）が抱える交絡と同じ問題 |
| 7-2 | LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory | [2410.10813](https://arxiv.org/abs/2410.10813) | 長期対話記憶の標準ベンチマーク |
| 7-3 | Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo) | [2402.17753](https://arxiv.org/abs/2402.17753) | 上記の原典側 |
| 7-4 | EverMemBench: Benchmarking Long-Term Interactive Memory in LLMs | [2602.01313](https://arxiv.org/abs/2602.01313) | 比較的新しいベンチマーク |
| 7-5 | How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior | [2505.16067](https://arxiv.org/abs/2505.16067) | 記憶管理の違いが振る舞いに与える影響を実証。記憶あり忠実度の交絡要因の洗い出しに |

---

## 8. 論文リストのメタ情報源

- [Agent-Memory-Paper-List (Shichun-Liu)](https://github.com/Shichun-Liu/Agent-Memory-Paper-List) — サーベイ「Memory in the Age of AI Agents」の付属論文リスト。継続的に更新される
- [Awesome-Personalized-LLMs](https://github.com/VanillaCreamer/Awesome-Personalized-LLMs) — パーソナライズLLMの論文集

---

## GDLの論点への当てはめ（暫定メモ）

- **MEM-02（外部化の維持）** → 1-1 の「主体の軸」で整理すると、GDLは*ユーザー向け記憶*、RAGは*経験の蓄積*。分界が理論的に裏づけられる
- **MEM-03（想起バイアス）** → 2-1 の重み付けを本人固有化するのが最短路。ただし 6-1 が「LLM側が言うことを聞かない」可能性を示している。**先に小さく検証すべき**
- **MEM-04（定型エピソード）** → 5-1 MemoryForge の三層解像度（L/G/E）を採用済み。立場の違い（実在か合成か）は精読で整理がついた。加えて 6-2 の贖罪型ナラティブ汚染対策として `narrative_style` を必須項目とすることを決定
- **MEM-05（忘却の設計）** → 4-1 FSFM の4機構がほぼそのまま設計テンプレートになる。4-6 ACT-R は個人差をパラメータで表す方法として有望
- **MEM-06（評価）** → 7-1 LoCoMo-Plus の Level-1/Level-2 分離を、そのまま「記憶なし忠実度／記憶あり忠実度」に対応させられる可能性が高い

---

## 変更履歴

| 日付 | 変更内容 |
|---|---|
| 2026-09-21 | 初版作成（30件） |
| 2026-10-10 | リポジトリ整理に伴い `research/memory/refs.md` に移設（旧 GDL_memory_refs.md）。分類の当てはめを論点ID（MEM-01〜07）に対応させ、精読済みの論文から studies/ の検討へリンクを追加 |
| 2026-10-10 | 5-1 MemoryForge の注記を訂正（「GDLへの対抗仮説」評価は誤りだった）。MEM-04 の当てはめを決定済みの内容に更新。根拠 → [MemoryForge論文の解釈](studies/2026-10-08_memoryforge_MemoryForge論文の解釈/) §3 |
