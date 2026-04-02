---
trigger: always_on
---

# 大分トリニータ戦評ブログ生成システム



`original_memo.md`（試合後のなぐり書き）を入力として、FOOTBALL LABのデータで検証・補強した1500〜2000字のブログ記事を自動生成するエージェントシステム。

---

## ファイル構成

```
.
├── original_memo.md                            ← 試合後のなぐり書きメモ（毎回上書き）
├── progress.md                                 ← 進捗管理（随時更新）
├── articles/YYYYMMDD_相手チーム名.md            ← 最終記事（note に貼り付ける原稿）
├── research_cache/YYYYMMDD_xxx_research.md     ← Phase 1 の中間出力
└── templates/match_report.md                   ← 記事構成テンプレート
```

---

## 記事執筆ワークフロー

```
① 人が original_memo.md を書く（試合後のなぐり書き）

② Phase1: research を実行
   → research_cache/YYYYMMDD_{相手}_research.md が生成される

   ★ research_cache を確認する

③ Phase2: write を実行
   → articles/YYYYMMDD_{相手}.md（下書き）が生成される

   ★ 下書きを確認する

④ Phase3: edit を実行
   → 執筆ガイドライン検証 → 修正 → 最終保存 → 完了レポート表示
```

---

## 進捗管理
`progress.md`に現在のPhase1と箇条書きで簡潔にやったことを書く。progress.mdは1つの記事執筆終了時にリセットされる。

