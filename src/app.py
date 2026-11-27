# -*- coding: utf-8 -*-
"""
================================================================================
AEGIS | Clinical Emergency Triage & Decision Support Knowledge-Based System
Course: New Trends in Information Systems (IS438) - Damietta University
Faculty of Computers & AI
Dual-Mode Engine: Multi-Cycle Forward-Chaining & Modus Ponens + Neo4j Graph
================================================================================
"""

import os
import html
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from inference_engine import MedicalTriageEngine, ESI_METADATA

# Page configuration - Sidebar completely collapsed & removed
st.set_page_config(
    page_title="Medical Triage & Emergency KBS",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# BILINGUAL LOCALIZATION DICTIONARIES
# ==============================================================================
PATIENTS_AR = {
    "P01": {"name": "خالد منصور", "gender": "ذكر", "complaint": "ألم ضاغط شديد بالصدر يمتد للذراع الأيسر مع تعرق بارد"},
    "P02": {"name": "سلمى حسن", "gender": "أنثى", "complaint": "التهاب بسيط بالحلق واحتقان أنفي وتكسير خفيف بالجسم لمدة يومين"},
    "P03": {"name": "طارق السيد", "gender": "ذكر", "complaint": "حمى مرتفعة وقشعريرة وضيق تنفس وتشوش بالوعي"},
    "P04": {"name": "نورهان عادل", "gender": "أنثى", "complaint": "تورم مفاجئ بالحلق وطفح جلدي عام بعد تناول مأكولات بحرية"},
    "P05": {"name": "يوسف إبراهيم", "gender": "ذكر", "complaint": "ألم موضعي أسفل يمين البطن مع ارتفاع حرارة وغثيان"},
    "P06": {"name": "أمينة فتحي", "gender": "أنثى", "complaint": "صداع نصفي نابض مع زغللة بصرية وغثيان خفيف"},
    "P07": {"name": "عمر نبيل", "gender": "ذكر", "complaint": "أزمة أزيز صدري حادة وضيق تنفس لم يستجب للبخاخ المنزلي"},
}

ESI_AR = {
    "ESI-1": "المستوى 1 (إنعاش فوري) — حالة حرجة مهددة للحياة تتطلب تدخلاً طبياً عاجلاً وفورياً بغرفة الإنعاش.",
    "ESI-2": "المستوى 2 (طوارئ عاجلة) — حالة عالية الخطورة أو اضطراب حاد في العلامات الحيوية (أقصى انتظار 10 دقائق).",
    "ESI-3": "المستوى 3 (حالة مستعجلة) — تحتاج إلى فحوصات تشخيصية متعددة وتقييم سريري عاجل (أقصى انتظار 30 دقيقة).",
    "ESI-4": "المستوى 4 (أقل استعجالاً) — حالة مستقرة مناسبة لمسار الفحص السريع (أقصى انتظار 60 دقيقة).",
    "ESI-5": "المستوى 5 (غير طارئة) — حالة مستقرة تماماً توجَّه للكشف الاعتيادي بالعيادات الخارجية (أقصى انتظار 120 دقيقة).",
}

COND_AR = {
    "COND01": "متلازمة الشريان التاجي الحادة / اشتباه احتشاء عضلة القلب (STEMI)",
    "COND02": "اشتباه سكتة دماغية حادة أو نوبة نقص تروية عابرة",
    "COND03": "صدمة حساسية حادة (تأق) مهددة لمجرى التنفس",
    "COND04": "اشتباه التهاب سحائي بكتيري حاد",
    "COND05": "إنتان حاد / صدمة إنتانية مصحوبة باضطراب دوراني",
    "COND06": "حماض كيتوني سكري حاد (ارتفاع السكر والكيتون)",
    "COND07": "أزمة ارتفاع ضغط دم حرج مع إصابة أعضاء هدفية",
    "COND08": "أزمة ربو شعبي حادة مصحوبة بضيق تنفسي شديد",
    "COND09": "اشتباه التهاب حاد في الزائدة الدودية",
    "COND10": "التهاب رئوي حاد مكتسب بالمجتمع",
    "COND11": "نزلة معوية حادة مع خطورة جفاف واضطراب شوارد",
    "COND12": "نوبة صداع نصفي حادة دون علامات عصبية بؤرية",
    "COND13": "عدوى فيروسية بسيطة بالجهاز التنفسي العلوي",
}

COND_NAME_MAP_AR = {
    "Acute Coronary Syndrome (STEMI Risk)": "متلازمة الشريان التاجي الحادة / اشتباه احتشاء عضلة القلب",
    "Acute Ischemic Stroke / TIA": "اشتباه سكتة دماغية حادة أو نوبة نقص تروية عابرة",
    "Severe Anaphylaxis Shock": "صدمة حساسية حادة (تأق) مهددة لمجرى التنفس",
    "Acute Bacterial Meningitis": "اشتباه التهاب سحائي بكتيري حاد",
    "Severe Sepsis / Septic Shock": "إنتان حاد / صدمة إنتانية مصحوبة باضطراب دوراني",
    "Diabetic Ketoacidosis (DKA)": "حماض كيتوني سكري حاد (ارتفاع السكر والكيتون)",
    "Hypertensive Emergency": "أزمة ارتفاع ضغط دم حرج مع إصابة أعضاء هدفية",
    "Severe Asthma Exacerbation": "أزمة ربو شعبي حادة مصحوبة بضيق تنفسي شديد",
    "Acute Appendicitis": "اشتباه التهاب حاد في الزائدة الدودية",
    "Community-Acquired Pneumonia": "التهاب رئوي حاد مكتسب بالمجتمع",
    "Acute Gastroenteritis": "نزلة معوية حادة مع خطورة جفاف واضطراب شوارد",
    "Acute Migraine Attack": "نوبة صداع نصفي حادة دون علامات عصبية بؤرية",
    "Mild Viral URI": "عدوى فيروسية بسيطة بالجهاز التنفسي العلوي",
}

SYM_AR = {
    "SYM01": "ألم ضاغط شديد خلف عظمة القص بالصدر",
    "SYM02": "ألم مشع إلى الذراع الأيسر أو الفك السفلي",
    "SYM03": "ضيق تنفس حاد وصعوبة في الشهيق",
    "SYM04": "اعوجاج مفاجئ بعضلات الوجه أو ضعف طرفي",
    "SYM05": "ثقل مفاجئ في النطق أو تلعثم وتشتت ذهني",
    "SYM06": "تيبس حاد بالرقبة مصحوب بحساسية مفرطة للضوء",
    "SYM07": "وذمة بالحلق وصعوبة بالغة بالبلع مع صرير تنفسي",
    "SYM08": "ألم موضعي متزايد بالحفرة الحرقفية اليمنى للبطن",
    "SYM09": "حمى مرتفعة ومستمرة تفوق 38.5 درجة مئوية",
    "SYM10": "أزيز صدري مسموع مصحوب بزفير مجهد",
    "SYM11": "صداع مفاجئ وشديد يشبه ضربة الرعد",
    "SYM12": "صداع نابض نصفي مصحوب بأورة بصرية وغثيان",
    "SYM13": "سعال منتج لبلغم صديدي",
    "SYM14": "قيء وإسهال متكرر مستمر",
    "SYM15": "التهاب موضعي بالحلق مصحوب باحتقان أنفي",
    "SYM16": "ارتفاع طفيف في درجة حرارة الجسم",
    "SYM17": "طفح جلدي شروي معمّم وحكة شديدة",
    "SYM18": "دوخة دورانية شديدة أو نوبة شبه إغماء",
    "SYM19": "عطش شديد وجفاف اللسان مع رائحة أسيتون",
    "SYM20": "اضطراب حاد وتشوش في مجال الإبصار",
    "SYM21": "تعرق غزير وبارد مع شحوب بالبشرة",
    "SYM22": "قشعريرة واضطراب بمستوى الوعي والتنبه",
    "SYM23": "آلام عامة بالعضلات وخمول بدني عام",
    "SYM24": "ألم بطني ارتدادي حاد عند رفع اليد بالفحص",
}

RISK_AR = {
    "RF01": "ارتفاع ضغط الدم المزمن",
    "RF02": "مرض السكري من النوع الثاني",
    "RF03": "قصور الشريان التاجي المزمن",
    "RF04": "الربو الشعبي / الانسداد الرئوي المزمن",
    "RF05": "ضعف الجهاز المناعي",
    "RF06": "العلاج بمضادات التخثر (سيولة الدم)",
    "RF07": "تاريخ تحسسي حاد مسبق",
    "RF08": "العمر أكبر من أو يساوي 65 سنة",
}

DISPOSITION_AR = {
    "Immediate Life-Saving Intervention (Resuscitation Bay)": "تدخل فوري لإنقاذ الحياة (غرفة الإنعاش والطوارئ الحرجة)",
    "Urgent Emergency Care (High-Risk / Red-Flag Alert)": "رعاية طوارئ عاجلة (حالة عالية الخطورة / تنبيه أحمر)",
    "Emergency Department Priority Assessment": "تقييم ذو أولوية بقسم الطوارئ وفحوصات عاجلة",
    "ER Fast Track / Urgent Care Assessment": "مسار الفحص السريع بقسم الطوارئ / رعاية عاجلة",
    "Routine Outpatient Clinic Consultation": "استشارة روتينية بالعيادات الخارجية",
}

DEPT_AR = {
    "Cardiology / Cath Lab": "قسم القلب / وحدة القسطرة والعناية المركزة",
    "Neurology / Stroke Unit": "قسم المخ والأعصاب / وحدة السكتة الدماغية",
    "Resuscitation Bay / Allergy": "غرفة الإنعاش / وحدة الحساسية والحرجة",
    "Infectious Disease / ICU": "قسم الأمراض المعدية / العناية المركزة",
    "Critical Care / Sepsis Team": "وحدة الحالات الحرجة / فريق علاج الإنتان",
    "Endocrinology / Acute Care": "قسم الغدد الصماء / الرعاية الحادة",
    "Emergency Acute Care": "قسم طب الطوارئ / الرعاية الحادة",
    "Pulmonary Emergency": "طوارئ الأمراض الصدرية والرئوية",
    "Emergency Medicine": "قسم طب الطوارئ",
    "Respiratory / Pulmonology": "قسم الصدرية والجهاز التنفسي",
    "General Surgery": "قسم الجراحة العامة",
    "Internal Medicine": "قسم الباطنة العامة",
    "Outpatient Clinic": "العيادات الخارجية",
    "Outpatient / Fast Track": "العيادات الخارجية / الفحص السريع",
}

BODY_SYSTEM_AR = {
    "Cardiovascular": "القلب والأوعية الدموية",
    "Neurological": "الجهاز العصبي",
    "Respiratory": "الجهاز التنفسي",
    "Gastrointestinal": "الجهاز الهضمي",
    "Systemic": "جهازي / عام",
    "Immunological": "المناعة والحساسية",
    "Endocrine": "الغدد الصماء والتمثيل الغذائي",
}

TIMEFRAME_AR = {
    "Immediate (0 min)": "فوري الآن (0 دقيقة)",
    "Immediate (< 5 min)": "فوري (< 5 دقائق)",
    "Immediate (< 10 min)": "فوري (< 10 دقائق)",
    "Immediate (< 15 min)": "فوري (< 15 دقيقة)",
    "Within 15 min": "خلال 15 دقيقة",
    "Within 30 min": "خلال 30 دقيقة",
    "Within 60 min": "خلال 60 دقيقة",
    "Stat": "عاجل وفوري (Stat)",
    "Strict Prohibition": "حظر طبي صارم",
    "Clinical Caution": "تحذير سريري حذر",
    "Routine Clinic": "عيادة روتينية",
}

PROTOCOLS_AR = {
    "PROT01": "تخطيط قلب كهربائي فوري بـ 12 اتجاهاً خلال 10 دقائق وفتح خط وريدي",
    "PROT02": "فحص تروبونين قلبي عاجل، وتعداد دم كامل، ووظائف كلى، وأشعة سينية على الصدر",
    "PROT03": "يمنع منعاً باتاً خروج المريض للعيادات الخارجية أو تأخير رسم القلب لانتظار كشف الاستقبال",
    "PROT04": "تفعيل فريق كود السكتة الدماغية فوراً وعمل أشعة مقطعية عاجلة على المخ دون صبغة",
    "PROT05": "يمنع إعطاء سوائل فموية أو طعام أو مضادات تجلط قبل نفي النزيف الدماغي بالأشعة المقطعية",
    "PROT06": "تجهيز حقن إبينفرين (أدرينالين) عضلياً 0.3-0.5 مجم، وأكسجين عالي التدفق، وحقيبة مجرى التنفس",
    "PROT07": "بدء عزل تنفسي فوري، وسحب عينات دم للمزرعة، وبدء مضادات حيوية وريدية عاجلة واسعة المجال",
    "PROT08": "بدء حزمة الإنتان الأولى: قياس اللاكتات، ومزارع الدم، ومحاليل وريدية بلورية، ومضادات حيوية واسعة المجال",
    "PROT09": "فحص سكر الدم والكيتون الشعيري وغازات الدم، وبدء محاليل ملحية وريدية سريعة لتعويض الجفاف",
    "PROT10": "إعادة قياس الضغط بالذراعين، وفحص قاع العين، ورسم قلب، ووظائف كلى، وفحص تروبونين",
    "PROT11": "جلسات استنشاق موسعة للشعب الهوائية (فنتولين + أتروفنت) ومراقبة مستمرة لتشبع الأكسجين",
    "PROT12": "إبقاء المريض صائماً تماماً (NPO)، وصورة دم كاملة، وCRP، واستشارة جراحة عامة عاجلة وموجات فوق صوتية / أشعة مقطعية على البطن",
    "PROT13": "يمنع إعطاء مسكنات فموية أو ملينات قبل تقييم جراح الطوارئ لتجنب إخفاء الأعراض أو انفجار الزائدة",
    "PROT14": "عمل أشعة سينية على الصدر، وقياس تشبع الأكسجين، ومزارع بلغم ودم في حال وجود حمى",
    "PROT15": "علاج تعويض السوائل فموياً أو وريدياً وتقييم شوارد المصل ووظائف الكلى",
    "PROT16": "تقييم المريض في غرفة هادئة ومظلمة وإعطاء بروتوكول علاج الصداع النصفي غير الأفيوني الموجه",
    "PROT17": "إرشادات رعاية داعمة بالعيادات الخارجية، وتناول السوائل، وتعليمات علامات الخطورة للعودة فوراً",
}

# ==============================================================================
# PHYSIOLOGICAL VITALS EVALUATOR
# ==============================================================================
def eval_vital_status(param: str, value: float, is_ar: bool = False) -> tuple[str, str, str]:
    if param == "hr":
        if value < 50 or value > 125:
            return ("حرج", "#b91c1c", "#fef2f2") if is_ar else ("Critical", "#b91c1c", "#fef2f2")
        elif value < 60:
            return ("تباطؤ نبض", "#d97706", "#fffbeb") if is_ar else ("Brady", "#d97706", "#fffbeb")
        elif value > 100:
            return ("تسارع نبض", "#d97706", "#fffbeb") if is_ar else ("Tachy", "#d97706", "#fffbeb")
        return ("طبيعي", "#059669", "#ecfdf5") if is_ar else ("Normal", "#059669", "#ecfdf5")
    elif param == "bp":
        if value >= 180 or value < 90:
            return ("أزمة ضغط", "#b91c1c", "#fef2f2") if is_ar else ("Crisis", "#b91c1c", "#fef2f2")
        elif value >= 140:
            return ("مرحلة 2", "#ea580c", "#fff7ed") if is_ar else ("Stage 2", "#ea580c", "#fff7ed")
        elif value >= 120:
            return ("مرتفع", "#d97706", "#fffbeb") if is_ar else ("Elevated", "#d97706", "#fffbeb")
        return ("طبيعي", "#059669", "#ecfdf5") if is_ar else ("Normal", "#059669", "#ecfdf5")
    elif param == "spo2":
        if value < 90:
            return ("نقص أكسجين حاد", "#b91c1c", "#fef2f2") if is_ar else ("Hypoxic", "#b91c1c", "#fef2f2")
        elif value <= 94:
            return ("أكسجين منخفض", "#ea580c", "#fff7ed") if is_ar else ("Low O2", "#ea580c", "#fff7ed")
        return ("مثالي", "#059669", "#ecfdf5") if is_ar else ("Optimal", "#059669", "#ecfdf5")
    elif param == "temp":
        if value >= 38.5 or value < 35.5:
            return ("حمى شديدة", "#b91c1c", "#fef2f2") if is_ar else ("Fever", "#b91c1c", "#fef2f2")
        elif value > 37.5:
            return ("ارتفاع طفيف", "#d97706", "#fffbeb") if is_ar else ("Warm", "#d97706", "#fffbeb")
        return ("طبيعي", "#059669", "#ecfdf5") if is_ar else ("Normal", "#059669", "#ecfdf5")
    elif param == "rr":
        if value > 26 or value < 10:
            return ("ضيق تنفس حاد", "#b91c1c", "#fef2f2") if is_ar else ("Distress", "#b91c1c", "#fef2f2")
        elif value > 20:
            return ("تسارع تنفس", "#d97706", "#fffbeb") if is_ar else ("Tachypnea", "#d97706", "#fffbeb")
        return ("طبيعي", "#059669", "#ecfdf5") if is_ar else ("Normal", "#059669", "#ecfdf5")
    return ("طبيعي", "#059669", "#ecfdf5") if is_ar else ("Normal", "#059669", "#ecfdf5")

# ==============================================================================
# APP STATE: LANGUAGE & ACTIVE PATIENT
# ==============================================================================
if "lang" not in st.session_state:
    st.session_state.lang = "English"

is_ar = (st.session_state.lang == "العربية")
dir_attr = "rtl" if is_ar else "ltr"
font_family = "var(--font-ar)" if is_ar else "var(--font-ui)"

# ==============================================================================
# CLINICAL STYLING (SIDEBAR 100% REMOVED + PURE CSS CROSS)
# ==============================================================================
THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Cairo:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
    --canvas: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --brand-blue: #2563eb;
    --brand-blue-soft: #eff6ff;
    --brand-blue-border: #bfdbfe;
    
    --esi1: #dc2626;
    --esi2: #ea580c;
    --esi3: #d97706;
    --esi4: #059669;
    --esi5: #2563eb;
    
    --font-ui: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-ar: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
    --font-mono: 'JetBrains Mono', Consolas, monospace;
}}

/* COMPLETE AND TOTAL SIDEBAR REMOVAL */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
section[data-testid="stSidebar"],
button[data-testid="baseButton-headerNoPadding"],
div[data-testid="collapsedControl"] {{
    display: none !important;
}}

/* Base Page Layout */
html, body, [class*="css"], .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .main .block-container {{
    font-family: {font_family} !important;
    background-color: var(--canvas) !important;
    color: var(--text-primary) !important;
    direction: {dir_attr} !important;
}}

.main .block-container {{
    max-width: 100% !important;
    padding: 1.25rem 2rem 3rem 2rem !important;
}}

/* Top Navigation Bar with Inline Controls */
.top-nav {{
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}}
.brand-group {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

/* PURE CSS WHITE MEDICAL CROSS (Immune to HTML sanitization) */
.brand-icon {{
    width: 38px;
    height: 38px;
    border-radius: 8px;
    background: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
}}
.brand-icon-cross {{
    position: relative;
    width: 18px;
    height: 18px;
    display: block;
}}
.brand-icon-cross::before, .brand-icon-cross::after {{
    content: "";
    position: absolute;
    background: #ffffff;
    border-radius: 2px;
}}
.brand-icon-cross::before {{
    top: 0;
    left: 7px;
    width: 4px;
    height: 18px;
}}
.brand-icon-cross::after {{
    top: 7px;
    left: 0;
    width: 18px;
    height: 4px;
}}

.brand-name {{
    font-size: 16px;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.2;
}}
.brand-desc {{
    font-size: 11.5px;
    color: var(--text-muted);
    margin-top: 2px;
}}

/* Knowledge Graph Mode Badge */
.kg-mode-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    background: #f1f5f9;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    margin-top: 4px;
    width: fit-content;
}}
.dot-indicator {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
}}

/* Patient Demographic Card */
.patient-card {{
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}}
.patient-meta-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}}
.patient-user {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.patient-avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #eff6ff;
    border: 1.5px solid #bfdbfe;
    color: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
}}
.patient-title-text {{
    font-size: 17px;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
}}
.patient-sub-text {{
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
}}
.complaint-quote {{
    font-size: 12.5px;
    color: var(--text-secondary);
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px;
    max-width: 480px;
}}

/* Vitals Ribbon */
.vitals-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin-top: 12px;
}}
.vital-item {{
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.vital-title {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.3px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}}
.vital-value {{
    font-family: var(--font-mono);
    font-size: 18px;
    font-weight: 800;
    color: var(--text-primary);
    margin: 3px 0;
}}
.vital-tag {{
    font-size: 10px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 4px;
    width: fit-content;
    white-space: nowrap;
}}

/* Triage Disposition Hero Banner */
.triage-banner {{
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 1.25rem;
    border: 1px solid var(--border);
    background: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}}
.triage-tier-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}
.esi-badge-lg {{
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 900;
    padding: 6px 14px;
    border-radius: 8px;
    color: #ffffff;
    white-space: nowrap;
    flex-shrink: 0;
}}
.esi-1-bg {{ background: var(--esi1); }}
.esi-2-bg {{ background: var(--esi2); }}
.esi-3-bg {{ background: var(--esi3); }}
.esi-4-bg {{ background: var(--esi4); }}
.esi-5-bg {{ background: var(--esi5); }}

.triage-headline {{
    font-size: 18px;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
}}
.triage-subtext {{
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 3px;
}}

.triage-wait-box {{
    text-align: inherit;
    min-width: 140px;
}}
.triage-wait-label {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
}}
.triage-wait-val {{
    font-family: var(--font-mono);
    font-size: 18px;
    font-weight: 800;
    color: var(--text-primary);
}}

/* Alert Strip */
.alert-strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    width: 100%;
}}
.alert-chip-crit {{
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
}}
.alert-chip-ok {{
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    color: #065f46;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
}}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px !important;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 14px !important;
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    white-space: nowrap !important;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    color: var(--brand-blue) !important;
    background: var(--brand-blue-soft) !important;
    border: 1px solid var(--brand-blue-border) !important;
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* Clean Custom Table */
.pro-table-wrapper {{
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow-x: auto;
    margin: 12px 0 18px 0;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}}
.pro-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: inherit;
}}
.pro-table th {{
    background: #f1f5f9;
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
}}
.pro-table td {{
    padding: 11px 14px;
    border-bottom: 1px solid #f1f5f9;
    color: var(--text-secondary);
    vertical-align: middle;
}}
.pro-table tr:last-child td {{
    border-bottom: none;
}}
.pro-table tr:hover td {{
    background: #f8fafc;
}}

/* Clinical Order Cards */
.card-flat {{
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
}}
.order-contra {{
    border-left: 4px solid #dc2626;
    background: #fffafa;
}}
.order-action {{
    border-left: 4px solid #ea580c;
    background: #fffcf9;
}}
.order-diag {{
    border-left: 4px solid #2563eb;
    background: #f9fbff;
}}
</style>
"""

st.html(THEME_CSS)

def esc(val: object) -> str:
    return html.escape(str(val))

# ==============================================================================
# ENGINE SINGLETON & DATA LOADER
# ==============================================================================
@st.cache_resource
def get_triage_engine():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    return MedicalTriageEngine(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password123",
        data_dir=data_dir,
    )

engine = get_triage_engine()
patients_map = engine.get_patients()
all_symptoms = engine.get_all_symptoms()
all_risks = engine.get_all_risk_factors()
patient_ids = list(patients_map.keys())

# Reverse symptom name to Arabic lookup map
SYM_NAME_TO_AR = {s["name"]: SYM_AR.get(sid, s["name"]) for sid, s in all_symptoms.items()}

# ==============================================================================
# 1. TOP BAR: TITLE, KNOWLEDGE GRAPH STATUS, PATIENT SELECTOR & LANGUAGE TOGGLE
# ==============================================================================
col_brand, col_patient, col_lang = st.columns([1.7, 1.4, 0.7], gap="medium")

with col_brand:
    app_title = "نظام الفرز الطبي وتحديد أولويات الطوارئ" if is_ar else "Medical Triage & Emergency KBS"
    app_desc = "نظام دعم اتخاذ القرار السريري • IS438" if is_ar else "Clinical Decision Support System • IS438"
    
    kg_label = (
        ("قاعدة المعرفة: متصل مع Neo4j (Live)" if is_ar else "Knowledge Graph: Neo4j Bolt Live")
        if engine.mode == "LIVE_NEO4J"
        else ("قاعدة المعرفة: وضع الملفات المحلي (CSV)" if is_ar else "Knowledge Graph: Local Mode (CSV)")
    )
    
    st.html(
        f"""
        <div class="brand-group">
            <div class="brand-icon"><span class="brand-icon-cross"></span></div>
            <div>
                <div class="brand-name">{esc(app_title)}</div>
                <div class="brand-desc">{esc(app_desc)}</div>
                <div class="kg-mode-badge"><span class="dot-indicator"></span> {esc(kg_label)}</div>
            </div>
        </div>
        """
    )

with col_patient:
    patient_label = "اختر سجل المريض" if is_ar else "Select Patient Record"
    selected_pid = st.selectbox(
        patient_label,
        options=patient_ids,
        format_func=lambda pid: (
            f"{pid} — {PATIENTS_AR.get(pid, {}).get('name', patients_map[pid]['name'])}"
            if is_ar
            else f"{pid} — {patients_map[pid]['name']}"
        ),
        label_visibility="collapsed",
    )

with col_lang:
    lang_choice = st.segmented_control(
        "Language",
        options=["English", "العربية"],
        default=st.session_state.lang,
        label_visibility="collapsed",
    )
    if lang_choice and lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

pat_rec, pat_syms, pat_risks = engine.get_patient_case(selected_pid)

# Evaluate active patient
trace = engine.evaluate_patient(selected_pid)
esi_color = ESI_METADATA[trace.triage_level]["color"]
esi_cls = f"esi-{trace.triage_level.split('-')[-1]}-bg"

# ==============================================================================
# 2. PATIENT EMR HEADER & VITALS RIBBON
# ==============================================================================
p_name = PATIENTS_AR.get(selected_pid, {}).get("name", pat_rec["name"]) if is_ar else pat_rec["name"]
p_gender = PATIENTS_AR.get(selected_pid, {}).get("gender", pat_rec["gender"]) if is_ar else pat_rec["gender"]
p_complaint = PATIENTS_AR.get(selected_pid, {}).get("complaint", pat_rec["chief_complaint"]) if is_ar else pat_rec["chief_complaint"]
p_initials = "".join([part[0] for part in pat_rec["name"].split()[:2]]).upper()

# Physiological Vitals evaluation
hr_tag, hr_c, hr_bg = eval_vital_status("hr", float(pat_rec["hr_bpm"]), is_ar)
bp_tag, bp_c, bp_bg = eval_vital_status("bp", float(pat_rec["bp_sys"]), is_ar)
spo2_tag, spo2_c, spo2_bg = eval_vital_status("spo2", float(pat_rec["spo2_pct"]), is_ar)
temp_tag, temp_c, temp_bg = eval_vital_status("temp", float(pat_rec["temp_c"]), is_ar)
rr_tag, rr_c, rr_bg = eval_vital_status("rr", float(pat_rec["rr_bpm"]), is_ar)

lbl_mrn = "رقم الملف" if is_ar else "MRN"
lbl_age = "العمر" if is_ar else "Age"
lbl_sex = "الجنس" if is_ar else "Sex"
lbl_syms = "الأعراض" if is_ar else "Symptoms"
lbl_risks = "الأمراض المزمنة" if is_ar else "Comorbidities"
lbl_complaint = "الشكوى الرئيسية" if is_ar else "Chief Complaint"
lbl_years = "سنة" if is_ar else "yrs"

st.html(
    f"""
    <div class="patient-card">
        <div class="patient-meta-row">
            <div class="patient-user">
                <div class="patient-avatar">{p_initials}</div>
                <div>
                    <h2 class="patient-title-text">{esc(p_name)}</h2>
                    <div class="patient-sub-text">
                        {lbl_mrn}: <strong>#{esc(selected_pid)}</strong> &nbsp;•&nbsp; 
                        {lbl_age}: <strong>{esc(pat_rec["age"])} {lbl_years}</strong> &nbsp;•&nbsp; 
                        {lbl_sex}: <strong>{esc(p_gender)}</strong> &nbsp;•&nbsp; 
                        {lbl_syms}: <strong>{len(pat_syms)}</strong> &nbsp;•&nbsp; 
                        {lbl_risks}: <strong>{len(pat_risks)}</strong>
                    </div>
                </div>
            </div>
            <div class="complaint-quote">
                <strong>{lbl_complaint}:</strong> "{esc(p_complaint)}"
            </div>
        </div>
        
        <div class="vitals-grid">
            <div class="vital-item">
                <div class="vital-title"><span>{'معدل النبض' if is_ar else 'Heart Rate'}</span> <span class="vital-tag" style="background:{hr_bg};color:{hr_c};">{hr_tag}</span></div>
                <div class="vital-value">{esc(pat_rec["hr_bpm"])} <span style="font-size:11px;color:#64748b;">bpm</span></div>
            </div>
            <div class="vital-item">
                <div class="vital-title"><span>{'ضغط الدم' if is_ar else 'BP'}</span> <span class="vital-tag" style="background:{bp_bg};color:{bp_c};">{bp_tag}</span></div>
                <div class="vital-value">{esc(pat_rec["bp_sys"])}/{esc(pat_rec["bp_dia"])} <span style="font-size:11px;color:#64748b;">mmHg</span></div>
            </div>
            <div class="vital-item">
                <div class="vital-title"><span>{'الأكسجين' if is_ar else 'SpO2'}</span> <span class="vital-tag" style="background:{spo2_bg};color:{spo2_c};">{spo2_tag}</span></div>
                <div class="vital-value">{esc(pat_rec["spo2_pct"])}%</div>
            </div>
            <div class="vital-item">
                <div class="vital-title"><span>{'الحرارة' if is_ar else 'Temp'}</span> <span class="vital-tag" style="background:{temp_bg};color:{temp_c};">{temp_tag}</span></div>
                <div class="vital-value">{esc(pat_rec["temp_c"])}°C</div>
            </div>
            <div class="vital-item">
                <div class="vital-title"><span>{'التنفس' if is_ar else 'Resp Rate'}</span> <span class="vital-tag" style="background:{rr_bg};color:{rr_c};">{rr_tag}</span></div>
                <div class="vital-value">{esc(pat_rec["rr_bpm"])} <span style="font-size:11px;color:#64748b;">/min</span></div>
            </div>
        </div>
    </div>
    """
)

# ==============================================================================
# 3. TRIAGE VERDICT HERO BANNER
# ==============================================================================
alerts_html = []
for va in trace.vital_alerts:
    val_txt = f"{'مؤشر حيوي حرج' if is_ar else 'Vital'}: {esc(va['parameter'])} ({esc(va['threshold'])})"
    alerts_html.append(f'<span class="alert-chip-crit">{val_txt}</span>')
for rfa in trace.red_flag_alerts:
    rfa_name = SYM_AR.get(rfa["symptom_id"], rfa["symptom_name"]) if is_ar else rfa["symptom_name"]
    rfa_txt = f"{'علامة خطورة حمراء' if is_ar else 'Red Flag'}: {esc(rfa_name)}"
    alerts_html.append(f'<span class="alert-chip-crit">{rfa_txt}</span>')
if not alerts_html:
    ok_txt = 'العلامات الحيوية مستقرة • لا توجد مؤشرات خطورة طارئة' if is_ar else 'Vitals Stable • No Emergency Red Flags Detected'
    alerts_html.append(f'<span class="alert-chip-ok">{ok_txt}</span>')

urgency_title = ESI_AR.get(trace.triage_level, trace.urgency_label) if is_ar else trace.urgency_label
disposition_display = DISPOSITION_AR.get(trace.disposition, trace.disposition) if is_ar else trace.disposition
routing_display = DEPT_AR.get(trace.recommended_department, trace.recommended_department) if is_ar else trace.recommended_department

lbl_disposition = "التوجيه السريري" if is_ar else "Disposition"
lbl_routing = "القسم المستهدف" if is_ar else "Target Routing"
lbl_wait = "أقصى وقت انتظار آمن" if is_ar else "Max Safe Wait Time"
lbl_min = "دقيقة" if is_ar else "min"

st.html(
    f"""
    <div class="triage-banner" style="border-left: 5px solid {esi_color};">
        <div class="triage-tier-left">
            <div class="esi-badge-lg {esi_cls}">{esc(trace.triage_level)}</div>
            <div>
                <h3 class="triage-headline">{esc(urgency_title)}</h3>
                <div class="triage-subtext">{lbl_disposition}: <strong>{esc(disposition_display)}</strong> &nbsp;•&nbsp; {lbl_routing}: <strong>{esc(routing_display)}</strong></div>
            </div>
        </div>
        <div class="triage-wait-box">
            <div class="triage-wait-label">{lbl_wait}</div>
            <div class="triage-wait-val" style="color:{esi_color};">{"≤ " if trace.max_wait_minutes > 0 else ""}{trace.max_wait_minutes} {lbl_min}</div>
        </div>
        <div class="alert-strip">
            {"".join(alerts_html)}
        </div>
    </div>
    """
)

# ==============================================================================
# 4. TABS NAVIGATION
# ==============================================================================
tab_titles = (
    ["التشخيص التفريقي", "البروتوكولات السريرية", "مسار الاستدلال", "شبكة المعرفة", "محاكي الحالات"]
    if is_ar
    else ["Differential Diagnosis", "Clinical Protocols", "Inference Trace", "Knowledge Graph", "Simulator"]
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

# ------------------------------------------------------------------------------
# TAB 1: DIFFERENTIAL DIAGNOSIS
# ------------------------------------------------------------------------------
with tab1:
    h_diff = "الحالات المشتبه بها وقوة أدلة شبكة المعرفة" if is_ar else "Suspected Conditions & Graph Evidence Ranking"
    st.markdown(f"#### {h_diff}")

    if trace.suspected_conditions:
        th_code = "الرمز" if is_ar else "Code"
        th_cond = "الحالة المرضية / التشخيص" if is_ar else "Condition / Diagnosis"
        th_esi = "مستوى ESI" if is_ar else "ESI Tier"
        th_evid = "قوة الأدلة" if is_ar else "Evidence"
        th_syms = "الأعراض المتطابقة" if is_ar else "Matched Symptoms"
        th_dept = "القسم المستهدف" if is_ar else "Target Unit"

        rows_html = []
        for c in trace.suspected_conditions:
            cond_display = COND_AR.get(c["condition_id"], c["name"]) if is_ar else c["name"]
            matched_syms = [SYM_NAME_TO_AR.get(s, s) if is_ar else s for s in c.get("matched_symptoms", [])]
            dept_display = DEPT_AR.get(c["department"], c["department"]) if is_ar else c["department"]
            ev_pct = int(c["confidence_score"])
            
            bar_color = "#dc2626" if ev_pct >= 75 else ("#ea580c" if ev_pct >= 50 else "#2563eb")
            esi_b = f'<span class="vital-tag" style="background:#f1f5f9;color:#0f172a;font-weight:700;">{esc(c["triage_level"])}</span>'

            rows_html.append(
                f"""<tr>
                    <td style="font-family:var(--font-mono);font-weight:700;color:#2563eb;">{esc(c["condition_id"])}</td>
                    <td><strong>{esc(cond_display)}</strong></td>
                    <td>{esi_b}</td>
                    <td style="width:160px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-family:var(--font-mono);font-weight:700;width:38px;">{ev_pct}%</span>
                            <div style="flex-grow:1;background:#e2e8f0;border-radius:9999px;height:7px;overflow:hidden;">
                                <div style="width:{min(100, ev_pct)}%;background:{bar_color};height:100%;"></div>
                            </div>
                        </div>
                    </td>
                    <td style="font-size:12px;">{esc(", ".join(matched_syms))}</td>
                    <td style="font-size:12px;">{esc(dept_display)}</td>
                </tr>"""
            )

        st.html(
            f"""<div class="pro-table-wrapper">
                <table class="pro-table">
                    <thead><tr>
                        <th>{th_code}</th>
                        <th>{th_cond}</th>
                        <th>{th_esi}</th>
                        <th>{th_evid}</th>
                        <th>{th_syms}</th>
                        <th>{th_dept}</th>
                    </tr></thead>
                    <tbody>{"".join(rows_html)}</tbody>
                </table>
            </div>"""
        )
    else:
        st.info("لا توجد حالات متطابقة في قاعدة المعرفة لهذا المزيج من الأعراض." if is_ar else "No matching clinical conditions found for current symptom presentation.")

    st.markdown("---")
    st.markdown(f"#### {'تصنيف الأعراض المسجلة للمريض' if is_ar else 'Presented Symptoms Classification'}")
    
    col_rf, col_std = st.columns(2)
    with col_rf:
        st.markdown(f"##### {'علامات الخطورة الحمراء' if is_ar else 'Critical Red Flags'}")
        rfs = [s for s in trace.presented_symptoms if s["is_red_flag"]]
        if rfs:
            for s in rfs:
                s_name = SYM_AR.get(s["symptom_id"], s["name"]) if is_ar else s["name"]
                sys_display = BODY_SYSTEM_AR.get(s["body_system"], s["body_system"]) if is_ar else s["body_system"]
                lbl_sys = "الجهاز" if is_ar else "System"
                lbl_weight = "الوزن" if is_ar else "Weight"
                st.html(
                    f'<div class="card-flat" style="border-left:3.5px solid #dc2626;padding:8px 12px;margin-bottom:6px;">'
                    f'<div style="font-weight:700;color:#991b1b;font-size:13px;">{esc(s_name)}</div>'
                    f'<div style="font-size:11px;color:#64748b;">{esc(s["symptom_id"])} • {lbl_sys}: {esc(sys_display)} • {lbl_weight}: {s["severity_weight"]}/5</div>'
                    f'</div>'
                )
        else:
            st.caption("لا توجد علامات خطورة حمراء مسجلة." if is_ar else "No red-flag symptom triggers present.")

    with col_std:
        st.markdown(f"##### {'الأعراض الاعتيادية' if is_ar else 'Standard Symptoms'}")
        stds = [s for s in trace.presented_symptoms if not s["is_red_flag"]]
        if stds:
            for s in stds:
                s_name = SYM_AR.get(s["symptom_id"], s["name"]) if is_ar else s["name"]
                sys_display = BODY_SYSTEM_AR.get(s["body_system"], s["body_system"]) if is_ar else s["body_system"]
                lbl_sys = "الجهاز" if is_ar else "System"
                lbl_weight = "الوزن" if is_ar else "Weight"
                st.html(
                    f'<div class="card-flat" style="border-left:3.5px solid #059669;padding:8px 12px;margin-bottom:6px;">'
                    f'<div style="font-weight:700;color:#065f46;font-size:13px;">{esc(s_name)}</div>'
                    f'<div style="font-size:11px;color:#64748b;">{esc(s["symptom_id"])} • {lbl_sys}: {esc(sys_display)} • {lbl_weight}: {s["severity_weight"]}/5</div>'
                    f'</div>'
                )
        else:
            st.caption("لا توجد أعراض اعتيادية مسجلة." if is_ar else "No standard symptoms reported.")

# ------------------------------------------------------------------------------
# TAB 2: CLINICAL PROTOCOLS & ORDERS
# ------------------------------------------------------------------------------
with tab2:
    st.markdown(f"#### {'البروتوكولات الطبية المعتمدة والمحظورات السريرية' if is_ar else 'Clinical Standing Orders & Safety Prohibitions'}")

    if trace.protocols:
        contra = [p for p in trace.protocols if p["action_type"] == "CONTRAINDICATION"]
        actions = [p for p in trace.protocols if p["action_type"] == "IMMEDIATE_INTERVENTION"]
        diags = [p for p in trace.protocols if p["action_type"] == "DIAGNOSTIC_WORKUP"]

        if contra:
            st.markdown(f"##### {'محظورات سريرية صارمة (يمنع إعطاؤها)' if is_ar else 'Strict Contraindications (Do Not Administer)'}")
            for p in contra:
                c_name = COND_NAME_MAP_AR.get(p["condition_name"], p["condition_name"]) if is_ar else p["condition_name"]
                inst_text = PROTOCOLS_AR.get(p["protocol_id"], p["instruction"]) if is_ar else p["instruction"]
                time_lbl = TIMEFRAME_AR.get(p["timeframe"], p["timeframe"]) if is_ar else p["timeframe"]
                st.html(
                    f'<div class="card-flat order-contra">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<strong style="color:#b91c1c;font-size:13.5px;">{esc(inst_text)}</strong>'
                    f'<span style="font-family:var(--font-mono);font-size:11px;background:#fee2e2;color:#991b1b;padding:2px 6px;border-radius:4px;">{esc(p["protocol_id"])}</span>'
                    f'</div>'
                    f'<div style="font-size:12px;color:#7f1d1d;margin-top:3px;">{"الحالة المرتبطة" if is_ar else "Condition"}: <strong>{esc(c_name)}</strong> • {esc(time_lbl)}</div>'
                    f'</div>'
                )

        if actions:
            st.markdown(f"##### {'تدخلات سريرية فورية عند السرير' if is_ar else 'Immediate Bedside Interventions'}")
            for p in actions:
                c_name = COND_NAME_MAP_AR.get(p["condition_name"], p["condition_name"]) if is_ar else p["condition_name"]
                inst_text = PROTOCOLS_AR.get(p["protocol_id"], p["instruction"]) if is_ar else p["instruction"]
                time_lbl = TIMEFRAME_AR.get(p["timeframe"], p["timeframe"]) if is_ar else p["timeframe"]
                st.html(
                    f'<div class="card-flat order-action">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<strong style="color:#9a3412;font-size:13.5px;">{esc(inst_text)}</strong>'
                    f'<span style="font-family:var(--font-mono);font-size:11px;background:#ffedd5;color:#9a3412;padding:2px 6px;border-radius:4px;">{esc(time_lbl)}</span>'
                    f'</div>'
                    f'<div style="font-size:12px;color:#7c2d12;margin-top:3px;">{"الحالة" if is_ar else "Condition"}: <strong>{esc(c_name)}</strong> • {esc(p["protocol_id"])}</div>'
                    f'</div>'
                )

        if diags:
            st.markdown(f"##### {'فحوصات تشخيصية وتحاليل معملية' if is_ar else 'Diagnostic Workups & Laboratory Assays'}")
            for p in diags:
                c_name = COND_NAME_MAP_AR.get(p["condition_name"], p["condition_name"]) if is_ar else p["condition_name"]
                inst_text = PROTOCOLS_AR.get(p["protocol_id"], p["instruction"]) if is_ar else p["instruction"]
                time_lbl = TIMEFRAME_AR.get(p["timeframe"], p["timeframe"]) if is_ar else p["timeframe"]
                st.html(
                    f'<div class="card-flat order-diag">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<strong style="color:#1e40af;font-size:13.5px;">{esc(inst_text)}</strong>'
                    f'<span style="font-family:var(--font-mono);font-size:11px;background:#eff6ff;color:#1e40af;padding:2px 6px;border-radius:4px;">{esc(time_lbl)}</span>'
                    f'</div>'
                    f'<div style="font-size:12px;color:#475569;margin-top:3px;">{"المؤشر السريري" if is_ar else "Indication"}: <strong>{esc(c_name)}</strong> • {esc(p["protocol_id"])}</div>'
                    f'</div>'
                )
    else:
        st.info("رعاية داعمة قياسية في العيادة الخارجية. لا توجد بروتوكولات طوارئ مطلوبة." if is_ar else "Standard outpatient supportive care. No emergency protocols required.")

# ------------------------------------------------------------------------------
# TAB 3: INFERENCE TRACE (XAI)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown(f"#### {'مسار التدقيق لمحرك الاستدلال الأمامي المنطقي' if is_ar else 'Deductive Forward-Chaining Audit Trail'}")

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("دورات التنفيذ" if is_ar else "Execution Cycles", f"{trace.inference_cycles}", "وصول لحالة الاستقرار" if is_ar else "Saturation Reached")
    col_m2.metric("حقائق الذاكرة العاملة" if is_ar else "Working Memory Facts", f"{trace.working_memory_size}", "قواعد أساسية ومستنتجة" if is_ar else "Base + Derived")
    col_m3.metric("القواعد المفعلة" if is_ar else "Fired Rules", f"{len(trace.fired_rules)}", "استدلال منطقي" if is_ar else "Modus Ponens")

    st.markdown(f"##### {'النتائج المنطقية للتدقيق السريري' if is_ar else 'Clinical Audit Rationale'}")
    th_m = "معيار التقييم" if is_ar else "Evaluation Metric"
    th_f = "النتيجة السريرية" if is_ar else "Clinical Reasoning Finding"
    th_s = "الحالة" if is_ar else "Status"

    aud_rows = []
    for a in trace.audit_summary:
        m_txt = a["metric"]
        f_txt = a["finding"]
        s_txt = a["status"]
        if is_ar:
            if m_txt == "Triage Decision":
                m_txt = "قرار الفرز النهائي"
                f_txt = f"يتطلب تدخلاً طبياً عاجلاً وفورياً ({urgency_title}) بعد {trace.inference_cycles} دورات استدلال." if "URGENT" in f_txt else f"رعاية عادية مناسبة للعيادات الخارجية بعد {trace.inference_cycles} دورات استدلال."
            elif m_txt == "Red-Flag Symptoms":
                m_txt = "علامات الخطورة الحمراء"
                f_txt = f"استنتج محرك الاستدلال علامات خطورة حمراء لـ {len(trace.red_flag_alerts)} عرض(أعراض). تم منع الخروج للعيادات الخارجية." if len(trace.red_flag_alerts) > 0 else "لم يتم رصد أي علامات خطورة حمراء."
            elif m_txt == "Vital Signs Status":
                m_txt = "حالة المؤشرات الحيوية"
                f_txt = "تم استنتاج عدم استقرار فسيولوجي في المؤشرات الحيوية للمريض." if "instability" in f_txt.lower() else "العلامات الحيوية ضمن الحدود الآمنة المستقرة."
            elif m_txt == "Primary Differential":
                m_txt = "التشخيص الأولي المرجّح"
                top_name = COND_AR.get(trace.suspected_conditions[0]["condition_id"], trace.suspected_conditions[0]["name"]) if trace.suspected_conditions else ""
                top_dept = DEPT_AR.get(trace.recommended_department, trace.recommended_department)
                f_txt = f"التشخيص الأكثر ترجيحاً: {top_name} (أدلة {trace.suspected_conditions[0]['confidence_score']:.0f}%) -> التوجيه إلى {top_dept}."
        
        aud_rows.append(
            f"""<tr>
                <td style="font-weight:700;">{esc(m_txt)}</td>
                <td>{esc(f_txt)}</td>
                <td><span class="vital-tag" style="background:#f1f5f9;color:#0f172a;">{esc(s_txt)}</span></td>
            </tr>"""
        )

    st.html(
        f"""<div class="pro-table-wrapper">
            <table class="pro-table">
                <thead><tr><th>{th_m}</th><th>{th_f}</th><th>{th_s}</th></tr></thead>
                <tbody>{"".join(aud_rows)}</tbody>
            </table>
        </div>"""
    )

    st.markdown(f"##### {'سجل القواعد الصورية التي تم تنفيذها' if is_ar else 'Production Rules Evaluated'}")
    th_r = "معرف القاعدة" if is_ar else "Rule ID"
    th_cy = "الدورة" if is_ar else "Cycle"
    th_if = "المقدمة المنطقية (IF)" if is_ar else "Premise (IF)"
    th_then = "النتيجة المستنتجة (THEN)" if is_ar else "Consequence (THEN)"

    rules_rows = []
    for r in trace.fired_rules:
        rules_rows.append(
            f"""<tr>
                <td style="font-family:var(--font-mono);font-weight:700;color:#2563eb;">{esc(r["rule_id"])}</td>
                <td><span class="vital-tag" style="background:#eff6ff;color:#1d4ed8;">{esc(r.get("cycle", "Cycle 1"))}</span></td>
                <td><code style="font-family:var(--font-mono);font-size:11.5px;color:#0f172a;background:#f1f5f9;padding:2px 6px;border-radius:4px;">{esc(r["formal_logic"])}</code></td>
                <td style="font-weight:600;">{esc(r["consequence"])}</td>
            </tr>"""
        )

    st.html(
        f"""<div class="pro-table-wrapper">
            <table class="pro-table">
                <thead><tr><th>{th_r}</th><th>{th_cy}</th><th>{th_if}</th><th>{th_then}</th></tr></thead>
                <tbody>{"".join(rules_rows)}</tbody>
            </table>
        </div>"""
    )

# ------------------------------------------------------------------------------
# TAB 4: KNOWLEDGE GRAPH (360° FREE DRAG + UNTANGLED EDGES + KARIM STYLE)
# ------------------------------------------------------------------------------
with tab4:
    st.markdown(f"#### {'المخطط الفرعي التفاعلي لشبكة المعرفة السريرية' if is_ar else 'Interactive Clinical Knowledge Graph Subgraph'}")

    p_lbl = "المريض" if is_ar else "Patient"
    rf_lbl = "عرض خطورة" if is_ar else "Red-Flag Symptom"
    std_lbl = "عرض اعتيادي" if is_ar else "Standard Symptom"
    risk_lbl = "عامل خطورة" if is_ar else "Risk Factor"
    cond_lbl = "حالة مرضية" if is_ar else "Condition"
    proto_lbl = "بروتوكول علاجي" if is_ar else "Clinical Protocol"

    kg_ctrl1, kg_ctrl2, kg_ctrl3 = st.columns(3)
    with kg_ctrl1:
        kg_show_edges = st.checkbox("إظهار مسميات العلاقات" if is_ar else "Show Edge Labels", value=True, key="kg_edge_lbls")
    with kg_ctrl2:
        kg_show_protos = st.checkbox("إظهار طبقة البروتوكولات" if is_ar else "Include Clinical Protocols", value=False, key="kg_protos")
    with kg_ctrl3:
        kg_physics = st.checkbox("تنافر تلقائي لفك التشابك" if is_ar else "Auto-Repulsion Physics", value=False, key="kg_physics")

    proto_legend_html = f'<span><span style="color:#0284c7;">■</span> <strong>{proto_lbl}</strong></span>' if kg_show_protos else ""
    st.html(
        f"""
        <div style="display:flex;flex-wrap:wrap;gap:14px;font-size:12px;background:#ffffff;border:1px solid #e2e8f0;padding:8px 14px;border-radius:6px;margin-bottom:10px;align-items:center;">
            <span><span style="color:#2563eb;">●</span> <strong>{p_lbl}</strong></span>
            <span><span style="color:#dc2626;">●</span> <strong>{rf_lbl}</strong></span>
            <span><span style="color:#059669;">●</span> <strong>{std_lbl}</strong></span>
            <span><span style="color:#d97706;">▲</span> <strong>{risk_lbl}</strong></span>
            <span><span style="color:#7c3aed;">■</span> <strong>{cond_lbl}</strong></span>
            {proto_legend_html}
        </div>
        """
    )

    try:
        from pyvis.network import Network

        net = Network(height="580px", width="100%", bgcolor="#fcfdff", font_color="#0f172a")
        physics_cfg = (
            """
            "physics": {
              "enabled": true,
              "solver": "repulsion",
              "repulsion": {
                "nodeDistance": 250,
                "centralGravity": 0.08,
                "springLength": 230,
                "springConstant": 0.03,
                "damping": 0.25
              },
              "stabilization": { "enabled": true, "iterations": 120 }
            }
            """
            if kg_physics
            else '"physics": { "enabled": false }'
        )

        net.set_options(f"""
        {{
          "layout": {{
            "improvedLayout": false,
            "hierarchical": {{ "enabled": false }}
          }},
          {physics_cfg},
          "interaction": {{
            "dragNodes": true,
            "zoomView": true,
            "dragView": true,
            "hover": true,
            "multiselect": true,
            "tooltipDelay": 100
          }},
          "nodes": {{
            "borderWidth": 2,
            "borderWidthSelected": 3,
            "shadow": {{
              "enabled": true,
              "color": "rgba(15, 23, 42, 0.08)",
              "size": 8,
              "x": 0,
              "y": 2
            }}
          }},
          "edges": {{
            "smooth": {{
              "type": "curvedCW",
              "roundness": 0.16
            }},
            "arrows": {{ "to": {{ "enabled": true, "scaleFactor": 0.7 }} }},
            "font": {{
              "size": 10,
              "face": "JetBrains Mono, Cairo, sans-serif",
              "color": "#475569",
              "background": "#fcfdff",
              "strokeWidth": 0,
              "align": "middle"
            }},
            "selectionWidth": 2.5
          }}
        }}
        """)

        def _cy(idx: int, total: int, step: int = 105) -> int:
            return int((idx - (total - 1) / 2.0) * step)

        x_pat = -480
        x_mid = -150
        x_cond = 210
        x_proto = 560

        p_display_name = p_name if is_ar else pat_rec["name"]
        p_node = f"pat_{selected_pid}"
        net.add_node(
            p_node,
            label=f"{p_display_name}\n({selected_pid})",
            title=f"Patient: {p_display_name} | HR: {pat_rec['hr_bpm']} | SpO2: {pat_rec['spo2_pct']}%",
            x=x_pat,
            y=0,
            color={"background": "#2563eb", "border": "#1d4ed8"},
            size=26,
            shape="dot",
            font={"color": "#0f172a", "size": 13, "bold": True},
        )

        # Stack Symptoms + Risk Factors cleanly on Level 1 (free to drag 360° after load)
        mid_nodes = [("SYM", s) for s in trace.presented_symptoms] + [("RISK", rf) for rf in trace.active_risk_factors]
        for idx, (kind, obj) in enumerate(mid_nodes):
            y_pos = _cy(idx, len(mid_nodes), step=105)
            if kind == "SYM":
                s = obj
                s_node = f"sym_{s['symptom_id']}"
                s_col = "#dc2626" if s["is_red_flag"] else "#059669"
                s_label = SYM_AR.get(s["symptom_id"], s["name"]) if is_ar else s["name"]
                edge_lbl = ("يعاني من" if is_ar else "PRESENTS") if kg_show_edges else ""
                net.add_node(
                    s_node,
                    label=s_label,
                    title=f"{s['body_system']} | Red Flag: {s['is_red_flag']} | Weight: {s['severity_weight']}/5",
                    x=x_mid,
                    y=y_pos,
                    color={"background": s_col, "border": s_col},
                    size=18,
                    shape="dot",
                    font={"color": s_col, "size": 11, "bold": s["is_red_flag"]},
                )
                net.add_edge(p_node, s_node, label=edge_lbl, title="PRESENTS_SYMPTOM", color=s_col, width=2)
            else:
                rf = obj
                r_node = f"rf_{rf['risk_id']}"
                r_label = RISK_AR.get(rf["risk_id"], rf["name"]) if is_ar else rf["name"]
                edge_lbl = ("عامل خطورة" if is_ar else "HAS_RISK") if kg_show_edges else ""
                net.add_node(
                    r_node,
                    label=r_label,
                    title=rf["escalation_note"],
                    x=x_mid,
                    y=y_pos,
                    color={"background": "#d97706", "border": "#b45309"},
                    size=18,
                    shape="triangle",
                    font={"color": "#b45309", "size": 11},
                )
                net.add_edge(p_node, r_node, label=edge_lbl, title="HAS_RISK_FACTOR", color="#d97706", width=1.8, dashes=True)

        top_conds = trace.suspected_conditions[:4]
        for idx, c in enumerate(top_conds):
            c_node = f"cond_{c['condition_id']}"
            c_label = COND_AR.get(c["condition_id"], c["name"]) if is_ar else c["name"]
            net.add_node(
                c_node,
                label=f"{c_label}\n[{c['triage_level']} • {c['confidence_score']:.0f}%]",
                title=c["clinical_summary"],
                x=x_cond,
                y=_cy(idx, len(top_conds), step=135),
                color={"background": "#7c3aed", "border": "#5b21b6"},
                size=22,
                shape="box",
                margin=10,
                shapeProperties={"borderRadius": 8},
                font={"color": "#ffffff", "size": 11, "bold": True},
            )
            ind_lbl = ("يشير إلى" if is_ar else "INDICATES") if kg_show_edges else ""
            for s in trace.presented_symptoms:
                if s["name"] in c["matched_symptoms"]:
                    net.add_edge(f"sym_{s['symptom_id']}", c_node, label=ind_lbl, title="INDICATES", color="#7c3aed", width=1.6)
            for esc_item in trace.risk_escalations:
                if esc_item["condition_id"] == c["condition_id"]:
                    esc_lbl = (f"يضاعف +{esc_item['points']}" if is_ar else f"ESCALATES +{esc_item['points']}") if kg_show_edges else ""
                    net.add_edge(f"rf_{esc_item['risk_id']}", c_node, label=esc_lbl, title=esc_item["rationale"], color="#d97706", width=1.8, dashes=True)

        if kg_show_protos and trace.protocols:
            cond_name_to_id = {c["name"]: c["condition_id"] for c in top_conds}
            shown_protos = trace.protocols[:5]
            for idx, p in enumerate(shown_protos):
                p_id_node = f"proto_{p['protocol_id']}"
                is_contra = p["action_type"] == "CONTRAINDICATION"
                p_col = "#dc2626" if is_contra else "#0284c7"
                p_bg = "#fef2f2" if is_contra else "#f0f9ff"
                p_fg = "#991b1b" if is_contra else "#0c4a6e"
                raw_instr = PROTOCOLS_AR.get(p["protocol_id"], p["instruction"]) if is_ar else p["instruction"]
                short_instr = raw_instr[:38] + ("..." if len(raw_instr) > 38 else "")
                net.add_node(
                    p_id_node,
                    label=f"{p['protocol_id']}\n{short_instr}",
                    title=raw_instr,
                    x=x_proto,
                    y=_cy(idx, len(shown_protos), step=115),
                    color={"background": p_bg, "border": p_col},
                    shape="box",
                    margin=8,
                    shapeProperties={"borderRadius": 8},
                    font={"color": p_fg, "size": 10.5, "bold": is_contra},
                )
                parent_cid = cond_name_to_id.get(p["condition_name"])
                if parent_cid:
                    plbl = (("ممنوع" if is_contra else "إجراء") if is_ar else ("CONTRAINDICATED" if is_contra else "PROTOCOL")) if kg_show_edges else ""
                    net.add_edge(f"cond_{parent_cid}", p_id_node, label=plbl, title=p["action_type"], color=p_col, width=1.6, dashes=[4, 4] if is_contra else False)

        graph_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_triage.html")
        net.save_graph(graph_path)
        with open(graph_path, "r", encoding="utf-8") as f:
            gh = f.read()

        hint_txt = "اسحب أي عقدة بحرية 360°" if is_ar else "Drag any node freely in 360°"
        fit_lbl = "توسيط" if is_ar else "Fit View"
        rst_lbl = "إعادة الترتيب" if is_ar else "Reset Layout"

        fit_js = f"""
<style>
  html, body {{
    background-color: #fcfdff !important;
    background-image: radial-gradient(rgba(15, 23, 42, 0.05) 1px, transparent 1px);
    background-size: 20px 20px;
    margin: 0;
    padding: 0;
    overflow: hidden;
    font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
  }}
  .kg-toolbar {{
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 999;
    display: flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(6px);
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  }}
  .kg-hint {{
    font-size: 11px;
    color: #64748b;
    padding: 0 8px;
    border-right: 1px solid #e2e8f0;
  }}
  .kg-btn {{
    border: 1px solid transparent;
    background: transparent;
    color: #334155;
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 9px;
    border-radius: 6px;
    cursor: pointer;
  }}
  .kg-btn:hover {{ background: #eff6ff; color: #0284c7; }}
</style>
<div class="kg-toolbar">
  <span class="kg-hint">{hint_txt}</span>
  <button class="kg-btn" onclick="kgZoom(1.22)">+</button>
  <button class="kg-btn" onclick="kgZoom(0.82)">-</button>
  <button class="kg-btn" onclick="kgFit()">{fit_lbl}</button>
  <button class="kg-btn" onclick="kgReset()">{rst_lbl}</button>
</div>
<script>
var initialPositions = null;
function kgCapture(){{
  if(!initialPositions && typeof network!=="undefined" && network!==null){{
    initialPositions = network.getPositions();
  }}
}}
function kgFit(){{
  if(typeof network!=="undefined"&&network!==null){{
    var el=document.getElementById("mynetwork");
    if(el&&el.clientWidth>50&&el.clientHeight>50){{
      kgCapture();
      network.redraw();
      network.fit({{animation:{{duration:240,easingFunction:"easeInOutQuad"}}}});
    }}
  }}
}}
function kgZoom(f){{
  if(typeof network!=="undefined"&&network!==null){{
    network.moveTo({{scale: network.getScale()*f, animation:{{duration:180,easingFunction:"easeInOutQuad"}}}});
  }}
}}
function kgReset(){{
  if(typeof network!=="undefined"&&network!==null&&initialPositions){{
    Object.keys(initialPositions).forEach(function(id){{
      network.moveNode(id, initialPositions[id].x, initialPositions[id].y);
    }});
    setTimeout(kgFit, 60);
  }}
}}
(function(){{
  var c=setInterval(function(){{
    if(typeof network!=="undefined"&&network!==null){{
      clearInterval(c);
      kgFit();
      var el=document.getElementById("mynetwork");
      if(el&&typeof ResizeObserver!=="undefined"){{
        new ResizeObserver(function(){{ setTimeout(kgFit, 60); }}).observe(el);
      }}
      if(el&&typeof IntersectionObserver!=="undefined"){{
        new IntersectionObserver(function(entries){{
          if(entries[0]&&entries[0].isIntersecting){{ setTimeout(kgFit, 80); }}
        }}).observe(el);
      }}
      window.addEventListener("resize", function(){{ setTimeout(kgFit, 60); }});
    }}
  }}, 80);
}})();
</script>
"""
        gh = gh.replace("<body>", "<body>")
        gh = gh.replace("</body>", fit_js + "</body>")
        components.html(gh, height=600)
    except Exception as e:
        st.warning(f"Unable to render graph: {e}")

# ------------------------------------------------------------------------------
# TAB 5: WALK-IN SIMULATOR
# ------------------------------------------------------------------------------
with tab5:
    st.markdown(f"#### {'محاكي فرز الحالات الطارئة الجديد' if is_ar else 'Live Walk-In Triage Simulator'}")

    presets_en = ["Code STEMI", "Septic Shock", "Acute Asthma", "Appendicitis", "Mild URI"]
    presets_ar = ["جلطة قلبية حادة", "صدمة إنتانية", "أزمة ربو حادة", "التهاب الزائدة", "نزلة برد بسيطة"]
    preset_options = presets_ar if is_ar else presets_en

    preset_label = "تحميل سيناريو سريري جاهز:" if is_ar else "Load Clinical Scenario Preset:"
    preset_choice = st.pills(
        preset_label,
        options=preset_options,
        default=None,
    )

    p_age = int(pat_rec["age"])
    p_hr = int(pat_rec["hr_bpm"])
    p_bp = int(pat_rec["bp_sys"])
    p_spo2 = int(pat_rec["spo2_pct"])
    p_temp = float(pat_rec["temp_c"])
    p_rr = int(pat_rec["rr_bpm"])
    p_syms = list(pat_syms)
    p_risks = list(pat_risks)

    if preset_choice in ("Code STEMI", "جلطة قلبية حادة"):
        p_age, p_hr, p_bp, p_spo2, p_temp, p_rr = 62, 118, 165, 93, 37.1, 24
        p_syms = ["SYM01", "SYM02", "SYM03", "SYM21"]
        p_risks = ["RF01", "RF02"]
    elif preset_choice in ("Septic Shock", "صدمة إنتانية"):
        p_age, p_hr, p_bp, p_spo2, p_temp, p_rr = 71, 130, 84, 88, 39.6, 29
        p_syms = ["SYM09", "SYM18", "SYM22"]
        p_risks = ["RF02", "RF08"]
    elif preset_choice in ("Acute Asthma", "أزمة ربو حادة"):
        p_age, p_hr, p_bp, p_spo2, p_temp, p_rr = 35, 112, 130, 91, 37.0, 26
        p_syms = ["SYM03", "SYM10"]
        p_risks = ["RF06"]
    elif preset_choice in ("Appendicitis", "التهاب الزائدة"):
        p_age, p_hr, p_bp, p_spo2, p_temp, p_rr = 22, 92, 120, 99, 38.2, 18
        p_syms = ["SYM08", "SYM24", "SYM09"]
        p_risks = []
    elif preset_choice in ("Mild URI", "نزلة برد بسيطة"):
        p_age, p_hr, p_bp, p_spo2, p_temp, p_rr = 26, 76, 116, 99, 37.2, 15
        p_syms = ["SYM15", "SYM16", "SYM23"]
        p_risks = []

    s_col1, s_col2 = st.columns([1.3, 1])
    with s_col1:
        lbl_syms_input = "الأعراض الظاهرة" if is_ar else "Presenting Symptoms"
        sim_syms = st.multiselect(
            lbl_syms_input,
            options=list(all_symptoms.keys()),
            default=p_syms,
            format_func=lambda sid: (
                f"{sid} — {SYM_AR.get(sid, all_symptoms[sid]['name'])} {'[علامة خطورة]' if all_symptoms[sid]['is_red_flag'] else ''}"
                if is_ar
                else f"{sid} — {all_symptoms[sid]['name']} {'[RED FLAG]' if all_symptoms[sid]['is_red_flag'] else ''}"
            ),
        )
        lbl_risks_input = "عوامل الخطورة والأمراض المزمنة" if is_ar else "Comorbidities / Risk Factors"
        sim_risks = st.multiselect(
            lbl_risks_input,
            options=list(all_risks.keys()),
            default=p_risks,
            format_func=lambda rid: (
                f"{rid} — {RISK_AR.get(rid, all_risks[rid]['name'])}"
                if is_ar
                else f"{rid} — {all_risks[rid]['name']}"
            ),
        )
    with s_col2:
        sim_age = st.number_input("عمر المريض" if is_ar else "Patient Age", min_value=1, max_value=110, value=p_age)
        v_sub1, v_sub2 = st.columns(2)
        with v_sub1:
            sim_spo2 = st.number_input("نسبة الأكسجين SpO2 %" if is_ar else "SpO2 %", min_value=50, max_value=100, value=p_spo2)
            sim_bp = st.number_input("الضغط الانقباضي" if is_ar else "Systolic BP", min_value=50, max_value=260, value=p_bp)
        with v_sub2:
            sim_hr = st.number_input("معدل النبض" if is_ar else "Heart Rate", min_value=20, max_value=220, value=p_hr)
            sim_temp = st.number_input("الحرارة °C" if is_ar else "Temp °C", min_value=34.0, max_value=43.0, value=p_temp, step=0.1)
        sim_rr = st.number_input("معدل التنفس /min" if is_ar else "Resp Rate (/min)", min_value=8, max_value=50, value=p_rr)

    sim_trace = engine.evaluate_custom_case(
        patient_id="SIM-WALKIN",
        patient_name="Walk-In Simulated Patient",
        age=int(sim_age),
        vitals={
            "hr_bpm": int(sim_hr),
            "bp_sys": int(sim_bp),
            "bp_dia": 80,
            "spo2_pct": int(sim_spo2),
            "temp_c": float(sim_temp),
            "rr_bpm": int(sim_rr),
        },
        symptom_ids=sim_syms,
        risk_ids=sim_risks,
    )

    sim_esi_col = ESI_METADATA[sim_trace.triage_level]["color"]
    sim_top = (
        COND_AR.get(sim_trace.suspected_conditions[0]["condition_id"], sim_trace.suspected_conditions[0]["name"])
        if sim_trace.suspected_conditions
        else ("قيد التقييم" if is_ar else "Under Evaluation")
    )
    sim_urgency_lbl = ESI_AR.get(sim_trace.triage_level, sim_trace.urgency_label) if is_ar else sim_trace.urgency_label
    sim_dept_lbl = DEPT_AR.get(sim_trace.recommended_department, sim_trace.recommended_department) if is_ar else sim_trace.recommended_department

    st.html(
        f"""
        <div class="triage-banner" style="border-left: 5px solid {sim_esi_col}; margin-top:14px;">
            <div class="triage-tier-left">
                <div class="esi-badge-lg esi-{sim_trace.triage_level.split('-')[-1]}-bg">{esc(sim_trace.triage_level)}</div>
                <div>
                    <h3 class="triage-headline">{'النتيجة المحاكاة' if is_ar else 'Simulated Disposition'}: {esc(sim_urgency_lbl)}</h3>
                    <div class="triage-subtext">{'التشخيص الأولي' if is_ar else 'Primary Condition'}: <strong>{esc(sim_top)}</strong> &nbsp;•&nbsp; {'القسم' if is_ar else 'Routing'}: <strong>{esc(sim_dept_lbl)}</strong></div>
                </div>
            </div>
            <div class="triage-wait-box">
                <div class="triage-wait-label">{'وقت الانتظار الأقصى' if is_ar else 'Target Wait'}</div>
                <div class="triage-wait-val" style="color:{sim_esi_col};">{sim_trace.max_wait_minutes} {'دقيقة' if is_ar else 'min'}</div>
            </div>
        </div>
        """
    )

# ==============================================================================
# CLINICAL SBAR SUMMARY HANDOFF NOTE
# ==============================================================================
st.markdown("---")
sbar_header = "تقرير التسليم السريري للمريض (نموذج ISBAR)" if is_ar else "Clinical SBAR Handoff Record (ISBAR Format)"
with st.expander(sbar_header, expanded=False):
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if is_ar:
        syms_display = [SYM_NAME_TO_AR.get(s["name"], s["name"]) for s in trace.presented_symptoms]
        risks_display = [RISK_AR.get(rf["risk_id"], rf["name"]) for rf in trace.active_risk_factors]
        top_cond_name_display = COND_AR.get(trace.suspected_conditions[0]["condition_id"], trace.suspected_conditions[0]["name"]) if trace.suspected_conditions else 'لا يوجد'
        target_dept_display = DEPT_AR.get(trace.recommended_department, trace.recommended_department)
        target_disp_display = DISPOSITION_AR.get(trace.disposition, trace.disposition)
        
        proto_lines = [f"- [{TIMEFRAME_AR.get(p['timeframe'], p['timeframe'])}] {PROTOCOLS_AR.get(p['protocol_id'], p['instruction'])}" for p in trace.protocols] if trace.protocols else ['- استشارة روتينية بالعيادات الخارجية.']
        formatted_protocols = chr(10).join(proto_lines)

        sbar_text = f"""================================================================================
تقرير التسليم السريري للحالات الطارئة (نموذج ISBAR) | نظام الفرز الذكي IS438
================================================================================
رقم الملف: {selected_pid}
الاسم: {p_name} | العمر: {pat_rec['age']} سنة | الجنس: {p_gender}
توقيت التسجيل: {now_str}

[I] التعريف بالحالة (IDENTIFICATION):
المريض {p_name}، يبلغ من العمر {pat_rec['age']} سنة، متواجد بقسم الطوارئ.

[S] الموقف الحالي (SITUATION):
- تصنيف الفرز المعتمد: {trace.triage_level} ({urgency_title})
- أقصى وقت انتظار آمن: {trace.max_wait_minutes} دقيقة
- القسم الطبي المستهدف: {target_dept_display}
- التوجيه السريري: {target_disp_display}

[B] الخلفية المرضية (BACKGROUND):
- الشكوى الرئيسية: "{p_complaint}"
- الأعراض المسجلة ({len(pat_syms)}): {', '.join(syms_display)}
- الأمراض المزمنة النشطة ({len(pat_risks)}): {', '.join(risks_display) if risks_display else 'لا توجد'}

[A] التقييم السريري والفسيولوجي (ASSESSMENT):
- العلامات الحيوية: النبض {pat_rec['hr_bpm']} نبضة/دقيقة ({hr_tag}) | الضغط {pat_rec['bp_sys']}/{pat_rec['bp_dia']} ملم زئبق ({bp_tag}) | الأكسجين {pat_rec['spo2_pct']}% ({spo2_tag}) | الحرارة {pat_rec['temp_c']} °C ({temp_tag}) | التنفس {pat_rec['rr_bpm']} /دقيقة ({rr_tag})
- التشخيص المرجّح الأول: {top_cond_name_display} (قوة الأدلة: {trace.suspected_conditions[0]['confidence_score']:.0f}%)
- علامات الخطورة الحمراء: {len(trace.red_flag_alerts)} علامات مرصودة
- الاستدلال المنطقي: اكتمل الاستدلال بعد {trace.inference_cycles} دورات وتم تفعيل {len(trace.fired_rules)} قاعدة صورية

[R] التوصيات والبروتوكولات الفورية (RECOMMENDATION):
{formatted_protocols}
================================================================================
"""
    else:
        sbar_text = f"""================================================================================
CLINICAL EMERGENCY TRIAGE SBAR NOTE | IS438 KNOWLEDGE-BASED SYSTEM
================================================================================
PATIENT ID: {selected_pid}
NAME: {p_name} | AGE: {pat_rec['age']} | GENDER: {p_gender}
RECORDED: {now_str}

[S] SITUATION:
- Assigned Triage: {trace.triage_level} ({trace.urgency_label})
- Max Safe Wait: {trace.max_wait_minutes} minutes
- Target Unit: {trace.recommended_department}

[B] BACKGROUND:
- Chief Complaint: {p_complaint}
- Reported Symptoms ({len(pat_syms)}): {', '.join([s['name'] for s in trace.presented_symptoms])}
- Active Comorbidities: {', '.join([rf['name'] for rf in trace.active_risk_factors]) if trace.active_risk_factors else 'None'}

[A] ASSESSMENT:
- Vitals: HR {pat_rec['hr_bpm']} bpm | BP {pat_rec['bp_sys']}/{pat_rec['bp_dia']} mmHg | SpO2 {pat_rec['spo2_pct']}% | Temp {pat_rec['temp_c']} °C | RR {pat_rec['rr_bpm']}/min
- Primary Suspected Diagnosis: {trace.suspected_conditions[0]['name'] if trace.suspected_conditions else 'None'} ({trace.suspected_conditions[0]['confidence_score']:.0f}% confidence)
- Red Flags: {len(trace.red_flag_alerts)} detected
- Multi-Cycle Inference: {trace.inference_cycles} Cycles, {len(trace.fired_rules)} Rules Fired

[R] RECOMMENDATION & ORDERS:
{chr(10).join([f"- [{p['action_type']}] {p['instruction']} ({p['timeframe']})" for p in trace.protocols]) if trace.protocols else '- Routine outpatient consultation.'}
================================================================================
"""

    st.text_area("نموذج تقرير التسليم السريري" if is_ar else "Structured SBAR Note", sbar_text, height=220)
    st.download_button(
        "تحميل تقرير التسليم السريري (.txt)" if is_ar else "Download Clinical Handoff Note (.txt)",
        data=sbar_text,
        file_name=f"triage_sbar_{selected_pid}.txt",
        mime="text/plain",
    )
