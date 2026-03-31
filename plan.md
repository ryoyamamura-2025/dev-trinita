# 大分トリニータ戦評ブログ生成システム — 実装方針

_作成日: 2026-03-31_

---

## プロジェクト概要

`draft.md`（試合後のなぐり書きメモ）を入力として、FOOTBALL LAB等のデータで感想を検証・補強し、1500〜2000字のブログ記事（Markdown）を生成するClaude Codeエージェントシステム。

---

## 設計方針

### 基本原則

- **個人利用**：チーム共有・Plugin化は不要
- **確実性重視**：フェーズ間でユーザーが必ず確認する（全自動実行はしない）
- **フェーズ独立**：各フェーズはコマンドを手動で叩いて起動する
- **コンテキスト分離**：各フェーズはSubagentとして独立実行し、大量のWeb検索結果がメインコンテキストを汚染しない

### draft.mdの役割

試合後のなぐり書きメモ専用。フィードバックの場所としては使わない。

---

## ファイル構成

```
/
├── CLAUDE.md                            ← プロジェクト概要・ファイル規約のみ（軽量）
├── draft.md                             ← 試合後のなぐり書きメモ（毎回上書き）
├── articles/
│   └── YYYYMMDD_相手チーム名.md         ← 最終記事（note に貼り付ける）
├── research_cache/
│   └── YYYYMMDD_相手チーム名_research.md ← Phase 1 の中間出力
│
└── .claude/
    ├── commands/
    │   ├── research.md                  ← /research で Phase 1 を起動
    │   ├── write.md                     ← /write   で Phase 2 を起動
    │   └── edit.md                      ← /edit    で Phase 3 を起動
    ├── agents/
    │   ├── research-agent.md            ← Phase 1 専用 Subagent
    │   ├── writer-agent.md              ← Phase 2 専用 Subagent
    │   └── editor-agent.md              ← Phase 3 専用 Subagent
    └── skills/
        ├── hypothesis-extraction/
        │   └── SKILL.md                 ← 感情表現→仮説変換ルール
        ├── football-lab/
        │   └── SKILL.md                 ← URL規則・チームコード・検索クエリ設計
        └── article-template/
            └── SKILL.md                 ← 記事構成・トーン・禁止事項
```

---

## コンポーネント設計

### Skills（専門知識の教科書）

複数のAgentが共有する再利用可能な知識。関連タスクで自動ロードされる。

| Skill | 内容 | 使用するAgent |
|---|---|---|
| `hypothesis-extraction` | 感情表現→仮説変換ルール、除外ルール（期待・願望はスキップ等） | research-agent |
| `football-lab` | チームコード一覧、マッチレポートURL生成規則、検索クエリ設計パターン | research-agent |
| `article-template` | 記事構成テンプレート、トーンルール、文字数、禁止事項 | writer-agent, editor-agent |

### Subagents（独立した担当者）

それぞれ独立した文脈で動作し、結果はファイル経由で受け渡す。

| Agent | skills | tools | 入力 | 出力 |
|---|---|---|---|---|
| `research-agent` | hypothesis-extraction, football-lab | WebSearch, Read, Write | draft.md | research_cache/YYYYMMDD_xxx_research.md |
| `writer-agent` | article-template | Read, Write | draft.md + research_cache | articles/YYYYMMDD_xxx.md（下書き） |
| `editor-agent` | article-template | Read, Write | articles/ の下書き | 最終保存 + 完了レポート |

### Commands（フェーズの起動トリガー）

| コマンド | やること | やらないこと |
|---|---|---|
| `/research` | 仮説抽出・データ収集・research_cache保存 | 記事を書かない |
| `/write` | research_cache + draft.md から記事下書き生成 | ファクトチェックしない・新規調査しない |
| `/edit` | チェックリスト検証・修正・最終保存・完了レポート表示 | 新しい調査をしない |

---

## ワークフロー

```
試合後
  → draft.md を書く

/research を実行
  → research-agent が起動
  → research_cache/YYYYMMDD_xxx_research.md を生成して終了

★ ユーザーが research_cache を確認
  パターンA: 問題なし
    → /write へ
  パターンB: 数値誤記・データ補完など小さな修正
    → research_cache を直接編集 → /write へ
  パターンC: 方向性の修正（調査の深さ・観点が違う等）
    → チャットで指示を出す（例：「後半の守備データが薄い。奪取CBPも探して」）
    → /research を再実行

/write を実行
  → writer-agent が起動（draft.md + research_cache を読み込む）
  → articles/YYYYMMDD_xxx.md（下書き）を生成して終了

★ ユーザーが下書きを確認
  パターンA: 問題なし
    → /edit へ
  パターンB: 表現・構成など小さな修正
    → 下書きを直接編集 → /edit へ
  パターンC: 方向性の修正（データ羅列になっている・感想との対比が薄い等）
    → チャットで指示を出す（例：「データ羅列になってる。感想との対比をもっと出して」）
    → /write を再実行

/edit を実行
  → editor-agent が起動
  → チェックリスト検証 → 修正 → 最終保存 → 完了レポート表示
```

---

## フィードバックの設計思想

| パターン | どんなとき | 操作 |
|---|---|---|
| そのまま次へ | 問題なし | 次のコマンドを実行 |
| 直接編集して次へ | 小さな修正（数値誤記・表現調整等） | ファイルを手動編集 → 次のコマンドを実行 |
| AIに再指示して再実行 | 方向性の修正が必要なとき | チャットで指示 → 同じコマンドを再実行 |

チャット指示はClaude Codeが文脈を保持するため、専用のフィードバックファイルや引数の仕組みは不要。

---

## 実装順序（推奨）

1. **Skills**（hypothesis-extraction → football-lab → article-template）
   - AgentとCommandの記述の土台になるため先に作る
2. **Agents**（research-agent → writer-agent → editor-agent）
   - Skillを参照しながら各フェーズの指示を記述する
3. **Commands**（research → write → edit）
   - 対応するAgentを起動するシンプルな記述
4. **CLAUDE.md**（最後に軽量版を書き直す）