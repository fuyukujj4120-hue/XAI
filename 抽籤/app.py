import time
import requests
import streamlit as st

# =========================
# 基本設定
# =========================
APP_TITLE = "HCI 實驗分組抽籤系統"

# Google Apps Script 部署後的 /exec 網址
ASSIGNMENT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxvacTvKldHZhZwYElBHi9F8KzTM3OFEhJy1r5ZaGVDa48a7jOHBfVL2cI3B1VtTYZA/exec"

ASSIGNMENT_SECRET = "hci_group_assignment_secret"

GROUP_APP_URLS = {
    "A": "https://hci-group1.streamlit.app/",
    "B": "https://hci-group2.streamlit.app/",
}

GROUP_LABELS = {
    "A": "A 組｜特徵導向 → 情緒導向",
    "B": "B 組｜情緒導向 → 特徵導向",
}

GROUP_LIMIT_PER_HOUR = 16

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="✦",
    layout="centered",
)

# =========================
# CSS：黑白手繪風
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(0,0,0,0.035), transparent 26%),
            radial-gradient(circle at bottom right, rgba(0,0,0,0.04), transparent 30%),
            #f8f7f2;
        color: #111;
    }

    .main-container {
        max-width: 780px;
        margin: 0 auto;
        padding-top: 28px;
    }

    .hero-card {
        background: #fffefa;
        border: 2.5px solid #111;
        border-radius: 20px 24px 18px 26px;
        padding: 34px 34px 30px 34px;
        box-shadow: 8px 8px 0 #111;
        text-align: center;
        margin-bottom: 22px;
        transform: rotate(-0.2deg);
    }

    .slot-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 34px;
        font-weight: 900;
        color: #111;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .slot-subtitle {
        font-size: 15px;
        color: #333;
        line-height: 1.75;
        margin-bottom: 20px;
    }

    .slot-machine {
        background:
            repeating-linear-gradient(
                45deg,
                #fffefa,
                #fffefa 10px,
                #f0eee8 10px,
                #f0eee8 20px
            );
        border: 3px solid #111;
        border-radius: 26px 20px 28px 22px;
        padding: 22px;
        box-shadow: 5px 5px 0 #111;
        margin: 16px auto 20px auto;
        position: relative;
    }

    .slot-machine::before,
    .slot-machine::after {
        content: "";
        position: absolute;
        width: 14px;
        height: 14px;
        border: 2px solid #111;
        border-radius: 50%;
        background: #fffefa;
        top: 10px;
    }

    .slot-machine::before { left: 12px; }
    .slot-machine::after { right: 12px; }

    .slot-window {
        background: #fff;
        border: 3px solid #111;
        border-radius: 16px 20px 14px 18px;
        padding: 28px 18px;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 3px 3px 0 rgba(0,0,0,0.12);
    }

    .slot-reel {
        font-family: 'Noto Serif TC', serif;
        font-size: 42px;
        font-weight: 900;
        color: #111;
        letter-spacing: 0.08em;
    }

    .limit-card {
        background: #fffefa;
        border: 2px solid #111;
        border-radius: 18px 16px 20px 14px;
        padding: 16px 20px;
        color: #111;
        font-size: 14px;
        line-height: 1.8;
        margin-bottom: 18px;
        box-shadow: 4px 4px 0 #111;
        transform: rotate(0.15deg);
    }

    .result-card {
        background: #fffefa;
        border: 2.5px solid #111;
        border-radius: 22px 18px 24px 20px;
        padding: 26px 24px;
        text-align: center;
        box-shadow: 6px 6px 0 #111;
        margin-top: 22px;
    }

    .result-group {
        font-family: 'Noto Serif TC', serif;
        font-size: 36px;
        font-weight: 900;
        color: #111;
        margin-bottom: 8px;
    }

    .result-label {
        font-size: 19px;
        font-weight: 800;
        color: #111;
        margin-bottom: 14px;
    }

    .result-note {
        font-size: 14px;
        color: #333;
        line-height: 1.7;
        margin-bottom: 18px;
    }

    .error-card {
        background: #fffefa;
        border: 2.5px solid #111;
        border-radius: 18px 20px 16px 22px;
        padding: 18px 20px;
        color: #111;
        font-weight: 800;
        text-align: center;
        margin-top: 20px;
        box-shadow: 5px 5px 0 #111;
    }

    div[data-testid="stTextInput"] label {
        font-size: 17px !important;
        font-weight: 900 !important;
        color: #111 !important;
    }

    .stTextInput input {
        background: #fffefa !important;
        border: 2.5px solid #111 !important;
        border-radius: 12px 14px 10px 16px !important;
        color: #111 !important;
        font-size: 16px !important;
        padding: 12px 14px !important;
        box-shadow: 3px 3px 0 #111 !important;
    }

    .stButton > button {
        background: #fffefa !important;
        color: #111 !important;
        border: 2.5px solid #111 !important;
        border-radius: 999px !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        letter-spacing: 0.08em !important;
        padding: 13px 30px !important;
        box-shadow: 5px 5px 0 #111 !important;
        transition: all 0.12s ease !important;
    }

    .stButton > button:hover {
        transform: translate(2px, 2px);
        box-shadow: 3px 3px 0 #111 !important;
        background: #f0eee8 !important;
        color: #111 !important;
    }

    .stButton > button:disabled {
        opacity: 0.45 !important;
        box-shadow: 3px 3px 0 #111 !important;
    }

    .stLinkButton > a {
        background: #111 !important;
        color: #fffefa !important;
        border: 2.5px solid #111 !important;
        border-radius: 999px !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        padding: 12px 30px !important;
        text-decoration: none !important;
        box-shadow: 5px 5px 0 #777 !important;
    }

    .small-note {
        color: #444;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 工具函式
# =========================
def normalize_participant_id(value: str) -> str:
    """
    前端只做基本清理，不把學號轉成數字。
    例如 00123 會保持成字串 00123。
    """
    return str(value or "").strip()


def assign_group(participant_id: str):
    if not ASSIGNMENT_WEBHOOK_URL or "請貼上" in ASSIGNMENT_WEBHOOK_URL:
        raise ValueError("尚未設定 Apps Script Web App /exec URL")

    payload = {
        "secret": ASSIGNMENT_SECRET,
        "participant_id": normalize_participant_id(participant_id),
        "limit_per_group_per_hour": GROUP_LIMIT_PER_HOUR,
    }

    resp = requests.post(ASSIGNMENT_WEBHOOK_URL, json=payload, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "分組失敗"))

    return data


def render_slot_display(text="READY"):
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
    reels = ["A 組", "B 組", "✦", "A 組", "B 組", "✧", "A 組", "B 組"]

    for i in range(18):
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
        time.sleep(0.07 + i * 0.01)

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
    f"""
    <div class="hero-card">
        <div style="font-size:48px;margin-bottom:8px;">✦</div>
        <div class="slot-title">{APP_TITLE}</div>
        <div class="slot-subtitle">
            請輸入受試者代號後按下抽籤。系統會自動分配至 A 組或 B 組。<br>
            每一小時內 A 組與 B 組各最多 {GROUP_LIMIT_PER_HOUR} 人。
        </div>
    """,
    unsafe_allow_html=True,
)

render_slot_display("A / B")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="limit-card">
        <b>分組規則</b><br>
        1. 系統會在 A 組與 B 組之間隨機分配。<br>
        2. 每小時 A 組最多 {GROUP_LIMIT_PER_HOUR} 人，B 組最多 {GROUP_LIMIT_PER_HOUR} 人。<br>
        3. 相同受試者代號若已分配過，會直接回傳原本分配結果，不會重新抽籤。<br>
        4. 若其中一組額滿，系統會自動分配至另一組。
    </div>
    """,
    unsafe_allow_html=True,
)

participant_id_raw = st.text_input(
    "受試者學號／代號",
    placeholder="例如：S001 或 00123",
)

participant_id = normalize_participant_id(participant_id_raw)

col1, col2, col3 = st.columns([1, 1.4, 1])
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
                ⚠️ 抽籤失敗<br>
                {result.get("error")}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        assigned_group = result.get("assigned_group")
        label = result.get("label")
        app_url = result.get("app_url")
        is_existing = result.get("existing_assignment", False)

        existing_text = "此代號已分配過，以下為原本分配結果。" if is_existing else "抽籤完成，請依照分配結果進入實驗。"

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-group">你被分配到 {assigned_group} 組</div>
                <div class="result-label">{label}</div>
                <div class="result-note">
                    {existing_text}<br>
                    本小時目前人數：A 組 {result.get("count_a", "-")} 人，B 組 {result.get("count_b", "-")} 人。<br>
                    受試者代號：{result.get("participant_id", participant_id)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if app_url:
            st.link_button(
                "進入實驗頁面",
                app_url,
                use_container_width=True,
            )

st.markdown("</div>", unsafe_allow_html=True)
