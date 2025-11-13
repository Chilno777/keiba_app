import time
import pandas as pd
import re
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Selenium関係
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ==============================
# 出馬表の取得（Selenium使用）
# ==============================
#horse_url
def fetch_syutubahyo_selenium(race_id):
    """Seleniumで出馬表を取得（URL正規化付き）"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin
    import pandas as pd

    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"📘 ブラウザでアクセス中: {url}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.RaceTable01"))
        )
    except:
        print("⚠️ 出馬表ロードを待機しましたが、要素が見つかりませんでした。")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    rows = []
    table = soup.select_one("table.RaceTable01")
    if not table:
        print("❌ 出馬表テーブルが見つかりません。")
        return pd.DataFrame()

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        horse_a = tr.find("a", href=re.compile("/horse/"))
        if not horse_a:
            continue

        horse_name = horse_a.get_text(strip=True)
        raw_href = horse_a.get("href", "").strip()

        # --- URL正規化処理 ---
        if not raw_href:
            continue

        # db.netkeiba.com に統一
        if raw_href.startswith("http"):
            horse_url = re.sub(r"^https*://race\.netkeiba\.com", "https://db.netkeiba.com", raw_href)
        else:
            horse_url = urljoin("https://db.netkeiba.com", raw_href)

        # 二重コロン修正
        horse_url = horse_url.replace("https::", "https:")

        # 騎手情報などを抽出
        jockey = tr.find("a", href=re.compile("/jockey/"))
        jockey_name = jockey.get_text(strip=True) if jockey else ""
        odds_tag = tr.find("td", class_="OddsTxt")
        odds = odds_tag.get_text(strip=True) if odds_tag else ""
        pop_tag = tr.find("td", class_="PopularTxt")
        pop = pop_tag.get_text(strip=True) if pop_tag else ""
        age = tds[3].get_text(strip=True)
        weight = tds[4].get_text(strip=True)

        rows.append({
            "馬名": horse_name,
            "騎手": jockey_name,
            "斤量": weight,
            "馬齢": age,
            "人気": pop,
            "単勝オッズ": odds,
            "horse_url": horse_url
        })

    df = pd.DataFrame(rows)
    df.to_csv("data/syutubahyo_auto.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 出馬表を取得しました（{len(df)}頭）")
    return df


# ==============================
# 各馬の過去5走を取得
# ==============================
import pandas as pd
import requests
from io import StringIO
from bs4 import BeautifulSoup
import re

def fetch_past_5races(horse_url, horse_name):
    """pandas.read_html() + BeautifulSoup バックアップ併用版"""
    print(f"🐎 {horse_name} の近5走を取得中...")
    try:
        res = requests.get(horse_url, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = "utf-8"
        html = res.text
    except Exception as e:
        print(f"⚠️ {horse_name}: ページ取得失敗 ({e})")
        return []

    # --- 方法1: pandas.read_html() ---
    try:
        from io import StringIO
        dfs = pd.read_html(StringIO(html))
        for df in dfs:
            if any("レース" in str(c) for c in df.columns):
                df.columns = [re.sub(r'\s+', '', str(c)) for c in df.columns]
                race_col = [c for c in df.columns if "レース" in c][0]
                keep_cols = [race_col] + [c for c in ["日付", "着順", "タイム", "人気", "通過", "着差"] if c in df.columns]
                df = df[keep_cols].head(5)
                df["馬名"] = horse_name
                print(f"✅ {horse_name}: {len(df)}件取得（read_html）")
                return df.to_dict("records")
    except Exception:
        pass  # fallbackへ

    # --- 方法2: BeautifulSoupでdiv構造を解析 ---
    soup = BeautifulSoup(html, "html.parser")
    race_blocks = soup.select("div.HorseList, div.Horse_5result, table.Horse_5result_table")

    if not race_blocks:
        print(f"⚠️ {horse_name}: 近走テーブルが見つかりません ({horse_url})")
        return []

    # 手動パース（最近の構成に対応）
    races = []
    rows = soup.select("tr.HorseList__row")
    for row in rows[:5]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) < 6:
            continue
        races.append({
            "馬名": horse_name,
            "レース名": cells[1],
            "日付": cells[0],
            "着順": cells[2],
            "タイム": cells[3],
            "人気": cells[4],
            "着差": cells[5] if len(cells) > 5 else "",
        })

    print(f"✅ {horse_name}: {len(races)}件取得（BeautifulSoup fallback）")
    return races


# ==============================
# メイン処理
# ==============================
def main():
    race_id = input("取得したいレースIDを入力（例：202405040811）: ").strip()
    df = fetch_syutubahyo_selenium(race_id)
    if df.empty:
        return

    all_races = []
    for _, row in df.iterrows():
        horse_name = row["馬名"]
        horse_url = row["horse_url"]
        print(f"🐎 {horse_name} の近5走を取得中...")
        races = fetch_past_5races(horse_url, horse_name)
        all_races.extend(races)

    race_df = pd.DataFrame(all_races)
    race_df.to_csv("data/race_data_auto.csv", index=False, encoding="utf-8-sig")
    print("✅ 全馬の過去5走を保存しました → data/race_data_auto.csv")


if __name__ == "__main__":
    main()
