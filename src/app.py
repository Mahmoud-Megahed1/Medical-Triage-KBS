# -*- coding: utf-8 -*-
"""
Medical Triage & Emergency Knowledge-Based System (IS438)
Application Entry Point — Clean Orchestration Layer
"""

import os
import streamlit as st

from inference_engine import MedicalTriageEngine
from ui.i18n_ar import COND_AR, SYM_AR, ACTION_AR
from ui.components import (
    esc,
    esi_badge,
    inject_design_system,
    render_disposition_banner,
    render_evidence_bar,
    render_header,
    render_knowledge_graph,
    render_kpi_grid,
    render_section_header,
    render_sidebar_patient_summary,
    render_table,
)

st.set_page_config(
    page_title="Medical Triage KBS | IS438",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
inject_design_system(os.path.join(BASE_DIR, "ui", "theme.css"))


@st.cache_resource
def load_triage_engine():
    data_path = os.path.join(os.path.dirname(BASE_DIR), "data")
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
# SIDEBAR: INTAKE & VITALS
# ==================================================================
st.sidebar.markdown("### Triage Intake Controls")
st.sidebar.html('<div class="ar-note" dir="rtl" style="font-size:12px;color:#64748b;margin-bottom:6px;">اختيار رقم المريض ومراجعة مؤشراته الحيوية.</div>')

patient_ids = list(patients_map.keys())
selected_pid = st.sidebar.selectbox(
    "Patient ID (رقم المريض)",
    options=patient_ids,
    format_func=lambda pid: f"{pid} - {patients_map[pid]['name']}",
)

pat_rec, pat_syms, pat_risks = engine.get_patient_case(selected_pid)
render_sidebar_patient_summary(pat_rec, len(pat_syms), len(pat_risks), engine.mode)

# ==================================================================
# MAIN WORKSPACE: VERDICT + KPI STRIP + 5 TABS
# ==================================================================
trace = engine.evaluate_patient(selected_pid)
top_cond = trace.suspected_conditions[0] if trace.suspected_conditions else None
top_cond_ar = COND_AR.get(top_cond["condition_id"], "أول تشخيص مرجّح") if top_cond else "لا يوجد تطابق محدد"

render_header()
render_disposition_banner(trace)
render_kpi_grid(trace, top_cond_ar)

# ==================================================================
# URL-PERSISTENT TAB NAVIGATION (Survives Browser Refresh / F5)
# ==================================================================
TAB_SPECS = [
    ("diagnosis", "Differential Diagnosis"),
    ("protocols", "Action Protocols"),
    ("trace", "Inference Trace"),
    ("graph", "Knowledge Graph"),
    ("simulator", "Triage Simulator"),
]
VALID_TABS = {slug for slug, _ in TAB_SPECS}

qp_tab = st.query_params.get("tab", "diagnosis")
if qp_tab not in VALID_TABS:
    qp_tab = "diagnosis"
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = qp_tab
elif st.query_params.get("tab") in VALID_TABS:
    st.session_state["active_tab"] = st.query_params.get("tab")

nav_cols = st.columns(len(TAB_SPECS))
for col, (slug, label) in zip(nav_cols, TAB_SPECS):
    is_active = st.session_state["active_tab"] == slug
    with col:
        if st.button(
            label,
            key=f"nav_{slug}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["active_tab"] = slug
            st.query_params["tab"] = slug
            st.rerun()

active_tab = st.session_state["active_tab"]

# ==================================================================
# TAB 1: DIFFERENTIAL DIAGNOSIS
# ==================================================================
if active_tab == "diagnosis":
    render_section_header(
        "Suspected Medical Conditions (Graph Evidence Ranking)",
        f"Traversed <code>(:Patient)-[:PRESENTS_SYMPTOM]-&gt;(:Symptom)&lt;-[:INDICATED_BY]-(:MedicalCondition)</code> for <strong>{esc(pat_rec['name'])}</strong>.",
        "الحالات الطبية المحتملة مرتبة حسب قوة تطابق الأعراض ومضاعفة عوامل الخطورة.",
    )

    if trace.suspected_conditions:
        cond_rows = []
        for c in trace.suspected_conditions:
            matched_str = ", ".join(c["matched_symptoms"])
            risk_str = ", ".join(c["risk_notes"]) if c["risk_notes"] else "None"
            cond_ar_txt = COND_AR.get(c["condition_id"], "")
            cond_cell = f'<strong style="color:#111827;">{esc(c["name"])}</strong>'
            if cond_ar_txt:
                cond_cell += f'<div class="ar-cell" dir="rtl">{esc(cond_ar_txt)}</div>'
            cond_rows.append([
                f'<span class="badge b-code">{esc(c["condition_id"])}</span>',
                cond_cell,
                esi_badge(c["triage_level"]),
                render_evidence_bar(c["confidence_score"]),
                f'<span style="font-size:12px;">{esc(matched_str)}</span>',
                f'<span style="font-size:12px;color:#64748b;">{esc(risk_str)}</span>',
                f'<span class="badge b-neutral">{esc(c["department"])}</span>',
            ])
        st.html(render_table(
            ["Code", "Suspected Condition", "ESI Tier", "Evidence", "Matched Symptoms", "Risk Escalation", "Target Unit"],
            cond_rows,
            ["8%", "23%", "9%", "10%", "21%", "14%", "15%"],
        ))
    else:
        st.info("No matching conditions found in the knowledge base for the reported symptom set.")

    render_section_header(
        "Reported Symptoms Classification",
        "Evaluation of presenting symptoms against clinical Red-Flag triage predicates.",
        "تصنيف الأعراض الظاهرة هل هي علامات خطورة حمراء أم أعراض اعتيادية.",
    )
    sym_rows = []
    for s in trace.presented_symptoms:
        flag_badge = (
            '<span class="badge b-esi1">RED FLAG</span><div class="ar-cell" dir="rtl">علامة خطورة حمراء</div>'
            if s["is_red_flag"]
            else '<span class="badge b-esi4">STANDARD</span><div class="ar-cell" dir="rtl">عرض غير طارئ</div>'
        )
        s_ar_txt = SYM_AR.get(s["symptom_id"], "")
        s_cell = f'<strong style="color:#111827;">{esc(s["name"])}</strong>'
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
# TAB 2: ACTION PROTOCOLS & SAFETY CONTRAINDICATIONS
# ==================================================================
elif active_tab == "protocols":
    render_section_header(
        "Required Interventions, Workups & Contraindications",
        "Retrieved via <code>(:MedicalCondition)-[:REQUIRES_PROTOCOL]-&gt;(:ClinicalProtocol)</code>.",
        "الإجراءات الطبية الفورية والفحوصات المطلوبة والممنوعات السريرية للحالة.",
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
                f'<strong style="color:#111827;">{esc(p["condition_name"])}</strong>',
                f'<span style="text-align:left;display:inline-block;">{esc(p["instruction"])}</span>',
                f'<span class="badge b-purple">{esc(p["timeframe"])}</span>',
            ])
        st.html(render_table(
            ["Protocol", "Category", "Associated Condition", "Clinical Instruction", "Timeframe"],
            p_rows,
            ["10%", "19%", "20%", "37%", "14%"],
        ))
    else:
        st.html(
            '<div class="ds-empty">'
            '<span>Standard supportive outpatient instructions apply. No critical restrictions triggered.</span>'
            '<span class="ar-pill" dir="rtl">تعليمات رعاية عادية</span>'
            '</div>'
        )

# ==================================================================
# TAB 3: INFERENCE ENGINE TRACE (FORWARD CHAINING & MODUS PONENS)
# ==================================================================
elif active_tab == "trace":
    render_section_header(
        "Executive Triage Audit",
        f"Converged in <strong>{trace.inference_cycles}</strong> Forward-Chaining cycles across <strong>{trace.working_memory_size}</strong> Working Memory facts.",
        "أولاً — ملخص قرار الفرز الطبي وأسباب تصنيف أولوية الحالة.",
    )
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
            f'<strong style="color:#111827;">{esc(a["metric"])}</strong>',
            f'<span>{esc(a["finding"])}</span>',
            sb,
        ])
    st.html(render_table(["Evaluation Metric", "Clinical Reasoning Finding", "Status"], aud_rows, ["22%", "60%", "18%"]))

    render_section_header(
        "Physiological & Red-Flag Escalations",
        "Critical vital thresholds and Modus Ponens symptom triggers overriding low-acuity care.",
        "ثانياً — علامات الخطورة في المؤشرات الحيوية والأعراض التي رفعت الأولوية.",
    )
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
        st.html(
            '<div class="ds-empty">'
            '<span>No emergency vital-sign abnormalities or red-flag symptoms detected.</span>'
            '<span class="ar-pill" dir="rtl">لا توجد مؤشرات خطورة طارئة</span>'
            '</div>'
        )

    render_section_header(
        "Fired Deductive Rules (Forward Chaining & Modus Ponens)",
        "Complete rule activation ledger ordered by Working Memory derivation cycle.",
        "ثالثاً — القواعد المنطقية الصورية التي نفذها محرك الاستدلال عبر الدورات.",
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
elif active_tab == "graph":
    render_section_header(
        "Interactive Clinical Knowledge Graph",
        "4-layer directed subgraph connecting Patient, Symptoms & Risk Factors, Suspected Conditions, and Clinical Protocols.",
        "رسم بياني تفاعلي من أربع طبقات يربط المريض والأعراض وعوامل الخطورة بالتشخيصات والبروتوكولات العلاجية.",
    )
    kg_c1, kg_c2, kg_c3 = st.columns([1, 1, 1])
    with kg_c1:
        show_proto_nodes = st.checkbox("Include Action Protocols (طبقة البروتوكولات)", value=True)
    with kg_c2:
        show_edge_lbls = st.checkbox("Display Edge Labels (مسميات العلاقات)", value=True)
    with kg_c3:
        enable_physics_repulsion = st.checkbox("Auto-Repulsion Physics (تنافر تلقائي)", value=False)
    render_knowledge_graph(
        pat_rec,
        selected_pid,
        trace,
        BASE_DIR,
        show_protocols=show_proto_nodes,
        show_edge_labels=show_edge_lbls,
        enable_physics=enable_physics_repulsion,
    )

# ==================================================================
# TAB 5: LIVE WHAT-IF TRIAGE SIMULATOR
# ==================================================================
elif active_tab == "simulator":
    render_section_header(
        "Live What-If Triage Simulator",
        "Modify presenting symptoms, risk factors, and vital signs to test rule chaining in real time.",
        "محاكي تفاعلي لاختبار حالة مريض جديدة ومتابعة تغيّر تصنيف الطوارئ فورياً.",
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

    render_disposition_banner(sim_trace, top_margin="12px")
