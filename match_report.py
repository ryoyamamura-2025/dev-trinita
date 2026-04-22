import re
import sys
import requests
import pandas as pd
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup

URL = "https://www.football-lab.jp/oita/report?year=2026&month=04&date=19"
YAHOO_URL = "https://soccer.yahoo.co.jp/jleague/category/j2j3ss/game/2026041911/text?gk=250"
OUTPUT_DIR = Path(".")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def fetch_yahoo_shots(url: str) -> pd.DataFrame:
    """スポーツナビのテキスト速報から時間帯別シュート・xGデータを取得する。"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = []
        for item in soup.find_all('div', class_='sc-textLive__item'):
            status_el = item.find('div', class_='sc-textLive__status')
            text_el   = item.find('p',   class_='sc-textLive__text')
            if not (status_el and text_el):
                continue
            content = text_el.get_text(strip=True)
            if not (content.startswith("ここまでのシュート") or content.startswith("この試合のシュート")):
                continue
            shots = re.findall(r'シュート:(.*?):(\d+)本、(.*?):(\d+)本', content)
            xg    = re.findall(r'ゴール期待値:(.*?):([\d.]+)、(.*?):([\d.]+)', content)
            if shots and xg:
                t1, s1, t2, s2 = shots[0]
                _,  x1, _,  x2 = xg[0]
                t1, t2 = t1.strip(), t2.strip()
                rows.append({
                    "時間":            status_el.get_text(strip=True),
                    f"{t1}_シュート":  int(s1),
                    f"{t1}_xG":        float(x1),
                    f"{t2}_シュート":  int(s2),
                    f"{t2}_xG":        float(x2),
                })
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_page(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def section_html(soup: BeautifulSoup, heading_text: str) -> str:
    heading = soup.find(['h2', 'h3', 'h4', 'h5', 'h6'], string=heading_text)
    content = []
    if heading:
        el = heading.find_next_sibling()
        while el and not el.name.startswith('h'):
            content.append(str(el))
            el = el.find_next_sibling()
    return ''.join(content)


def df_to_md(df: pd.DataFrame) -> str:
    """pandas DataFrame → Markdown table (no external deps)."""
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep    = "| " + " | ".join("---" for _ in cols) + " |"
    rows   = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join([header, sep] + rows)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def extract_basic_info(soup: BeautifulSoup) -> dict:
    info = {"home": "HOME", "away": "AWAY", "score_h": "?", "score_a": "?"}
    vs = soup.find('div', class_='vsHeader')
    if vs:
        # team names: <td class="tName r"> and <td class="tName l">
        th = vs.select_one('td.tName.r span')
        ta = vs.select_one('td.tName.l span')
        if th:
            info["home"] = clean_text(th.get_text())
        if ta:
            info["away"] = clean_text(ta.get_text())
        # scores: row has three <td class="numL c"> → [home_score, "-", away_score]
        score_cells = vs.select('td.numL.c')
        if len(score_cells) >= 3:
            info["score_h"] = clean_text(score_cells[0].get_text())
            info["score_a"] = clean_text(score_cells[2].get_text())
    return info


def build_header_md(soup: BeautifulSoup, info: dict) -> str:
    title = soup.find('title')
    title_text = clean_text(title.get_text()) if title else "Match Report"
    title_text = title_text.rsplit(' | ', 2)[0]
    return "\n".join([
        f"# {title_text}",
        "",
        f"**{info['home']}  {info['score_h']} - {info['score_a']}  {info['away']}**",
        "",
    ])


def build_review_md(soup: BeautifulSoup) -> str:
    raw = section_html(soup, '戦評')
    if not raw:
        return ""
    text = BeautifulSoup(raw, 'html.parser').get_text(strip=True)
    return f"## 戦評\n\n{text}\n"


def build_scorers_md(soup: BeautifulSoup, info: dict) -> str:
    raw = section_html(soup, '得点者')
    if not raw:
        return ""
    lines = ["## 得点者", ""]
    for tr in BeautifulSoup(raw, 'html.parser').find_all('tr'):
        cols = tr.find_all('td')
        if len(cols) >= 5:
            time = clean_text(cols[2].get_text())
            hp   = clean_text(cols[0].get_text())
            ap   = clean_text(cols[4].get_text())
            if hp:
                lines.append(f"- {time}' **{info['home']}**: {hp}")
            if ap:
                lines.append(f"- {time}' **{info['away']}**: {ap}")
    lines.append("")
    return "\n".join(lines)


def build_stats_md(soup: BeautifulSoup, info: dict) -> str:
    raw = section_html(soup, 'スタッツ')
    if not raw:
        return ""
    try:
        df_s = pd.read_html(StringIO(raw))[0]
        rows = []
        for i in range(0, len(df_s) - 1, 2):
            rows.append({
                '項目':                        df_s.iloc[i,   0],
                f'{info["home"]}(今季平均)':   df_s.iloc[i+1, 0],
                f'{info["home"]}(当日)':       df_s.iloc[i+1, 2],
                f'{info["away"]}(当日)':       df_s.iloc[i+1, 4],
                f'{info["away"]}(今季平均)':   df_s.iloc[i+1, 6],
            })
        return f"## スタッツ\n\n{df_to_md(pd.DataFrame(rows))}\n"
    except Exception:
        return ""


def build_cbp_md(soup: BeautifulSoup, info: dict) -> str:
    raw = section_html(soup, 'チャンスビルディングポイント')
    if not raw:
        return ""
    try:
        dfs = pd.read_html(StringIO(raw))
        category_names = ["攻撃", "パス", "クロス", "ドリブル", "シュート", "奪取", "守備", "セーブ"]
        lines = ["## チャンスビルディングポイント", ""]
        for i, name in enumerate(category_names, 1):
            if i >= len(dfs):
                break
            df = dfs[i].copy()
            if len(df.columns) >= 5:
                df.columns = [
                    f'{info["home"]} 選手',
                    f'{info["home"]} 値',
                    'ポイント',
                    f'{info["away"]} 値',
                    f'{info["away"]} 選手',
                ]
                df = df[[f'{info["home"]} 選手', 'ポイント', f'{info["away"]} 選手']]
                lines += [f"### {name}", "", df_to_md(df), ""]
        return "\n".join(lines)
    except Exception:
        return ""


def build_members_md(soup: BeautifulSoup) -> str:
    boxes  = soup.find_all('div', class_='boxHalf')
    labels = [['HOME 先発', 'HOME 控え'], ['AWAY 先発', 'AWAY 控え']]
    inner  = []
    for b_idx, box in enumerate(boxes[:2]):
        for t_idx, table in enumerate(box.find_all('table')[:2]):
            label = labels[b_idx][t_idx]
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                df = df[df.iloc[:, 0].isin(['GK', 'DF', 'MF', 'FW'])]
                df = df.dropna(axis=1, how='all').reset_index(drop=True)
                if df.empty:
                    continue
                if len(df.columns) >= 3:
                    base = ['ポジション', '背番号', '選手名']
                    extra = ['出場時間'] + [f'項目{k+1}' for k in range(len(df.columns) - 4)]
                    df.columns = base + extra[:len(df.columns) - 3]
                inner += [f"### {label}", "", df_to_md(df), ""]
            except Exception:
                continue
    if not inner:
        return ""
    return "\n".join(["## メンバー", ""] + inner)


def build_timeline_md(soup: BeautifulSoup, shots_df=None) -> str:
    boxes = soup.find_all('div', class_='boxTimeline')
    if not boxes:
        return ""

    data: dict = {}
    for box in boxes:
        current_slot = None
        for row in box.find_all('tr'):
            time_cell = row.find('td', class_='timebase')
            if time_cell:
                txt = time_cell.get_text(strip=True)
                if re.match(r'\d{2}-\d{2}', txt):
                    current_slot = txt
                    data[current_slot] = {
                        '時間帯':      txt,
                        'HOME 保持率': '',
                        'AWAY 保持率': '',
                        'HOME スタイル': [],
                        'AWAY スタイル': [],
                    }
                continue
            if not current_slot:
                continue

            label_cell = row.find('td', class_='dataTtl')
            label = label_cell.get_text(strip=True) if label_cell else ''

            if label == 'Possession':
                h = row.find('td', class_='homePoss')
                a = row.find('td', class_='awayPoss')
                if h:
                    data[current_slot]['HOME 保持率'] = h.get_text(strip=True)
                if a:
                    data[current_slot]['AWAY 保持率'] = a.get_text(strip=True)
            elif label == 'Style':
                for td in row.find_all('td', class_=re.compile('^[rl]$')):
                    key = 'HOME スタイル' if 'r' in td.get('class', []) else 'AWAY スタイル'
                    for div in td.find_all('div'):
                        img = div.find('img')
                        if img and img.get('alt') and img['alt'] not in data[current_slot][key]:
                            data[current_slot][key].append(img['alt'])

    if not data:
        return ""

    slots = sorted(data.values(), key=lambda x: int(x['時間帯'].split('-')[0]))
    lines = [
        "## 時間帯別データ",
        "",
        "| 時間帯 | HOME 保持率 | AWAY 保持率 | HOME スタイル | AWAY スタイル |",
        "|---|---|---|---|---|",
    ]
    for s in slots:
        lines.append(
            f"| {s['時間帯']} "
            f"| {s['HOME 保持率']} "
            f"| {s['AWAY 保持率']} "
            f"| {', '.join(s['HOME スタイル'])} "
            f"| {', '.join(s['AWAY スタイル'])} |"
        )
    lines.append("")

    if shots_df is not None and not shots_df.empty:
        lines += ["### シュート・ゴール期待値の推移（スポーツナビ）", ""]
        lines.append(df_to_md(shots_df))
        lines.append("")

    return "\n".join(lines)


def build_hotzone_md(soup: BeautifulSoup) -> str:
    elements = soup.find_all(class_='hotzone')
    if not elements:
        return ""

    def rgba_alpha(style: str) -> float:
        m = re.search(r'rgba\([^,]+,[^,]+,[^,]+,\s*([-\d.]+)\s*\)', style)
        return float(m.group(1)) if m else 0.0

    # Build a global intensity → level mapping for consistent scaling
    all_alphas = []
    for el in elements:
        t = el if el.name == 'table' else el.find('table')
        if not t:
            continue
        for td in t.find_all(['td', 'th']):
            m = re.search(r'background(?:-color)?:\s*(.*?)(;|$)', td.get('style', ''))
            if m:
                all_alphas.append(rgba_alpha(m.group(1).strip()))

    if not all_alphas:
        return ""

    level_map = {v: i for i, v in enumerate(sorted(set(all_alphas)))}
    max_level  = max(level_map.values())

    zone_labels = [
        "HOME ホットゾーン(前半)", "AWAY ホットゾーン(前半)",
        "HOME ホットゾーン(後半)", "AWAY ホットゾーン(後半)",
    ]
    lines = ["## ホットゾーン", f"*(0 = 低頻度 / {max_level} = 高頻度)*", ""]

    for i, el in enumerate(elements):
        t = el if el.name == 'table' else el.find('table')
        if not t:
            continue
        matrix = []
        for row in t.find_all('tr'):
            row_vals = []
            for td in row.find_all(['td', 'th']):
                m = re.search(r'background(?:-color)?:\s*(.*?)(;|$)', td.get('style', ''))
                alpha = rgba_alpha(m.group(1).strip()) if m else 0.0
                row_vals.append(level_map.get(alpha, 0))
            if row_vals:
                matrix.append(row_vals)
        if not matrix:
            continue

        label = zone_labels[i] if i < len(zone_labels) else f"ホットゾーン {i}"
        num_cols = len(matrix[0])
        header = "| |" + "".join(f" {j} |" for j in range(num_cols))
        sep    = "|---|" + "---|" * num_cols
        lines += [f"### {label}", "", header, sep]
        for r_i, row in enumerate(matrix):
            lines.append(f"| **{r_i}** |" + "".join(f" {v} |" for v in row))
        lines.append("")

    return "\n".join(lines)


def build_stream_md(soup: BeautifulSoup, info: dict) -> str:
    all_scripts = "\n".join(s.string for s in soup.find_all('script') if s.string)
    pts = re.findall(
        r'\[\s*(\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]',
        all_scripts,
    )
    if not pts:
        return ""
    try:
        df = pd.DataFrame([(float(a), float(b), float(c)) for a, b, c in pts],
                          columns=['分', info['home'], info['away']])
        half = len(df) // 2
        df.insert(0, '前後半', ['前半'] * half + ['後半'] * (len(df) - half))

        lines = ["## マッチストリームデータ", ""]
        lines.append(df_to_md(df))
        lines.append("")
        return "\n".join(lines)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_sources_md(football_lab_url: str, yahoo_url: str = "") -> str:
    lines = ["## データの出典", ""]
    lines.append(f"- Football Lab マッチレポート（{football_lab_url}）")
    if yahoo_url:
        lines.append(f"- スポーツナビ テキスト速報（{yahoo_url}）")
    lines.append("")
    return "\n".join(lines)


def derive_filename(url: str) -> str:
    m = re.search(r'/(\w+)/report\?year=(\d{4})&month=(\d+)&date=(\d+)', url)
    if m:
        team, y, mo, d = m.groups()
        return f"{team}_{y}{mo.zfill(2)}{d.zfill(2)}_report.md"
    return "match_report.md"


def main(url: str = URL, yahoo_url: str = YAHOO_URL) -> None:
    print(f"Fetching: {url}")
    soup = fetch_page(url)
    info = extract_basic_info(soup)
    print(f"Match: {info['home']} {info['score_h']} - {info['score_a']} {info['away']}")

    shots_df = pd.DataFrame()
    if yahoo_url:
        print(f"Fetching Yahoo live text: {yahoo_url}")
        shots_df = fetch_yahoo_shots(yahoo_url)
        print(f"  → {len(shots_df)} shot/xG snapshots found")

    sections = [
        build_header_md(soup, info),
        build_review_md(soup),
        build_scorers_md(soup, info),
        build_stats_md(soup, info),
        build_cbp_md(soup, info),
        build_members_md(soup),
        build_timeline_md(soup, shots_df if not shots_df.empty else None),
        build_hotzone_md(soup),
        build_stream_md(soup, info),
        build_sources_md(url, yahoo_url),
    ]

    content = "\n".join(s for s in sections if s)
    out = OUTPUT_DIR / derive_filename(url)
    out.write_text(content, encoding='utf-8')
    print(f"Saved: {out}")


if __name__ == '__main__':
    url       = sys.argv[1] if len(sys.argv) > 1 else URL
    yahoo_url = sys.argv[2] if len(sys.argv) > 2 else YAHOO_URL
    main(url, yahoo_url)
