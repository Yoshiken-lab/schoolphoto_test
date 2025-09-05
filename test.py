# Sunday-first calendar (Streamlit web app)
# Run: streamlit run sunday_calendar_streamlit.py
import calendar
import datetime as dt
import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="スクールフォトキャパ管理_β", layout="wide")

WEEK_LABELS = ['日','月','火','水','木','金','土']

# ====== 簡易イベント保存先（ローカルJSON） ======
EVENT_FILE = Path("events.json")

def load_events() -> dict:
    """JSON -> dict[str, list[str]] where key = 'YYYY-MM-DD'."""
    if EVENT_FILE.exists():
        try:
            return json.loads(EVENT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_events(events: dict) -> None:
    """dict -> JSON (pretty)."""
    EVENT_FILE.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")

def month_matrix(year: int, month: int):
    cal = calendar.Calendar(firstweekday=6)  # Sunday
    # list[list[date]] (weeks of 7 dates incl. prev/next month days)
    return cal.monthdatescalendar(year, month)

def build_calendar_html(year: int, month: int, events: dict[str, list[str]]) -> str:
    today = dt.date.today()
    weeks = month_matrix(year, month)

    styles = """
    <style>
    .cal { border-collapse: collapse; margin: 0 auto; }
    .cal th, .cal td { border: 1px solid #ddd; padding: 8px; text-align: right;
                       width: 48px; height: 42px; position: relative; }
    .cal caption { font-weight: 700; font-size: 1.15rem; margin-bottom: .6rem; }
    .wday { background: #f7f7f7; text-align:center; font-weight:600; }
    .out { color: #bbb; }
    .today { background: #ffe7a1; font-weight: 700; }
    .sun { color: #d44747; }
    .sat { color: #2b62d1; }
    .has-event::after {
        content: "";
        position: absolute;
        bottom: 6px; left: 50%; transform: translateX(-50%);
        width: 6px; height: 6px; border-radius: 50%; background: #2b62d1;
    }
    </style>
    """

    html = [styles, f"<table class='cal'>"]
    html.append(f"<caption>{year}年 {month}月</caption>")
    # header
    html.append("<tr>")
    for i, label in enumerate(WEEK_LABELS):
        cls = "wday"
        if i == 0: cls += " sun"
        if i == 6: cls += " sat"
        html.append(f"<th class='{cls}'>{label}</th>")
    html.append("</tr>")

    # body
    for week in weeks:
        html.append("<tr>")
        for i, d in enumerate(week):
            cls = []
            if d.month != month: cls.append("out")
            if d == today: cls.append("today")
            if i == 0: cls.append("sun")
            if i == 6: cls.append("sat")
            # イベント点表示
            if events.get(str(d)):
                cls.append("has-event")

            num = d.day
            html.append(f"<td class='{' '.join(cls)}'>{num}</td>")
        html.append("</tr>")
    html.append("</table>")
    return ''.join(html)

# ====== UI ======
st.title("日曜始まりカレンダー")

# 初期状態
if 'year' not in st.session_state or 'month' not in st.session_state:
    t = dt.date.today()
    st.session_state.year = t.year
    st.session_state.month = t.month

# イベント状態
if 'events' not in st.session_state:
    # TODO: 起動時に常にファイルから読み込むならここをload_events()に。
    st.session_state.events = load_events()

left, right = st.columns([2.2, 1.0])

with left:
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
    with col1:
        if st.button("← 前月"):
            y, m = st.session_state.year, st.session_state.month
            m0 = m - 1
            if m0 == 0:
                st.session_state.year = y - 1
                st.session_state.month = 12
            else:
                st.session_state.month = m0
    with col5:
        if st.button("次月 →"):
            y, m = st.session_state.year, st.session_state.month
            m0 = m + 1
            if m0 == 13:
                st.session_state.year = y + 1
                st.session_state.month = 1
            else:
                st.session_state.month = m0
    with col3:
        if st.button("今日へ"):
            t = dt.date.today()
            st.session_state.year = t.year
            st.session_state.month = t.month

    with col2:
        y = st.number_input("年", min_value=1900, max_value=2100,
                            value=st.session_state.year, step=1)
    with col4:
        m = st.selectbox("月", list(range(1, 13)), index=st.session_state.month - 1)

    # 値変更の反映
    if int(y) != st.session_state.year or (m) != st.session_state.month:
        st.session_state.year = int(y)
        st.session_state.month = int(m)

    # カレンダー描画
    st.markdown(
        build_calendar_html(st.session_state.year, st.session_state.month, st.session_state.events),
        unsafe_allow_html=True
    )

with right:
    st.subheader("イベント追加")
    # 入力UI
    default_date = dt.date(st.session_state.year, st.session_state.month, 1)
    event_date = st.date_input("日付", value=min(default_date, dt.date.today()))
    title = st.text_input("タイトル", placeholder="例: 写真撮影（午前）")
    add = st.button("追加")
    if add and title.strip():
        key = str(event_date)
        st.session_state.events.setdefault(key, []).append(title.strip())
        save_events(st.session_state.events)  # 永続化
        st.success(f"追加しました：{event_date}「{title}」")

    # 月内イベント一覧
    st.subheader("この月のイベント")
    # 該当月のみ抽出して表示
    y, m = st.session_state.year, st.session_state.month
    items = []
    for k, titles in st.session_state.events.items():
        d = dt.date.fromisoformat(k)
        if d.year == y and d.month == m:
            for idx, t_ in enumerate(titles):
                items.append((d, idx, t_))
    items.sort(key=lambda x: (x[0], x[1]))

    if not items:
        st.caption("（この月のイベントはまだありません）")
    else:
        for d, idx, t_ in items:
            cols = st.columns([3, 7, 2])
            cols[0].markdown(f"**{d.strftime('%Y/%m/%d')}**")
            cols[1].markdown(t_)
            if cols[2].button("削除", key=f"del-{d}-{idx}"):
                # 指定要素を削除
                arr = st.session_state.events[str(d)]
                arr.pop(idx)
                if not arr:
                    st.session_state.events.pop(str(d))
                save_events(st.session_state.events)  # 永続化
                st.success(f"削除しました：{d}「{t_}」")
                st.experimental_rerun()

st.caption("※ 今日は薄い黄色でハイライト。日曜＝赤、土曜＝青。イベントがある日は青い●が表示されます。")