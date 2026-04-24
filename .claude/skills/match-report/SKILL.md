---
name: match-report
description: 「〇〇戦のマッチレポートを作って」などの指示でトリガー。試合日（YYYYMMDD）と Yahoo game_id（YYYYMMDDXX）を調べ、.claude/skills/match-report/match_report.py を実行して research_cache/ に Markdown レポートを保存する。
user-invocable: true
---

# スキル: マッチレポート生成

## 必要な変数

| 変数 | 形式 | 取得方法 |
|---|---|---|
| `date` | `YYYYMMDD` | ユーザー指定の試合日。不明なら WebFetch: `https://www.football-lab.jp/oita/match?year=YYYY` で確認 |
| `game_id` | `YYYYMMDDXX` | WebSearch: `大分トリニータ {相手名} YYYYMMDD site:soccer.yahoo.co.jp` |

## 実行手順

**Step 1**: `date`（`YYYYMMDD`）を確定する

**Step 2**: Yahoo `game_id` を WebSearch で特定する  
→ 見つからない場合は空文字列（`""`）を使用

**Step 3**: スクリプトを実行する

```bash
# Yahoo あり
uv run python .claude/skills/match-report/match_report.py {date} {game_id} research_cache

# Yahoo なし
uv run python .claude/skills/match-report/match_report.py {date} "" research_cache
```

**Step 4**: 生成されたファイルのパス（`research_cache/oita_{date}_report.md`）を報告する
