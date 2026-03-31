---
name: football-lab
description: FOOTBALL LAB のマッチレポートURL規則・チームコード一覧・CBP指標の説明・検索クエリ設計パターン。research-agent がデータ取得を行う際に参照する。
user-invocable: false
---

# スキル: FOOTBALL LAB データ取得

## マッチレポート URL 規則

```
https://www.football-lab.jp/{チームコード}/report?year=YYYY&month=MM&date=DD
```

**例**: 2026年3月21日の大分 vs FC琉球
```
https://www.football-lab.jp/oita/report?year=2026&month=03&date=21
```

---

## J2 チームコード一覧

| チーム | コード |
|--------|--------|
| 大分トリニータ | oita |
| FC琉球 | ryuk |
| ロアッソ熊本 | kuma |
| ギラヴァンツ北九州 | kiky |
| レノファ山口 | r-ya |
| 愛媛FC | ehim |
| 鹿児島ユナイテッド | kufc |
| テゲバジャーロ宮崎 | myzk |

※ 上記以外のチームは WebSearch で `{チーム名} football-lab チームコード` を検索して確認する

---

## CBP 指標の説明

CBP（チャンスビルディングポイント）とは、FOOTBALL LABが独自算出する「チャンス構築への貢献度」を示す指標。

| 指標名 | 意味 |
|--------|------|
| 攻撃CBP | 攻撃でチャンスを作った量・質 |
| 守備CBP | 守備で相手のチャンスを潰した量・質 |
| 奪取CBP | ボール奪取でチャンスに繋げた量・質 |
| パスCBP | パスでチャンスを作った量・質 |
| シュートCBP | シュートでチャンスに繋げた量・質 |
| ゴールCBP | ゴールへの直接貢献度 |

---

## 検索クエリ設計パターン

### 試合単体
- `大分トリニータ football-lab マッチレポート {YYYY}年{MM}月{DD}日`
- `大分トリニータ {相手チーム名} {YYYY}/{MM}/{DD} スタッツ`
- `site:football-lab.jp oita report {YYYY}`

### シーズン推移・平均
- `大分トリニータ CBP {YYYY} シーズン平均`
- `大分トリニータ football-lab {YYYY} チームスタイル`

### リーグ比較・ランキング
- `J2 守備CBP ランキング {YYYY}`
- `J2 攻撃CBP 上位 {YYYY}`
- `J2 {指標名} ランキング {YYYY} football-lab`

### 個人データ
- `{選手名} football-lab CBP {YYYY}`
- `大分トリニータ 個人CBP ランキング {YYYY}`
- `{選手名} football-lab {YYYY} マッチレポート`

---

## データ取得の注意事項

1. **支持データと反証データの両方を探す** — 都合のいいデータだけ集めない
2. **今節値と今季平均を両方取得** — 今節値だけでは文脈がわからない
3. **データが見つからない場合は「データなし」と明記** — 推測で補わない
4. **FOOTBALL LABのデータは必ずURLを出典として記載**
5. **他試合（別節）のデータを混入させない**
6. **WebFetch でマッチレポートURLを直接取得することを優先** — Search より正確
