# /research — Phase 1: リサーチフェーズを実行

`draft.md` を読み込み、FOOTBALL LABのデータで仮説を検証して `research_cache/` に保存します。

## 実行手順

以下の手順で実行してください:

1. `.claude/agents/research-agent.md` を Read ツールで読む
2. そのファイルの内容を prompt として、**Agent ツール（subagent_type: "general-purpose"）** を起動する
   - エージェントはメインの会話とは独立したコンテキストで動作する
   - 大量のWeb検索結果がこの会話を汚染しない
3. エージェントが完了したら、生成された `research_cache/` ファイルのパスをユーザーに報告する

## 完了後のメッセージ

エージェント完了後、以下を表示してください:

```
📋 リサーチ完了
ファイル: research_cache/{YYYYMMDD}_{相手チーム名}_research.md

次のステップ:
  - research_cache のファイルを確認する
  - 問題なければ /write を実行
  - 修正が必要なら直接ファイルを編集 → /write を実行
  - 調査の方向性を変えたい場合はチャットで指示 → /research を再実行
```
