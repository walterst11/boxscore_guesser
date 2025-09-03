import re
import time
import urllib.parse
import pandas as pd
import streamlit as st
import base64

# =========================
# Helper to embed images
# =========================
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Load team logos
patriots_logo = get_base64_image("patriots_logo.png")
falcons_logo = get_base64_image("falcons_logo.png")

# =========================
# Game data (Super Bowl LI)
# =========================
game_info = {
    "title": "Super Bowl LI",
    "score": "Patriots 34 - 28 Falcons",
    "stadium": "NRG Stadium",
    "date": "Feb 5, 2017",
    "attendance": "70,807",
}

# Patriots stats
patriots_stats = {
    "Tom Brady": "Passing: 43/62, 466 Yds, 2 TD, 1 INT; Rushing: 1 CAR, 15 Yds",
    "LeGarrette Blount": "Rushing: 11 CAR, 31 Yds",
    "James White": "Rushing: 6 CAR, 29 Yds, 2 TD; Receiving: 14 REC, 110 Yds, 1 TD",
    "Dion Lewis": "Rushing: 6 CAR, 27 Yds; Receiving: 1 REC, 2 Yds",
    "Julian Edelman": "Rushing: 1 CAR, 2 Yds; Receiving: 5 REC, 87 Yds",
    "Danny Amendola": "Receiving: 8 REC, 78 Yds, 1 TD",
    "Malcolm Mitchell": "Receiving: 6 REC, 70 Yds",
    "Martellus Bennett": "Receiving: 5 REC, 62 Yds",
    "Chris Hogan": "Receiving: 4 REC, 57 Yds",
}

# Falcons stats
falcons_stats = {
    "Matt Ryan": "Passing: 17/23, 284 Yds, 2 TD, 0 INT",
    "Devonta Freeman": "Rushing: 11 CAR, 75 Yds, 1 TD; Receiving: 2 REC, 46 Yds",
    "Tevin Coleman": "Rushing: 7 CAR, 29 Yds; Receiving: 1 REC, 6 Yds, 1 TD",
    "Julio Jones": "Receiving: 4 REC, 87 Yds",
    "Taylor Gabriel": "Receiving: 3 REC, 76 Yds",
    "Austin Hooper": "Receiving: 3 REC, 32 Yds, 1 TD",
    "Mohamed Sanu": "Receiving: 2 REC, 25 Yds",
    "Patrick DiMarco": "Receiving: 2 REC, 12 Yds",
}

all_players = {**patriots_stats, **falcons_stats}

# =========================
# Parsing helpers
# =========================
def parse_passing(s):
    m = re.search(r"Passing:\s*(\d+)/(\d+),\s*(\d+)\s*Yds,\s*(\d+)\s*TD(?:,\s*(\d+)\s*INT)?", s, re.I)
    if not m: return None
    cmp_, att, yds, td, inte = m.groups()
    return {"Player": "", "Cmp": int(cmp_), "Att": int(att), "Yds": int(yds), "TD": int(td), "INT": int(inte or 0)}

def parse_rushing(s):
    m = re.search(r"Rushing:\s*(\d+)\s*CAR,\s*(\d+)\s*Yds(?:,\s*(\d+)\s*TD)?", s, re.I)
    if not m: return None
    car, yds, td = m.groups()
    return {"Player": "", "CAR": int(car), "Yds": int(yds), "TD": int(td or 0)}

def parse_receiving(s):
    m = re.search(r"Receiving:\s*(\d+)\s*REC,\s*(\d+)\s*Yds(?:,\s*(\d+)\s*TD)?", s, re.I)
    if not m: return None
    rec, yds, td = m.groups()
    return {"Player": "", "REC": int(rec), "Yds": int(yds), "TD": int(td or 0)}

def build_df(stats_dict, found, game_over, parser, cols):
    rows = []
    for player, s in stats_dict.items():
        parsed = parser(s)
        if parsed:
            parsed["Player"] = player if (player in found or game_over) else "—"
            rows.append(parsed)
    if not rows: 
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols]

# =========================
# HTML render helper
# =========================
def df_to_html(df):
    if df.empty:
        return ""
    def row_style(row):
        if row["Player"] != "—":
            return ' style="background-color:#c6efce; color:#006100;"'
        return ""
    headers = "".join([f"<th>{col}</th>" for col in df.columns])
    rows = ""
    for _, row in df.iterrows():
        style = row_style(row)
        cells = "".join([f"<td>{val}</td>" for val in row.values])
        rows += f"<tr{style}>{cells}</tr>"
    return f"""
    <table style="border-collapse:collapse; font-size:12px; margin:0; width:100%;">
      <thead><tr>{headers}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """

# =========================
# Streamlit UI setup
# =========================
st.set_page_config(layout="centered")

# Responsive CSS
st.markdown("""
<style>
/* ==== Desktop defaults ==== */
.block-container { padding-top: 3rem; padding-bottom: 0rem; }
table, th, td {
    border: 1px solid #ddd;
    padding: 2px 6px;
}
th {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    text-align: center;
}
td {
    text-align: center;
}
td:first-child, th:first-child {
    text-align: left;
    min-width: 140px;
    white-space: nowrap;
}

/* ==== Desktop defaults ==== */
.desktop-header { display: flex; align-items: center; }
.desktop-header > div { flex: 1; }

/* ==== Mobile tweaks ==== */
@media (max-width: 768px) {
  .desktop-header {
    flex-wrap: wrap;
    justify-content: center;
    text-align: center;
  }
  .desktop-header .score-col {
    order: 2;
    width: 100%;
    margin-top: 6px;
  }
  .desktop-header .stadium-col {
    order: 3;
    width: 100%;
    margin-top: 6px;
    text-align: center;
  }
  .desktop-header .logo {
    order: 1;
    flex: 0 0 auto;
    margin: 0 12px;
  }

  /* 👇 Add these font+logo size tweaks inside the same block */
  .desktop-header .score-col div:first-child {
    font-size: 0.5em !important;  /* title */
  }
  .desktop-header .score-col div:last-child {
    font-size: 0.5em !important; /* score */
  }
  .desktop-header .stadium-col {
    font-size: 0.1em !important;
    text-align: center !important;
  }
  .desktop-header .logo img {
    height: 45px !important;
  }
}
</style>
""", unsafe_allow_html=True)


# ===== Header (desktop 4-column, stacks on mobile) =====
st.markdown(f"""
<div class="desktop-header">
  <div>
    <img src='data:image/png;base64,{patriots_logo}' style='height:60px; margin-top:-8px;'>
  </div>
  <div>
    <div style='font-weight:600;font-size:1.1em;'>{game_info['title']}</div>
    <div style='font-size:1em;color:#333;'>{game_info['score']}</div>
  </div>
  <div>
    <img src='data:image/png;base64,{falcons_logo}' style='height:60px; margin-top:8px;'>
  </div>
  <div style="font-size:0.9em; text-align:right;">
    <b>Stadium:</b> {game_info['stadium']}<br>
    <b>Date:</b> {game_info['date']}<br>
    <b>Attendance:</b> {game_info['attendance']}
  </div>
</div>
""", unsafe_allow_html=True)

# ===== State =====
if "start_time" not in st.session_state: st.session_state.start_time = time.time()
if "found" not in st.session_state: st.session_state.found = set()
if "wrong" not in st.session_state: st.session_state.wrong = []
if "game_over" not in st.session_state: st.session_state.game_over = False
if "final_time" not in st.session_state: st.session_state.final_time = None

# ===== Guess input =====
gi, gb = st.columns([4,1])
with gi:
    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Guess player:", "", key="guess_input", label_visibility="collapsed")
        submitted = st.form_submit_button("Go")
with gb:
    if st.button("Give Up", use_container_width=True) and not st.session_state.game_over:
        st.session_state.game_over = True
        st.session_state.final_time = int(time.time() - st.session_state.start_time)

# ===== Process guess =====
if submitted and guess and not st.session_state.game_over:
    g = guess.strip().lower()
    matched = False
    for player in all_players:
        parts = player.lower().split()
        last_name = parts[-1] if parts else player.lower()
        if g == player.lower() or g == last_name:
            st.session_state.found.add(player)
            matched = True
    if not matched and g not in [w.lower() for w in st.session_state.wrong]:
        st.session_state.wrong.append(guess.strip())

# ===== Scoreboard =====
with gb:
    total, found_ct = len(all_players), len(st.session_state.found)
    if not st.session_state.game_over and found_ct < total:
        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f"<p style='font-size:12px; text-align:center;'>Score: {found_ct}/{total}<br>⏱ {elapsed}s</p>", unsafe_allow_html=True)
    else:
        if st.session_state.final_time is None:
            st.session_state.final_time = int(time.time() - st.session_state.start_time)
        st.markdown(f"<p style='font-size:12px; text-align:center;'>Final: {found_ct}/{total}<br>⏱ {st.session_state.final_time}s</p>", unsafe_allow_html=True)

        share_text = f"I scored {found_ct}/{total} in {st.session_state.final_time}s on the NFL Box Score Guesser! 🏈"
        url = "https://x.com/intent/tweet?text=" + urllib.parse.quote(share_text)
        st.markdown(f"<p style='text-align:center;'><a href='{url}' target='_blank'>Share on X</a></p>", unsafe_allow_html=True)

# =========================
# Stats sections
# =========================
def render_section(title, parser, cols):
    st.markdown(f"<h6 style='margin:3px 0;'>{title}</h6>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    df1 = build_df(patriots_stats, st.session_state.found, st.session_state.game_over, parser, cols)
    df2 = build_df(falcons_stats, st.session_state.found, st.session_state.game_over, parser, cols)

    def sort_df(df):
        sort_cols = [c for c in ["Yds", "TD"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols, ascending=[False]*len(sort_cols))
        return df.reset_index(drop=True)

    if not df1.empty:
        c1.markdown(df_to_html(sort_df(df1)), unsafe_allow_html=True)
    if not df2.empty:
        c2.markdown(df_to_html(sort_df(df2)), unsafe_allow_html=True)

render_section("Passing", parse_passing, ["Player","Cmp","Att","Yds","TD","INT"])
render_section("Rushing", parse_rushing, ["Player","CAR","Yds","TD"])
render_section("Receiving", parse_receiving, ["Player","REC","Yds","TD"])

# ===== Wrong guesses =====
if st.session_state.wrong:
    st.markdown("**❌ Wrong guesses:**", unsafe_allow_html=True)
    chips_html = "<div style='display:flex;flex-wrap:wrap;gap:4px;'>"
    for w in st.session_state.wrong:
        chips_html += f"<span style='background-color:#fdd; border:1px solid #f99; border-radius:10px; padding:1px 6px; font-size:11px;'>{w}</span>"
    chips_html += "</div>"
    st.markdown(chips_html, unsafe_allow_html=True)

# ===== Celebration =====
if not st.session_state.game_over and len(st.session_state.found) == len(all_players):
    st.balloons()
    st.success(f"🎉 All {len(all_players)} players in {int(time.time() - st.session_state.start_time)} seconds!")
    st.session_state.game_over = True
    st.session_state.final_time = int(time.time() - st.session_state.start_time)
