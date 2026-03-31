# 大分トリニータ戦評ブログ生成システム

`draft.md`（試合後のなぐり書き）を入力として、FOOTBALL LABのデータで検証・補強した1500〜2000字のブログ記事を自動生成する Claude Code エージェントシステム。

---

## ファイル構成

```
draft.md                                     ← 試合後のなぐり書きメモ（毎回上書き）
articles/YYYYMMDD_相手チーム名.md            ← 最終記事（note に貼り付ける）
research_cache/YYYYMMDD_xxx_research.md      ← Phase 1 の中間出力

.claude/
├── commands/research.md                     ← /research で Phase 1 を起動
├── commands/write.md                        ← /write   で Phase 2 を起動
├── commands/edit.md                         ← /edit    で Phase 3 を起動
├── agents/research-agent.md                 ← Phase 1 専用 Subagent
├── agents/writer-agent.md                   ← Phase 2 専用 Subagent
├── agents/editor-agent.md                   ← Phase 3 専用 Subagent
└── skills/
    ├── hypothesis-extraction/SKILL.md       ← 感情表現→仮説変換ルール
    ├── football-lab/SKILL.md                ← URL規則・チームコード・検索クエリ
    └── article-template/SKILL.md           ← 記事構成・トーン・禁止事項
```

---

## ワークフロー

```
① draft.md を書く（試合後のなぐり書き）

② /research を実行
   → research_cache/YYYYMMDD_{相手}_research.md が生成される

   ★ research_cache を確認する

③ /write を実行
   → articles/YYYYMMDD_{相手}.md（下書き）が生成される

   ★ 下書きを確認する

④ /edit を実行
   → チェックリスト検証 → 修正 → 最終保存 → 完了レポート表示
```

---

## フィードバックパターン

| 状況 | 操作 |
|---|---|
| 問題なし | そのまま次のコマンドへ |
| 小さな修正（数値誤記・表現調整） | ファイルを直接編集 → 次のコマンドへ |
| 方向性の修正（調査の深さ・観点が違う等） | チャットで指示 → 同じコマンドを再実行 |

チャット指示はClaude Codeが文脈を保持するため、追加の仕組みは不要。

---

## 制約

- データが見つからない場合は「データなし」と明記し、推測で補わない
- FOOTBALL LABのデータは必ずURLを出典として記載する
- draft.md に書いていない試合（別節）のデータを混入させない
- 記事の主語は常に「大分トリニータ」視点
