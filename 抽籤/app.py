import time
import requests
import streamlit as st

# =========================
# 基本設定
# =========================
APP_TITLE = "實驗分組抽籤"

ASSIGNMENT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxvacTvKldHZhZwYElBHi9F8KzTM3OFEhJy1r5ZaGVDa48a7jOHBfVL2cI3B1VtTYZA/exec"
ASSIGNMENT_SECRET = "hci_group_assignment_secret"

GROUP_APP_URLS = {
    "A": "https://0610-a.streamlit.app/",
    "B": "https://0610-b.streamlit.app/",
}



# 不再使用每小時限制。若後端 Apps Script 仍要求 limit 欄位，傳入極大值作為不限制。
NO_LIMIT_VALUE = 999999

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🐱",
    layout="centered",
)

# =========================
# CSS：黑白手繪風格
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

    :root {
        --ink: #111111;
        --paper: #fbfbf7;
        --paper-2: #f0f0ea;
        --gray: #6b6b6b;
        --line: #111111;
        --shadow: rgba(0,0,0,0.18);
    }

    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 12%, rgba(0,0,0,0.035), transparent 28%),
            radial-gradient(circle at 85% 22%, rgba(0,0,0,0.025), transparent 25%),
            radial-gradient(circle at 40% 86%, rgba(0,0,0,0.03), transparent 30%),
            repeating-linear-gradient(
                0deg,
                rgba(0,0,0,0.018) 0px,
                rgba(0,0,0,0.018) 1px,
                transparent 1px,
                transparent 6px
            ),
            var(--paper);
        color: var(--ink);
    }

    .main-container {
        max-width: 760px;
        margin: 0 auto;
        padding: 26px 6px 40px 6px;
    }

    .sketch-card {
        background: var(--paper);
        border: 2.5px solid var(--line);
        border-radius: 28px 18px 30px 20px;
        box-shadow: 8px 8px 0 var(--ink);
        position: relative;
    }

    .sketch-card::before {
        content: "";
        position: absolute;
        inset: 8px -8px -8px 8px;
        border: 1.5px dashed rgba(0,0,0,0.22);
        border-radius: 28px 18px 30px 20px;
        pointer-events: none;
        z-index: -1;
    }

    .hero-card {
        padding: 34px 32px 30px 32px;
        text-align: center;
        margin-bottom: 22px;
        overflow: hidden;
    }

    .hero-card::after {
        content: "CAT";
        position: absolute;
        right: -18px;
        top: 16px;
        font-family: 'Noto Serif TC', serif;
        font-size: 72px;
        font-weight: 900;
        color: rgba(0,0,0,0.045);
        transform: rotate(10deg);
        letter-spacing: 0.06em;
    }

    .paw-deco {
        font-size: 20px;
        opacity: 0.8;
        letter-spacing: 6px;
        margin-bottom: 8px;
        color: var(--ink);
    }

    .cat-ears {
        font-size: 36px;
        line-height: 1;
        filter: grayscale(1);
        margin-bottom: 4px;
    }

    .slot-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 30px;
        font-weight: 900;
        color: var(--ink);
        letter-spacing: 0.06em;
        line-height: 1.35;
        margin-bottom: 10px;
    }

    .slot-subtitle {
        font-size: 14.5px;
        color: #333333;
        line-height: 1.85;
        margin-bottom: 18px;
    }

    .slot-machine {
        background: var(--paper-2);
        border: 2.5px solid var(--line);
        border-radius: 22px 16px 24px 18px;
        padding: 18px;
        box-shadow: 5px 5px 0 var(--ink);
        margin: 16px auto 20px auto;
        position: relative;
        transform: rotate(-0.4deg);
    }

    .slot-machine::before,
    .slot-machine::after {
        content: "●";
        position: absolute;
        top: 8px;
        font-size: 12px;
        color: var(--ink);
    }

    .slot-machine::before { left: 12px; }
    .slot-machine::after  { right: 12px; }

    .slot-window {
        background: #ffffff;
        border: 2px solid var(--line);
        border-radius: 16px 18px 14px 16px;
        padding: 28px 18px;
        min-height: 112px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 3px 3px 0 rgba(0,0,0,0.08);
    }

    .slot-reel {
        font-family: 'Noto Serif TC', serif;
        font-size: 42px;
        font-weight: 900;
        color: var(--ink);
        letter-spacing: 0.06em;
        filter: grayscale(1);
    }

    .rule-card {
        background: #ffffff;
        border: 2px solid var(--line);
        border-left: 8px solid var(--line);
        border-radius: 16px 14px 18px 12px;
        padding: 18px 20px;
        color: var(--ink);
        font-size: 14px;
        line-height: 1.95;
        margin: 22px 0 20px 0;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.16);
    }

    .rule-card b {
        font-family: 'Noto Serif TC', serif;
        font-size: 16px;
        letter-spacing: 0.03em;
    }

    .result-card {
        background: #ffffff;
        border: 2.5px solid var(--line);
        border-radius: 24px 16px 24px 18px;
        padding: 30px 24px;
        text-align: center;
        box-shadow: 8px 8px 0 var(--ink);
        margin-top: 24px;
        position: relative;
    }

    .result-card::before {
        content: "RESULT";
        position: absolute;
        left: 18px;
        top: 12px;
        font-size: 11px;
        letter-spacing: 0.18em;
        font-weight: 900;
        color: #555;
    }

    .result-group {
        font-family: 'Noto Serif TC', serif;
        font-size: 36px;
        font-weight: 900;
        color: var(--ink);
        margin-bottom: 8px;
    }

    .result-label {
        font-size: 18px;
        font-weight: 900;
        color: var(--ink);
        margin-bottom: 16px;
    }

    .result-note {
        font-size: 14px;
        color: #222;
        line-height: 1.85;
        margin-bottom: 18px;
        background: #f5f5f1;
        border: 1.8px dashed var(--ink);
        border-radius: 12px;
        padding: 13px 16px;
    }

    .error-card {
        background: #ffffff;
        border: 2.5px solid var(--line);
        border-radius: 14px;
        padding: 18px 20px;
        color: var(--ink);
        font-weight: 900;
        text-align: center;
        margin-top: 20px;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.18);
    }

    div[data-testid="stTextInput"] label {
        font-size: 16px !important;
        font-weight: 900 !important;
        color: var(--ink) !important;
    }

    .stTextInput input {
        background: #ffffff !important;
        border: 2px solid var(--ink) !important;
        border-radius: 14px !important;
        color: var(--ink) !important;
        font-size: 16px !important;
        padding: 13px 14px !important;
        box-shadow: 4px 4px 0 rgba(0,0,0,0.16) !important;
    }

    .stTextInput input:focus {
        border-color: var(--ink) !important;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.25) !important;
        outline: none !important;
    }

    .stButton > button {
        background: var(--ink) !important;
        color: #ffffff !important;
        border: 2px solid var(--ink) !important;
        border-radius: 999px !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        letter-spacing: 0.06em !important;
        padding: 13px 30px !important;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.22) !important;
        transition: all 0.12s ease !important;
    }

    .stButton > button:hover {
        transform: translate(1px, 1px) rotate(-0.3deg);
        box-shadow: 3px 3px 0 rgba(0,0,0,0.22) !important;
        background: #2b2b2b !important;
    }

    .stButton > button:disabled {
        background: #bfbfbf !important;
        border-color: #bfbfbf !important;
        color: #ffffff !important;
        opacity: 0.7 !important;
        box-shadow: 2px 2px 0 rgba(0,0,0,0.12) !important;
    }

    .stLinkButton > a {
        background: var(--ink) !important;
        color: #ffffff !important;
        border: 2px solid var(--ink) !important;
        border-radius: 999px !important;
        font-size: 17px !important;
        font-weight: 900 !important;
        padding: 12px 30px !important;
        text-decoration: none !important;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.22) !important;
    }

    .small-note {
        color: #444;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 8px;
    }

    @media (max-width: 640px) {
        .main-container {
            padding: 14px 2px 32px 2px;
        }

        .hero-card {
            padding: 26px 20px 24px 20px;
            border-radius: 22px 16px 24px 18px;
            box-shadow: 5px 5px 0 var(--ink);
        }

        .slot-title {
            font-size: 24px;
        }

        .slot-reel {
            font-size: 34px;
        }

        .slot-window {
            min-height: 92px;
            padding: 22px 12px;
        }

        .result-group {
            font-size: 30px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 工具函式
# =========================
def normalize_participant_id(value: str) -> str:
    """保留前導 0，僅去除前後空白。"""
    return str(value or "").strip()


def assign_group(participant_id: str):
    if not ASSIGNMENT_WEBHOOK_URL or "請貼上" in ASSIGNMENT_WEBHOOK_URL:
        raise ValueError("尚未設定 Apps Script Web App /exec URL")

    payload = {
        "secret": ASSIGNMENT_SECRET,
        "participant_id": normalize_participant_id(participant_id),
        # 不再限制每小時；保留此欄位是為了相容舊 Apps Script。
        "limit_per_group_per_hour": NO_LIMIT_VALUE,
        # 若 Apps Script 已改版，可用這兩個欄位判斷全時間統計。
        "limit_scope": "all_time",
        "count_scope": "all_time",
    }

    resp = requests.post(ASSIGNMENT_WEBHOOK_URL, json=payload, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "分組失敗"))

    return data


def render_slot_display(text="A 組 ／ B 組"):
    st.markdown(
        f"""
        <div class="slot-machine">
            <div class="slot-window">
                <div class="slot-reel">{text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def slot_animation():
    placeholder = st.empty()
    reels = ["A 組", "B 組", "◇", "A 組", "B 組", "◆", "A 組", "B 組", "◇"]

    for i in range(20):
        text = reels[i % len(reels)]
        placeholder.markdown(
            f"""
            <div class="slot-machine">
                <div class="slot-window">
                    <div class="slot-reel">{text}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.07 + i * 0.012)

    return placeholder


# =========================
# Session State
# =========================
if "assigned_result" not in st.session_state:
    st.session_state.assigned_result = None

if "last_participant_id" not in st.session_state:
    st.session_state.last_participant_id = ""


# =========================
# UI
# =========================
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero-card sketch-card">
        <div class="paw-deco">◇ ◆ ◇</div>
        <div class="cat-ears">🐱</div>
        <div class="slot-title"><br>實驗分組抽籤</div>
        <div class="slot-subtitle">
            請輸入受試者代號後按下抽籤。<br>
            系統會自動將您分配至 A 組或 B 組。<br>
            相同受試者代號若已分配過，會直接回傳原本的分配結果。
        </div>
    """,
    unsafe_allow_html=True,
)

render_slot_display("A 組 ／ B 組")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="rule-card">
        <b>分組規則</b><br>
        1. 系統在 A 組與 B 組之間分配，盡量維持兩組總人數平衡。<br>
        2. 本版本不再限制每小時人數，會以所有已登記資料作為分組依據。<br>
        3. 相同受試者代號若已分配過，會直接回傳原本分配結果。<br>
        4. 請確認代號輸入正確，避免重複或錯誤分配。
    </div>
    """,
    unsafe_allow_html=True,
)

participant_id_raw = st.text_input(
    "受試者學號／代號",
    placeholder="例如：S001 或 00123",
)

participant_id = normalize_participant_id(participant_id_raw)

col1, col2, col3 = st.columns([1, 1.6, 1])
with col2:
    draw_clicked = st.button(
        "開始抽籤",
        type="primary",
        use_container_width=True,
        disabled=not bool(participant_id),
    )

if draw_clicked:
    try:
        slot_placeholder = slot_animation()
        result = assign_group(participant_id)

        assigned_group = result.get("assigned_group")
        label = GROUP_LABELS.get(assigned_group, assigned_group)
        app_url = GROUP_APP_URLS.get(assigned_group, "")

        st.session_state.assigned_result = {
            **result,
            "label": label,
            "app_url": app_url,
        }
        st.session_state.last_participant_id = participant_id

        slot_placeholder.markdown(
            f"""
            <div class="slot-machine">
                <div class="slot-window">
                    <div class="slot-reel">{assigned_group} 組</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.session_state.assigned_result = {
            "error": str(e)
        }

result = st.session_state.assigned_result

if result:
    if result.get("error"):
        st.markdown(
            f"""
            <div class="error-card">
                抽籤失敗<br>
                <span style="font-weight:400;font-size:13px;">{result.get("error")}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        assigned_group = result.get("assigned_group")
        label = result.get("label")
        app_url = result.get("app_url")
        is_existing = result.get("existing_assignment", False)

        existing_text = "此代號已分配過，以下為原本分配結果。" if is_existing else "抽籤完成，請點擊下方按鈕進入實驗。"

        count_a = result.get("count_a", result.get("total_a", "-"))
        count_b = result.get("count_b", result.get("total_b", "-"))

        st.markdown(
            f"""
            <div class="result-card">
                <div style="font-size:42px;margin-bottom:6px;filter:grayscale(1);">🐱</div>
                <div class="result-group">你被分配到 {assigned_group} 組</div>
                <div class="result-label">{label}</div>
                <div class="result-note">
                    {existing_text}<br>
                    目前累計人數：A 組 {count_a} 人，B 組 {count_b} 人。<br>
                    受試者代號：{result.get("participant_id", participant_id)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if app_url:
            st.link_button(
                f"進入 {assigned_group} 組實驗頁面",
                app_url,
                use_container_width=True,
            )

st.markdown("</div>", unsafe_allow_html=True)

