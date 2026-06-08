import time
import requests
import streamlit as st

# =========================
# 基本設定
# =========================
APP_TITLE = "🐱 家貓情緒研究｜實驗分組抽籤"

ASSIGNMENT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxvacTvKldHZhZwYElBHi9F8KzTM3OFEhJy1r5ZaGVDa48a7jOHBfVL2cI3B1VtTYZA/exec"

ASSIGNMENT_SECRET = "hci_group_assignment_secret"

GROUP_APP_URLS = {
    "A": "https://0610-a.streamlit.app/",
    "B": "https://0610-b.streamlit.app/",
}

GROUP_LABELS = {
    "A": "A 組｜特徵導向 → 情緒導向",
    "B": "B 組｜情緒導向 → 特徵導向",
}

GROUP_LIMIT_PER_HOUR = 16

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🐱",
    layout="centered",
)

# =========================
# CSS：貓咪溫暖主題
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
            radial-gradient(circle at 15% 20%, rgba(230,126,34,0.08), transparent 35%),
            radial-gradient(circle at 85% 80%, rgba(192,57,43,0.06), transparent 35%),
            radial-gradient(circle at 50% 50%, rgba(245,176,118,0.04), transparent 60%),
            #fdf6ed;
        color: #3a1a00;
    }

    .main-container {
        max-width: 720px;
        margin: 0 auto;
        padding-top: 24px;
    }

    /* 貓爪裝飾用 */
    .paw-deco {
        font-size: 22px;
        opacity: 0.35;
        letter-spacing: 4px;
        margin-bottom: 6px;
    }

    .hero-card {
        background: linear-gradient(145deg, #fffaf4, #fff3e0);
        border: 2.5px solid #c0622a;
        border-radius: 28px 20px 26px 22px;
        padding: 32px 32px 28px 32px;
        box-shadow: 6px 6px 0 #e8a06a, 12px 12px 0 rgba(192,98,42,0.12);
        text-align: center;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }

    .hero-card::before {
        content: "🐾";
        position: absolute;
        top: -8px;
        right: 18px;
        font-size: 60px;
        opacity: 0.06;
        transform: rotate(15deg);
    }

    .slot-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 28px;
        font-weight: 900;
        color: #7a2d00;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }

    .slot-subtitle {
        font-size: 14.5px;
        color: #a0622a;
        line-height: 1.8;
        margin-bottom: 16px;
    }

    .slot-machine {
        background: linear-gradient(160deg, #fff8f0, #fdebd0);
        border: 2.5px solid #c0622a;
        border-radius: 22px 18px 24px 20px;
        padding: 18px;
        box-shadow: 4px 4px 0 #e8a06a;
        margin: 14px auto 18px auto;
        position: relative;
    }

    .slot-machine::before,
    .slot-machine::after {
        content: "🐾";
        position: absolute;
        top: 8px;
        font-size: 16px;
        opacity: 0.4;
    }

    .slot-machine::before { left: 10px; }
    .slot-machine::after  { right: 10px; }

    .slot-window {
        background: #fffbf5;
        border: 2px solid #c0622a;
        border-radius: 16px 18px 14px 16px;
        padding: 26px 18px;
        min-height: 110px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 2px 2px 6px rgba(192,98,42,0.1);
    }

    .slot-reel {
        font-family: 'Noto Serif TC', serif;
        font-size: 40px;
        font-weight: 900;
        color: #7a2d00;
        letter-spacing: 0.06em;
    }

    .limit-card {
        background: linear-gradient(145deg, #fff8f0, #fef0e0);
        border: 2px solid #e8a06a;
        border-left: 5px solid #e67e22;
        border-radius: 14px 16px 12px 18px;
        padding: 16px 20px;
        color: #6b3500;
        font-size: 14px;
        line-height: 1.9;
        margin-bottom: 18px;
        box-shadow: 3px 3px 0 rgba(230,126,34,0.18);
    }

    .result-card {
        background: linear-gradient(145deg, #fff8f0, #fdebd0);
        border: 2.5px solid #c0622a;
        border-radius: 24px 18px 22px 20px;
        padding: 28px 24px;
        text-align: center;
        box-shadow: 6px 6px 0 #e8a06a;
        margin-top: 22px;
    }

    .result-group {
        font-family: 'Noto Serif TC', serif;
        font-size: 34px;
        font-weight: 900;
        color: #7a2d00;
        margin-bottom: 6px;
    }

    .result-label {
        font-size: 18px;
        font-weight: 800;
        color: #c0622a;
        margin-bottom: 14px;
    }

    .result-note {
        font-size: 14px;
        color: #8b4500;
        line-height: 1.8;
        margin-bottom: 18px;
        background: rgba(255,255,255,0.6);
        border-radius: 10px;
        padding: 12px 16px;
    }

    .error-card {
        background: #fff8f0;
        border: 2px solid #c0622a;
        border-radius: 14px;
        padding: 18px 20px;
        color: #7a2d00;
        font-weight: 800;
        text-align: center;
        margin-top: 20px;
        box-shadow: 4px 4px 0 rgba(192,98,42,0.2);
    }

    div[data-testid="stTextInput"] label {
        font-size: 16px !important;
        font-weight: 900 !important;
        color: #7a2d00 !important;
    }

    .stTextInput input {
        background: #fffaf4 !important;
        border: 2px solid #c0622a !important;
        border-radius: 12px !important;
        color: #3a1a00 !important;
        font-size: 16px !important;
        padding: 12px 14px !important;
        box-shadow: 3px 3px 0 rgba(192,98,42,0.15) !important;
    }

    .stTextInput input:focus {
        border-color: #e67e22 !important;
        box-shadow: 3px 3px 0 rgba(230,126,34,0.3) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #e67e22, #c0392b) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 999px !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        letter-spacing: 0.06em !important;
        padding: 13px 30px !important;
        box-shadow: 4px 4px 0 rgba(192,57,43,0.35) !important;
        transition: all 0.12s ease !important;
    }

    .stButton > button:hover {
        transform: translate(1px, 1px);
        box-shadow: 3px 3px 0 rgba(192,57,43,0.35) !important;
        opacity: 0.92;
    }

    .stButton > button:disabled {
        background: linear-gradient(135deg, #e8c4a0, #d4a08a) !important;
        opacity: 0.6 !important;
        box-shadow: 2px 2px 0 rgba(0,0,0,0.1) !important;
    }

    .stLinkButton > a {
        background: linear-gradient(135deg, #e67e22, #c0392b) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 999px !important;
        font-size: 17px !important;
        font-weight: 900 !important;
        padding: 12px 30px !important;
        text-decoration: none !important;
        box-shadow: 4px 4px 0 rgba(192,57,43,0.3) !important;
    }

    .small-note {
        color: #a06030;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 8px;
    }

    .cat-ears {
        font-size: 32px;
        line-height: 1;
        margin-bottom: -4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 工具函式
# =========================
def normalize_participant_id(value: str) -> str:
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


def render_slot_display(text="😺 / 😸"):
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
    reels = ["😺 A 組", "😸 B 組", "🐾", "😺 A 組", "😸 B 組", "🐱", "A 組", "B 組", "🐾"]

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
    f"""
    <div class="hero-card">
        <div class="paw-deco">🐾 🐾 🐾</div>
        <div class="cat-ears">🐱</div>
        <div class="slot-title">家貓情緒研究<br>實驗分組抽籤</div>
        <div class="slot-subtitle">
            請輸入受試者代號後按下抽籤。<br>
            系統會自動將您分配至 A 組或 B 組。<br>
            每小時內 A 組與 B 組各最多 {GROUP_LIMIT_PER_HOUR} 人。
        </div>
    """,
    unsafe_allow_html=True,
)

render_slot_display("A 組 ／ B 組")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="limit-card">
        🐾 <b>分組規則</b><br>
        1. 系統在 A 組與 B 組之間隨機分配，確保兩組人數平衡。<br>
        2. 每小時 A 組最多 {GROUP_LIMIT_PER_HOUR} 人，B 組最多 {GROUP_LIMIT_PER_HOUR} 人。<br>
        3. 相同受試者代號若已分配過，會直接回傳原本分配結果。<br>
        4. 若其中一組額滿，系統會自動分配至另一組。
    </div>
    """,
    unsafe_allow_html=True,
)

participant_id_raw = st.text_input(
    "🐱 受試者學號／代號",
    placeholder="例如：S001 或 00123",
)

participant_id = normalize_participant_id(participant_id_raw)

col1, col2, col3 = st.columns([1, 1.6, 1])
with col2:
    draw_clicked = st.button(
        "🐾 開始抽籤",
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

        cat_emoji = "😺" if assigned_group == "A" else "😸"

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
                    <div class="slot-reel">{cat_emoji} {assigned_group} 組</div>
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
                😿 抽籤失敗<br>
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

        cat_emoji = "😺" if assigned_group == "A" else "😸"
        existing_text = "😸 此代號已分配過，以下為原本分配結果。" if is_existing else "🎉 抽籤完成！請點擊下方按鈕進入實驗。"

        st.markdown(
            f"""
            <div class="result-card">
                <div style="font-size:52px;margin-bottom:6px;">{cat_emoji}</div>
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
                f"🐾 進入 {assigned_group} 組實驗頁面",
                app_url,
                use_container_width=True,
            )

st.markdown("</div>", unsafe_allow_html=True)
