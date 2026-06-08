import json
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

APP_PAGE_TITLE = "🐱 家貓情緒標註系統｜第 2 組"
OUTPUT_CSV = Path("hci_cat_annotation_group2.csv")
GROUP_ID = "2"
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
if not IMAGE_DIR.exists():
    IMAGE_DIR = BASE_DIR.parent / "images"
ANNOTATION_DIR = BASE_DIR / "annotations"
if not ANNOTATION_DIR.exists():
    ANNOTATION_DIR = BASE_DIR.parent / "annotations"

SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyMDrGh8WRV-ZyuEFY8uzmVASLSm9JEfZC4pqqGg398KFT8uKWBpNXaLO-9NGGqM17vLQ/exec"
SHEET_SECRET = "hci_cat_annotation_secret"

IMAGE_SET_1 = [
    {"image_id": "set1_001", "path": str(ANNOTATION_DIR / "video9_frame_0.jpg")},
    {"image_id": "set1_002", "path": str(ANNOTATION_DIR / "video61_frame_5.jpg")},
    {"image_id": "set1_003", "path": str(ANNOTATION_DIR / "video39_frame_14.jpg")},
]

IMAGE_SET_2 = [
    {"image_id": "set2_001", "path": str(ANNOTATION_DIR / "video30_frame_3.jpg")},
    {"image_id": "set2_002", "path": str(ANNOTATION_DIR / "video10_frame_4.jpg")},
    {"image_id": "set2_003", "path": str(ANNOTATION_DIR / "00000001_016.jpg")},
]

STAGE_PLAN = [
    {
        "stage_name": "第一階段",
        "flow_type": "B",
        "flow_name": "情緒導向",
        "photo_set_name": "照片組 1",
        "images": IMAGE_SET_1,
        "description": "先選擇初步情緒，再檢查部位特徵，最後確認或修改情緒。",
    },
    {
        "stage_name": "第二階段",
        "flow_type": "A",
        "flow_name": "特徵導向",
        "photo_set_name": "照片組 2",
        "images": IMAGE_SET_2,
        "description": "先標註眼睛、耳朵、尾巴、身體姿勢，再選擇最終情緒。",
    },
]

# ── 情緒定義（含圖片路徑）──
EMOTION_SCHEMA = {
    "害怕": {
        "icon": "😿",
        "definition": "由立即感知到的危險或危險的威脅引起的，表現為警惕和試圖撤退或逃跑。",
        "image": IMAGE_DIR / "fear.png",
    },
    "憤怒": {
        "icon": "😾",
        "definition": "由執行行動/實現目標的願望受挫或資源競爭引起，表現為攻擊性或攻擊威脅。",
        "image": IMAGE_DIR / "anger.png",
    },
    "歡樂/玩耍": {
        "icon": "😺",
        "definition": "表現為非功能性行為，包括運動遊戲、社交遊戲或物件遊戲。",
        "image": IMAGE_DIR / "joy.png",
    },
    "滿意": {
        "icon": "😽",
        "definition": "由需求和願望得到滿足而產生的正向情緒狀態，表現為休息、平靜和親和。",
        "image": IMAGE_DIR / "contentment.png",
    },
    "好奇": {
        "icon": "🐾",
        "definition": "由新奇或顯著刺激引起，表現為注意、定向或探索行為。",
        "image": IMAGE_DIR / "interest.png",
    },
    "中性": {
        "icon": "➖",
        "definition": "不明顯屬於特定情緒，偏中性、休息或日常活動的狀態。",
        "image": None,
    },
}

# 對應到 EMOTION_OPTIONS 的情緒定義查詢（做彈性映射）
EMOTION_OPTIONS = [
    "害怕",
    "憤怒",
    "歡樂/玩耍",
    "滿意",
    "好奇",
    "中性",
    "其他／無法判斷",
]

EMOTION_ICONS = {
    "害怕": "😿",
    "憤怒": "😾",
    "滿意": "😽",
    "好奇": "🐾",
    "中性": "➖",
    "其他／無法判斷": "❓",
    "歡樂/玩耍": "😺",
}

FEATURE_OPTIONS = {
    "眼睛": [
        "睜大",
        "半睜／放鬆",
        "緊閉",
        "瞳孔放大",
        "直視",
        "避免眼神接觸",
        "無法辨識",
        "其他",
    ],
    "耳朵": [
        "直立",
        "朝向刺激物",
        "側向",
        "壓平",
        "無法辨識",
        "其他",
    ],
    "尾巴": [
        "豎起",
        "水平",
        "放鬆",
        "夾起",
        "壓低僵硬",
        "快速甩動",
        "無法辨識",
        "其他",
    ],
    "身體／姿勢": [
        "放鬆",
        "緊繃",
        "壓低",
        "前傾",
        "拱背",
        "炸毛",
        "發抖／僵硬",
        "姿勢變化頻繁",
        "無法辨識",
        "其他",
    ],
}

UNCERTAIN_REASONS = [
    "影像品質不足",
    "線索不足",
    "多種情緒並存",
    "超出現有分類",
    "其他",
]

st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

    /* ── Global reset & base ── */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }

    /* Subtle warm parchment background */
    .stApp {
        background: #f7f4ef;
    }

    /* ── Main title ── */
    .main-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 26px;
        font-weight: 700;
        color: #1a1208;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
        line-height: 1.35;
    }

    /* ── Headings override ── */
    h2 {
        font-family: 'Noto Serif TC', serif !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #2c1f0e !important;
        letter-spacing: 0.03em !important;
        margin-top: 28px !important;
        margin-bottom: 10px !important;
        padding-bottom: 6px;
        border-bottom: 2px solid #d4b896;
    }

    h3 {
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #4a3520 !important;
        letter-spacing: 0.04em !important;
        margin-top: 20px !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
    }

    h4 {
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #5c4433 !important;
        margin-top: 14px !important;
        margin-bottom: 6px !important;
    }

    /* ── Subtitle ── */
    .sub-title {
        color: #7a6650;
        font-size: 14px;
        font-weight: 300;
        margin-bottom: 24px;
        letter-spacing: 0.02em;
    }

    /* ── Cards ── */
    .flow-card {
        padding: 16px 20px;
        border: 1px solid #e0d4c0;
        border-left: 4px solid #c9a96e;
        border-radius: 4px;
        background: #fffdf8;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(180,140,80,0.07);
        transition: box-shadow 0.2s;
        font-size: 14px;
        line-height: 1.7;
        color: #3b2e1e;
    }

    .flow-card:hover {
        box-shadow: 0 3px 12px rgba(180,140,80,0.14);
    }

    .active-card {
        padding: 14px 20px;
        border: 1.5px solid #b07d3a;
        border-left: 5px solid #b07d3a;
        border-radius: 4px;
        background: linear-gradient(135deg, #fffdf5 0%, #fff8e8 100%);
        margin-bottom: 16px;
        box-shadow: 0 2px 10px rgba(176,125,58,0.12);
        font-size: 14px;
        line-height: 1.7;
        color: #3b2e1e;
    }

    /* ── Warning box ── */
    .warn-box {
        padding: 12px 16px;
        border-radius: 4px;
        background: #fffbf0;
        border: 1px solid #e8c76d;
        border-left: 4px solid #e8a800;
        margin: 10px 0 16px 0;
        font-size: 13px;
        color: #5a4000;
    }

    /* ── Placeholder image area ── */
    .placeholder {
        height: 400px;
        border: 1.5px dashed #c9b08a;
        border-radius: 8px;
        background: linear-gradient(160deg, #faf6ef 0%, #f0e9db 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #9e8060;
        font-size: 16px;
        font-weight: 500;
        text-align: center;
        padding: 20px;
        letter-spacing: 0.04em;
    }

    /* ── Emotion definition card (sidebar) ── */
    .emotion-def-card {
        background: #fffdf8;
        border: 1px solid #e0d4c0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #3b2e1e;
        line-height: 1.6;
    }

    .emotion-def-card .emotion-icon {
        font-size: 22px;
        margin-right: 6px;
    }

    .emotion-def-card .emotion-name {
        font-size: 15px;
        font-weight: 700;
        color: #4a3520;
    }

    .emotion-def-card .emotion-def-text {
        margin-top: 6px;
        color: #5c4433;
        font-size: 12.5px;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        width: 480px !important;
        min-width: 480px !important;
        background: #fdf9f3 !important;
        border-right: 1px solid #e0d4c0;
    }

    section[data-testid="stSidebar"] img {
        max-height: 480px;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(140,100,40,0.15);
    }

    section[data-testid="stSidebar"] h3 {
        color: #4a3520 !important;
        border-bottom: 1px solid #e0d4c0 !important;
        padding-bottom: 6px;
        text-transform: none !important;
    }

    /* ── Streamlit widget tweaks ── */
    div[data-testid="stRadio"] > label {
        font-size: 14px !important;
        color: #3b2e1e !important;
    }

    div[data-testid="stRadio"] > div {
        gap: 6px !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #b07d3a 0%, #8c5f20 100%) !important;
        color: #fffdf8 !important;
        border: none !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 8px rgba(140,95,32,0.25) !important;
        transition: all 0.2s !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(140,95,32,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary / default button */
    .stButton > button:not([kind="primary"]) {
        background: #fffdf8 !important;
        color: #5c4433 !important;
        border: 1.5px solid #c9a96e !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 13px !important;
        transition: all 0.2s !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: #f5ede0 !important;
        border-color: #b07d3a !important;
    }

    /* Text input */
    .stTextInput input, .stTextArea textarea {
        background: #fffdf8 !important;
        border: 1.5px solid #d4c4a8 !important;
        border-radius: 4px !important;
        color: #1a1208 !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 14px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #b07d3a !important;
        box-shadow: 0 0 0 3px rgba(176,125,58,0.12) !important;
    }

    /* Divider */
    hr {
        border-color: #e0d4c0 !important;
        margin: 16px 0 !important;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 4px !important;
        font-size: 13px !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #fffdf8 !important;
        color: #5c4433 !important;
        border: 1.5px solid #c9a96e !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 13px !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f0e9db; }
    ::-webkit-scrollbar-thumb { background: #c9a96e; border-radius: 3px; }

    /* Sidebar emotion quick view buttons */
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        border-radius: 8px !important;
        font-size: 13px !important;
        padding: 7px 10px !important;
        transition: all 0.15s !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #f5ede0 !important;
        border-color: #b07d3a !important;
        color: #8c5f20 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Dialog：情緒定義快速查看（只顯示定義與圖片，不顯示特徵）──
@st.dialog("情緒定義")
def show_emotion_dialog(emotion_name: str):
    item = EMOTION_SCHEMA.get(emotion_name)
    if not item:
        st.warning("找不到此情緒的定義。")
        return
    icon = item.get("icon", "")
    st.markdown(
        f'<div style="font-size:22px;font-weight:800;color:#4a3520;margin-bottom:8px;">'
        f'{icon} {emotion_name}</div>',
        unsafe_allow_html=True,
    )
    img_path = item.get("image")
    if img_path and Path(img_path).exists():
        st.image(str(img_path), width=260)
    st.markdown(f"**定義：** {item['definition']}")


def get_stage_plan():
    return STAGE_PLAN


def init_state():
    defaults = {
        "participant_id": "",
        "page": "intro",
        "stage_index": 0,
        "image_index": 0,
        "task_start_time": None,
        "pending_stage_records": [],
        "pending_cloud_rows": [],
        "cloud_sync_attempted": False,
        "last_save_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_stage():
    return get_stage_plan()[st.session_state.stage_index]


def current_image():
    stage = current_stage()
    images = stage["images"]
    if st.session_state.image_index >= len(images):
        return None
    return images[st.session_state.image_index]


def reset_task_timer():
    st.session_state.task_start_time = time.time()


def request_scroll_to_top():
    st.session_state["scroll_to_top"] = True


def do_scroll_to_top_if_needed():
    if st.session_state.pop("scroll_to_top", False):
        components.html(
            """
            <script>
            function forceScrollToTop() {
                try {
                    const doc = window.parent.document;

                    // 1) 先處理瀏覽器本身的捲動
                    window.parent.scrollTo(0, 0);
                    doc.documentElement.scrollTop = 0;
                    doc.body.scrollTop = 0;

                    // 2) Streamlit 不同版本的主要捲動容器可能不同，全部嘗試歸零
                    const selectors = [
                        'section.main',
                        'section[data-testid="stAppViewContainer"]',
                        'div[data-testid="stAppViewContainer"]',
                        'div[data-testid="stVerticalBlock"]',
                        'main',
                        '.stApp'
                    ];

                    selectors.forEach((selector) => {
                        doc.querySelectorAll(selector).forEach((el) => {
                            try {
                                el.scrollTop = 0;
                                if (el.scrollTo) {
                                    el.scrollTo({ top: 0, left: 0, behavior: "auto" });
                                }
                            } catch (e) {}
                        });
                    });

                    // 3) 最保險：把所有可捲動的主要區塊都拉回頂端
                    doc.querySelectorAll('section, main, div').forEach((el) => {
                        try {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop = 0;
                            }
                        } catch (e) {}
                    });

                } catch (e) {}
            }

            forceScrollToTop();
            setTimeout(forceScrollToTop, 50);
            setTimeout(forceScrollToTop, 150);
            setTimeout(forceScrollToTop, 300);
            setTimeout(forceScrollToTop, 600);
            setTimeout(forceScrollToTop, 1000);
            setTimeout(forceScrollToTop, 1500);
            </script>
            """,
            height=0,
        )


def clear_temp_csv_and_session_records():
    try:
        if OUTPUT_CSV.exists():
            OUTPUT_CSV.unlink()
    except Exception as e:
        st.warning(f"暫存 CSV 無法刪除：{e}")

    st.session_state.pending_stage_records = []
    st.session_state.pending_cloud_rows = []
    st.session_state.cloud_sync_attempted = False
    st.session_state.last_save_message = ""


def reset_all():
    st.session_state.page = "intro"
    st.session_state.stage_index = 0
    st.session_state.image_index = 0
    st.session_state.task_start_time = None
    st.session_state.pending_stage_records = []
    st.session_state.pending_cloud_rows = []
    st.session_state.cloud_sync_attempted = False
    st.session_state.last_save_message = ""


def append_records_to_google_sheet(records):
    if not SHEET_WEBHOOK_URL.strip():
        return False, "尚未設定 SHEET_WEBHOOK_URL，因此只儲存本機 CSV。"

    payload = {
        "secret": SHEET_SECRET,
        "records": records,
    }
    resp = requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "Unknown Google Sheet error"))
    return True, f"已同步 {data.get('inserted', len(records))} 筆到 Google Sheet。"


DATA_COLUMNS = [
    "group_id",
    "stage_name",
    "photo_set_name",
    "participant_id",
    "flow_type",
    "image_id",
    "initial_emotion",
    "selected_features",
    "final_emotion",
    "uncertain_reason",
    "uncertain_other_text",
    "confidence",
    "annotation_time",
    "emotion_changed",
    "workload_q1",
    "workload_q2",
    "workload_q3",
    "confidence_q1",
    "confidence_q2",
    "confidence_q3",
    "clarity_score",
    "usefulness_score",
    "intention_score",
    "open_feedback",
]


def save_records(records):
    rows = [{col: record.get(col, "") for col in DATA_COLUMNS} for record in records]
    df_new = pd.DataFrame(rows, columns=DATA_COLUMNS)

    if OUTPUT_CSV.exists():
        df_old = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        for col in DATA_COLUMNS:
            if col not in df_old.columns:
                df_old[col] = ""
        df_old = df_old[DATA_COLUMNS]
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = df_all[DATA_COLUMNS]
    df_all.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    st.session_state.setdefault("pending_cloud_rows", []).extend(rows)


def sync_to_cloud():
    rows = st.session_state.get("pending_cloud_rows", [])
    if not rows:
        return True, "沒有需要同步的資料。"

    ok, msg = append_records_to_google_sheet(rows)
    if ok:
        st.session_state["pending_cloud_rows"] = []
    st.session_state["last_save_message"] = msg
    return ok, msg


def go_previous_page():
    page = st.session_state.get("page", "intro")

    if page == "task":
        if st.session_state.image_index > 0:
            st.session_state.image_index -= 1
            if st.session_state.pending_stage_records:
                st.session_state.pending_stage_records.pop()
            reset_task_timer()
        elif st.session_state.stage_index > 0:
            st.session_state.stage_index -= 1
            prev_stage = get_stage_plan()[st.session_state.stage_index]
            st.session_state.image_index = max(len(prev_stage["images"]) - 1, 0)
            st.session_state.page = "task"
            reset_task_timer()
        else:
            st.session_state.page = "intro"

    elif page == "stage_questionnaire":
        stage = current_stage()
        st.session_state.page = "task"
        st.session_state.image_index = max(len(stage["images"]) - 1, 0)
        reset_task_timer()

    elif page == "done":
        st.session_state.page = "stage_questionnaire"

    else:
        st.session_state.page = "intro"

    request_scroll_to_top()
    st.rerun()


def render_back_button():
    if st.session_state.get("page") != "intro":
        if st.button("← 上一頁"):
            go_previous_page()


def render_placeholder(image_id):
    st.markdown(
        f'<div class="placeholder">圖片預覽區<br>目前尚未放入實際照片<br>image_id：{image_id}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_image():
    with st.sidebar:
        stage = current_stage()
        image = current_image()
        st.markdown("### 家貓照片")
        st.caption(f"{stage['stage_name']}｜版本 {stage['flow_type']}｜{stage['photo_set_name']}")
        if image is None:
            st.info("此階段已完成。")
            return
        st.caption(f"image_id：{image['image_id']}")
        path = image.get("path", "")
        if path and Path(path).exists():
            st.image(path, use_container_width=True)
        else:
            render_placeholder(image["image_id"])


def render_sidebar_emotion_quickview():
    """Sidebar 底部：情緒定義快速查看（只顯示定義與圖片）"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<div style="font-size:13px;font-weight:700;color:#4a3520;margin-bottom:8px;">'
            '📖 情緒定義快速查看</div>',
            unsafe_allow_html=True,
        )

        # 只列出有定義的情緒（對應 EMOTION_OPTIONS 的子集）
        quickview_emotions = [
            ("害怕", "😿 害怕"),
            ("憤怒", "😾 憤怒"),
            ("歡樂/玩耍", "😺 歡樂/玩耍"),
            ("滿意", "😽 滿意"),
            ("好奇", "🐾 好奇"),
        ]

        col1, col2 = st.columns(2)
        for i, (emotion_key, label) in enumerate(quickview_emotions):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                if st.button(label, key=f"sidebar_emotion_def_{emotion_key}", use_container_width=True):
                    show_emotion_dialog(emotion_key)


def build_selected_features(feature_values, feature_other_text):
    result = {}
    for group_name, choice in feature_values.items():
        if choice == "其他":
            text = feature_other_text.get(group_name, "").strip()
            result[group_name] = f"其他：{text}" if text else "其他"
        else:
            result[group_name] = choice or ""
    return json.dumps(result, ensure_ascii=False)


def render_feature_selector(prefix):
    feature_values = {}
    feature_other_text = {}
    for group_name, options in FEATURE_OPTIONS.items():
        st.markdown(f"#### {group_name}")
        choice = st.radio(
            f"請選擇{group_name}最符合的觀察結果",
            options,
            index=None,
            key=f"{prefix}_feature_{group_name}",
        )
        feature_values[group_name] = choice or ""
        if choice == "其他":
            feature_other_text[group_name] = st.text_input(
                f"請補充{group_name}其他特徵",
                key=f"{prefix}_feature_other_{group_name}",
            )
        else:
            feature_other_text[group_name] = ""
        st.divider()
    return feature_values, feature_other_text


def render_uncertain_reason(prefix, final_emotion):
    if final_emotion != "其他／無法判斷":
        return "", ""
    st.markdown("### 其他／無法判斷原因")
    reason = st.radio(
        "若選擇其他／無法判斷，請記錄原因",
        UNCERTAIN_REASONS,
        index=None,
        key=f"{prefix}_uncertain_reason",
    )
    other_text = ""
    if reason == "其他":
        other_text = st.text_input("請補充其他原因", key=f"{prefix}_uncertain_other_text")
    return reason or "", other_text


def build_base_record(stage, image, initial_emotion, selected_features, final_emotion, uncertain_reason, uncertain_other_text, confidence):
    annotation_time = round(time.time() - st.session_state.task_start_time, 2)
    if stage["flow_type"] == "B":
        emotion_changed = str(initial_emotion != final_emotion)
    else:
        emotion_changed = ""

    return {
        "group_id": GROUP_ID,
        "stage_name": stage["stage_name"],
        "photo_set_name": stage["photo_set_name"],
        "participant_id": st.session_state.participant_id,
        "flow_type": stage["flow_type"],
        "image_id": image["image_id"],
        "initial_emotion": initial_emotion,
        "selected_features": selected_features,
        "final_emotion": final_emotion,
        "uncertain_reason": uncertain_reason,
        "uncertain_other_text": uncertain_other_text,
        "confidence": confidence,
        "annotation_time": annotation_time,
        "emotion_changed": emotion_changed,
        "workload_q1": "",
        "workload_q2": "",
        "workload_q3": "",
        "confidence_q1": "",
        "confidence_q2": "",
        "confidence_q3": "",
        "clarity_score": "",
        "usefulness_score": "",
        "intention_score": "",
        "open_feedback": "",
    }


def go_next_image_or_questionnaire(record):
    st.session_state.pending_stage_records.append(record)
    stage = current_stage()
    st.session_state.image_index += 1
    st.session_state.task_start_time = None
    if st.session_state.image_index >= len(stage["images"]):
        st.session_state.page = "stage_questionnaire"
    request_scroll_to_top()
    st.rerun()


def render_flow_a(stage, image, prefix):
    st.markdown("## Step 1：觀看家貓照片")
    st.write("請先觀察左側照片，再進行部位特徵標註。")

    st.markdown("## Step 2：標註部位特徵")
    feature_values, feature_other_text = render_feature_selector(prefix)

    st.markdown("## Step 3：根據前述特徵選擇最終情緒")
    final_emotion = st.radio(
        "最終情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_final_emotion",
        format_func=lambda x: f"{EMOTION_ICONS.get(x, '')} {x}",
    )

    uncertain_reason, uncertain_other_text = render_uncertain_reason(prefix, final_emotion or "")

    st.markdown("## Step 4：填寫標註信心程度")
    confidence = st.radio(
        "標註信心程度",
        [1, 2, 3, 4, 5],
        index=None,
        horizontal=True,
        key=f"{prefix}_confidence",
    )

    required_ok = bool(final_emotion) and confidence is not None
    if final_emotion == "其他／無法判斷" and not uncertain_reason:
        required_ok = False

    if st.button("送出此張標註", type="primary", disabled=not required_ok):
        record = build_base_record(
            stage=stage,
            image=image,
            initial_emotion="",
            selected_features=build_selected_features(feature_values, feature_other_text),
            final_emotion=final_emotion,
            uncertain_reason=uncertain_reason,
            uncertain_other_text=uncertain_other_text,
            confidence=confidence,
        )
        go_next_image_or_questionnaire(record)

    st.divider()
    render_back_button()


def render_flow_b(stage, image, prefix):
    st.markdown("## Step 1：觀看家貓照片")
    st.write("請先觀察左側照片，依照整體感受選擇初步情緒。")

    st.markdown("## Step 2：依整體感受選擇初步情緒")
    initial_emotion = st.radio(
        "初步情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_initial_emotion",
        format_func=lambda x: f"{EMOTION_ICONS.get(x, '')} {x}",
    )

    st.markdown("## Step 3：標註部位特徵")
    feature_values, feature_other_text = render_feature_selector(prefix)

    st.markdown("## Step 4：再次確認或修改最終情緒")
    final_emotion = st.radio(
        "最終情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_final_emotion",
        format_func=lambda x: f"{EMOTION_ICONS.get(x, '')} {x}",
    )

    

    uncertain_reason, uncertain_other_text = render_uncertain_reason(prefix, final_emotion or "")

    st.markdown("## Step 5：填寫標註信心程度")
    confidence = st.radio(
        "標註信心程度",
        [1, 2, 3, 4, 5],
        index=None,
        horizontal=True,
        key=f"{prefix}_confidence",
    )

    required_ok = bool(initial_emotion) and bool(final_emotion) and confidence is not None
    if final_emotion == "其他／無法判斷" and not uncertain_reason:
        required_ok = False

    if st.button("送出此張標註", type="primary", disabled=not required_ok):
        record = build_base_record(
            stage=stage,
            image=image,
            initial_emotion=initial_emotion,
            selected_features=build_selected_features(feature_values, feature_other_text),
            final_emotion=final_emotion,
            uncertain_reason=uncertain_reason,
            uncertain_other_text=uncertain_other_text,
            confidence=confidence,
        )
        go_next_image_or_questionnaire(record)

    st.divider()
    render_back_button()


LIKERT_OPTIONS = [
    "非常不同意",
    "不同意",
    "普通",
    "同意",
    "非常同意",
]

LIKERT_SCORE_MAP = {
    "非常不同意": 1,
    "不同意": 2,
    "普通": 3,
    "同意": 4,
    "非常同意": 5,
}

QUESTIONNAIRE_CSS = """
<style>
/* ── 問卷區塊卡片 ── */
.q-section-card {
    background: #fffdf8;
    border: 1px solid #e0d4c0;
    border-radius: 10px;
    padding: 22px 26px 18px 26px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(180,140,80,0.07);
}

.q-section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid #e8d8be;
}

.q-section-icon {
    font-size: 20px;
    line-height: 1;
}

.q-section-title {
    font-family: 'Noto Serif TC', serif;
    font-size: 16px;
    font-weight: 700;
    color: #4a3520;
    letter-spacing: 0.04em;
}

.q-section-subtitle {
    font-size: 11.5px;
    color: #9e8060;
    margin-top: 1px;
}

/* ── 單題卡片：一題一框 ── */
.q-item {
    background: #fcfaf7;
    border: 1.8px solid #d8cfc2;
    border-radius: 14px;
    padding: 18px 22px 16px 22px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(180,140,80,0.05);
}

.q-item-label {
    font-family: 'Noto Serif TC', serif;
    font-size: 18px;
    color: #3b2e1e;
    font-weight: 700;
    margin-bottom: 12px;
    line-height: 1.5;
}

/* 問卷 Likert 選項：單行置中，且和題目同字體 */
div[data-testid="stRadio"] {
    width: 100% !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 26px !important;
    width: 100% !important;
    margin: 8px auto 0 auto !important;
    transform: translateX(3em) !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    flex: 0 0 auto !important;
    white-space: nowrap !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label p {
    font-family: 'Noto Serif TC', serif !important;
    font-size: 18px !important;
    font-weight: 400 !important;
    margin: 0 !important;
    white-space: nowrap !important;
}

/* 完成度提示 */
.q-progress-tip {
    font-size: 12.5px;
    color: #9e8060;
    text-align: center;
    margin: 6px 0 14px 0;
    letter-spacing: 0.02em;
}

.q-complete-tip {
    font-size: 12.5px;
    color: #6b8c5a;
    text-align: center;
    margin: 6px 0 14px 0;
    font-weight: 600;
}

/* 開放回饋區 */
.q-feedback-card {
    background: #fffdf8;
    border: 1px solid #e0d4c0;
    border-radius: 10px;
    padding: 20px 26px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(180,140,80,0.07);
}

.q-feedback-label {
    font-size: 13.5px;
    color: #4a3520;
    font-weight: 600;
    margin-bottom: 8px;
}

.q-feedback-hint {
    font-size: 12px;
    color: #9e8060;
    margin-bottom: 10px;
}
</style>
"""


def likert(item_no, label, key):
    clean_label = label.rstrip("。")

    st.markdown('<div class="q-item">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="q-item-label">Q{item_no}: {clean_label}</div>',
        unsafe_allow_html=True,
    )

    choice = st.radio(
        clean_label,
        LIKERT_OPTIONS,
        index=None,
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )

    st.markdown('</div>', unsafe_allow_html=True)
    return LIKERT_SCORE_MAP.get(choice) if choice is not None else None


def avg_or_none(values):
    if any(v is None for v in values):
        return None
    return round(sum(values) / len(values), 2)


def render_stage_questionnaire():
    stage = current_stage()
    si = st.session_state.stage_index

    st.markdown(QUESTIONNAIRE_CSS, unsafe_allow_html=True)

    left, center, right = st.columns([1, 2.4, 1])
    with center:

        # ── 頁面標題 ──
        st.markdown(
            f"""
            <div style="text-align:center;margin-bottom:6px;">
                <div style="font-size:28px;margin-bottom:6px;">📋</div>
                <div class="main-title" style="text-align:center;">
                    {stage["stage_name"]} 使用體驗問卷
                </div>
                <div class="sub-title" style="text-align:center;margin-top:4px;">
                    版本 {stage["flow_type"]}：{stage["flow_name"]}｜請根據剛才的標註體驗作答
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════
        # 區塊一：認知負荷
        # ══════════════════════════════════════

        with st.container():
            wl1 = likert(1, "我覺得此標註流程需要花費較多心力", f"q_{si}_wl1")

            wl2 = likert(2, "我在使用此流程時需要反覆思考才能完成標註", f"q_{si}_wl2")

            wl3 = likert(3, "我覺得此流程的判斷負擔較高", f"q_{si}_wl3")

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════
        # 區塊二：標註信心
        # ══════════════════════════════════════

        with st.container():
            cf1 = likert(4, "我對自己最後選擇的情緒結果有信心", f"q_{si}_cf1")

            cf2 = likert(5, "我認為自己的標註結果有足夠依據", f"q_{si}_cf2")

            cf3 = likert(6, "我能根據照片中的特徵做出合理判斷", f"q_{si}_cf3")

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════
        # 區塊三：流程清楚度、有用性與使用意圖
        # ══════════════════════════════════════

        with st.container():
            clarity = likert(7, "我能清楚理解此標註流程的操作順序", f"q_{si}_clarity")

            usefulness = likert(8, "我認為此流程有助於我判斷家貓情緒", f"q_{si}_usefulness")

            intention = likert(9, "若未來需要標註家貓情緒，我願意使用此流程", f"q_{si}_intention")

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════
        # 區塊四：開放式回饋
        # ══════════════════════════════════════

        open_feedback = st.text_area(
            "請說明此流程的使用感受、判斷困難或改進建議（選填）",
            key=f"q_{si}_open_feedback",
            height=110,
            placeholder="例如：步驟順序感覺很自然、某張照片特別難判斷耳朵方向…",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 完成提示與送出按鈕 ──
        complete = all(v is not None for v in [wl1, wl2, wl3, cf1, cf2, cf3, clarity, usefulness, intention])
        answered = sum(1 for v in [wl1, wl2, wl3, cf1, cf2, cf3, clarity, usefulness, intention] if v is not None)
        total_q = 9

        if complete:
            st.markdown(
                f'<div class="q-complete-tip">✅ 所有 {total_q} 題已填答完畢，可以送出！</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="q-progress-tip">已填答 {answered} / {total_q} 題，請完成所有題目後送出。</div>',
                unsafe_allow_html=True,
            )

        if st.button("儲存此階段並進入下一階段 →", type="primary", disabled=not complete, use_container_width=True):
            stage_records = []
            for record in st.session_state.pending_stage_records:
                record = dict(record)
                record["workload_q1"] = wl1
                record["workload_q2"] = wl2
                record["workload_q3"] = wl3
                record["confidence_q1"] = cf1
                record["confidence_q2"] = cf2
                record["confidence_q3"] = cf3
                record["clarity_score"] = clarity
                record["usefulness_score"] = usefulness
                record["intention_score"] = intention
                record["open_feedback"] = open_feedback
                stage_records.append(record)

            save_records(stage_records)
            st.session_state.pending_stage_records = []
            st.session_state.stage_index += 1
            st.session_state.image_index = 0
            st.session_state.task_start_time = None

            if st.session_state.stage_index >= len(get_stage_plan()):
                st.session_state.page = "done"
            else:
                st.session_state.page = "task"
                reset_task_timer()
            request_scroll_to_top()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        render_back_button()


def render_intro():
    st.markdown(
        f'<div class="main-title">🐱 {APP_PAGE_TITLE.replace("🐱 ", "")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sub-title">一個網頁完成同一組受試者的兩個階段：A 與 B 都會做，但順序與照片組不同。</div>', unsafe_allow_html=True)

    participant_id = st.text_input("受試者學號／代號", value=st.session_state.participant_id)
    st.session_state.participant_id = participant_id.strip()

    st.markdown("### 本組實驗安排")
    for idx, stage in enumerate(get_stage_plan(), start=1):
        st.markdown(
            f"""
            <div class="flow-card">
            <b>{idx}. {stage['stage_name']}</b><br>
            版本 {stage['flow_type']}：{stage['flow_name']} ＋ {stage['photo_set_name']}<br>
            <span style="color:#7a6650;">{stage['description']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 情緒定義總覽（只顯示定義，不顯示特徵）──
    st.markdown("### 情緒定義參考")
    st.caption("點選下方情緒名稱可快速查看定義與圖片說明。")

    for emo_name, emo_item in EMOTION_SCHEMA.items():
        icon = emo_item.get("icon", "")
        definition = emo_item.get("definition", "")
        img_path = emo_item.get("image")
        has_img = img_path and Path(img_path).exists()

        with st.expander(f"{icon} {emo_name}", expanded=False):
            if has_img:
                st.image(str(img_path), width=260)
            st.markdown(f"**定義：** {definition}")

    if st.button("開始本組實驗", type="primary", disabled=not bool(st.session_state.participant_id)):
        clear_temp_csv_and_session_records()
        st.session_state.page = "task"
        st.session_state.stage_index = 0
        st.session_state.image_index = 0
        st.session_state.pending_stage_records = []
        reset_task_timer()
        request_scroll_to_top()
        st.rerun()


def render_task():
    render_sidebar_image()
    render_sidebar_emotion_quickview()

    stage = current_stage()
    image = current_image()

    if image is None:
        st.session_state.page = "stage_questionnaire"
        request_scroll_to_top()
        st.rerun()
        return

    st.markdown(
        f'<div class="main-title">🐱 {stage["stage_name"]}｜版本 {stage["flow_type"]}：{stage["flow_name"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="active-card">{stage["description"]}<br>目前照片：{st.session_state.image_index + 1} / {len(stage["images"])}｜image_id：{image["image_id"]}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.task_start_time is None:
        reset_task_timer()

    prefix = f"s{st.session_state.stage_index}_i{st.session_state.image_index}_{stage['flow_type']}"

    if stage["flow_type"] == "A":
        render_flow_a(stage, image, prefix)
    else:
        render_flow_b(stage, image, prefix)


def render_done():
    # ── 自動嘗試一次雲端同步 ──
    if not st.session_state.get("cloud_sync_attempted", False):
        st.session_state["cloud_sync_attempted"] = True
        try:
            ok, msg = sync_to_cloud()
            st.session_state["last_save_message"] = msg
        except Exception as e:
            st.session_state["last_save_message"] = f"CSV 已儲存，但 Google Sheet 同步失敗：{e}"

    msg = st.session_state.get("last_save_message", "")
    pending_count = len(st.session_state.get("pending_cloud_rows", []))
    synced = pending_count == 0

    st.markdown(
        """
        <style>
        .done-hero {
            text-align: center;
            padding: 40px 20px 28px 20px;
            margin-bottom: 28px;
        }
        .done-hero-icon {
            font-size: 56px;
            line-height: 1;
            margin-bottom: 14px;
            animation: pop-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }
        @keyframes pop-in {
            0%   { transform: scale(0.4); opacity: 0; }
            100% { transform: scale(1);   opacity: 1; }
        }
        .done-hero-title {
            font-family: 'Noto Serif TC', serif;
            font-size: 26px;
            font-weight: 700;
            color: #1a1208;
            letter-spacing: 0.04em;
            margin-bottom: 8px;
        }
        .done-hero-sub {
            font-size: 14px;
            color: #7a6650;
            letter-spacing: 0.02em;
            line-height: 1.7;
        }
        /* 階段摘要徽章 */
        .stage-badges {
            display: flex;
            justify-content: center;
            gap: 14px;
            flex-wrap: wrap;
            margin: 18px 0 0 0;
        }
        .stage-badge {
            background: linear-gradient(135deg, #fffdf5 0%, #fff8e8 100%);
            border: 1.5px solid #c9a96e;
            border-radius: 30px;
            padding: 6px 18px;
            font-size: 13px;
            font-weight: 600;
            color: #8c5f20;
            letter-spacing: 0.03em;
        }
        /* 狀態卡片 */
        .done-card {
            background: #fffdf8;
            border: 1px solid #e0d4c0;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(180,140,80,0.07);
        }
        .done-card-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ede3d1;
        }
        .done-card-icon { font-size: 18px; }
        .done-card-title {
            font-family: 'Noto Serif TC', serif;
            font-size: 15px;
            font-weight: 700;
            color: #4a3520;
        }
        /* 同步成功 */
        .sync-ok {
            background: linear-gradient(135deg, #f0faf0 0%, #e8f5e8 100%);
            border: 1px solid #a8d8a8;
            border-left: 4px solid #5a9a5a;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 13.5px;
            color: #2d6a2d;
            font-weight: 500;
        }
        /* 同步失敗 */
        .sync-fail {
            background: #fffbf0;
            border: 1px solid #e8c76d;
            border-left: 4px solid #c9880a;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 13.5px;
            color: #5a4000;
        }
        /* 分隔線裝飾 */
        .done-divider {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 24px 0;
            color: #c9a96e;
            font-size: 12px;
            letter-spacing: 0.08em;
        }
        .done-divider::before,
        .done-divider::after {
            content: '';
            flex: 1;
            border-top: 1px solid #e0d4c0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2.4, 1])
    with center:

        # ── Hero 區：完成大標 ──
        stage_badges_html = "".join(
            f'<span class="stage-badge">✓ {s["stage_name"]}｜版本 {s["flow_type"]}</span>'
            for s in get_stage_plan()
        )
        st.markdown(
            f"""
            <div class="done-hero">
                <div class="done-hero-icon">🎉</div>
                <div class="done-hero-title">實驗全部完成！</div>
                <div class="done-hero-sub">
                    感謝您完成本組兩個階段的家貓情緒標註實驗<br>
                    請確認資料已同步至雲端，並通知實驗人員。
                </div>
                <div class="stage-badges">{stage_badges_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 雲端同步狀態卡 ──
        st.markdown(
            """
            <div class="done-card">
              <div class="done-card-header">
                <span class="done-card-icon">☁️</span>
                <span class="done-card-title">雲端同步狀態</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if synced:
            st.markdown(
                f'<div class="sync-ok">✅ Google Sheet 同步完成！{msg}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="sync-fail">⚠️ 尚有 {pending_count} 筆資料未上傳至 Google Sheet，請點擊下方按鈕重試。'
                + (f'<br><span style="font-size:12px;opacity:0.8;">{msg}</span>' if msg else "")
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("☁️ 重新上傳至 Google Sheet", type="primary", use_container_width=True):
                try:
                    ok, msg2 = sync_to_cloud()
                    st.session_state["last_save_message"] = msg2
                    st.rerun()
                except Exception as e:
                    st.session_state["last_save_message"] = f"重新同步失敗：{e}"
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 匯出資料卡 ──
        st.markdown(
            """
            <div class="done-card">
              <div class="done-card-header">
                <span class="done-card-icon">📄</span>
                <span class="done-card-title">下載標註資料</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if OUTPUT_CSV.exists():
            st.markdown(
                f'<div style="font-size:13px;color:#7a6650;margin-bottom:10px;">'
                f'資料已儲存於本機：<code style="background:#f0e9db;padding:2px 6px;border-radius:4px;font-size:12px;">'
                f'{OUTPUT_CSV.name}</code></div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                "📥 下載 CSV 備份",
                OUTPUT_CSV.read_bytes(),
                file_name=OUTPUT_CSV.name,
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.markdown(
                '<div style="font-size:13px;color:#9e8060;">目前尚無本機 CSV 檔案。</div>',
                unsafe_allow_html=True,
            )

        # ── 分隔 ──
        st.markdown(
            '<div class="done-divider">· · ·</div>',
            unsafe_allow_html=True,
        )

        # ── 重新開始按鈕 ──
        st.markdown(
            '<div style="text-align:center;font-size:13px;color:#9e8060;margin-bottom:10px;">'
            '若需要重新填寫，請點擊下方按鈕。',
            unsafe_allow_html=True,
        )
        if st.button("↩ 回首頁重新開始", use_container_width=True):
            reset_all()
            request_scroll_to_top()
            st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)


def main():
    init_state()
    st.markdown('<div id="page_top_anchor"></div>', unsafe_allow_html=True)

    if st.session_state.page == "intro":
        render_intro()
    elif st.session_state.page == "task":
        render_task()
    elif st.session_state.page == "stage_questionnaire":
        render_stage_questionnaire()
    elif st.session_state.page == "done":
        render_done()

    do_scroll_to_top_if_needed()


if __name__ == "__main__":
    main()
