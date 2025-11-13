import streamlit as st
import pandas as pd
from pathlib import Path

# データの読み込み
syutubahyo_path = Path("data/syutubahyo_data.csv")
race_data_path = Path("data/race_jp23_data.csv")

syutubahyo_df = pd.read_csv(syutubahyo_path)
#race_data_df = pd.read_csv(race_data_path)
race_data_df = pd.read_csv(race_data_path, engine="python", on_bad_lines="skip")


#タイトル
st.title("2023ジャパンカップ出馬表＆競馬新聞")

#----- 印デザイン -----
#印の選択肢
mark_options = ["", "◎", "〇", "▲", "△", "✓", "消"]

# セッションステートに印の状態を保存
if "marks" not in st.session_state:
    st.session_state["marks"] = {}

# ---- 印の保存・読み込み機能 ----
marks_path = Path("data/marks.csv")

# 起動時に保存データがあれば読み込む
if marks_path.exists():
    saved_marks = pd.read_csv(marks_path)
    for _, row in saved_marks.iterrows():
        st.session_state["marks"][row["馬名"]] = row["印"]
    st.info("過去の印データを読み込みました。")

# 保存ボタン
if st.button("印を保存する"):
    marks_df = pd.DataFrame(
        [(name, mark) for name, mark in st.session_state["marks"].items()],
        columns=["馬名", "印"]
    )
    marks_df.to_csv(marks_path, index=False, encoding="utf-8-sig")
    st.success("印データを保存しました！")


#----- 印選択部分 -----
# 各馬ごとの印入力
st.subheader("印選択") #見出し
for i, row in syutubahyo_df.iterrows():#pandasのDataFrame（出馬表）を１行ずつ処理
    horse_name = row["馬名"] #syutubahyo.csvから馬名を拾ってくる。○○＝row["〇〇"]で拡張可能
    current_mark = st.session_state["marks"].get(horse_name, "")#印をsession_stateから取り出す
    
    # セレクトボックスで印選択
    selected_mark = st.selectbox(
        f"{horse_name}（{row['性齢']}・{row['騎手']}・{row['人気']}番人気（{row['単勝オッズ']}倍）)",
        mark_options,
        index=mark_options.index(current_mark) if current_mark in mark_options else 0,
        key=f"mark_{horse_name}"#馬のセレクトボックスを識別
    )#st.selectbox()でプルダウンメニュ＝を作る
    
    # 選択内容を保存
    st.session_state["marks"][horse_name] = selected_mark

# 「消」印を付けた馬を除外
visible_horses = [
    horse for horse, mark in st.session_state["marks"].items() if mark != "消"
]

filtered_df = syutubahyo_df[syutubahyo_df["馬名"].isin(visible_horses)]

# ---- 出馬表のデザイン ----
st.write("２０２３ジャパンカップ出馬表")

waku_colors = {
    1: "#FFFFFF",  # 白
    2: "#000000",  # 黒
    3: "#FF0000",  # 赤
    4: "#002AFF",  # 青
    5: "#FFFF00",  # 黄
    6: "#15FF00",  # 緑
    7: "#FF8000",  # 橙
    8: "#FF00D4",  # 桃
}

for _, row in syutubahyo_df.iterrows():
    horse_name = row["馬名"]
    mark = st.session_state["marks"].get(horse_name, "")
    waku = int(row["枠番"])
    umaban = int(row["馬番"])
    color = waku_colors.get(waku, "#FFFFFF")
    
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;
                    border:1px solid #ccc;border-radius:8px;
                    margin:6px 0;padding:8px;
                    background-color:#f9f9f9;'>
            <div style='background-color:{color};
                        color:{'white' if waku in [2,3,7,8] else 'black'};
                        font-weight:bold;font-size:20px;
                        width:50px;height:50px;display:flex;
                        align-items:center;justify-content:center;
                        border-radius:6px;margin-right:10px;'>
                {row['馬番']}
            </div>
            <div style='flex:1;'>
                <b>{horse_name}</b>（{row['性齢']}・{row['騎手']}）<br>
                <span style='font-size:12px;color:gray;'>馬番:{row['馬番']}・{row['人気']}人気({row['単勝オッズ']}倍)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    #st.markdown(..., unsafe_allow_html=True)

# ---- UIを競馬新聞風に----
# ---- 並び替えオプション ----
st.subheader("表示順の設定（競馬新聞部分）")

sort_option = st.selectbox(
    "表示順を選択してください",
    ["馬番順（そのまま）", "人気順（昇順）", "単勝オッズ順（昇順）"]
)

# 並び替え用データフレーム
sorted_df = syutubahyo_df.copy()
if sort_option == "人気順（昇順）":
    sorted_df = sorted_df.sort_values("人気", ascending=True)
elif sort_option == "単勝オッズ順（昇順）":
    sorted_df = sorted_df.sort_values("単勝オッズ", ascending=True)

# 並び替え後の馬リストを使う
horse_list = sorted_df["馬名"].tolist()


# ---- 近5走データ-----
st.write("### 近５走成績（競馬新聞風・高密度）")

# スクロールバーを非表示にするCSS
st.markdown(
    '<style>'
    'div[data-testid="stHorizontalBlock"]::-webkit-scrollbar{display:none;}'
    'div[data-testid="stHorizontalBlock"]{-ms-overflow-style:none;scrollbar-width:none;}'
    '</style>',
    unsafe_allow_html=True
)

for horse in horse_list:
    mark = st.session_state["marks"].get(horse, "")
    if mark == "消":
        st.warning(f"『{horse}』は『消』印が付いているため、近5走は非表示です。")
        continue

    horse_past = race_data_df[race_data_df["馬名"] == horse].head(5)
    if len(horse_past) == 0:
        continue

    st.markdown(f"#### 🐴 {horse}", unsafe_allow_html=True)

    cards = []
    for _, r in horse_past.iterrows():
        race_name = str(r.get("レース名","") or "")
        grade = str(r.get("グレード","") or "")
        date = str(r.get("日付","") or r.get("レース日","") or "")
        course = str(r.get("コース","") or "")
        result = str(r.get("着順","") or "")
        time = str(r.get("タイム","") or "")
        pop = str(r.get("人気","") or "")
        diff = str(r.get("着差","") or "")
        jockey = str(r.get("騎手","") or "")
        passing = str(r.get("通過","") or "")
        weight = str(r.get("斤量","") or "")
        last3f = str(r.get("上り","") or "")

        # 着順に応じた色分け
        bg_color = "#fffdfa"
        border_color = "#ccc"
        if result == "1":
            bg_color = "#fff8dc"; border_color = "#d1b000"  # 金
        elif result == "2":
            bg_color = "#eaf3ff"; border_color = "#4a90e2"  # 青
        elif result == "3":
            bg_color = "#ffeaea"; border_color = "#ff7070"  # 赤

        # HTMLを構築
        card_html = (
            f'<div style="flex:0 0 210px;height:150px;background:{bg_color};'
            f'border:1px solid {border_color};border-radius:8px;box-shadow:1px 1px 3px rgba(0,0,0,0.12);'
            f'padding:6px 8px;margin-right:8px;font-family:Yu Gothic,Meiryo,sans-serif;font-size:12px;line-height:1.3;color:#222;">'
            f'<div style="font-weight:700;font-size:13px;color:#333;">{race_name} <span style="font-size:10px;color:#555;">{grade}</span></div>'
            f'<div style="font-size:11px;color:#666;margin-bottom:4px;">{date}　{course}</div>'
            f'<div style="margin-bottom:3px;">着：<b>{result}</b>　人：{pop}　差：{diff}　時計：{time} <span style="color:#777;">（上り {last3f}）</span></div>'
            f'<div style="margin-bottom:3px;">{jockey}（{weight}）　通過：{passing}</div>'
            f'</div>'
        )
        cards.append(card_html)

    # 横並び表示
    container_html = (
        '<div style="display:flex;gap:8px;overflow-x:auto;padding:6px 2px;-webkit-overflow-scrolling:touch;">'
        + ''.join(cards) +
        '</div>'
    )


    st.markdown(container_html, unsafe_allow_html=True)
