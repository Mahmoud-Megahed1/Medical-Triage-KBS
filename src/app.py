# -*- coding: utf-8 -*-
"""
Medical Triage & Emergency Knowledge-Based System (IS438)
Bilingual (EN / AR BiDi-Safe) Knowledge Graph & Rule-Based Deductive Inference Dashboard
Course: New Trends in Information Systems (IS438) - Damietta University
Supervisor: Dr. Aya Gamal | TA: Eng. Amal
"""

import os
import html
import streamlit as st
import streamlit.components.v1 as components
from inference_engine import MedicalTriageEngine, ESI_METADATA

st.set_page_config(
    page_title="Medical Triage KBS | IS438",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================================
# BILINGUAL ARABIC EXPLANATION DICTIONARIES (BiDi-Safe UI Layer)
# ==================================================================
ESI_AR = {
    "ESI-1": "المستوى الأول — حالة حرجة تتطلب تدخل إنعاش فوري الآن بدون أي انتظار",
    "ESI-2": "المستوى الثاني — طوارئ عاجلة ذات خطورة عالية (الحد الأقصى للانتظار عشر دقائق)",
    "ESI-3": "المستوى الثالث — حالة عاجلة تحتاج تقييم سريع وفحوصات في قسم الطوارئ",
    "ESI-4": "المستوى الرابع — حالة أقل استعجالاً مناسبة لمسار الكشف السريع",
    "ESI-5": "المستوى الخامس — حالة مستقرة غير طارئة توجَّه للكشف العادي بالعيادة الخارجية",
}

COND_AR = {
    "COND01": "اشتباه جلطة أو قصور حاد في الشريان التاجي للقلب",
    "COND02": "اشتباه سكتة دماغية حادة أو جلطة مخية عابرة",
    "COND03": "صدمة تحسسية حادة مع خطورة انسداد مجرى التنفس",
    "COND04": "اشتباه التهاب سحائي بكتيري في أغشية المخ",
    "COND05": "تسمم دموي أو عدوى جهازية حادة مع اضطراب العلامات الحيوية",
    "COND06": "حماض كيتوني سكري حاد (ارتفاع شديد بالسكر والأسيتون)",
    "COND07": "أزمة ارتفاع ضغط الدم الحاد مع أعراض خطورة",
    "COND08": "أزمة ربو شعبي حادة وضيق تنفس شديد",
    "COND09": "اشتباه التهاب حاد في الزائدة الدودية",
    "COND10": "التهاب رئوي مكتسب يتطلب أشعة ومضادات حيوية",
    "COND11": "نزلة معوية حادة مع احتمالية جفاف",
    "COND12": "نوبة صداع نصفي حادة بدون علامات خطورة عصبية",
    "COND13": "عدوى فيروسية بسيطة في الجهاز التنفسي العلوي",
}

SYM_AR = {
    "SYM01": "ألم ضاغط شديد بالصدر",
    "SYM02": "ألم يمتد للذراع الأيسر أو الفك",
    "SYM03": "ضيق شديد في التنفس",
    "SYM04": "اعوجاج مفاجئ بالوجه أو ضعف بالذراع",
    "SYM05": "ثقل في النطق أو تشوش ذهني مفاجئ",
    "SYM06": "تيبس في الرقبة مع حساسية شديدة للضوء",
    "SYM07": "تورم بالحلق أو صعوبة حادة في البلع والتنفس",
    "SYM08": "ألم موضعي أسفل يمين البطن",
    "SYM09": "حمى مرتفعة مستمرة",
    "SYM10": "أزيز بالصدر وصعوبة في الزفير",
    "SYM11": "صداع شديد مفاجئ",
    "SYM12": "صداع نصفي نابض مصحوب بزغللة",
    "SYM13": "سعال مصحوب ببلغم صديدي",
    "SYM14": "قيء وإسهال مستمر",
    "SYM15": "التهاب بسيط بالحلق واحتقان بالأنف",
    "SYM16": "ارتفاع طفيف في درجة الحرارة",
    "SYM17": "طفح جلدي عام أو حساسية جلدية",
    "SYM18": "دوخة شديدة أو شبه إغماء",
    "SYM19": "عطش شديد ورائحة أسيتون بالفم",
    "SYM20": "تشوش بالرؤية مع صداع شديد",
    "SYM21": "تعرق بارد مفاجئ",
    "SYM22": "قشعريرة شديدة واضطراب بالوعي",
    "SYM23": "تكسير خفيف بالجسم وإرهاق عام",
    "SYM24": "ألم ارتدادي حاد عند فحص البطن",
}

ACTION_AR = {
    "IMMEDIATE_INTERVENTION": "تدخل طبي عاجل",
    "DIAGNOSTIC_WORKUP": "فحوصات وتحاليل مطلوبة",
    "CONTRAINDICATION": "تحذير وممنوع طبياً",
}

# ==================================================================
# CLEAN LIGHT MODE DESIGN SYSTEM (Geist + Cairo + BiDi Isolation)
# ==================================================================
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;600;700;800&family=Geist:wght@400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg: #ffffff;
    --bg-subtle: #f8fafc;
    --bg-sidebar: #f3f4f6;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --text: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --accent: #2563eb;
    --accent-soft: #eff6ff;
    --esi1: #dc2626;
    --esi1-soft: #fef2f2;
    --esi2: #ea580c;
    --esi2-soft: #fff7ed;
    --esi3: #d97706;
    --esi3-soft: #fffbeb;
    --esi4: #059669;
    --esi4-soft: #ecfdf5;
    --esi5: #2563eb;
    --esi5-soft: #eff6ff;
    --purple: #7c3aed;
    --purple-soft: #f5f3ff;
    --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Geist Mono', Consolas, monospace;
    --font-ar: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
}

html, body, [class*="css"], .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .main .block-container {
    font-family: var(--font-sans) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Full-width content expansion when sidebar is open or collapsed */
[data-testid="stMainBlockContainer"],
.stMainBlockContainer,
[data-testid="stAppViewBlockContainer"],
.main .block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    padding-top: 2.2rem !important;
}

h1, h2, h3, h4, h5, h6,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: var(--text) !important;
    font-family: var(--font-sans) !important;
    font-weight: 700 !important;
}

a, a:visited, a:hover, a:active {
    color: var(--accent) !important;
    text-decoration: none !important;
}

/* ===== BiDi-SAFE ARABIC ISOLATION CLASSES ===== */
.ar-box {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: isolate !important;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-right: 3px solid #2563eb;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0 14px 0;
    font-size: 13px;
    color: #1e293b;
    line-height: 1.65;
}
.ar-sub {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: isolate !important;
    font-size: 12px;
    color: #475569;
    margin-top: 3px;
    line-height: 1.5;
}
.ar-cell {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    text-align: center !important;
    unicode-bidi: isolate !important;
    font-size: 11.5px;
    color: #475569;
    margin-top: 4px;
    line-height: 1.45;
}
.ar-pill {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    unicode-bidi: isolate !important;
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 5px;
    padding: 1px 7px;
    font-size: 11px;
    font-weight: 600;
}

/* Sidebar (only enforce width when expanded; collapse cleanly to 0px so main fills screen) */
[data-testid="stSidebar"][aria-expanded="true"],
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
    min-width: 355px !important;
    max-width: 405px !important;
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0 !important;
    width: 0 !important;
    max-width: 0 !important;
    margin-left: 0 !important;
    overflow: hidden !important;
    border-right: none !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.7rem !important;
}
[data-testid="stSidebar"] label {
    color: var(--text-secondary) !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.45px !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 15px !important;
    margin-bottom: 2px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 18px !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* Header */
.top-header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 14px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
}
.brand-title {
    font-size: 22px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.4px;
    margin: 0;
    line-height: 1.3;
}
.brand-meta {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 3px;
}
.tech-badge {
    display: inline-flex;
    align-items: center;
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    padding: 5px 12px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-secondary);
    letter-spacing: 0.4px;
    text-transform: uppercase;
    white-space: nowrap;
}

/* Disposition Banner */
.triage-banner {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}
.triage-banner-title {
    font-size: 16px;
    font-weight: 800;
    margin: 0;
    direction: ltr;
    text-align: left;
}
.triage-banner-sub {
    font-size: 13px;
    margin-top: 4px;
    direction: ltr;
    text-align: left;
}
.triage-banner-ar {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: isolate !important;
    font-size: 13.5px;
    font-weight: 700;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed rgba(0, 0, 0, 0.12);
}

/* KPI Grid */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 18px;
}
.kpi-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
}
.kpi-label {
    font-size: 10.5px;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.kpi-ar-title {
    font-family: var(--font-ar) !important;
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: isolate !important;
    font-size: 11.5px;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 21px;
    font-weight: 800;
    font-family: var(--font-mono);
    line-height: 1.2;
}
.kpi-sub {
    font-size: 11.5px;
    color: var(--text-muted);
    margin-top: 5px;
}

/* Sidebar Cards */
.detail-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0 8px 0;
    font-size: 12.5px;
}
.detail-row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    color: var(--text-muted);
}
.detail-row strong {
    color: var(--text);
    font-weight: 600;
}
.vitals-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-top: 4px;
}
.vital-pill {
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 11.5px;
}
.vital-pill span {
    display: block;
    color: var(--text-muted);
    font-size: 10px;
    text-transform: uppercase;
}
.vital-pill strong {
    font-family: var(--font-mono);
    color: var(--text);
    font-size: 12.5px;
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 18px 0;
    font-size: 13px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    direction: ltr;
    text-align: left;
}
.data-table th {
    background: var(--bg-subtle);
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.45px;
    padding: 10px 12px;
    text-align: center;
    vertical-align: middle;
    border-bottom: 1px solid var(--border);
}
.data-table td {
    text-align: center;
    vertical-align: middle;
    padding: 10px 12px;
    border-bottom: 1px solid #f1f5f9;
    color: var(--text-secondary);
    font-size: 13px;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }

/* Badges */
.badge {
    font-family: var(--font-mono);
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    display: inline-block;
    white-space: nowrap;
}
.b-code { background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(37,99,235,0.22); }
.b-esi1 { background: var(--esi1-soft); color: var(--esi1); border: 1px solid rgba(220,38,38,0.28); }
.b-esi2 { background: var(--esi2-soft); color: var(--esi2); border: 1px solid rgba(234,88,12,0.28); }
.b-esi3 { background: var(--esi3-soft); color: var(--esi3); border: 1px solid rgba(217,119,6,0.28); }
.b-esi4 { background: var(--esi4-soft); color: var(--esi4); border: 1px solid rgba(5,150,105,0.25); }
.b-esi5 { background: var(--esi5-soft); color: var(--esi5); border: 1px solid rgba(37,99,235,0.25); }
.b-purple { background: var(--purple-soft); color: var(--purple); border: 1px solid rgba(124,58,237,0.25); }
.b-neutral { background: #f1f5f9; color: var(--text-secondary); border: 1px solid var(--border); }

.sec-desc {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 6px;
    line-height: 1.55;
    direction: ltr;
    text-align: left;
}
.empty-state {
    background: var(--esi4-soft);
    border: 1px solid rgba(5,150,105,0.2);
    border-radius: 8px;
    padding: 12px 16px;
    color: var(--esi4);
    font-size: 13px;
}
.mode-badge {
    margin-top: 10px;
    padding: 7px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-muted);
}
.graph-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 12px;
    color: var(--text-secondary);
}
.legend-item { display: inline-flex; align-items: center; gap: 6px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.legend-box { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

iframe {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
</style>
"""

st.html(THEME_CSS)


def esc(val: object) -> str:
    return html.escape(str(val))


def esi_badge(esi: str) -> str:
    cls_map = {
        "ESI-1": "b-esi1",
        "ESI-2": "b-esi2",
        "ESI-3": "b-esi3",
        "ESI-4": "b-esi4",
        "ESI-5": "b-esi5",
    }
    return f'<span class="badge {cls_map.get(esi, "b-neutral")}">{esc(esi)}</span>'


def render_table(headers: list, rows: list, widths: list = None) -> str:
    ws = widths or [""] * len(headers)
    th = "".join(
        f'<th style="width:{w};">{esc(h)}</th>' if w else f"<th>{esc(h)}</th>"
        for h, w in zip(headers, ws)
    )
    trs = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="data-table"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


@st.cache_resource
def load_triage_engine():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    return MedicalTriageEngine(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password123",
        data_dir=data_path,
    )


engine = load_triage_engine()
patients_map = engine.get_patients()
all_symptoms = engine.get_all_symptoms()
all_risks = engine.get_all_risk_factors()

# ==================================================================
# SIDEBAR: PATIENT RECORD SELECTOR & VITALS (BILINGUAL BiDi-SAFE)
# ==================================================================
st.sidebar.markdown("### Triage Intake Controls")
st.sidebar.html(
    '<div class="ar-sub" dir="rtl" style="margin-bottom:10px;">'
    'لوحة التحكم لاختيار سجل المريض وعرض علاماته الحيوية قبل تشغيل محرك الاستدلال.'
    '</div>'
)

patient_ids = list(patients_map.keys())
selected_pid = st.sidebar.selectbox(
    "Patient ID (رقم المريض)",
    options=patient_ids,
    format_func=lambda pid: f"{pid} - {patients_map[pid]['name']}",
)

pat_rec, pat_syms, pat_risks = engine.get_patient_case(selected_pid)

st.sidebar.html(
    f'<div class="detail-card">'
    f'<div class="detail-row"><span>Patient</span><strong>{esc(pat_rec["name"])}</strong></div>'
    f'<div class="detail-row"><span>Age / Gender</span><strong>{esc(pat_rec["age"])} yrs / {esc(pat_rec["gender"])}</strong></div>'
    f'<div class="detail-row"><span>Symptoms</span><strong>{len(pat_syms)} reported</strong></div>'
    f'<div class="detail-row"><span>Risk Factors</span><strong>{len(pat_risks)} active</strong></div>'
    f'<div class="ar-sub" dir="rtl">ملخص بيانات الحالة المسجلة وعدد الأعراض وعوامل الخطورة.</div>'
    f'</div>'
)

st.sidebar.markdown("#### Recorded Vital Signs")
st.sidebar.html(
    f'<div class="ar-sub" dir="rtl" style="margin-bottom:6px;">العلامات الحيوية المقاسة للمريض</div>'
    f'<div class="vitals-grid">'
    f'<div class="vital-pill"><span>Heart Rate (النبض)</span><strong>{esc(pat_rec["hr_bpm"])} bpm</strong></div>'
    f'<div class="vital-pill"><span>BP (ضغط الدم)</span><strong>{esc(pat_rec["bp_sys"])}/{esc(pat_rec["bp_dia"])}</strong></div>'
    f'<div class="vital-pill"><span>SpO2 (الأكسجين)</span><strong>{esc(pat_rec["spo2_pct"])}%</strong></div>'
    f'<div class="vital-pill"><span>Temp / RR (الحرارة / التنفس)</span><strong>{esc(pat_rec["temp_c"])} C | {esc(pat_rec["rr_bpm"])}/min</strong></div>'
    f'</div>'
)

st.sidebar.html(
    f'<div class="detail-card" style="margin-top:10px;">'
    f'<div style="font-size:10.5px;color:#64748b;text-transform:uppercase;font-weight:700;margin-bottom:4px;">Chief Complaint <span class="ar-pill" dir="rtl">الشكوى الرئيسية</span></div>'
    f'<div style="color:#0f172a;font-size:12px;line-height:1.45;">{esc(pat_rec["chief_complaint"])}</div>'
    f'</div>'
)

st.sidebar.html(
    f'<div class="mode-badge">'
    f'<div>GRAPH ENGINE: {esc(engine.mode)}</div>'
    f'<div class="ar-sub" dir="rtl" style="font-size:10.5px;">وضع التشغيل الحالي لقاعدة المعرفة</div>'
    f'</div>'
)

# ==================================================================
# RUN INFERENCE ENGINE
# ==================================================================
trace = engine.evaluate_patient(selected_pid)
esi_meta = ESI_METADATA[trace.triage_level]
esi_color = esi_meta["color"]

banner_bg_map = {
    "ESI-1": ("#fef2f2", "#fecaca", "#991b1b"),
    "ESI-2": ("#fff7ed", "#fed7aa", "#9a3412"),
    "ESI-3": ("#fffbeb", "#fde68a", "#92400e"),
    "ESI-4": ("#ecfdf5", "#a7f3d0", "#065f46"),
    "ESI-5": ("#eff6ff", "#bfdbfe", "#1e40af"),
}
b_bg, b_border, b_text = banner_bg_map.get(trace.triage_level, ("#f8fafc", "#e2e8f0", "#0f172a"))

# Header
st.html(
    '<div class="top-header">'
    '<div>'
    '<h1 class="brand-title">Medical Triage &amp; Emergency Priority Knowledge System</h1>'
    '<div class="brand-meta">Rule-Based Clinical Inference &amp; Knowledge Graph Traversal Engine</div>'
    '<div class="ar-sub" dir="rtl" style="font-size:13px;color:#1e293b;font-weight:600;">'
    'نظام الفرز الطبي وتحديد أولوية الطوارئ القائم على شبكة المعرفة وقواعد الاستدلال المنطقي'
    '</div>'
    '</div>'
    '<div><span class="tech-badge">IS438 • Knowledge-Based Systems</span></div>'
    '</div>'
)

# Verdict Banner
urgent_tag = "IMMEDIATE / URGENT CARE REQUIRED" if trace.requires_urgent_care else "STANDARD / NON-URGENT CARE"
urgent_ar = "القرار النهائي للحالة — تحتاج تدخل طبي عاجل في الطوارئ" if trace.requires_urgent_care else "القرار النهائي للحالة — حالة مستقرة مناسبة للكشف العادي"
esi_explain_ar = ESI_AR.get(trace.triage_level, "")

st.html(
    f'<div class="triage-banner" style="background:{b_bg};border:1px solid {b_border};color:{b_text};">'
    f'<div style="width:100%;">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">'
    f'<div>'
    f'<div class="triage-banner-title">{esc(trace.urgency_label)} — {esc(urgent_tag)}</div>'
    f'<div class="triage-banner-sub">Disposition: <strong>{esc(trace.disposition)}</strong> • Target Routing: <strong>{esc(trace.recommended_department)}</strong></div>'
    f'</div>'
    f'<div>{esi_badge(trace.triage_level)}</div>'
    f'</div>'
    f'<div class="triage-banner-ar" dir="rtl">{esc(urgent_ar)} ({esc(esi_explain_ar)})</div>'
    f'</div>'
    f'</div>'
)

# KPI Cards
top_cond_obj = trace.suspected_conditions[0] if trace.suspected_conditions else None
top_cond_name = top_cond_obj["name"] if top_cond_obj else "No Specific Match"
top_cond_ar = COND_AR.get(top_cond_obj["condition_id"], "أول تشخيص مرجّح من الأعراض") if top_cond_obj else "لا يوجد تطابق محدد"
top_cond_score = f"{top_cond_obj['confidence_score']:.0f}%" if top_cond_obj else "0%"
rf_count = len(trace.red_flag_alerts) + len(trace.vital_alerts)

st.html(
    f'<div class="kpi-grid">'
    f'<div class="kpi-card">'
    f'<div class="kpi-label">Assigned Triage Tier</div>'
    f'<div class="kpi-ar-title" dir="rtl">تصنيف خطورة الحالة</div>'
    f'<div class="kpi-value" style="color:{esi_color};">{esc(trace.triage_level)}</div>'
    f'<div class="kpi-sub">Max Wait: &lt;= {trace.max_wait_minutes} minutes</div>'
    f'</div>'
    f'<div class="kpi-card">'
    f'<div class="kpi-label">Red Flags &amp; Vital Alerts</div>'
    f'<div class="kpi-ar-title" dir="rtl">إشارات الخطورة الفورية</div>'
    f'<div class="kpi-value" style="color:{"#dc2626" if rf_count > 0 else "#059669"};">{rf_count}</div>'
    f'<div class="kpi-sub">{len(trace.red_flag_alerts)} symptom flags, {len(trace.vital_alerts)} vital alerts</div>'
    f'</div>'
    f'<div class="kpi-card">'
    f'<div class="kpi-label">Primary Suspected Condition</div>'
    f'<div class="kpi-ar-title" dir="rtl">التشخيص المحتمل الأول</div>'
    f'<div class="kpi-value" style="font-size:14.5px;color:#0f172a;">{esc(top_cond_name)}</div>'
    f'<div class="ar-sub" dir="rtl" style="font-size:11px;">{esc(top_cond_ar)} ({esc(top_cond_score)})</div>'
    f'</div>'
    f'<div class="kpi-card">'
    f'<div class="kpi-label">Assigned Department</div>'
    f'<div class="kpi-ar-title" dir="rtl">القسم الطبي الموجّه إليه</div>'
    f'<div class="kpi-value" style="font-size:14.5px;color:#2563eb;">{esc(trace.recommended_department)}</div>'
    f'<div class="kpi-sub">{len(trace.protocols)} clinical protocol(s) triggered</div>'
    f'</div>'
    f'</div>'
)

tab_diag, tab_proto, tab_trace, tab_graph, tab_sim = st.tabs([
    "1. Differential Diagnosis (التشخيص المحتمل)",
    "2. Action Protocols (البروتوكول والتحذيرات)",
    "3. Inference Trace (تفسير القواعد)",
    "4. Knowledge Graph (شبكة المعرفة)",
    "5. Live Simulator (محاكاة حالة جديدة)",
])

# ==================================================================
# TAB 1: TRIAGE & DIFFERENTIAL DIAGNOSIS
# ==================================================================
with tab_diag:
    st.markdown("#### Suspected Medical Conditions (Graph Evidence Ranking)")
    st.html(
        f'<div class="sec-desc">Differential conditions inferred for <strong>{esc(pat_rec["name"])}</strong> '
        f'by traversing <code>(:Patient)-[:PRESENTS_SYMPTOM]-&gt;(:Symptom)&lt;-[:INDICATED_BY]-(:MedicalCondition)</code>.</div>'
        '<div class="ar-box" dir="rtl">'
        'يوضح هذا الجدول الحالات الطبية المحتملة المرتبطة بأعراض المريض داخل شبكة المعرفة، مرتبة حسب نسبة قوة الأدلة وعوامل الخطورة المصاحبة لتسهيل شرح السبب الطبي.'
        '</div>'
    )

    if trace.suspected_conditions:
        cond_rows = []
        for c in trace.suspected_conditions:
            matched_str = ", ".join(c["matched_symptoms"])
            risk_str = ", ".join(c["risk_notes"]) if c["risk_notes"] else "None"
            cond_ar_txt = COND_AR.get(c["condition_id"], "")
            cond_cell = f'<strong style="color:#0f172a;">{esc(c["name"])}</strong>'
            if cond_ar_txt:
                cond_cell += f'<div class="ar-cell" dir="rtl">{esc(cond_ar_txt)}</div>'
            cond_rows.append([
                f'<span class="badge b-code">{esc(c["condition_id"])}</span>',
                cond_cell,
                esi_badge(c["triage_level"]),
                f'<strong style="font-family:var(--font-mono);color:#2563eb;">{c["confidence_score"]:.0f}%</strong>',
                f'<span style="font-size:12px;">{esc(matched_str)}</span>',
                f'<span style="font-size:12px;color:#64748b;">{esc(risk_str)}</span>',
                f'<span class="badge b-neutral">{esc(c["department"])}</span>',
            ])
        st.html(render_table(
            ["Code", "Suspected Condition", "ESI Tier", "Evidence", "Matched Symptoms", "Risk Escalation", "Target Unit"],
            cond_rows,
            ["8%", "23%", "9%", "8%", "22%", "15%", "15%"],
        ))
    else:
        st.info("No matching conditions found in the knowledge base for the reported symptom set.")

    st.markdown("#### Reported Symptoms Classification")
    st.html(
        '<div class="ar-box" dir="rtl">'
        'تصنيف الأعراض الظاهرة على المريض هل هي علامات خطورة حمراء تستوجب تدخلاً فورياً أم أعراض اعتيادية.'
        '</div>'
    )
    sym_rows = []
    for s in trace.presented_symptoms:
        flag_badge = (
            '<span class="badge b-esi1">RED FLAG</span><div class="ar-cell" dir="rtl">علامة خطورة حمراء</div>'
            if s["is_red_flag"]
            else '<span class="badge b-esi4">STANDARD</span><div class="ar-cell" dir="rtl">عرض غير طارئ</div>'
        )
        s_ar_txt = SYM_AR.get(s["symptom_id"], "")
        s_cell = f'<strong style="color:#0f172a;">{esc(s["name"])}</strong>'
        if s_ar_txt:
            s_cell += f'<div class="ar-cell" dir="rtl">{esc(s_ar_txt)}</div>'
        sym_rows.append([
            f'<span class="badge b-code">{esc(s["symptom_id"])}</span>',
            s_cell,
            f'<span class="badge b-neutral">{esc(s["body_system"])}</span>',
            flag_badge,
            f'<span style="font-family:var(--font-mono);">Weight {s["severity_weight"]}/5</span>',
        ])
    st.html(render_table(
        ["Symptom ID", "Symptom Name", "Body System", "Red-Flag Status", "Severity"],
        sym_rows,
        ["12%", "34%", "18%", "20%", "16%"],
    ))

# ==================================================================
# TAB 2: CLINICAL ACTION PROTOCOLS & CONTRAINDICATIONS
# ==================================================================
with tab_proto:
    st.markdown("#### Required Interventions, Workups & Contraindications")
    st.html(
        '<div class="sec-desc">Actionable protocols and clinical prohibitions retrieved via <code>(:MedicalCondition)-[:REQUIRES_PROTOCOL]-&gt;(:ClinicalProtocol)</code>.</div>'
        '<div class="ar-box" dir="rtl">'
        'يعرض هذا القسم الإجراءات الطبية المطلوبة فوراً، والفحوصات التشخيصية اللازمة، والمحظورات الطبية التي يمنع على الطاقم الطبي فعلها للحالة.'
        '</div>'
    )

    if trace.protocols:
        p_rows = []
        for p in trace.protocols:
            atype = p["action_type"]
            ar_cat = ACTION_AR.get(atype, "")
            if atype == "CONTRAINDICATION":
                ab = f'<span class="badge b-esi1">CONTRAINDICATION</span><div class="ar-cell" dir="rtl">{esc(ar_cat)}</div>'
            elif atype == "IMMEDIATE_INTERVENTION":
                ab = f'<span class="badge b-esi2">IMMEDIATE ACTION</span><div class="ar-cell" dir="rtl">{esc(ar_cat)}</div>'
            else:
                ab = f'<span class="badge b-code">DIAGNOSTIC WORKUP</span><div class="ar-cell" dir="rtl">{esc(ar_cat)}</div>'
            p_rows.append([
                f'<span class="badge b-code">{esc(p["protocol_id"])}</span>',
                ab,
                f'<strong style="color:#0f172a;">{esc(p["condition_name"])}</strong>',
                f'<span style="text-align:left;display:inline-block;">{esc(p["instruction"])}</span>',
                f'<span class="badge b-purple">{esc(p["timeframe"])}</span>',
            ])
        st.html(render_table(
            ["Protocol", "Category", "Associated Condition", "Clinical Instruction", "Timeframe"],
            p_rows,
            ["10%", "19%", "20%", "37%", "14%"],
        ))
    else:
        st.html('<div class="empty-state">Standard supportive outpatient instructions apply. No critical restrictions triggered.</div>')

# ==================================================================
# TAB 3: INFERENCE ENGINE TRACE (WHY / WHY NOT)
# ==================================================================
with tab_trace:
    st.markdown("#### Inference Engine Explanation Trace (Why / Why Not)")
    st.html(
        '<div class="sec-desc">Transparent audit trail showing every forward-chaining deduction, vital sign escalation, comorbidity amplification, and Modus Ponens rule activation.</div>'
        '<div class="ar-box" dir="rtl">'
        'هذا التبويب هو جوهر النظام المعرفي؛ يشرح بالتفصيل لماذا وصل النظام إلى قرار الطوارئ أو الكشف العادي، وما هي القواعد المنطقية التي تم تفعيلها خطوة بخطوة.'
        '</div>'
    )

    # 1. Executive Summary
    st.markdown("##### 1. Executive Triage Audit")
    st.html('<div class="ar-sub" dir="rtl" style="margin-bottom:6px;">أولاً — ملخص قرار الفرز الطبي وأسباب تصنيف الحالة</div>')
    aud_rows = []
    for a in trace.audit_summary:
        st_val = a["status"]
        if st_val in ("ESI-1", "RED_FLAG", "VITAL_ALERT"):
            sb = f'<span class="badge b-esi1">{esc(st_val)}</span>'
        elif st_val == "ESI-2":
            sb = f'<span class="badge b-esi2">{esc(st_val)}</span>'
        elif st_val == "ESI-3":
            sb = f'<span class="badge b-esi3">{esc(st_val)}</span>'
        elif st_val in ("CLEAR", "STABLE", "ESI-4"):
            sb = f'<span class="badge b-esi4">{esc(st_val)}</span>'
        else:
            sb = f'<span class="badge b-esi5">{esc(st_val)}</span>'
        aud_rows.append([
            f'<strong style="color:#0f172a;">{esc(a["metric"])}</strong>',
            f'<span>{esc(a["finding"])}</span>',
            sb,
        ])
    st.html(render_table(["Evaluation Metric", "Clinical Reasoning Finding", "Status"], aud_rows, ["22%", "60%", "18%"]))

    # 2. Vital & Red-Flag Escalations
    st.markdown("##### 2. Physiological & Red-Flag Escalations")
    st.html('<div class="ar-sub" dir="rtl" style="margin-bottom:6px;">ثانياً — علامات الخطورة في المؤشرات الحيوية والأعراض التي رفعت درجة الأولوية</div>')
    if trace.vital_alerts or trace.red_flag_alerts:
        esc_rows = []
        for va in trace.vital_alerts:
            esc_rows.append([
                '<span class="badge b-esi1">VITAL SIGN</span><div class="ar-cell" dir="rtl">مؤشر حيوي حرج</div>',
                f'<strong>{esc(va["parameter"])}</strong>',
                f'<span class="badge b-neutral">{esc(va["threshold"])}</span>',
                esc(va["meaning"]),
            ])
        for rfa in trace.red_flag_alerts:
            esc_rows.append([
                '<span class="badge b-esi2">RED-FLAG SYMPTOM</span><div class="ar-cell" dir="rtl">عرض خطورة حمراء</div>',
                f'<strong>{esc(rfa["symptom_name"])}</strong>',
                f'<span class="badge b-neutral">{esc(rfa["body_system"])}</span>',
                esc(rfa["action"]),
            ])
        st.html(render_table(["Trigger Source", "Observed Finding", "Threshold / System", "Escalation Effect"], esc_rows, ["18%", "23%", "16%", "43%"]))
    else:
        st.html('<div class="empty-state">No emergency vital-sign abnormalities or red-flag symptoms detected. <span class="ar-pill" dir="rtl">لا توجد مؤشرات خطورة طارئة</span></div>')

    # 3. Fired Formal Rules
    st.markdown("##### 3. Fired Deductive Rules (Forward Chaining & Modus Ponens)")
    st.html(
        f'<div class="sec-desc">Converged in <strong>{trace.inference_cycles}</strong> forward-chaining cycle(s) across <strong>{trace.working_memory_size}</strong> Working Memory facts.</div>'
        '<div class="ar-sub" dir="rtl" style="margin-bottom:6px;">ثالثاً — القواعد المنطقية الصورية التي نفذها محرك الاستدلال الأمامي عبر دورات الذاكرة العاملة لإثبات النتيجة</div>'
    )
    rule_rows = []
    for r in trace.fired_rules:
        rule_rows.append([
            f'<span class="badge b-code">{esc(r["rule_id"])}</span>',
            f'<span class="badge b-purple">{esc(r.get("cycle", "Cycle 1"))}</span>',
            f'<code style="font-family:var(--font-mono);font-size:11px;color:#1e293b;background:#f1f5f9;padding:3px 8px;border-radius:4px;display:inline-block;">{esc(r["formal_logic"])}</code>',
            f'<span style="font-size:12.5px;color:#334155;">{esc(r["consequence"])}</span>',
        ])
    st.html(render_table(["Rule ID", "Cycle", "Formal Premise", "Inferred Consequence"], rule_rows, ["14%", "10%", "40%", "36%"]))

# ==================================================================
# TAB 4: INTERACTIVE KNOWLEDGE GRAPH
# ==================================================================
with tab_graph:
    st.markdown("#### Interactive Clinical Knowledge Graph")
    st.html(
        '<div class="sec-desc">Live subgraph linking the patient to reported symptoms, active comorbidities, and suspected conditions.</div>'
        '<div class="ar-box" dir="rtl">'
        'رسم بياني تفاعلي يوضح شبكة العلاقات في قاعدة المعرفة بين المريض وأعراضه والأمراض المزمنة والتشخيصات المحتملة (يمكن سحب العقد وتكبير الرسم).'
        '</div>'
    )

    st.html(
        '<div class="graph-legend">'
        '<span class="legend-item"><span class="legend-dot" style="background:#2563eb;"></span> Patient <span class="ar-pill" dir="rtl">المريض</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#dc2626;"></span> Red-Flag Symptom <span class="ar-pill" dir="rtl">عرض خطورة</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#059669;"></span> Standard Symptom <span class="ar-pill" dir="rtl">عرض عادي</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#d97706;"></span> Risk Factor <span class="ar-pill" dir="rtl">عامل خطورة</span></span>'
        '<span class="legend-item"><span class="legend-box" style="background:#7c3aed;"></span> Suspected Condition <span class="ar-pill" dir="rtl">تشخيص محتمل</span></span>'
        '</div>'
    )

    try:
        from pyvis.network import Network

        net = Network(height="560px", width="100%", bgcolor="#ffffff", font_color="#0f172a")
        net.set_options("""
        {
          "layout": {
            "improvedLayout": true,
            "hierarchical": {
              "enabled": true,
              "direction": "LR",
              "sortMethod": "directed",
              "levelSeparation": 240,
              "nodeSpacing": 130,
              "treeSpacing": 160
            }
          },
          "physics": {
            "enabled": false
          },
          "interaction": {
            "dragNodes": true,
            "zoomView": true,
            "dragView": true,
            "hover": true
          },
          "edges": {
            "smooth": {
              "type": "cubicBezier",
              "forceDirection": "horizontal",
              "roundness": 0.4
            },
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 0.7 }
            }
          }
        }
        """)

        p_node = f"pat_{selected_pid}"
        net.add_node(p_node, label=f"{pat_rec['name']}\n({selected_pid})", level=0, color="#2563eb", size=26, shape="dot", font={"color": "#0f172a", "size": 13, "bold": True})

        for s in trace.presented_symptoms:
            s_node = f"sym_{s['symptom_id']}"
            s_col = "#dc2626" if s["is_red_flag"] else "#059669"
            net.add_node(s_node, label=s["name"], title=f"{s['body_system']} | Red Flag: {s['is_red_flag']}", level=1, color=s_col, size=18, shape="dot", font={"color": s_col, "size": 11})
            net.add_edge(p_node, s_node, title="PRESENTS_SYMPTOM", color=s_col, width=2)

        for rf in trace.active_risk_factors:
            r_node = f"rf_{rf['risk_id']}"
            net.add_node(r_node, label=rf["name"], title=rf["escalation_note"], level=1, color="#d97706", size=18, shape="triangle", font={"color": "#b45309", "size": 11})
            net.add_edge(p_node, r_node, title="HAS_RISK_FACTOR", color="#d97706", width=1.8, dashes=True)

        for c in trace.suspected_conditions[:4]:
            c_node = f"cond_{c['condition_id']}"
            net.add_node(
                c_node,
                label=f"{c['name']}\n[{c['triage_level']} • {c['confidence_score']:.0f}%]",
                title=c["clinical_summary"],
                level=2,
                color="#7c3aed",
                size=22,
                shape="box",
                font={"color": "#ffffff", "size": 11, "bold": True},
            )
            for s in trace.presented_symptoms:
                if s["name"] in c["matched_symptoms"]:
                    net.add_edge(f"sym_{s['symptom_id']}", c_node, title="INDICATES", color="#7c3aed", width=1.6)
            for esc_item in trace.risk_escalations:
                if esc_item["condition_id"] == c["condition_id"]:
                    net.add_edge(f"rf_{esc_item['risk_id']}", c_node, title=f"ESCALATES (+{esc_item['points']})", color="#d97706", width=1.6, dashes=True)

        graph_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_triage.html")
        net.save_graph(graph_path)
        with open(graph_path, "r", encoding="utf-8") as f:
            gh = f.read()

        fit_js = """
<script>
(function(){
  function refit(){
    if(typeof network!=="undefined"&&network!==null){
      var el=document.getElementById("mynetwork");
      if(el&&el.clientWidth>50&&el.clientHeight>50){
        network.redraw();
        network.fit({animation:{duration:250,easingFunction:"easeInOutQuad"}});
      }
    }
  }
  var c=setInterval(function(){
    if(typeof network!=="undefined"&&network!==null){
      clearInterval(c);
      refit();
      var el=document.getElementById("mynetwork");
      if(el&&typeof ResizeObserver!=="undefined"){
        new ResizeObserver(function(){ setTimeout(refit, 60); }).observe(el);
      }
      if(el&&typeof IntersectionObserver!=="undefined"){
        new IntersectionObserver(function(entries){
          if(entries[0]&&entries[0].isIntersecting){ setTimeout(refit, 80); }
        }).observe(el);
      }
      window.addEventListener("resize", function(){ setTimeout(refit, 60); });
    }
  }, 80);
})();
</script>
"""
        gh = gh.replace("<body>", '<body style="background:#ffffff;margin:0;padding:0;overflow:hidden;">')
        gh = gh.replace("</body>", fit_js + "</body>")
        components.html(gh, height=580)
    except Exception as e:
        st.warning(f"Unable to render interactive graph: {e}")

# ==================================================================
# TAB 5: LIVE WHAT-IF TRIAGE SIMULATOR
# ==================================================================
with tab_sim:
    st.markdown("#### Live What-If Triage Simulator")
    st.html(
        '<div class="sec-desc">Simulate a brand-new walk-in emergency patient by selecting symptoms, comorbidities, and vital signs to test the rule engine live.</div>'
        '<div class="ar-box" dir="rtl">'
        'محاكي تفاعلي لتجربة حالة مريض جديدة أمام اللجنة: أضف أو احذف أعراضاً أو عدّل العلامات الحيوية (مثل نسبة الأكسجين أو الضغط) وشاهد تغيّر مستوى الفرز الفوري.'
        '</div>'
    )

    sim_c1, sim_c2 = st.columns([1.4, 1])
    with sim_c1:
        sym_options = list(all_symptoms.keys())
        sim_syms = st.multiselect(
            "Select Presenting Symptoms (اختر الأعراض الظاهرة)",
            options=sym_options,
            default=pat_syms,
            format_func=lambda sid: f"{sid} - {all_symptoms[sid]['name']} {'[RED FLAG]' if all_symptoms[sid]['is_red_flag'] else ''}",
        )
        rf_options = list(all_risks.keys())
        sim_risks = st.multiselect(
            "Select Risk Factors / Comorbidities (الأمراض المزمنة وعوامل الخطورة)",
            options=rf_options,
            default=pat_risks,
            format_func=lambda rid: f"{rid} - {all_risks[rid]['name']}",
        )

    with sim_c2:
        sim_age = st.number_input("Patient Age (العمر بالسنوات)", min_value=1, max_value=110, value=int(pat_rec["age"]))
        v1, v2 = st.columns(2)
        with v1:
            sim_spo2 = st.number_input("SpO2 % (نسبة الأكسجين)", min_value=50, max_value=100, value=int(pat_rec["spo2_pct"]))
            sim_bpsys = st.number_input("Systolic BP (الضغط الانقباضي)", min_value=50, max_value=260, value=int(pat_rec["bp_sys"]))
        with v2:
            sim_hr = st.number_input("Heart Rate (النبض)", min_value=20, max_value=220, value=int(pat_rec["hr_bpm"]))
            sim_temp = st.number_input("Temp C (درجة الحرارة)", min_value=34.0, max_value=42.5, value=float(pat_rec["temp_c"]), step=0.1)
        sim_rr = st.number_input("Resp Rate (معدل التنفس)", min_value=8, max_value=50, value=int(pat_rec["rr_bpm"]))

    sim_trace = engine.evaluate_custom_case(
        patient_id="SIM-WALKIN",
        patient_name="Simulated Patient",
        age=int(sim_age),
        vitals={
            "hr_bpm": int(sim_hr),
            "bp_sys": int(sim_bpsys),
            "bp_dia": 80,
            "spo2_pct": int(sim_spo2),
            "temp_c": float(sim_temp),
            "rr_bpm": int(sim_rr),
        },
        symptom_ids=sim_syms,
        risk_ids=sim_risks,
    )

    s_bg, s_bd, s_tx = banner_bg_map.get(sim_trace.triage_level, ("#f8fafc", "#e2e8f0", "#0f172a"))
    sim_top_obj = sim_trace.suspected_conditions[0] if sim_trace.suspected_conditions else None
    sim_top = sim_top_obj["name"] if sim_top_obj else "Unspecified Symptoms"
    sim_top_ar = ESI_AR.get(sim_trace.triage_level, "")

    st.html(
        f'<div class="triage-banner" style="background:{s_bg};border:1px solid {s_bd};color:{s_tx};margin-top:12px;">'
        f'<div style="width:100%;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">'
        f'<div>'
        f'<div class="triage-banner-title">Simulated Output: {esc(sim_trace.urgency_label)}</div>'
        f'<div class="triage-banner-sub">Top Suspected Condition: <strong>{esc(sim_top)}</strong> • Route: <strong>{esc(sim_trace.recommended_department)}</strong> • Rules Fired: <strong>{len(sim_trace.fired_rules)}</strong></div>'
        f'</div>'
        f'<div>{esi_badge(sim_trace.triage_level)}</div>'
        f'</div>'
        f'<div class="triage-banner-ar" dir="rtl">{esc(sim_top_ar)}</div>'
        f'</div>'
        f'</div>'
    )
