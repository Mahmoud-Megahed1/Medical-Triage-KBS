"""Reusable Design-System UI Components for Medical Triage KBS."""

import os
import html
import streamlit as st
import streamlit.components.v1 as components

from inference_engine import ESI_METADATA
from ui.i18n_ar import ESI_AR


def esc(val: object) -> str:
    return html.escape(str(val))


def inject_design_system(css_path: str) -> None:
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.html(f"<style>{css}</style>")


def esi_badge(esi: str) -> str:
    cls_map = {
        "ESI-1": "b-esi1",
        "ESI-2": "b-esi2",
        "ESI-3": "b-esi3",
        "ESI-4": "b-esi4",
        "ESI-5": "b-esi5",
    }
    return f'<span class="badge {cls_map.get(esi, "b-neutral")}">{esc(esi)}</span>'


def render_evidence_bar(score: float) -> str:
    pct = max(0, min(100, int(round(score))))
    return (
        f'<div class="ds-ev-wrap">'
        f'<span class="ds-ev-num">{pct}%</span>'
        f'<div class="ds-ev-track"><div class="ds-ev-fill" style="width:{pct}%;"></div></div>'
        f'</div>'
    )


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
    return (
        '<div class="ds-table-wrap">'
        f'<table class="data-table"><thead><tr>{th}</tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table>'
        '</div>'
    )


def render_section_header(title_en: str, desc_en: str, desc_ar: str) -> None:
    st.html(
        '<div class="ds-section-bar">'
        '<div>'
        f'<div class="ds-section-en">{esc(title_en)}</div>'
        f'<div class="ds-section-desc">{desc_en}</div>'
        '</div>'
        f'<div class="ds-section-ar" dir="rtl">{esc(desc_ar)}</div>'
        '</div>'
    )


def render_header() -> None:
    st.html(
        '<div class="ds-header">'
        '<div>'
        '<h1 class="ds-brand-title">Medical Triage &amp; Emergency Priority System</h1>'
        '<div class="ds-brand-sub">Clinical Rule Reasoning &amp; Multi-Hop Knowledge Graph Triage</div>'
        '<div class="ds-header-ar" dir="rtl">نظام الفرز الطبي وتحديد أولوية الطوارئ القائم على شبكة المعرفة والاستدلال المنطقي</div>'
        '</div>'
        '<div><span class="ds-context-pill">IS438 • Clinical Decision Support</span></div>'
        '</div>'
    )


def render_disposition_banner(trace, top_margin: str = "0") -> None:
    banner_palette = {
        "ESI-1": ("#fef2f2", "#fecaca", "#991b1b"),
        "ESI-2": ("#fff7ed", "#fed7aa", "#9a3412"),
        "ESI-3": ("#fffbeb", "#fde68a", "#92400e"),
        "ESI-4": ("#ecfdf5", "#a7f3d0", "#065f46"),
        "ESI-5": ("#eff6ff", "#bfdbfe", "#1e40af"),
    }
    bg, bd, fg = banner_palette.get(trace.triage_level, ("#f8fafc", "#e2e8f0", "#111827"))
    urgent_tag = "URGENT / EMERGENCY CARE REQUIRED" if trace.requires_urgent_care else "STANDARD / OUTPATIENT CARE"
    urgent_ar = (
        "القرار النهائي للحالة — تحتاج تدخل طبي عاجل في الطوارئ"
        if trace.requires_urgent_care
        else "القرار النهائي للحالة — حالة مستقرة مناسبة للكشف العادي"
    )
    dot_html = '<span class="ds-live-dot critical"></span>' if trace.triage_level in ("ESI-1", "ESI-2") else ""
    esi_ar = ESI_AR.get(trace.triage_level, "")

    st.html(
        f'<div class="ds-banner" style="background:{bg};border:1px solid {bd};color:{fg};margin-top:{top_margin};">'
        f'<div class="ds-banner-top">'
        f'<div>'
        f'<div class="ds-banner-title">{dot_html}<span>{esc(trace.urgency_label)} — {esc(urgent_tag)}</span></div>'
        f'<div class="ds-banner-sub">Disposition: <strong>{esc(trace.disposition)}</strong> • Unit: <strong>{esc(trace.recommended_department)}</strong></div>'
        f'</div>'
        f'<div>{esi_badge(trace.triage_level)}</div>'
        f'</div>'
        f'<div class="ds-banner-ar" dir="rtl">{esc(urgent_ar)} ({esc(esi_ar)})</div>'
        f'</div>'
    )


def render_kpi_grid(trace, top_cond_ar: str) -> None:
    esi_color = ESI_METADATA[trace.triage_level]["color"]
    top_cond = trace.suspected_conditions[0] if trace.suspected_conditions else None
    top_name = top_cond["name"] if top_cond else "No Specific Match"
    top_score = f"{top_cond['confidence_score']:.0f}%" if top_cond else "0%"
    rf_count = len(trace.red_flag_alerts) + len(trace.vital_alerts)

    st.html(
        '<div class="ds-kpi-grid">'
        '<div class="ds-kpi-card">'
        '<div class="ds-kpi-top"><span class="ds-kpi-label">Triage Tier</span><span class="ds-kpi-ar" dir="rtl">تصنيف الخطورة</span></div>'
        f'<div class="ds-kpi-value" style="color:{esi_color};">{esc(trace.triage_level)}</div>'
        f'<div class="ds-kpi-sub">Max Wait &lt;= {trace.max_wait_minutes} min</div>'
        '</div>'
        '<div class="ds-kpi-card">'
        '<div class="ds-kpi-top"><span class="ds-kpi-label">Safety Alerts</span><span class="ds-kpi-ar" dir="rtl">إشارات الخطورة</span></div>'
        f'<div class="ds-kpi-value" style="color:{"#dc2626" if rf_count > 0 else "#059669"};">{rf_count}</div>'
        f'<div class="ds-kpi-sub">{len(trace.red_flag_alerts)} symptoms, {len(trace.vital_alerts)} vitals</div>'
        '</div>'
        '<div class="ds-kpi-card">'
        '<div class="ds-kpi-top"><span class="ds-kpi-label">Top Condition</span><span class="ds-kpi-ar" dir="rtl">التشخيص المرجّح</span></div>'
        f'<div class="ds-kpi-value text-fit">{esc(top_name)}</div>'
        f'<div class="ar-note" dir="rtl" style="font-size:11px;color:#64748b;margin-top:4px;">{esc(top_cond_ar)} ({esc(top_score)})</div>'
        '</div>'
        '<div class="ds-kpi-card">'
        '<div class="ds-kpi-top"><span class="ds-kpi-label">Target Unit</span><span class="ds-kpi-ar" dir="rtl">القسم المختص</span></div>'
        f'<div class="ds-kpi-value text-fit" style="color:#2563eb;">{esc(trace.recommended_department)}</div>'
        f'<div class="ds-kpi-sub">{len(trace.protocols)} protocol(s) • {trace.inference_cycles} cycles</div>'
        '</div>'
        '</div>'
    )


def render_sidebar_patient_summary(pat_rec: dict, sym_count: int, risk_count: int, mode: str) -> None:
    st.sidebar.html(
        '<div class="ds-side-panel">'
        f'<div class="ds-kv-row"><span>Patient</span><strong>{esc(pat_rec["name"])}</strong></div>'
        f'<div class="ds-kv-row"><span>Age / Gender</span><strong>{esc(pat_rec["age"])} yrs / {esc(pat_rec["gender"])}</strong></div>'
        f'<div class="ds-kv-row"><span>Symptoms</span><strong>{sym_count} reported</strong></div>'
        f'<div class="ds-kv-row"><span>Risk Factors</span><strong>{risk_count} active</strong></div>'
        '</div>'
    )

    st.sidebar.markdown("#### Vital Signs")
    st.sidebar.html(
        '<div class="ar-note" dir="rtl" style="font-size:11.5px;margin-bottom:4px;">المؤشرات الحيوية المقاسة للحالة</div>'
        '<div class="ds-vitals-grid">'
        f'<div class="ds-vital-cell"><div class="ds-vital-label">Heart Rate (النبض)</div><div class="ds-vital-val">{esc(pat_rec["hr_bpm"])} <span class="ds-vital-unit">bpm</span></div></div>'
        f'<div class="ds-vital-cell"><div class="ds-vital-label">BP (ضغط الدم)</div><div class="ds-vital-val">{esc(pat_rec["bp_sys"])}/{esc(pat_rec["bp_dia"])} <span class="ds-vital-unit">mmHg</span></div></div>'
        f'<div class="ds-vital-cell"><div class="ds-vital-label">SpO2 (الأكسجين)</div><div class="ds-vital-val">{esc(pat_rec["spo2_pct"])}<span class="ds-vital-unit">%</span></div></div>'
        f'<div class="ds-vital-cell"><div class="ds-vital-label">Temp / RR (حرارة / تنفس)</div><div class="ds-vital-val">{esc(pat_rec["temp_c"])} C <span class="ds-vital-unit">| {esc(pat_rec["rr_bpm"])}/m</span></div></div>'
        '</div>'
    )

    st.sidebar.html(
        '<div class="ds-side-panel" style="margin-top:8px;">'
        '<div style="font-size:10.5px;color:#64748b;text-transform:uppercase;font-weight:700;margin-bottom:4px;">Chief Complaint <span class="ar-pill" dir="rtl">الشكوى الرئيسية</span></div>'
        f'<div style="color:#111827;font-size:12.5px;line-height:1.45;">{esc(pat_rec["chief_complaint"])}</div>'
        '</div>'
    )

    st.sidebar.html(
        '<div class="ds-mode-chip">'
        f'<span>ENGINE: {esc(mode)}</span>'
        '<span class="ar-pill" dir="rtl" style="font-size:10px;">وضع المحرك</span>'
        '</div>'
    )


def render_knowledge_graph(
    pat_rec: dict,
    selected_pid: str,
    trace,
    graph_dir: str,
    show_protocols: bool = True,
    show_edge_labels: bool = True,
    enable_physics: bool = False,
) -> None:
    proto_legend = (
        '<span class="legend-item"><span class="legend-box" style="background:#f0f9ff;border:1.5px solid #0284c7;"></span> Protocol <span class="ar-pill" dir="rtl">إجراء علاجي</span></span>'
        if show_protocols
        else ""
    )
    st.html(
        '<div class="graph-legend">'
        '<span class="legend-item"><span class="legend-dot" style="background:#eff6ff;border:2px solid #2563eb;"></span> Patient <span class="ar-pill" dir="rtl">المريض</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#fef2f2;border:2px solid #dc2626;"></span> Red-Flag Symptom <span class="ar-pill" dir="rtl">عرض خطورة</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#ecfdf5;border:2px solid #059669;"></span> Standard Symptom <span class="ar-pill" dir="rtl">عرض عادي</span></span>'
        '<span class="legend-item"><span class="legend-dot" style="background:#fffbeb;border:2px solid #d97706;"></span> Risk Factor <span class="ar-pill" dir="rtl">عامل خطورة</span></span>'
        '<span class="legend-item"><span class="legend-box" style="background:#f5f3ff;border:1.5px solid #6d28d9;"></span> Suspected Condition <span class="ar-pill" dir="rtl">تشخيص محتمل</span></span>'
        f'{proto_legend}'
        '</div>'
    )

    try:
        from pyvis.network import Network

        net = Network(height="580px", width="100%", bgcolor="#fcfdff", font_color="#111827")
        physics_json = (
            """
            "physics": {
              "enabled": true,
              "solver": "repulsion",
              "repulsion": {
                "nodeDistance": 260,
                "centralGravity": 0.08,
                "springLength": 240,
                "springConstant": 0.03,
                "damping": 0.25
              },
              "stabilization": { "enabled": true, "iterations": 120 }
            }
            """
            if enable_physics
            else '"physics": { "enabled": false }'
        )

        net.set_options(f"""
        {{
          "layout": {{
            "improvedLayout": false,
            "hierarchical": {{ "enabled": false }}
          }},
          {physics_json},
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
              "size": 10,
              "x": 0,
              "y": 3
            }},
            "font": {{
              "face": "Plus Jakarta Sans, Segoe UI, sans-serif"
            }}
          }},
          "edges": {{
            "smooth": {{
              "type": "curvedCW",
              "roundness": 0.14
            }},
            "arrows": {{
              "to": {{ "enabled": true, "scaleFactor": 0.65 }}
            }},
            "font": {{
              "size": 10,
              "face": "JetBrains Mono, Consolas, monospace",
              "color": "#475569",
              "background": "#fcfdff",
              "strokeWidth": 0,
              "align": "middle"
            }},
            "selectionWidth": 2.5
          }}
        }}
        """)

        # Compute clean non-overlapping initial (x, y) coordinates so nodes start organized
        # while hierarchical layout is OFF (allowing 360-degree free dragging in all directions!)
        x_patient = -540
        x_layer1 = -190
        x_cond = 200
        x_proto = 580

        def centered_y(idx: int, total: int, step: int = 115) -> int:
            return int((idx - (total - 1) / 2.0) * step)

        # Level 0: Patient Root Node
        p_node = f"pat_{selected_pid}"
        net.add_node(
            p_node,
            label=f"PATIENT • {selected_pid}\n{pat_rec['name']}\n({pat_rec['age']}y • SpO2 {pat_rec['spo2_pct']}%)",
            title=f"Patient: {pat_rec['name']} ({selected_pid}) | HR: {pat_rec['hr_bpm']} bpm | BP: {pat_rec['bp_sys']}/{pat_rec['bp_dia']} | SpO2: {pat_rec['spo2_pct']}%",
            x=x_patient,
            y=0,
            shape="box",
            margin=12,
            shapeProperties={"borderRadius": 10},
            color={"background": "#eff6ff", "border": "#2563eb", "highlight": {"background": "#dbeafe", "border": "#1d4ed8"}},
            font={"color": "#1e3a8a", "size": 12, "bold": True},
        )

        # Level 1: Presenting Symptoms + Risk Factors stacked with generous vertical spacing
        layer1_items = [("SYM", s) for s in trace.presented_symptoms] + [("RISK", rf) for rf in trace.active_risk_factors]
        total_l1 = len(layer1_items)
        for idx, (kind, obj) in enumerate(layer1_items):
            y_pos = centered_y(idx, total_l1, step=110)
            if kind == "SYM":
                s = obj
                s_node = f"sym_{s['symptom_id']}"
                is_rf = s["is_red_flag"]
                bg_c = "#fef2f2" if is_rf else "#ecfdf5"
                bd_c = "#dc2626" if is_rf else "#059669"
                fg_c = "#991b1b" if is_rf else "#065f46"
                tag = "RED FLAG" if is_rf else "SYMPTOM"
                net.add_node(
                    s_node,
                    label=f"{s['symptom_id']} • {tag}\n{s['name']}",
                    title=f"System: {s['body_system']} | Severity Weight: {s['severity_weight']}/5 | Red Flag: {is_rf}",
                    x=x_layer1,
                    y=y_pos,
                    shape="box",
                    margin=9,
                    shapeProperties={"borderRadius": 8},
                    color={"background": bg_c, "border": bd_c, "highlight": {"background": bg_c, "border": bd_c}},
                    font={"color": fg_c, "size": 11, "bold": is_rf},
                )
                net.add_edge(
                    p_node,
                    s_node,
                    label="PRESENTS" if show_edge_labels else "",
                    title="PRESENTS_SYMPTOM",
                    color={"color": bd_c, "highlight": bd_c},
                    width=2 if is_rf else 1.5,
                )
            else:
                rf = obj
                r_node = f"rf_{rf['risk_id']}"
                net.add_node(
                    r_node,
                    label=f"{rf['risk_id']} • RISK\n{rf['name']}",
                    title=f"Category: {rf['category']} | Note: {rf['escalation_note']}",
                    x=x_layer1,
                    y=y_pos,
                    shape="box",
                    margin=9,
                    shapeProperties={"borderRadius": 8},
                    color={"background": "#fffbeb", "border": "#d97706", "highlight": {"background": "#fef3c7", "border": "#b45309"}},
                    font={"color": "#92400e", "size": 11},
                )
                net.add_edge(
                    p_node,
                    r_node,
                    label="HAS_RISK" if show_edge_labels else "",
                    title="HAS_RISK_FACTOR",
                    color={"color": "#d97706", "highlight": "#b45309"},
                    width=1.6,
                    dashes=[5, 4],
                )

        # Level 2: Suspected Medical Conditions (Top 4)
        top_conditions = trace.suspected_conditions[:4]
        for idx, c in enumerate(top_conditions):
            c_node = f"cond_{c['condition_id']}"
            esi_tier = c["triage_level"]
            c_border = "#dc2626" if esi_tier == "ESI-1" else ("#ea580c" if esi_tier == "ESI-2" else "#6d28d9")
            net.add_node(
                c_node,
                label=f"{c['condition_id']} • {esi_tier} ({c['confidence_score']:.0f}%)\n{c['name']}",
                title=f"{c['clinical_summary']} | Department: {c['department']}",
                x=x_cond,
                y=centered_y(idx, len(top_conditions), step=145),
                shape="box",
                margin=11,
                shapeProperties={"borderRadius": 9},
                color={"background": "#f5f3ff", "border": c_border, "highlight": {"background": "#ede9fe", "border": "#5b21b6"}},
                font={"color": "#2e1065", "size": 11.5, "bold": True},
            )
            for s in trace.presented_symptoms:
                if s["name"] in c["matched_symptoms"]:
                    net.add_edge(
                        f"sym_{s['symptom_id']}",
                        c_node,
                        label="INDICATES" if show_edge_labels else "",
                        title="INDICATED_BY",
                        color={"color": "#7c3aed", "highlight": "#5b21b6"},
                        width=1.7,
                    )
            for esc_item in trace.risk_escalations:
                if esc_item["condition_id"] == c["condition_id"]:
                    net.add_edge(
                        f"rf_{esc_item['risk_id']}",
                        c_node,
                        label=f"ESCALATES +{esc_item['points']}" if show_edge_labels else "",
                        title=esc_item["rationale"],
                        color={"color": "#d97706", "highlight": "#b45309"},
                        width=1.7,
                        dashes=[6, 4],
                    )

        # Level 3: Action Protocols & Contraindications
        if show_protocols and trace.protocols:
            cond_name_to_id = {c["name"]: c["condition_id"] for c in top_conditions}
            shown_protos = trace.protocols[:5]
            for idx, p in enumerate(shown_protos):
                p_id_node = f"proto_{p['protocol_id']}"
                is_contra = p["action_type"] == "CONTRAINDICATION"
                p_bg = "#fff1f2" if is_contra else "#f0f9ff"
                p_bd = "#e11d48" if is_contra else "#0284c7"
                p_fg = "#881337" if is_contra else "#0c4a6e"
                short_instr = p["instruction"][:40] + ("..." if len(p["instruction"]) > 40 else "")
                net.add_node(
                    p_id_node,
                    label=f"{p['protocol_id']} • {p['timeframe']}\n{short_instr}",
                    title=f"{p['action_type']}: {p['instruction']}",
                    x=x_proto,
                    y=centered_y(idx, len(shown_protos), step=125),
                    shape="box",
                    margin=9,
                    shapeProperties={"borderRadius": 8},
                    color={"background": p_bg, "border": p_bd, "highlight": {"background": p_bg, "border": p_bd}},
                    font={"color": p_fg, "size": 10.5, "bold": is_contra},
                )
                parent_cid = cond_name_to_id.get(p["condition_name"])
                if parent_cid:
                    net.add_edge(
                        f"cond_{parent_cid}",
                        p_id_node,
                        label="CONTRAINDICATED" if (show_edge_labels and is_contra) else ("PROTOCOL" if show_edge_labels else ""),
                        title=f"REQUIRES_PROTOCOL ({p['action_type']})",
                        color={"color": p_bd, "highlight": p_bd},
                        width=1.6,
                        dashes=[4, 4] if is_contra else False,
                    )

        graph_path = os.path.join(graph_dir, "graph_triage.html")
        net.save_graph(graph_path)
        with open(graph_path, "r", encoding="utf-8") as f:
            gh = f.read()

        toolbar_and_fit = """
<style>
  html, body {
    background-color: #fcfdff !important;
    background-image: radial-gradient(rgba(15, 23, 42, 0.055) 1px, transparent 1px);
    background-size: 20px 20px;
    margin: 0;
    padding: 0;
    overflow: hidden;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }
  .kg-toolbar {
    position: fixed;
    top: 12px;
    right: 12px;
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
  }
  .kg-hint {
    font-size: 11px;
    color: #64748b;
    padding: 0 8px;
    border-right: 1px solid #e2e8f0;
  }
  .kg-btn {
    border: 1px solid transparent;
    background: transparent;
    color: #334155;
    font-size: 11.5px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .kg-btn:hover {
    background: #eff6ff;
    color: #2563eb;
  }
</style>
<div class="kg-toolbar">
  <span class="kg-hint">Drag any node freely in 360°</span>
  <button class="kg-btn" onclick="kgZoom(1.22)">Zoom +</button>
  <button class="kg-btn" onclick="kgZoom(0.82)">Zoom -</button>
  <button class="kg-btn" onclick="kgFit()">Fit View</button>
  <button class="kg-btn" onclick="kgReset()">Reset Layout</button>
</div>
<script>
var initialPositions = null;
function kgCaptureInitial(){
  if(!initialPositions && typeof network!=="undefined" && network!==null){
    initialPositions = network.getPositions();
  }
}
function kgFit(){
  if(typeof network!=="undefined"&&network!==null){
    var el=document.getElementById("mynetwork");
    if(el&&el.clientWidth>50&&el.clientHeight>50){
      kgCaptureInitial();
      network.redraw();
      network.fit({animation:{duration:240,easingFunction:"easeInOutQuad"}});
    }
  }
}
function kgZoom(factor){
  if(typeof network!=="undefined"&&network!==null){
    var scale = network.getScale() * factor;
    network.moveTo({scale: scale, animation:{duration:180,easingFunction:"easeInOutQuad"}});
  }
}
function kgReset(){
  if(typeof network!=="undefined"&&network!==null&&initialPositions){
    Object.keys(initialPositions).forEach(function(id){
      network.moveNode(id, initialPositions[id].x, initialPositions[id].y);
    });
    setTimeout(kgFit, 60);
  }
}
(function(){
  var c=setInterval(function(){
    if(typeof network!=="undefined"&&network!==null){
      clearInterval(c);
      kgFit();
      var el=document.getElementById("mynetwork");
      if(el&&typeof ResizeObserver!=="undefined"){
        new ResizeObserver(function(){ setTimeout(kgFit, 60); }).observe(el);
      }
      if(el&&typeof IntersectionObserver!=="undefined"){
        new IntersectionObserver(function(entries){
          if(entries[0]&&entries[0].isIntersecting){ setTimeout(kgFit, 80); }
        }).observe(el);
      }
      window.addEventListener("resize", function(){ setTimeout(kgFit, 60); });
    }
  }, 80);
})();
</script>
"""
        gh = gh.replace("</body>", toolbar_and_fit + "</body>")
        components.html(gh, height=600)
    except Exception as e:
        st.warning(f"Unable to render interactive graph: {e}")
