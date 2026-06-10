"""
家貓情緒標註研究系統
版本 B：情緒導向式部位特徵提示
流程：受試者基本資料 → 照片標註（先選情緒，再顯示對應特徵提示）→ 整體反饋 → 完成
"""

import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# 基本設定
# ─────────────────────────────────────────────
APP_PAGE_TITLE = "🐱 家貓情緒標註｜版本 B"
OUTPUT_CSV = Path("annotation_version_b.csv")
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ANNOTATION_DIR = PROJECT_ROOT  / "annotations"
IMAGE_DIR = PROJECT_ROOT  / "imgaes"  # 情緒定義圖片資料夾（依目前資料夾名稱）

SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwxNvaZl8movCnWa3iaJt-yOg9kJAWkAMK_ESWGa9H9Ttkc97gWIeQxb8mDjCkWSg0Lnw/exec"
SHEET_SECRET = "hci_cat_annotation_secret"

# ─────────────────────────────────────────────
# 照片清單
# ─────────────────────────────────────────────
IMAGES = [
    {"image_id": "cat_easy", "difficulty": "易", "path": str(ANNOTATION_DIR / "cat_easy.png")},
    {"image_id": "cat_medium", "difficulty": "中", "path": str(ANNOTATION_DIR / "cat_medium.png")},
    {"image_id": "cat_hard", "difficulty": "難", "path": str(ANNOTATION_DIR / "cat_hard.png")},
]

# ─────────────────────────────────────────────
# 情緒選項
# ─────────────────────────────────────────────
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
    "歡樂/玩耍": "😺",
    "滿意": "😽",
    "好奇": "🐾",
    "中性": "➖",
}

EMOTION_DEFINITIONS = {
    "害怕": "由立即感知到的危險或危險的威脅引起的，表現為警惕和試圖撤退或逃跑。",
    "憤怒": "由執行行動／實現目標的願望受挫或資源競爭引起，表現為攻擊性或攻擊威脅。",
    "歡樂/玩耍": "表現為非功能性行為，包括運動遊戲、社交遊戲或物件遊戲。",
    "滿意": "由需求和願望得到滿足而產生的正向情緒狀態，表現為休息、平靜和親和。",
    "好奇": "由新奇或顯著刺激引起，表現為注意、定向或探索行為。",
    "中性": "無任何明顯情緒特徵，整體狀態平穩，未呈現明確的害怕、憤怒、歡樂／玩耍、滿意或好奇線索。",
}

EMOTION_IMAGES = {
    "害怕": IMAGE_DIR / "fear.png",
    "憤怒": IMAGE_DIR / "anger.png",
    "歡樂/玩耍": IMAGE_DIR / "joy.png",
    "滿意": IMAGE_DIR / "contentment.png",
    "好奇": IMAGE_DIR / "interest.png",
    "中性": None,
}

UNCERTAIN_REASONS = ["影像品質不足", "線索不足", "多種情緒並存", "超出現有分類"]

# ─────────────────────────────────────────────
# Step 2 專用：情緒導向式部位特徵提示
# 這裡只顯示文獻整理後的可能特徵，不放「無法辨識」和「其他」
# ─────────────────────────────────────────────
EMOTION_FEATURE_HINTS = {
    "害怕": {
        "眼睛": [
            "睜大",
            "瞳孔放大",
            "緊閉",
            "避免眼神接觸",
        ],
        "耳朵": [
            "側向",
            "壓平",
        ],
        "尾巴": [
            "夾起",
        ],
        "身體／姿勢": [
            "緊繃",
            "壓低",
            "拱背",
            "炸毛",
            "發抖／僵硬",
        ],
    },

    "憤怒": {
        "眼睛": [
            "睜大",
            "瞳孔放大",
            "直視",
        ],
        "耳朵": [
            "側向",
        ],
        "尾巴": [
            "壓低僵硬",
            "快速甩動",
        ],
        "身體／姿勢": [
            "炸毛",
            "前傾",
            "拱背",
            "緊繃",
         
        ],
    },

    "歡樂/玩耍": {
        "眼睛": [
            "瞳孔放大",
            "瞳孔變圓",
            "放鬆/柔軟",
        ],
        "耳朵": [
            "直立",
        ],
        "尾巴": [
            "豎起",
        ],
        "身體／姿勢": [
            "用爪子抓/拍打物體",
            "咬物體",
            "滾動/展示腹部",
            "手抓物體同時用腳踢",
        ],
    },

    "滿意": {
        "眼睛": [
            "半睜",
            "放鬆/柔軟",
        ],
        "耳朵": [
            "直立",
        ],
        "尾巴": [
            "放鬆",
            "豎起",
        ],
        "身體／姿勢": [
            "放鬆",
            "蹲坐",
            "蜷曲躺臥",
            "伸展",
            "梳理毛髮",
            "踩踏",
        ],
    },

    "好奇": {
        "眼睛": [
            "瞳孔放大",
            "瞳孔變圓",
            "直視",
            "眼神專注",
        ],
        "耳朵": [
            "朝向刺激物",
        ],
        "尾巴": [
            "水平",
            "豎起",
        ],
        "身體／姿勢": [
            "前傾",
            "前肢倚靠",
            "頭往前伸",
            "嗅聞",
        ],
    },
}

# ─────────────────────────────────────────────
# Step 3 專用：全部特徵選項
# 不依情緒限制，所有部位特徵都可選
# ─────────────────────────────────────────────
FEATURE_OPTIONS = {
    "眼睛": [
        "睜大",
        "半睜",
        "緊閉",
        "瞳孔放大",
        "瞳孔變圓",
        "直視",
        "眼神專注",
        "避免眼神接觸",
        "放鬆/柔軟",
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
        "用爪子抓/拍打物體",
        "咬物體",
        "滾動/展示腹部",
        "手抓物體同時用腳踢",
        "蹲坐",
        "蜷曲躺臥",
        "伸展",
        "梳理毛髮",
        "踩踏",
        "前肢倚靠",
        "頭往前伸",
        "嗅聞",
        "無法辨識",
        "其他",
    ],
}

# ─────────────────────────────────────────────
# 量表選項
# ─────────────────────────────────────────────
LIKERT_OPTIONS = ["非常不同意", "不同意", "普通", "同意", "非常同意"]
LIKERT_SCORE_MAP = {
    "非常不同意": 1,
    "不同意": 2,
    "普通": 3,
    "同意": 4,
    "非常同意": 5,
}

CAT_UNDERSTANDING_OPTIONS = ["非常不了解", "不了解", "普通", "了解", "非常了解"]
CAT_UNDERSTANDING_SCORE_MAP = {
    "非常不了解": 1,
    "不了解": 2,
    "普通": 3,
    "了解": 4,
    "非常了解": 5,
}

CONFIDENCE_OPTIONS = ["非常沒信心", "沒信心", "普通", "有信心", "非常有信心"]
CONFIDENCE_SCORE_MAP = {
    "非常沒信心": 1,
    "沒信心": 2,
    "普通": 3,
    "有信心": 4,
    "非常有信心": 5,
}

DIFFICULTY_OPTIONS = ["非常容易", "容易", "普通", "困難", "非常困難"]
DIFFICULTY_SCORE_MAP = {
    "非常容易": 1,
    "容易": 2,
    "普通": 3,
    "困難": 4,
    "非常困難": 5,
}

HELPFULNESS_OPTIONS = ["完全沒有幫助", "沒有幫助", "普通", "有幫助", "非常有幫助"]
HELPFULNESS_SCORE_MAP = {
    "完全沒有幫助": 1,
    "沒有幫助": 2,
    "普通": 3,
    "有幫助": 4,
    "非常有幫助": 5,
}

OVERALL_QUESTIONS = [
    ("overall_easy", "Q1：在本次標註過程中，我覺得判斷家貓情緒是容易的。"),
    ("overall_intuition", "Q2：在本次標註過程中，我是依靠直覺判斷家貓情緒。"),
    ("overall_explainable", "Q3：在本次標註過程中，我能明確說明自己為什麼選擇該情緒。"),
    ("overall_observation_clarity", "Q4：在本次標註過程中，我能清楚知道應該優先觀察哪些部位來判斷情緒。"),
]

DATA_COLUMNS = [
    "annotator_id",
    "questionnaire_version",
    "has_cat_experience",
    "current_cat_owner",
    "cat_understanding_score",
    "animal_related_background",
    "cat_emotion_basic_knowledge",
    "prior_knowledge_group",
    "image_id",
    "difficulty",
    "condition",
    "final_emotion",
    "confidence",
    "difficulty_score",
    "uncertain_reason",
    "additional_note",
    "eye_feature",
    "ear_feature",
    "posture_feature",
    "tail_feature",
    "prompt_helpfulness",
    "annotation_started_at",
    "annotation_submitted_at",
    "annotation_time_seconds",
    "overall_easy",
    "overall_intuition",
    "overall_explainable",
    "overall_observation_clarity",
]

# ─────────────────────────────────────────────
# 頁面設定 & CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=APP_PAGE_TITLE,
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.stApp { background: #fdf6ed; }
.main-title {
    font-family: 'Noto Serif TC', serif; font-size: 24px; font-weight: 700;
    color: #4a2000; letter-spacing: 0.04em; margin-bottom: 4px;
}
.sub-title { color: #a0622a; font-size: 14px; margin-bottom: 20px; }
h2 {
    font-family: 'Noto Serif TC', serif !important; font-size: 17px !important;
    font-weight: 700 !important; color: #6b3a00 !important;
    border-bottom: 2px solid #f0b27a; padding-bottom: 6px;
    margin-top: 22px !important; margin-bottom: 10px !important;
}
h3 { font-size: 15px !important; color: #784212 !important; margin-top: 16px !important; }
h4 { font-size: 14px !important; color: #a04000 !important; margin-top: 12px !important; }
.version-badge {
    display: inline-block; background: #fdf2e9; color: #784212;
    border: 1.5px solid #f0b27a; border-radius: 20px;
    padding: 4px 16px; font-size: 13px; font-weight: 700;
    letter-spacing: 0.06em; margin-bottom: 14px;
}
.info-card {
    padding: 14px 18px; border: 1px solid #f5cba7;
    border-left: 4px solid #e67e22; border-radius: 4px;
    background: #fdf2e9; margin-bottom: 14px;
    font-size: 14px; line-height: 1.7; color: #4a2000;
}
.feature-hint-card {
    padding: 16px 20px; border: 1px solid #a9dfbf;
    border-left: 4px solid #27ae60; border-radius: 6px;
    background: #eafaf1; margin-bottom: 16px;
    font-size: 13.5px; line-height: 1.9; color: #145a32;
}
.bias-card {
    padding: 14px 18px; border: 1px solid #f7dc6f;
    border-left: 4px solid #f1c40f; border-radius: 6px;
    background: #fff9e6; margin-bottom: 16px;
    font-size: 13.5px; line-height: 1.8; color: #5a4000;
}
.warn-card {
    padding: 12px 16px; border-radius: 4px; background: #fffbf0;
    border: 1px solid #f9e79f; border-left: 4px solid #f1c40f;
    margin: 10px 0 14px 0; font-size: 13px; color: #5a4000;
}
.emo-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; border-radius: 6px;
    background: #fdf2e9; border: 1px solid #f5cba7;
    margin-bottom: 7px; font-size: 13px; line-height: 1.6;
}
.emo-row .icon { font-size: 20px; min-width: 28px; }
.emo-row .name { font-weight: 700; color: #784212; min-width: 90px; }
.emo-row .def  { color: #a04000; }
.placeholder {
    height: 380px; border: 1.5px dashed #f0b27a; border-radius: 8px;
    background: linear-gradient(160deg, #fdf2e9 0%, #fae5d3 100%);
    display: flex; align-items: center; justify-content: center;
    color: #c0874a; font-size: 15px; text-align: center; padding: 20px;
}
section[data-testid="stSidebar"] {
    background: #fdf6ed !important;
    border-right: 1px solid #f5cba7;
}
section[data-testid="stSidebar"] img {
    width: 100% !important;
    max-height: 60vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(231,76,60,0.12);
}
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        background: #fdf6ed !important;
    }
    section[data-testid="stSidebar"] img {
        max-height: 48vh;
    }
    .main-title {
        font-size: 21px;
    }
    .sub-title,
    .info-card,
    .feature-hint-card,
    .bias-card {
        font-size: 13px;
    }
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e67e22 0%, #c0392b 100%) !important;
    color: #fff !important; border: none !important; border-radius: 4px !important;
    font-size: 14px !important; font-weight: 700 !important; padding: 10px 24px !important;
}
.stButton > button:not([kind="primary"]) {
    background: #fdf2e9 !important; color: #784212 !important;
    border: 1.5px solid #f0b27a !important; border-radius: 4px !important;
}
.feature-group {
    background: #fffdf8; border: 1px solid #f5cba7;
    border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;
}
.feature-group-title {
    font-weight: 700; color: #6b3a00; font-size: 14px; margin-bottom: 8px;
}
.progress-tip { font-size: 12.5px; color: #a0622a; margin: 6px 0 14px 0; }
.complete-tip { font-size: 12.5px; color: #1a8a4a; font-weight: 600; margin: 6px 0 14px 0; }
hr { border-color: #f5cba7 !important; margin: 16px 0 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "intro",
        "annotator_id": "",
        "has_cat_experience": None,
        "current_cat_owner": None,
        "cat_understanding_score": None,
        "animal_related_background": None,
        "cat_emotion_basic_knowledge": None,
        "prior_knowledge_group": "",
        "image_index": 0,
        "task_start_time": None,
        "pending_records": [],
        "final_records": [],
        "cloud_sync_attempted": False,
        "last_save_message": "",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def scroll_top():
    st.session_state["scroll_to_top"] = True


def do_scroll():
    if st.session_state.pop("scroll_to_top", False):
        components.html(
            """<script>
            function t(){
                try{
                    window.parent.scrollTo(0,0);
                    ['section.main','main','.stApp'].forEach(function(s){
                        window.parent.document.querySelectorAll(s).forEach(function(el){
                            el.scrollTop=0;
                        });
                    });
                }catch(e){}
            }
            t();
            [100,300,600].forEach(function(d){setTimeout(t,d);});
            </script>""",
            height=0,
        )


def reset_timer():
    st.session_state.task_start_time = time.time()


def format_timestamp(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def current_image():
    idx = st.session_state.image_index
    return IMAGES[idx] if idx < len(IMAGES) else None


def compute_group():
    exp = st.session_state.has_cat_experience
    score = st.session_state.cat_understanding_score or 0
    emotion_knowledge = st.session_state.cat_emotion_basic_knowledge

    return "高先備知識" if (exp == "是" or score >= 4 or emotion_knowledge == "是") else "低先備知識"


def base_fields():
    return {
        "annotator_id": st.session_state.annotator_id,
        "questionnaire_version": "版本 B",
        "has_cat_experience": st.session_state.has_cat_experience or "",
        "current_cat_owner": st.session_state.current_cat_owner or "",
        "cat_understanding_score": st.session_state.cat_understanding_score or "",
        "animal_related_background": st.session_state.animal_related_background or "",
        "cat_emotion_basic_knowledge": st.session_state.cat_emotion_basic_knowledge or "",
        "prior_knowledge_group": st.session_state.prior_knowledge_group,
    }


def save_records(records):
    rows = [{col: r.get(col, "") for col in DATA_COLUMNS} for r in records]
    df_new = pd.DataFrame(rows, columns=DATA_COLUMNS)

    if OUTPUT_CSV.exists():
        df_old = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")

        for col in DATA_COLUMNS:
            if col not in df_old.columns:
                df_old[col] = ""

        df_all = pd.concat([df_old[DATA_COLUMNS], df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")


def sync_to_cloud(rows):
    if not SHEET_WEBHOOK_URL.strip():
        return False, "尚未設定 SHEET_WEBHOOK_URL。"

    resp = requests.post(
        SHEET_WEBHOOK_URL,
        json={"secret": SHEET_SECRET, "records": rows},
        timeout=20,
    )
    resp.raise_for_status()

    data = resp.json()

    if not data.get("ok"):
        raise ValueError(data.get("error", "Unknown error"))

    return True, f"已同步 {data.get('inserted', len(rows))} 筆至 Google Sheet。"


def build_feature_str(selections, group_name, other_texts):
    sel = selections.get(group_name, [])

    if not sel:
        return ""

    parts = []

    for s in sel:
        if s == "其他":
            extra = other_texts.get(group_name, "").strip()
            parts.append(f"其他：{extra}" if extra else "其他")
        else:
            parts.append(s)

    return "、".join(parts)


def render_emotion_feature_hint(final_emotion):
    hint_options = EMOTION_FEATURE_HINTS.get(final_emotion, {})

    hint_lines = []

    for group_name, options in hint_options.items():
        if options:
            hint_lines.append(f"&nbsp;&nbsp;<b>{group_name}</b>：{'、'.join(options)}")

    return hint_lines


# ─────────────────────────────────────────────
# 頁面 1：首頁
# ─────────────────────────────────────────────
def render_intro():
    st.markdown('<div class="version-badge">版本 B</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">🐱 家貓情緒標註研究</div>', unsafe_allow_html=True)
    

    annotator_id = st.text_input("受試者學號／代號", value=st.session_state.annotator_id)
    st.session_state.annotator_id = annotator_id.strip()

    st.markdown("### 情緒類別定義參考")

    for emo, defn in EMOTION_DEFINITIONS.items():
        icon = EMOTION_ICONS.get(emo, "")
        emo_img = EMOTION_IMAGES.get(emo)

        with st.expander(f"{icon} {emo}", expanded=False):
            if emo_img and Path(emo_img).exists():
                st.image(str(emo_img), use_container_width=True)

            st.markdown(
                f"""
                <div class="emo-row">
                    <span class="icon">{icon}</span>
                    <span class="name">{emo}</span>
                    <span class="def">{defn}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("開始標註 →", type="primary", disabled=not bool(st.session_state.annotator_id)):
        st.session_state.page = "background"
        scroll_top()
        st.rerun()


# ─────────────────────────────────────────────
# 頁面 2：先備知識問卷
# ─────────────────────────────────────────────
def render_background():
    st.markdown('<div class="version-badge">版本 B</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">受試者基本資料</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">請回答以下問題，作為後續分析的分組依據。</div>', unsafe_allow_html=True)

    has_exp = st.radio("1. 您是否曾經養過貓？", ["是", "否"], index=None, key="bg_exp")
    cur_own = st.radio("2. 您目前是否有養貓？", ["是", "否"], index=None, key="bg_own")

    bg = st.radio(
        "3. 您是否具有動物照護、獸醫、動物行為或相關背景？",
        ["是", "否"],
        index=None,
        key="bg_background",
    )

    emotion_knowledge = st.radio(
        "4. 您是否對貓咪常見情緒表現有基本認知，例如害怕、生氣、滿意或好奇時可能出現的特徵？",
        ["是", "否"],
        index=None,
        key="bg_emotion_knowledge",
    )

    understand_choice = st.radio(
        "5. 您對貓咪行為的了解程度",
        CAT_UNDERSTANDING_OPTIONS,
        index=None,
        horizontal=True,
        key="bg_understand",
    )
    understand = CAT_UNDERSTANDING_SCORE_MAP.get(understand_choice) if understand_choice else None

    ready = all(v is not None for v in [has_exp, cur_own, bg, emotion_knowledge, understand])

    if st.button("完成填寫，進入標註 →", type="primary", disabled=not ready):
        st.session_state.has_cat_experience = has_exp
        st.session_state.current_cat_owner = cur_own
        st.session_state.cat_understanding_score = understand
        st.session_state.animal_related_background = bg
        st.session_state.cat_emotion_basic_knowledge = emotion_knowledge
        st.session_state.prior_knowledge_group = compute_group()
        st.session_state.page = "task"
        st.session_state.image_index = 0
        st.session_state.pending_records = []
        reset_timer()
        scroll_top()
        st.rerun()

    st.divider()

    if st.button("← 上一頁"):
        st.session_state.page = "intro"
        scroll_top()
        st.rerun()


# ─────────────────────────────────────────────
# 頁面 3：照片標註
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        image = current_image()

        st.markdown(
            '<div class="version-badge" style="margin-bottom:10px;">版本 B</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### 家貓照片")

        if image is None:
            st.info("所有照片已完成標註。")
            return

        idx = st.session_state.image_index
        st.caption(f"第 {idx + 1} / {len(IMAGES)} 張")

        path = image.get("path", "")

        if path and Path(path).exists():
            st.image(path, use_container_width=True)
        else:
            st.markdown(
                f'<div class="placeholder">🐱 照片預覽區<br><small>{image["image_id"]}</small></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("**📖 情緒定義**")

        for emo, defn in EMOTION_DEFINITIONS.items():
            emo_img = EMOTION_IMAGES.get(emo)

            with st.expander(f"{EMOTION_ICONS.get(emo, '')} {emo}", expanded=False):
                if emo_img and Path(emo_img).exists():
                    st.image(str(emo_img), use_container_width=True)

                st.caption(defn)


def render_task():
    render_sidebar()

    image = current_image()

    if image is None:
        st.session_state.page = "overall_feedback"
        scroll_top()
        st.rerun()
        return

    idx = st.session_state.image_index
    prefix = f"b_i{idx}"

    st.markdown('<div class="version-badge">版本 B</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">🐱 家貓情緒標註</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="info-card" style="border-left-color:#e67e22;">
            請先觀看左側照片並選擇主要情緒。<br>
            系統接著會依據您所選的情緒，顯示該情緒可能出現的部位特徵提示。<br>
            接著請從完整特徵清單中勾選實際可觀察到的特徵。<br><br>
            <b>第 {idx + 1} / {len(IMAGES)} 張</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.task_start_time is None:
        reset_timer()

    # ── Step 1：先選擇情緒 ──
    st.markdown("## Step 1：選擇主要情緒")
    final_emotion = st.radio(
        "請先根據照片，選擇您認為最符合的主要情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_emotion",
        format_func=lambda x: f"{EMOTION_ICONS.get(x, '')} {x}",
    )

    uncertain_reason = ""

    if final_emotion == "其他／無法判斷":
        st.markdown(
            '<div class="warn-card">請說明「其他／無法判斷」的原因：</div>',
            unsafe_allow_html=True,
        )
        uncertain_reason = (
            st.radio(
                "原因",
                UNCERTAIN_REASONS,
                index=None,
                key=f"{prefix}_uncertain",
            )
            or ""
        )

    # ── Step 2：依所選情緒顯示觀察提示 ──
    st.markdown("## Step 2：閱讀所選情緒的部位特徵提示")

    skip_feature_selection = False

    if final_emotion and final_emotion not in ["中性", "其他／無法判斷"]:
        hint_lines = render_emotion_feature_hint(final_emotion)

        st.markdown(
            f"""
            <div class="feature-hint-card">
                <b>📋 您目前選擇的情緒：{EMOTION_ICONS.get(final_emotion, '')} {final_emotion}</b><br>
                以下內容為此情緒「可能出現」的部位特徵，僅作為觀察方向，並非標準答案。
            </div>
            """,
            unsafe_allow_html=True,
        )

        if hint_lines:
            st.markdown(
                f"""
                <div class="feature-hint-card">
                    {'<br>'.join(hint_lines)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="bias-card">
                <b>⚠️ 避免確認偏誤提醒：</b><br>
                系統提供的特徵只是「可能出現」的觀察方向，並不代表照片中一定存在這些特徵，
                <b>請不要因為看到提示就勾選該特徵</b>。<br>
                請只勾選照片中 <b>實際可觀察到</b>，且您認為能支持情緒判斷的特徵。<br>
                若提示中沒有列出，但您認為照片中有其他支持判斷的特徵，請在下一步選擇「其他」並補充說明。
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif final_emotion == "中性":
        st.markdown(
            """
            <div class="feature-hint-card">
                您選擇的是「中性」，因此系統不提供特定情緒部位特徵提示。<br>
                但下一步仍可依照片情況勾選可觀察到的部位特徵，或選擇「無法辨識／其他」。
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif final_emotion == "其他／無法判斷":
        skip_feature_selection = True
        st.markdown(
            """
            <div class="feature-hint-card">
                您選擇的是「其他／無法判斷」，因此系統不提供特定情緒部位特徵提示。<br>
                且無須勾選任何部位特徵。
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.info("請先選擇主要情緒，系統才會顯示對應的部位特徵提示。")

    # ── Step 3：不依情緒限制，全部特徵皆可選 ──
    feature_selections = {}
    feature_other_texts = {}

    if not skip_feature_selection:
        st.markdown("## Step 3：勾選支持情緒判斷的部位特徵")
        st.caption(
            "請選取您在照片中實際觀察到、且用以支持情緒判斷的特徵(可複選)。"
            "若該部位看不清楚，請選擇「無法辨識」；若有清單未列出的特徵，請選擇「其他」並補充說明。"
        )

        col_left, col_right = st.columns(2)
        feature_items = list(FEATURE_OPTIONS.items())

        for i, (group_name, options) in enumerate(feature_items):
            target_col = col_left if i % 2 == 0 else col_right

            with target_col:
                st.markdown(
                    f'<div class="feature-group"><div class="feature-group-title">{group_name}</div>',
                    unsafe_allow_html=True,
                )

                selected = st.multiselect(
                    f"觀察到的{group_name}特徵",
                    options,
                    key=f"{prefix}_feat_{group_name}",
                    label_visibility="collapsed",
                )
                feature_selections[group_name] = selected

                if "其他" in selected:
                    other_text = st.text_input(
                        f"請補充{group_name}其他特徵",
                        key=f"{prefix}_feat_other_{group_name}",
                    )
                    feature_other_texts[group_name] = other_text
                else:
                    feature_other_texts[group_name] = ""

                st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("## Step 3：部位特徵")
        st.info("此類別不需勾選部位特徵，請直接填寫下一步。")

    # ── Step 4：一起填寫信心、難度與提示幫助程度 ──
    st.markdown("## Step 4：填寫標註信心、判斷難度與提示幫助程度")

    confidence_choice = st.radio(
        "1. 您對此張照片情緒標註的信心程度",
        CONFIDENCE_OPTIONS,
        index=None,
        horizontal=True,
        key=f"{prefix}_conf",
    )
    confidence = CONFIDENCE_SCORE_MAP.get(confidence_choice) if confidence_choice else None

    difficulty_choice = st.radio(
        "2. 您覺得此張照片的情緒判斷難度",
        DIFFICULTY_OPTIONS,
        index=None,
        horizontal=True,
        key=f"{prefix}_diff",
    )
    difficulty_score = DIFFICULTY_SCORE_MAP.get(difficulty_choice) if difficulty_choice else None

    prompt_helpfulness_choice = st.radio(
        "3. 所選情緒對應的部位特徵提示，對您判斷情緒的幫助程度",
        HELPFULNESS_OPTIONS,
        index=None,
        horizontal=True,
        key=f"{prefix}_helpfulness",
    )
    prompt_helpfulness = HELPFULNESS_SCORE_MAP.get(prompt_helpfulness_choice) if prompt_helpfulness_choice else None

    additional_note = st.text_area(
        "補充說明（選填）",
        key=f"{prefix}_note",
        height=75,
       
    )

    required_ok = (
        bool(final_emotion)
        and confidence is not None
        and difficulty_score is not None
        and prompt_helpfulness is not None
        and (final_emotion != "其他／無法判斷" or bool(uncertain_reason))
    )

    if st.button("送出此張標註 →", type="primary", disabled=not required_ok):
        annotation_started_ts = st.session_state.task_start_time
        annotation_submitted_ts = time.time()
        annotation_time_seconds = (
            round(annotation_submitted_ts - annotation_started_ts, 2)
            if annotation_started_ts
            else ""
        )

        record = {
            **base_fields(),
            "image_id": image["image_id"],
            "difficulty": image["difficulty"],
            "condition": "情緒導向式部位特徵提示",
            "final_emotion": final_emotion,
            "confidence": confidence,
            "difficulty_score": difficulty_score,
            "uncertain_reason": uncertain_reason,
            "additional_note": additional_note,
            "eye_feature": build_feature_str(feature_selections, "眼睛", feature_other_texts),
            "ear_feature": build_feature_str(feature_selections, "耳朵", feature_other_texts),
            "posture_feature": build_feature_str(feature_selections, "身體／姿勢", feature_other_texts),
            "tail_feature": build_feature_str(feature_selections, "尾巴", feature_other_texts),
            "prompt_helpfulness": prompt_helpfulness,
            "annotation_started_at": format_timestamp(annotation_started_ts),
            "annotation_submitted_at": format_timestamp(annotation_submitted_ts),
            "annotation_time_seconds": annotation_time_seconds,
            "overall_easy": "",
            "overall_intuition": "",
            "overall_explainable": "",
            "overall_observation_clarity": "",
        }

        st.session_state.pending_records.append(record)
        st.session_state.image_index += 1
        reset_timer()

        if st.session_state.image_index >= len(IMAGES):
            st.session_state.page = "overall_feedback"

        scroll_top()
        st.rerun()

    st.divider()

    if idx > 0 and st.button("← 上一張"):
        st.session_state.image_index -= 1

        if st.session_state.pending_records:
            st.session_state.pending_records.pop()

        reset_timer()
        scroll_top()
        st.rerun()


# ─────────────────────────────────────────────
# 頁面 4：整體反饋問卷
# ─────────────────────────────────────────────
def render_overall_feedback():
    st.markdown('<div class="version-badge">版本 B：情緒導向式部位特徵提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">📋 整體標註體驗反饋</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">以下題目請針對剛才所有照片的標註過程整體評估（非單張照片）。</div>',
        unsafe_allow_html=True,
    )

    scores = {}

    for field, question in OVERALL_QUESTIONS:
        clean_q = question.rstrip("。")
        st.markdown(
            f'<div style="background:#fdf2e9;border:1.5px solid #f5cba7;border-radius:10px;'
            f'padding:16px 20px;margin-bottom:14px;">'
            f'<div style="font-family:Noto Serif TC,serif;font-size:16px;font-weight:700;'
            f'color:#4a2000;margin-bottom:10px;">{clean_q}</div></div>',
            unsafe_allow_html=True,
        )

        choice = st.radio(
            clean_q,
            LIKERT_OPTIONS,
            index=None,
            horizontal=True,
            key=f"overall_{field}",
            label_visibility="collapsed",
        )
        scores[field] = LIKERT_SCORE_MAP.get(choice) if choice else None

    answered = sum(1 for v in scores.values() if v is not None)
    total = len(scores)
    complete = answered == total

    if complete:
        st.markdown('<div class="complete-tip">✅ 所有題目已填答完畢！</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="progress-tip">已填答 {answered} / {total} 題。</div>',
            unsafe_allow_html=True,
        )

    if st.button("完成標註，儲存資料 →", type="primary", disabled=not complete, use_container_width=True):
        final_records = []

        for rec in st.session_state.pending_records:
            r = dict(rec)

            for field, _ in OVERALL_QUESTIONS:
                r[field] = scores[field]

            final_records.append(r)

        st.session_state.final_records = final_records
        save_records(final_records)
        st.session_state.page = "done"
        scroll_top()
        st.rerun()

    st.divider()

    if st.button("← 返回最後一張照片"):
        st.session_state.page = "task"
        st.session_state.image_index = len(IMAGES) - 1

        if st.session_state.pending_records:
            st.session_state.pending_records.pop()

        reset_timer()
        scroll_top()
        st.rerun()


# ─────────────────────────────────────────────
# 頁面 5：完成
# ─────────────────────────────────────────────
def render_done():
    if not st.session_state.get("cloud_sync_attempted"):
        st.session_state["cloud_sync_attempted"] = True

        try:
            rows = [
                {col: r.get(col, "") for col in DATA_COLUMNS}
                for r in st.session_state.get("final_records", [])
            ]
            ok, msg = sync_to_cloud(rows)
            st.session_state["last_save_message"] = msg

        except Exception as e:
            st.session_state["last_save_message"] = f"CSV 已儲存，Google Sheet 同步失敗：{e}"

    msg = st.session_state.get("last_save_message", "")
    left, center, right = st.columns([1, 2.2, 1])

    with center:
        st.markdown(
            """<div style="text-align:center;padding:36px 20px 24px;">
            <div style="font-size:52px;margin-bottom:12px;">🎉</div>
            <div class="main-title" style="text-align:center;">版本 B 標註完成！</div>
            <div class="sub-title" style="text-align:center;margin-top:4px;">
                感謝您完成版本 B 的家貓情緒標註<br>請通知實驗人員您已完成。
            </div></div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="version-badge">版本 B</div>',
            unsafe_allow_html=True,
        )

        if msg and "失敗" not in msg and "未設定" not in msg:
            st.success(f"☁️ {msg}")

        elif msg and ("失敗" in msg or "未設定" in msg):
            st.warning(f"⚠️ {msg}")

            if st.button("重新上傳至 Google Sheet", type="primary", use_container_width=True):
                try:
                    rows = [
                        {col: r.get(col, "") for col in DATA_COLUMNS}
                        for r in st.session_state.get("final_records", [])
                    ]
                    _, msg2 = sync_to_cloud(rows)
                    st.session_state["last_save_message"] = msg2
                    st.rerun()

                except Exception as e:
                    st.session_state["last_save_message"] = f"同步失敗：{e}"
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if OUTPUT_CSV.exists():
            st.download_button(
                "📥 下載版本 B CSV 備份",
                OUTPUT_CSV.read_bytes(),
                file_name=OUTPUT_CSV.name,
                mime="text/csv",
                use_container_width=True,
            )

        st.divider()

        if st.button("↩ 回首頁重新開始", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            scroll_top()
            st.rerun()


# ─────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────
def main():
    init_state()
    st.markdown('<div id="page_top_anchor"></div>', unsafe_allow_html=True)

    page = st.session_state.page

    if page == "intro":
        render_intro()
    elif page == "background":
        render_background()
    elif page == "task":
        render_task()
    elif page == "overall_feedback":
        render_overall_feedback()
    elif page == "done":
        render_done()

    do_scroll()


if __name__ == "__main__":
    main()
