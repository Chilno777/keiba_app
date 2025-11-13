import streamlit as st
import pandas as pd
from pathlib import Path

# データの読み込み
syutubahyo_path = Path("data/syutubahyo.csv")
race_data_path = Path("data/race_data.csv")

syutubahyo_df = pd.read_csv(syutubahyo_path)
race_data_df = pd.read_csv(race_data_path)

st.title("🐎 出馬表ビューア（印付きバージョン）")

# ---- 印の選択肢 ----
mark_options = ["", "◎", "○", "▲", "△", "×", "消"]

# セッションステートに印の状態を保存
if "marks" not in st.session_state:
    st.session_state["marks"] = {}

# 各馬ごとの印入力
st.subheader("出馬表")
for i, row in syutubahyo_df.iterrows():
    horse_name = row["馬名"]
    current_mark = st.session_state["marks"].get(horse_name, "")
    
    # セレクトボックスで印選択
    selected_mark = st.selectbox(
        f"{horse_name}（{row['性齢']}歳・{row['騎手']}）",
        mark_options,
        index=mark_options.index(current_mark) if current_mark in mark_options else 0,
        key=f"mark_{horse_name}"
    )
    
    # 選択内容を保存
    st.session_state["marks"][horse_name] = selected_mark

# 「消」印を付けた馬を除外
visible_horses = [
    horse for horse, mark in st.session_state["marks"].items() if mark != "消"
]

filtered_df = syutubahyo_df[syutubahyo_df["馬名"].isin(visible_horses)]

# ---- 近5走データ（競馬新聞風カード形式・修正版）----
st.write("### 📰 近５走成績（競馬新聞風）")

# （任意）スクロールバー非表示の CSS を安全に挿入
st.markdown(
    '<style>'
    'div[data-testid="stHorizontalBlock"]::-webkit-scrollbar{display:none;}'
    'div[data-testid="stHorizontalBlock"]{ -ms-overflow-style:none; scrollbar-width:none;}'
    '</style>',
    unsafe_allow_html=True
)

for horse in syutubahyo_df["馬名"]:
    mark = st.session_state["marks"].get(horse, "")
    if mark == "消":
        st.warning(f"『{horse}』は『消』印が付いているため、近5走は非表示です。")
        continue

    horse_past = race_data_df[race_data_df["馬名"] == horse].head(5)
    if len(horse_past) == 0:
        continue

    st.markdown(f"#### 🐴 {horse}", unsafe_allow_html=True)

    # カード群を作成（注意：文字列の先頭に改行を入れない）
    cards = []
    for _, r in horse_past.iterrows():
        race_name = str(r.get("レース名","") or "")
        date = str(r.get("日付","") or r.get("レース日","") or "")
        course = str(r.get("コース","") or "")
        result = str(r.get("着順","") or "")
        time = str(r.get("タイム","") or "")
        pop = str(r.get("人気","") or "")
        diff = str(r.get("着差","") or r.get("差","") or "")

        # 着順に応じた色分け（例）
        bg_color = "#fffdfa"
        border_color = "#ccc"
        if result == "1":
            bg_color = "#fff5b5"; border_color = "#d1b000"
        elif result == "2":
            bg_color = "#e3f0ff"; border_color = "#6fa8ff"
        elif result == "3":
            bg_color = "#ffe1e1"; border_color = "#ff6f6f"

        # card_html を組み立てるときは先頭に改行を入れない
        card_html = (
            f'<div style="flex:0 0 200px;height:135px;background:{bg_color};'
            f'border:1px solid {border_color};border-radius:6px;box-shadow:1px 1px 3px rgba(0,0,0,0.12);'
            f'padding:6px 8px;margin-right:8px;font-family:Yu Gothic,Meiryo,sans-serif;font-size:12px;line-height:1.2;color:#222;">'
            f'<div style="font-weight:700;font-size:13px;border-bottom:1px solid #bbb;margin-bottom:2px;">{date}　{race_name}</div>'
            f'<div style="font-size:11.5px;color:#333;margin-bottom:3px;">{course}</div>'
            f'<div style="margin-bottom:3px;"><b>着：</b><b style="font-size:14px;">{result}</b>　<span style="color:#555;">人：</span>{pop}　<span style="color:#555;">着差：</span>{diff}</div>'
            f'<div style="margin-bottom:3px;"><span style="color:#555;">通過：</span>{r.get("通過","")}　<span style="color:#555;">時計：</span>{time}</div>'
            f'</div>'
        )
        cards.append(card_html)

    container_html = (
        '<div style="display:flex;gap:8px;overflow-x:auto;padding:6px 2px;-webkit-overflow-scrolling:touch;scrollbar-width:none;">'
        + ''.join(cards) +
        '</div>'
    )

    # ここで HTML を生描画（unsafe_allow_html=True が必須）
    st.markdown(container_html, unsafe_allow_html=True)
