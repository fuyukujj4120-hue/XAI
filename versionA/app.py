"""
家貓情緒標註研究系統
版本 A：無部位特徵提示
流程：受試者基本資料 → 照片標註（直覺式）→ 整體反饋 → 完成
"""

import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# 基本設定
# ─────────────────────────────────────────────
APP_PAGE_TITLE = "🐱 家貓情緒標註｜版本 A：無部位特徵提示"
OUTPUT_CSV = Path("annotation_version_a.csv")
BASE_DIR = Path(__file__).resolve().parent
ANNOTATION_DIR = BASE_DIR / "annotations"

SHEET_WEBHOOK_URL = ""   # 填入 Google Apps Script URL 即可啟用雲端同步
SHEET_SECRET = "hci_cat_annotation_secret"

# ─────────────────────────────────────────────
# 照片清單（請依實際路徑修改）
# ─────────────────────────────────────────────
IMAGES = [
    {"image_id": "cat_easy",   "difficulty": "易", "path": str(ANNOTATION_DIR / "cat_easy.jpg")},
    {"image_id": "cat_medium", "difficulty": "中", "path": str(ANNOTATION_DIR / "cat_medium.jpg")},
    {"image_id": "cat_hard",   "difficulty": "難", "path": str(ANNOTATION_DIR / "cat_hard.jpg")},
]

# ─────────────────────────────────────────────
# 情緒選項
# ─────────────────────────────────────────────
EMOTION_OPTIONS = [
    "害怕／焦慮",
    "生氣／防衛",
    "放鬆／滿意",
    "興趣／警覺",
    "中性",
    "其他／無法判斷",
]
EMOTION_ICONS = {
    "害怕／焦慮":    "😿",
    "生氣／防衛":    "😾",
    "放鬆／滿意":    "😽",
    "興趣／警覺":    "🐾",
    "中性":          "➖",
    "其他／無法判斷": "❓",
}
EMOTION_DEFINITIONS = {
    "害怕／焦慮":    "耳朵後壓、身體壓低、瞳孔放大、試圖退縮或警戒",
    "生氣／防衛":    "身體緊繃、耳朵側壓或後壓、尾巴快速擺動、露齒或攻擊姿勢",
    "放鬆／滿意":    "眼睛半閉、姿勢放鬆、耳朵自然、與環境互動平穩",
    "興趣／警覺":    "注意力明顯集中、耳朵朝向刺激來源、身體前傾或探索姿勢",
    "中性":          "無明顯正向或負向情緒線索，整體狀態平穩",
    "其他／無法判斷": "影像品質不足、線索不足、多種情緒並存或超出現有分類",
}

UNCERTAIN_REASONS = ["影像品質不足", "線索不足", "多種情緒並存", "超出現有分類", "其他"]

LIKERT_OPTIONS  = ["非常不同意", "不同意", "普通", "同意", "非常同意"]
LIKERT_SCORE_MAP = {"非常不同意": 1, "不同意": 2, "普通": 3, "同意": 4, "非常同意": 5}

OVERALL_QUESTIONS = [
    ("overall_easy",                "Q1：在本次標註過程中，我覺得判斷家貓情緒是容易的。"),
    ("overall_intuition",           "Q2：在本次標註過程中，我是依靠直覺判斷家貓情緒。"),
    ("overall_explainable",         "Q3：在本次標註過程中，我能明確說明自己為什麼選擇該情緒。"),
    ("overall_observation_clarity", "Q4：在本次標註過程中，我能清楚知道應該優先觀察哪些部位來判斷情緒。"),
]

DATA_COLUMNS = [
    "annotator_id", "questionnaire_version",
    "has_cat_experience", "current_cat_owner",
    "cat_understanding_score", "animal_related_background", "prior_knowledge_group",
    "image_id", "difficulty", "condition",
    "final_emotion", "confidence", "difficulty_score",
    "uncertain_reason", "additional_note",
    "overall_easy", "overall_intuition", "overall_explainable", "overall_observation_clarity",
]

# ─────────────────────────────────────────────
# 頁面設定 & CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.stApp { background: #f0f6ff; }
.main-title {
    font-family: 'Noto Serif TC', serif; font-size: 24px; font-weight: 700;
    color: #0d2b4f; letter-spacing: 0.04em; margin-bottom: 4px;
}
.sub-title { color: #4a6fa5; font-size: 14px; margin-bottom: 20px; }
h2 {
    font-family: 'Noto Serif TC', serif !important; font-size: 17px !important;
    font-weight: 700 !important; color: #1a3a6b !important;
    border-bottom: 2px solid #85c1e9; padding-bottom: 6px;
    margin-top: 22px !important; margin-bottom: 10px !important;
}
h3 { font-size: 15px !important; color: #1a5276 !important; margin-top: 16px !important; }
h4 { font-size: 14px !important; color: #2874a6 !important; margin-top: 12px !important; }
.version-badge {
    display: inline-block; background: #d6eaf8; color: #1a5276;
    border: 1.5px solid #85c1e9; border-radius: 20px;
    padding: 4px 16px; font-size: 13px; font-weight: 700;
    letter-spacing: 0.06em; margin-bottom: 14px;
}
.info-card {
    padding: 14px 18px; border: 1px solid #aed6f1;
    border-left: 4px solid #2980b9; border-radius: 4px;
    background: #ebf5fb; margin-bottom: 14px;
    font-size: 14px; line-height: 1.7; color: #1a3a6b;
}
.warn-card {
    padding: 12px 16px; border-radius: 4px; background: #fffbf0;
    border: 1px solid #f9e79f; border-left: 4px solid #f1c40f;
    margin: 10px 0 14px 0; font-size: 13px; color: #5a4000;
}
.emo-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; border-radius: 6px;
    background: #ebf5fb; border: 1px solid #aed6f1;
    margin-bottom: 7px; font-size: 13px; line-height: 1.6;
}
.emo-row .icon { font-size: 20px; min-width: 28px; }
.emo-row .name { font-weight: 700; color: #1a5276; min-width: 90px; }
.emo-row .def  { color: #2874a6; }
.placeholder {
    height: 380px; border: 1.5px dashed #85c1e9; border-radius: 8px;
    background: linear-gradient(160deg, #ebf5fb 0%, #d6eaf8 100%);
    display: flex; align-items: center; justify-content: center;
    color: #4a6fa5; font-size: 15px; text-align: center; padding: 20px;
}
section[data-testid="stSidebar"] {
    width: 460px !important; min-width: 460px !important;
    background: #e8f4fd !important; border-right: 1px solid #aed6f1;
}
section[data-testid="stSidebar"] img {
    max-height: 460px; object-fit: contain; border-radius: 8px;
    box-shadow: 0 2px 12px rgba(41,128,185,0.18);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2980b9 0%, #1a5276 100%) !important;
    color: #fff !important; border: none !important; border-radius: 4px !important;
    font-size: 14px !important; font-weight: 700 !important; padding: 10px 24px !important;
}
.stButton > button:not([kind="primary"]) {
    background: #ebf5fb !important; color: #1a5276 !important;
    border: 1.5px solid #85c1e9 !important; border-radius: 4px !important;
}
.progress-tip { font-size: 12.5px; color: #4a6fa5; margin: 6px 0 14px 0; }
.complete-tip { font-size: 12.5px; color: #1a8a4a; font-weight: 600; margin: 6px 0 14px 0; }
hr { border-color: #aed6f1 !important; margin: 16px 0 !important; }
</style>
""", unsafe_allow_html=True)

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
        components.html("""<script>
        function t(){try{window.parent.scrollTo(0,0);
        ['section.main','main','.stApp'].forEach(function(s){
        window.parent.document.querySelectorAll(s).forEach(function(el){el.scrollTop=0;});});}catch(e){}}
        t();[100,300,600].forEach(function(d){setTimeout(t,d);});
        </script>""", height=0)


def reset_timer():
    st.session_state.task_start_time = time.time()


def current_image():
    idx = st.session_state.image_index
    return IMAGES[idx] if idx < len(IMAGES) else None


def compute_group():
    exp   = st.session_state.has_cat_experience
    score = st.session_state.cat_understanding_score or 0
    return "高先備知識" if (exp == "是" or score >= 4) else "低先備知識"


def base_fields():
    return {
        "annotator_id":           st.session_state.annotator_id,
        "questionnaire_version":  "A",
        "has_cat_experience":     st.session_state.has_cat_experience or "",
        "current_cat_owner":      st.session_state.current_cat_owner or "",
        "cat_understanding_score": st.session_state.cat_understanding_score or "",
        "animal_related_background": st.session_state.animal_related_background or "",
        "prior_knowledge_group":  st.session_state.prior_knowledge_group,
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
    resp = requests.post(SHEET_WEBHOOK_URL,
                         json={"secret": SHEET_SECRET, "records": rows}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "Unknown error"))
    return True, f"已同步 {data.get('inserted', len(rows))} 筆至 Google Sheet。"


# ─────────────────────────────────────────────
# 頁面 1：首頁
# ─────────────────────────────────────────────

def render_intro():
    st.markdown('<div class="version-badge">版本 A：無部位特徵提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">🐱 家貓情緒標註研究</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">版本 A：請直接觀看照片，依直覺選擇情緒類別。</div>', unsafe_allow_html=True)

    annotator_id = st.text_input("受試者學號／代號", value=st.session_state.annotator_id)
    st.session_state.annotator_id = annotator_id.strip()

    st.markdown("### 情緒類別定義參考")
    for emo, defn in EMOTION_DEFINITIONS.items():
        icon = EMOTION_ICONS.get(emo, "")
        st.markdown(
            f'<div class="emo-row"><span class="icon">{icon}</span>'
            f'<span class="name">{emo}</span><span class="def">{defn}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("開始標註 →", type="primary",
                 disabled=not bool(st.session_state.annotator_id)):
        st.session_state.page = "background"
        scroll_top(); st.rerun()


# ─────────────────────────────────────────────
# 頁面 2：先備知識問卷
# ─────────────────────────────────────────────

def render_background():
    st.markdown('<div class="version-badge">版本 A：無部位特徵提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">受試者基本資料</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">請回答以下問題，作為後續分析的分組依據。</div>', unsafe_allow_html=True)

    has_exp = st.radio("1. 您是否曾經養過貓？", ["是", "否"], index=None, key="bg_exp")
    cur_own = st.radio("2. 您目前是否有養貓？", ["是", "否"], index=None, key="bg_own")
    understand = st.radio(
        "3. 您對貓咪行為的了解程度（1=非常不了解，5=非常了解）",
        [1, 2, 3, 4, 5], index=None, horizontal=True, key="bg_understand",
    )
    bg = st.radio(
        "4. 您是否具有動物照護、獸醫、動物行為或相關背景？",
        ["是", "否"], index=None, key="bg_background",
    )

    ready = all(v is not None for v in [has_exp, cur_own, understand, bg])
    if st.button("完成填寫，進入標註 →", type="primary", disabled=not ready):
        st.session_state.has_cat_experience      = has_exp
        st.session_state.current_cat_owner       = cur_own
        st.session_state.cat_understanding_score = understand
        st.session_state.animal_related_background = bg
        st.session_state.prior_knowledge_group   = compute_group()
        st.session_state.page = "task"
        st.session_state.image_index = 0
        st.session_state.pending_records = []
        reset_timer(); scroll_top(); st.rerun()

    st.divider()
    if st.button("← 上一頁"):
        st.session_state.page = "intro"; scroll_top(); st.rerun()


# ─────────────────────────────────────────────
# 頁面 3：照片標註（版本 A）
# ─────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        image = current_image()
        st.markdown('<div class="version-badge" style="margin-bottom:10px;">版本 A：無部位特徵提示</div>',
                    unsafe_allow_html=True)
        st.markdown("### 家貓照片")
        if image is None:
            st.info("所有照片已完成標註。"); return
        idx = st.session_state.image_index
        st.caption(f"第 {idx+1} / {len(IMAGES)} 張｜難易度：{image['difficulty']}｜{image['image_id']}")
        path = image.get("path", "")
        if path and Path(path).exists():
            st.image(path, use_container_width=True)
        else:
            st.markdown(
                f'<div class="placeholder">🐱 照片預覽區<br><small>{image["image_id"]}</small></div>',
                unsafe_allow_html=True,
            )
        # 情緒定義快速查看
        st.markdown("---")
        st.markdown("**📖 情緒定義**")
        for emo, defn in EMOTION_DEFINITIONS.items():
            with st.expander(f"{EMOTION_ICONS.get(emo,'')} {emo}", expanded=False):
                st.caption(defn)


def render_task():
    render_sidebar()
    image = current_image()
    if image is None:
        st.session_state.page = "overall_feedback"; scroll_top(); st.rerun(); return

    idx = st.session_state.image_index
    prefix = f"a_i{idx}"

    st.markdown('<div class="version-badge">版本 A：無部位特徵提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">🐱 家貓情緒標註</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="info-card">請直接觀看左側照片，依照您的直覺與觀察選擇最符合的情緒。<br>'
        f'<b>第 {idx+1} / {len(IMAGES)} 張</b>｜難易度：{image["difficulty"]}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.task_start_time is None:
        reset_timer()

    # Step 1
    st.markdown("## Step 1：觀看家貓照片")
    st.write("請仔細觀察左側照片後再作答。")

    # Step 2：選擇情緒
    st.markdown("## Step 2：選擇主要情緒")
    final_emotion = st.radio(
        "請選擇最符合的情緒",
        EMOTION_OPTIONS, index=None,
        key=f"{prefix}_emotion",
        format_func=lambda x: f"{EMOTION_ICONS.get(x,'')} {x}",
    )

    uncertain_reason = ""
    if final_emotion == "其他／無法判斷":
        st.markdown('<div class="warn-card">請說明「其他／無法判斷」的原因：</div>',
                    unsafe_allow_html=True)
        uncertain_reason = st.radio(
            "原因", UNCERTAIN_REASONS, index=None, key=f"{prefix}_uncertain"
        ) or ""

    # Step 3：信心
    st.markdown("## Step 3：填寫標註信心")
    confidence = st.radio(
        "信心程度（1=非常沒信心，5=非常有信心）",
        [1, 2, 3, 4, 5], index=None, horizontal=True, key=f"{prefix}_conf",
    )

    # Step 4：難度
    st.markdown("## Step 4：填寫判斷難度")
    difficulty_score = st.radio(
        "判斷難度（1=非常容易，5=非常困難）",
        [1, 2, 3, 4, 5], index=None, horizontal=True, key=f"{prefix}_diff",
    )

    additional_note = st.text_area(
        "補充說明（選填）", key=f"{prefix}_note", height=75,
        placeholder="例如：主要觀察耳朵方向、整體感覺很緊繃…",
    )

    required_ok = (
        bool(final_emotion) and confidence is not None and difficulty_score is not None
        and (final_emotion != "其他／無法判斷" or bool(uncertain_reason))
    )

    if st.button("送出此張標註 →", type="primary", disabled=not required_ok):
        record = {
            **base_fields(),
            "image_id":       image["image_id"],
            "difficulty":     image["difficulty"],
            "condition":      "無部位特徵提示",
            "final_emotion":  final_emotion,
            "confidence":     confidence,
            "difficulty_score": difficulty_score,
            "uncertain_reason": uncertain_reason,
            "additional_note":  additional_note,
            # 整體反饋稍後填
            "overall_easy": "", "overall_intuition": "",
            "overall_explainable": "", "overall_observation_clarity": "",
        }
        st.session_state.pending_records.append(record)
        st.session_state.image_index += 1
        reset_timer()
        if st.session_state.image_index >= len(IMAGES):
            st.session_state.page = "overall_feedback"
        scroll_top(); st.rerun()

    st.divider()
    if idx > 0 and st.button("← 上一張"):
        st.session_state.image_index -= 1
        if st.session_state.pending_records:
            st.session_state.pending_records.pop()
        reset_timer(); scroll_top(); st.rerun()


# ─────────────────────────────────────────────
# 頁面 4：整體反饋問卷
# ─────────────────────────────────────────────

def render_overall_feedback():
    st.markdown('<div class="version-badge">版本 A：無部位特徵提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">📋 整體標註體驗反饋</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">以下題目請針對剛才所有照片的標註過程整體評估（非單張照片）。</div>',
        unsafe_allow_html=True,
    )

    scores = {}
    for field, question in OVERALL_QUESTIONS:
        clean_q = question.rstrip("。")
        st.markdown(
            f'<div style="background:#ebf5fb;border:1.5px solid #aed6f1;border-radius:10px;'
            f'padding:16px 20px;margin-bottom:14px;">'
            f'<div style="font-family:Noto Serif TC,serif;font-size:16px;font-weight:700;'
            f'color:#1a3a6b;margin-bottom:10px;">{clean_q}</div></div>',
            unsafe_allow_html=True,
        )
        choice = st.radio(
            clean_q, LIKERT_OPTIONS, index=None, horizontal=True,
            key=f"overall_{field}", label_visibility="collapsed",
        )
        scores[field] = LIKERT_SCORE_MAP.get(choice) if choice else None

    answered = sum(1 for v in scores.values() if v is not None)
    total = len(scores)
    complete = answered == total

    if complete:
        st.markdown('<div class="complete-tip">✅ 所有題目已填答完畢！</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="progress-tip">已填答 {answered} / {total} 題。</div>',
                    unsafe_allow_html=True)

    if st.button("完成標註，儲存資料 →", type="primary", disabled=not complete,
                 use_container_width=True):
        final_records = []
        for rec in st.session_state.pending_records:
            r = dict(rec)
            for field, _ in OVERALL_QUESTIONS:
                r[field] = scores[field]
            final_records.append(r)
        st.session_state.final_records = final_records
        save_records(final_records)
        st.session_state.page = "done"
        scroll_top(); st.rerun()

    st.divider()
    if st.button("← 返回最後一張照片"):
        st.session_state.page = "task"
        st.session_state.image_index = len(IMAGES) - 1
        if st.session_state.pending_records:
            st.session_state.pending_records.pop()
        reset_timer(); scroll_top(); st.rerun()


# ─────────────────────────────────────────────
# 頁面 5：完成
# ─────────────────────────────────────────────

def render_done():
    if not st.session_state.get("cloud_sync_attempted"):
        st.session_state["cloud_sync_attempted"] = True
        try:
            rows = [{col: r.get(col, "") for col in DATA_COLUMNS}
                    for r in st.session_state.get("final_records", [])]
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
            <div class="main-title" style="text-align:center;">版本 A 標註完成！</div>
            <div class="sub-title" style="text-align:center;margin-top:4px;">
                感謝您完成版本 A 的家貓情緒標註<br>請通知實驗人員您已完成。
            </div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="version-badge">版本 A：無部位特徵提示</div>', unsafe_allow_html=True)

        if msg and "失敗" not in msg and "未設定" not in msg:
            st.success(f"☁️ {msg}")
        elif msg and ("失敗" in msg or "未設定" in msg):
            st.warning(f"⚠️ {msg}")
            if st.button("重新上傳至 Google Sheet", type="primary", use_container_width=True):
                try:
                    rows = [{col: r.get(col, "") for col in DATA_COLUMNS}
                            for r in st.session_state.get("final_records", [])]
                    _, msg2 = sync_to_cloud(rows)
                    st.session_state["last_save_message"] = msg2
                    st.rerun()
                except Exception as e:
                    st.session_state["last_save_message"] = f"同步失敗：{e}"
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if OUTPUT_CSV.exists():
            st.download_button("📥 下載版本 A CSV 備份",
                               OUTPUT_CSV.read_bytes(),
                               file_name=OUTPUT_CSV.name,
                               mime="text/csv",
                               use_container_width=True)
        st.divider()
        if st.button("↩ 回首頁重新開始", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            scroll_top(); st.rerun()


# ─────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────

def main():
    init_state()
    st.markdown('<div id="page_top_anchor"></div>', unsafe_allow_html=True)
    page = st.session_state.page
    if   page == "intro":             render_intro()
    elif page == "background":        render_background()
    elif page == "task":              render_task()
    elif page == "overall_feedback":  render_overall_feedback()
    elif page == "done":              render_done()
    do_scroll()

if __name__ == "__main__":
    main()
