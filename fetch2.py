import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def fetch_syutubahyo_with_selenium(race_id):
    """Seleniumで__NEXT_DATA__を含む出馬表を取得"""
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"📘 アクセス中: {url}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(3)  # JS読み込み待ち

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("❌ __NEXT_DATA__ が見つかりません。JavaScript未実行の可能性。")
        return pd.DataFrame()

    data = json.loads(script_tag.string)
    try:
        horses = data["props"]["pageProps"]["race"]["horses"]
    except KeyError:
        print("⚠️ horses データが見つかりません。構造変更の可能性。")
        return pd.DataFrame()

    rows = []
    for h in horses:
        horse_name = h.get("name", "")
        jockey = h.get("jockey", {}).get("name", "")
        age = h.get("age", "")
        weight = h.get("burdenWeight", "")
        odds = h.get("odds", "")
        pop = h.get("popularity", "")
        horse_id = h.get("id", "")
        horse_url = f"https://db.netkeiba.com/horse/{horse_id}/"

        rows.append({
            "馬名": horse_name,
            "騎手": jockey,
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


def fetch_past_5races_nextdata(horse_url, horse_name):
    """馬ごとの__NEXT_DATA__から過去5走取得"""
    import requests
    res = requests.get(horse_url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print(f"⚠️ {horse_name}: __NEXT_DATA__ が見つかりません ({horse_url})")
        return []

    data = json.loads(script_tag.string)
    try:
        race_list = data["props"]["pageProps"]["horseResult"]["pastResults"]
    except KeyError:
        print(f"⚠️ {horse_name}: 過去走データが見つかりません。")
        return []

    races = []
    for r in race_list[:5]:
        races.append({
            "馬名": horse_name,
            "レース名": r.get("raceName", ""),
            "グレード": r.get("grade", ""),
            "日付": r.get("date", ""),
            "コース": r.get("courseName", ""),
            "着順": r.get("finish", ""),
            "タイム": r.get("time", ""),
            "人気": r.get("popularity", ""),
            "着差": r.get("margin", ""),
        })
    print(f"✅ {horse_name}: {len(races)}件取得")
    return races


def main():
    race_id = input("取得したいレースIDを入力（例：202405040811）: ").strip()
    df = fetch_syutubahyo_with_selenium(race_id)
    if df.empty:
        return

    all_races = []
    for _, row in df.iterrows():
        horse_name = row["馬名"]
        horse_url = row["horse_url"]
        print(f"🐎 {horse_name} の近5走を取得中...")
        races = fetch_past_5races_nextdata(horse_url, horse_name)
        all_races.extend(races)

    race_df = pd.DataFrame(all_races)
    race_df.to_csv("data/race_data_auto.csv", index=False, encoding="utf-8-sig")
    print("✅ 全馬の過去5走を保存しました → data/race_data_auto.csv")


if __name__ == "__main__":
    main()
