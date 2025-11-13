import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

def fetch_race_with_selenium(race_id):
    """netkeiba 出馬表ページから __NEXT_DATA__ をSeleniumで抽出"""
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"📘 アクセス中: {url}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(4)  # JS描画待ち

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("❌ __NEXT_DATA__ が見つかりません。")
        return pd.DataFrame()

    data = json.loads(script_tag.string)
    try:
        horses = data["props"]["pageProps"]["race"]["horses"]
    except KeyError:
        print("⚠️ horsesデータが見つかりません。構造が変わった可能性があります。")
        return pd.DataFrame()

    df = pd.DataFrame(horses)
    df.to_csv("data/syutubahyo_auto.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 出馬表を取得しました（{len(df)}頭）")
    return df


if __name__ == "__main__":
    race_id = input("取得したいレースIDを入力（例：202405040811）: ").strip()
    fetch_race_with_selenium(race_id)
