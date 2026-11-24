"""
Medical Triage & Emergency Knowledge-Based System (IS438)
True Multi-Cycle Forward-Chaining & Modus Ponens Inference Engine
Dual-Mode Knowledge Base: Live Neo4j Cypher + Local CSV Knowledge Graph Fallback.

Architecture:
1. WorkingMemory: Stores base facts (Patient vitals, symptoms, age, risk factors) and derived facts.
2. ProductionRule: Explicit declarative IF (premise) -> THEN (assert derived facts) rules.
3. Forward-Chaining Agenda Loop: Iteratively evaluates rules against Working Memory across
   multiple cycles until fixed-point saturation (no new facts inferred).
"""

import os
import csv
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Callable, Set


ESI_METADATA: Dict[str, Dict[str, Any]] = {
    "ESI-1": {
        "rank": 1,
        "label": "ESI-1 | Immediate Resuscitation",
        "disposition": "Immediate Life-Saving Intervention (Resuscitation Bay)",
        "color": "#dc2626",
        "max_wait_minutes": 0,
    },
    "ESI-2": {
        "rank": 2,
        "label": "ESI-2 | Emergent Priority",
        "disposition": "Urgent Emergency Care (High-Risk / Red-Flag Alert)",
        "color": "#ea580c",
        "max_wait_minutes": 10,
    },
    "ESI-3": {
        "rank": 3,
        "label": "ESI-3 | Urgent Evaluation",
        "disposition": "Emergency Department Priority Assessment",
        "color": "#d97706",
        "max_wait_minutes": 30,
    },
    "ESI-4": {
        "rank": 4,
        "label": "ESI-4 | Less Urgent Standard",
        "disposition": "ER Fast Track / Urgent Care Assessment",
        "color": "#059669",
        "max_wait_minutes": 60,
    },
    "ESI-5": {
        "rank": 5,
        "label": "ESI-5 | Non-Urgent Outpatient",
        "disposition": "Routine Outpatient Clinic Consultation",
        "color": "#2563eb",
        "max_wait_minutes": 120,
    },
}

Fact = Tuple[Any, ...]


class WorkingMemory:
    """Fact base storing asserted predicates for forward-chaining inference."""

    def __init__(self):
        self._facts: Set[Fact] = set()
        self.history: List[Tuple[int, Fact]] = []

    def assert_fact(self, fact: Fact, cycle: int = 0) -> bool:
        if fact not in self._facts:
            self._facts.add(fact)
            self.history.append((cycle, fact))
            return True
        return False

    def query(self, predicate: str, *pattern: Any) -> List[Fact]:
        """Match facts by predicate name; None acts as wildcard."""
        results = []
        for f in self._facts:
            if f[0] != predicate:
                continue
            if len(pattern) > len(f) - 1:
                continue
            matched = True
            for idx, val in enumerate(pattern):
                if val is not None and f[idx + 1] != val:
                    matched = False
                    break
            if matched:
                results.append(f)
        return sorted(results, key=lambda x: str(x))

    def has(self, fact: Fact) -> bool:
        return fact in self._facts


@dataclass
class ProductionRule:
    """Declarative IF-THEN rule evaluated by Modus Ponens during Forward Chaining."""
    rule_id: str
    evaluate: Callable[[WorkingMemory], List[Tuple[Fact, str, str, str]]]
    # evaluate(wm) returns list of (new_fact, specific_rule_id, formal_logic, consequence)


class TriageTrace:
    """Structured explanation trace recording forward-chaining cycles, derived facts, and protocols."""

    def __init__(self, patient_id: str, patient_name: str, vitals: Dict[str, Any]):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.vitals = vitals
        self.triage_level: str = "ESI-5"
        self.urgency_label: str = ESI_METADATA["ESI-5"]["label"]
        self.disposition: str = ESI_METADATA["ESI-5"]["disposition"]
        self.recommended_department: str = "Outpatient Clinic"
        self.max_wait_minutes: int = 120
        self.requires_urgent_care: bool = False
        self.inference_cycles: int = 0
        self.working_memory_size: int = 0
        self.suspected_conditions: List[Dict[str, Any]] = []
        self.red_flag_alerts: List[Dict[str, str]] = []
        self.vital_alerts: List[Dict[str, str]] = []
        self.risk_escalations: List[Dict[str, Any]] = []
        self.protocols: List[Dict[str, str]] = []
        self.fired_rules: List[Dict[str, str]] = []
        self.audit_summary: List[Dict[str, str]] = []
        self.presented_symptoms: List[Dict[str, Any]] = []
        self.active_risk_factors: List[Dict[str, str]] = []

    def record_rule(self, rule_id: str, formal_logic: str, consequence: str, cycle: int = 1):
        self.fired_rules.append({
            "rule_id": rule_id,
            "cycle": f"Cycle {cycle}",
            "formal_logic": formal_logic,
            "consequence": consequence,
        })

    def add_audit(self, metric: str, finding: str, status: str):
        self.audit_summary.append({
            "metric": metric,
            "finding": finding,
            "status": status,
        })


class MedicalTriageEngine:
    """
    Dual-mode Knowledge-Based System with genuine multi-cycle Forward Chaining & Modus Ponens.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password123",
        data_dir: Optional[str] = None,
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
        )
        self.driver = None
        self.mode = "LOCAL_GRAPH"

        self._load_local_csv_kb()
        test_driver = None
        try:
            from neo4j import GraphDatabase
            test_driver = GraphDatabase.driver(uri, auth=(user, password))
            test_driver.verify_connectivity()
            with test_driver.session() as session:
                count_rec = session.run("MATCH (c:MedicalCondition) RETURN count(c) AS cnt").single()
                if count_rec and count_rec["cnt"] > 0:
                    self.driver = test_driver
                    self.mode = "LIVE_NEO4J"
                else:
                    test_driver.close()
        except Exception:
            if test_driver is not None:
                try:
                    test_driver.close()
                except Exception:
                    pass
            self.driver = None
            self.mode = "LOCAL_GRAPH"

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    @staticmethod
    def _read_csv_rows(path: str) -> List[Dict[str, str]]:
        if not os.path.exists(path):
            return []
        with open(path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _load_local_csv_kb(self):
        self.symptoms: Dict[str, Dict[str, Any]] = {}
        self.conditions: Dict[str, Dict[str, Any]] = {}
        self.condition_symptoms: Dict[str, List[Dict[str, Any]]] = {}
        self.risk_factors: Dict[str, Dict[str, str]] = {}
        self.risk_links: Dict[str, List[Dict[str, Any]]] = {}
        self.protocols_by_cond: Dict[str, List[Dict[str, str]]] = {}
        self.patients: Dict[str, Dict[str, Any]] = {}
        self.patient_symptoms: Dict[str, List[str]] = {}
        self.patient_risks: Dict[str, List[str]] = {}

        for row in self._read_csv_rows(os.path.join(self.data_dir, "symptoms.csv")):
            self.symptoms[row["symptom_id"]] = {
                "symptom_id": row["symptom_id"],
                "name": row["name"],
                "body_system": row["body_system"],
                "is_red_flag": row["is_red_flag"].strip().lower() == "true",
                "severity_weight": int(row["severity_weight"]),
            }

        for row in self._read_csv_rows(os.path.join(self.data_dir, "conditions.csv")):
            self.conditions[row["condition_id"]] = {
                "condition_id": row["condition_id"],
                "name": row["name"],
                "triage_level": row["triage_level"],
                "urgency_label": row["urgency_label"],
                "department": row["department"],
                "max_wait_minutes": int(row["max_wait_minutes"]),
                "clinical_summary": row["clinical_summary"],
            }

        for row in self._read_csv_rows(os.path.join(self.data_dir, "condition_symptoms.csv")):
            cid = row["condition_id"]
            self.condition_symptoms.setdefault(cid, []).append({
                "symptom_id": row["symptom_id"],
                "role": row["role"],
                "weight": int(row["weight"]),
            })

        for row in self._read_csv_rows(os.path.join(self.data_dir, "risk_factors.csv")):
            self.risk_factors[row["risk_id"]] = row

        for row in self._read_csv_rows(os.path.join(self.data_dir, "risk_condition_links.csv")):
            rid = row["risk_id"]
            self.risk_links.setdefault(rid, []).append({
                "condition_id": row["condition_id"],
                "escalation_points": int(row["escalation_points"]),
                "clinical_rationale": row["clinical_rationale"],
            })

        for row in self._read_csv_rows(os.path.join(self.data_dir, "action_protocols.csv")):
            cid = row["condition_id"]
            self.protocols_by_cond.setdefault(cid, []).append(row)

        for row in self._read_csv_rows(os.path.join(self.data_dir, "patients.csv")):
            self.patients[row["patient_id"]] = {
                "patient_id": row["patient_id"],
                "name": row["name"],
                "age": int(row["age"]),
                "gender": row["gender"],
                "hr_bpm": int(row["hr_bpm"]),
                "bp_sys": int(row["bp_sys"]),
                "bp_dia": int(row["bp_dia"]),
                "spo2_pct": int(row["spo2_pct"]),
                "temp_c": float(row["temp_c"]),
                "rr_bpm": int(row["rr_bpm"]),
                "chief_complaint": row["chief_complaint"],
            }

        for row in self._read_csv_rows(os.path.join(self.data_dir, "patient_symptoms.csv")):
            self.patient_symptoms.setdefault(row["patient_id"], []).append(row["symptom_id"])

        for row in self._read_csv_rows(os.path.join(self.data_dir, "patient_risk_factors.csv")):
            self.patient_risks.setdefault(row["patient_id"], []).append(row["risk_id"])

    def get_patients(self) -> Dict[str, Dict[str, Any]]:
        if self.mode == "LIVE_NEO4J" and self.driver:
            with self.driver.session() as session:
                rows = session.run(
                    """
                    MATCH (p:Patient)
                    RETURN p.patient_id AS patient_id, p.name AS name, p.age AS age,
                           p.gender AS gender, p.hr_bpm AS hr_bpm, p.bp_sys AS bp_sys,
                           p.bp_dia AS bp_dia, p.spo2_pct AS spo2_pct, p.temp_c AS temp_c,
                           p.rr_bpm AS rr_bpm, p.chief_complaint AS chief_complaint
                    ORDER BY p.patient_id
                    """
                ).data()
                return {r["patient_id"]: r for r in rows}
        return dict(self.patients)

    def get_all_symptoms(self) -> Dict[str, Dict[str, Any]]:
        if self.mode == "LIVE_NEO4J" and self.driver:
            with self.driver.session() as session:
                rows = session.run(
                    """
                    MATCH (s:Symptom)
                    RETURN s.symptom_id AS symptom_id, s.name AS name,
                           s.body_system AS body_system, s.is_red_flag AS is_red_flag,
                           s.severity_weight AS severity_weight
                    ORDER BY s.symptom_id
                    """
                ).data()
                return {r["symptom_id"]: r for r in rows}
        return dict(self.symptoms)

    def get_all_risk_factors(self) -> Dict[str, Dict[str, str]]:
        if self.mode == "LIVE_NEO4J" and self.driver:
            with self.driver.session() as session:
                rows = session.run(
                    """
                    MATCH (r:RiskFactor)
                    RETURN r.risk_id AS risk_id, r.name AS name,
                           r.category AS category, r.escalation_note AS escalation_note
                    ORDER BY r.risk_id
                    """
                ).data()
                return {r["risk_id"]: r for r in rows}
        return dict(self.risk_factors)

    def get_patient_case(self, patient_id: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
        if self.mode == "LIVE_NEO4J" and self.driver:
            with self.driver.session() as session:
                rec = session.run(
                    """
                    MATCH (p:Patient {patient_id: $pid})
                    OPTIONAL MATCH (p)-[:PRESENTS_SYMPTOM]->(s:Symptom)
                    OPTIONAL MATCH (p)-[:HAS_RISK_FACTOR]->(rf:RiskFactor)
                    RETURN p {.*} AS patient,
                           collect(DISTINCT s.symptom_id) AS symptom_ids,
                           collect(DISTINCT rf.risk_id) AS risk_ids
                    """,
                    pid=patient_id,
                ).single()
                if not rec:
                    raise KeyError(f"Patient ID '{patient_id}' not found in Neo4j Knowledge Graph.")
                return rec["patient"], rec["symptom_ids"], rec["risk_ids"]

        if patient_id not in self.patients:
            raise KeyError(f"Patient ID '{patient_id}' not found in Knowledge Base.")
        return (
            dict(self.patients[patient_id]),
            list(self.patient_symptoms.get(patient_id, [])),
            list(self.patient_risks.get(patient_id, [])),
        )

    def _fetch_graph_reasoning_context(
        self, symptom_ids: List[str], risk_ids: List[str]
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, str]]]]:
        if self.mode == "LIVE_NEO4J" and self.driver:
            with self.driver.session() as session:
                cond_rows = session.run(
                    """
                    MATCH (c:MedicalCondition)-[ind:INDICATED_BY]->(s:Symptom)
                    WHERE s.symptom_id IN $sids
                    WITH DISTINCT c
                    MATCH (c)-[all_ind:INDICATED_BY]->(all_s:Symptom)
                    OPTIONAL MATCH (c)-[:REQUIRES_PROTOCOL]->(pr:ClinicalProtocol)
                    RETURN c {.*} AS cond,
                           collect(DISTINCT {
                               symptom_id: all_s.symptom_id,
                               symptom_name: all_s.name,
                               role: all_ind.role,
                               weight: all_ind.weight
                           }) AS cond_syms,
                           collect(DISTINCT pr {.*}) AS protocols
                    """,
                    sids=symptom_ids,
                ).data()

                conditions_map: Dict[str, Dict[str, Any]] = {}
                cond_syms_map: Dict[str, List[Dict[str, Any]]] = {}
                protocols_map: Dict[str, List[Dict[str, str]]] = {}

                for row in cond_rows:
                    c = row["cond"]
                    cid = c["condition_id"]
                    conditions_map[cid] = c
                    cond_syms_map[cid] = row["cond_syms"]
                    protocols_map[cid] = [p for p in row["protocols"] if p]

                # Include all risk links (so newly derived RF08 in Cycle 1 can trigger Cycle 2 chaining!)
                risk_rows = session.run(
                    """
                    MATCH (rf:RiskFactor)-[esc:ESCALATES_RISK_OF]->(c:MedicalCondition)
                    RETURN rf.risk_id AS risk_id,
                           rf.name AS risk_name,
                           c.condition_id AS condition_id,
                           esc.escalation_points AS escalation_points,
                           esc.clinical_rationale AS clinical_rationale
                    """
                ).data()
                risk_links_map: Dict[str, List[Dict[str, Any]]] = {}
                for rr in risk_rows:
                    risk_links_map.setdefault(rr["risk_id"], []).append(rr)

                return conditions_map, cond_syms_map, risk_links_map, protocols_map

        return self.conditions, self.condition_symptoms, self.risk_links, self.protocols_by_cond

    # ------------------------------------------------------------------
    # Declarative Production Rule Base for Forward Chaining
    # ------------------------------------------------------------------
    def _build_production_rules(
        self,
        all_symptoms: Dict[str, Dict[str, Any]],
        all_risks: Dict[str, Dict[str, str]],
        conditions_map: Dict[str, Dict[str, Any]],
        cond_syms_map: Dict[str, List[Dict[str, Any]]],
    ) -> List[ProductionRule]:

        def r_age_to_rf08(wm: WorkingMemory):
            out = []
            for _, pid, age in wm.query("Age"):
                if age >= 65 and not wm.has(("HasRiskFactor", pid, "RF08")) and "RF08" in all_risks:
                    out.append((
                        ("HasRiskFactor", pid, "RF08"),
                        "AGE-RF08",
                        f"Age({pid}) = {age} >= 65",
                        "Assert HasRiskFactor(RF08: Age >= 65 Years) into Working Memory",
                    ))
            return out

        def r_vital_spo2(wm: WorkingMemory):
            out = []
            for _, pid, val in wm.query("SpO2"):
                if val < 90:
                    out.append((
                        ("VitalAlert", pid, "SpO2", f"SpO2 = {val}%", "< 90%", "ESI-1", "Severe hypoxemia; immediate oxygen and airway resuscitation required"),
                        "VITAL-SPO2-CRIT",
                        f"SpO2({pid}) = {val}% < 90%",
                        "Assert VitalAlert(SpO2, ESI-1 Critical Hypoxemia)",
                    ))
                elif val < 94:
                    out.append((
                        ("VitalAlert", pid, "SpO2", f"SpO2 = {val}%", "90% - 93%", "ESI-2", "Borderline hypoxia requiring urgent oxygenation and respiratory workup"),
                        "VITAL-SPO2-LOW",
                        f"SpO2({pid}) = {val}% < 94%",
                        "Assert VitalAlert(SpO2, ESI-2 Emergent Hypoxia)",
                    ))
            return out

        def r_vital_bp(wm: WorkingMemory):
            out = []
            for _, pid, val in wm.query("SystolicBP"):
                if val < 90:
                    out.append((
                        ("VitalAlert", pid, "BP_LOW", f"Systolic BP = {val} mmHg", "< 90 mmHg", "ESI-1", "Hypotension / distributive or cardiogenic shock risk"),
                        "VITAL-BP-SHOCK",
                        f"SystolicBP({pid}) = {val} < 90",
                        "Assert VitalAlert(SystolicBP, ESI-1 Shock Risk)",
                    ))
                elif val >= 180:
                    out.append((
                        ("VitalAlert", pid, "BP_HIGH", f"Systolic BP = {val} mmHg", ">= 180 mmHg", "ESI-2", "Hypertensive urgency/crisis; evaluate end-organ damage"),
                        "VITAL-BP-HTN",
                        f"SystolicBP({pid}) = {val} >= 180",
                        "Assert VitalAlert(SystolicBP, ESI-2 Hypertensive Crisis)",
                    ))
            return out

        def r_vital_hr(wm: WorkingMemory):
            out = []
            for _, pid, val in wm.query("HeartRate"):
                if val > 130 or val < 45:
                    out.append((
                        ("VitalAlert", pid, "HR", f"Heart Rate = {val} bpm", "> 130 or < 45 bpm", "ESI-2", "Severe tachycardia or bradycardia causing hemodynamic risk"),
                        "VITAL-HR-CRIT",
                        f"HeartRate({pid}) = {val} outside [45, 130]",
                        "Assert VitalAlert(HeartRate, ESI-2 Arrhythmia Risk)",
                    ))
            return out

        def r_vital_sirs(wm: WorkingMemory):
            out = []
            for _, pid, temp in wm.query("TempC"):
                for _, _, hr in wm.query("HeartRate", pid):
                    if temp >= 39.5 and hr >= 100:
                        out.append((
                            ("VitalAlert", pid, "SIRS", f"Temp = {temp:.1f} C + HR = {hr}", "Temp >= 39.5 C & HR >= 100", "ESI-2", "High-grade fever with tachycardia; screen for systemic sepsis"),
                            "VITAL-SIRS",
                            f"TempC({pid}) >= 39.5 ∧ HeartRate({pid}) >= 100",
                            "Assert VitalAlert(SIRS, ESI-2 Sepsis Screen)",
                        ))
            return out

        def r_vital_rr(wm: WorkingMemory):
            out = []
            for _, pid, val in wm.query("RespRate"):
                if val >= 26:
                    out.append((
                        ("VitalAlert", pid, "RR", f"Respiratory Rate = {val} /min", ">= 26 /min", "ESI-2", "Significant tachypnea indicating respiratory or metabolic distress"),
                        "VITAL-RR-HIGH",
                        f"RespRate({pid}) = {val} >= 26",
                        "Assert VitalAlert(RespRate, ESI-2 Tachypnea)",
                    ))
            return out

        def r_chain_vital_to_esi(wm: WorkingMemory):
            """Chained Rule: VitalAlert(pid, ..., tier, ...) -> RequireMinESI(pid, tier)"""
            out = []
            for _, pid, param, _, _, tier, _ in wm.query("VitalAlert"):
                out.append((
                    ("RequireMinESI", pid, tier, f"VitalAlert:{param}"),
                    f"CHAIN-VITAL-{param}",
                    f"VitalAlert({pid}, {param}) -> RequireMinESI({pid}, {tier})",
                    f"Escalate patient minimum urgency floor to {tier}",
                ))
            return out

        def r_mp_red_flag_symptom(wm: WorkingMemory):
            """Modus Ponens: PresentsSymptom(p, s) ∧ IsRedFlag(s) -> RedFlagDetected(p, s)"""
            out = []
            for _, pid, sid in wm.query("PresentsSymptom"):
                if wm.has(("IsRedFlag", sid)):
                    sname = all_symptoms[sid]["name"]
                    out.append((
                        ("RedFlagDetected", pid, sid),
                        f"MP-RED-{sid}",
                        f"PresentsSymptom({pid}, {sid}) ∧ IsRedFlag({sid})",
                        f"Derive RedFlagDetected({sname}) -> Escalate triage & block outpatient discharge",
                    ))
            return out

        def r_chain_red_flag_to_block_and_esi(wm: WorkingMemory):
            """Chained Rule: RedFlagDetected(p, s) -> BlockOutpatient(p) & RequireMinESI(p, ESI-2)"""
            out = []
            for _, pid, sid in wm.query("RedFlagDetected"):
                out.append((
                    ("BlockOutpatient", pid),
                    f"CHAIN-BLK-{sid}",
                    f"RedFlagDetected({pid}, {sid})",
                    "Assert BlockOutpatient & RequireMinESI(ESI-2)",
                ))
                out.append((
                    ("RequireMinESI", pid, "ESI-2", f"RedFlag:{sid}"),
                    f"CHAIN-ESI-{sid}",
                    f"RedFlagDetected({pid}, {sid})",
                    "Escalate minimum triage tier to ESI-2",
                ))
            return out

        def r_mp_candidate_condition(wm: WorkingMemory):
            """Modus Ponens: PresentsSymptom(p, s) ∧ Indicates(c, s) -> CandidateCondition(p, c)"""
            out = []
            for _, pid, sid in wm.query("PresentsSymptom"):
                for _, cid, _s, _role, _w in wm.query("Indicates", None, sid):
                    cname = conditions_map[cid]["name"]
                    out.append((
                        ("CandidateCondition", pid, cid),
                        f"MP-COND-MATCH-{cid}",
                        f"PresentsSymptom({pid}, {sid}) ∧ Indicates({cid}, {sid})",
                        f"Activate hypothesis CandidateCondition({cname}) in Working Memory",
                    ))
            return out

        def r_chain_risk_amplification(wm: WorkingMemory):
            """Chained Rule: CandidateCondition(p, c) ∧ HasRiskFactor(p, rf) ∧ Escalates(rf, c, pts) -> RiskAmplified(p, c, rf, pts)"""
            out = []
            for _, pid, cid in wm.query("CandidateCondition"):
                for _, _, rid in wm.query("HasRiskFactor", pid):
                    for _, _, _, pts, rationale in wm.query("Escalates", rid, cid):
                        cname = conditions_map[cid]["name"]
                        rname = all_risks.get(rid, {}).get("name", rid)
                        out.append((
                            ("RiskAmplified", pid, cid, rid, pts, rationale),
                            f"RISK-{rid}-{cid}",
                            f"CandidateCondition({pid}, {cid}) ∧ HasRiskFactor({pid}, {rid}) ∧ Escalates({rid}, {cid})",
                            f"Amplify {cname} likelihood by +{pts} pts due to {rname}",
                        ))
            return out

        def r_chain_score_condition(wm: WorkingMemory):
            """Chained Rule: Aggregates CandidateCondition + matched weights + RiskAmplified -> ScoredCondition"""
            out = []
            for _, pid, cid in wm.query("CandidateCondition"):
                # Wait until AGE-RF08 and RiskAmplified have settled for this patient/condition
                ages = wm.query("Age", pid)
                if ages and ages[0][2] >= 65 and "RF08" in all_risks and not wm.has(("HasRiskFactor", pid, "RF08")):
                    continue
                pending_risk = False
                for _, _, rid in wm.query("HasRiskFactor", pid):
                    if wm.query("Escalates", rid, cid) and not wm.query("RiskAmplified", pid, cid, rid):
                        pending_risk = True
                        break
                if pending_risk:
                    continue

                req_syms = cond_syms_map.get(cid, [])
                if not req_syms:
                    continue
                total_weight = sum(x["weight"] for x in req_syms)
                matched_weight = 0
                has_rf_trigger = False
                for item in req_syms:
                    if wm.has(("PresentsSymptom", pid, item["symptom_id"])):
                        matched_weight += item["weight"]
                        if item["role"] == "RED_FLAG_TRIGGER":
                            has_rf_trigger = True
                base_pct = (matched_weight / max(total_weight, 1)) * 100.0
                bonus = sum(f[4] for f in wm.query("RiskAmplified", pid, cid))
                total_score = round(min(100.0, base_pct + bonus), 1)
                cond_esi = conditions_map[cid]["triage_level"]
                out.append((
                    ("ScoredCondition", pid, cid, round(base_pct, 1), bonus, total_score, has_rf_trigger, cond_esi),
                    f"SCORE-{cid}",
                    f"CandidateCondition({pid}, {cid}) ∧ BaseEvidence={base_pct:.0f}% ∧ RiskBonus=+{bonus}",
                    f"Derive ScoredCondition({conditions_map[cid]['name']} = {total_score:.0f}%, {cond_esi})",
                ))
            return out

        def r_chain_condition_to_esi(wm: WorkingMemory):
            """Chained Rule: ScoredCondition with score >= 45% or red-flag trigger -> RequireMinESI"""
            out = []
            for _, pid, cid, _base, _bonus, score, has_rf, tier in wm.query("ScoredCondition"):
                if score >= 45.0 or has_rf:
                    out.append((
                        ("RequireMinESI", pid, tier, f"Condition:{cid}"),
                        f"MP-COND-{cid}",
                        f"ScoredCondition({pid}, {cid}, {score:.0f}%) ∧ StrongClinicalEvidence",
                        f"Suspect {conditions_map[cid]['name']} [{tier}] -> RequireMinESI({tier})",
                    ))
            return out

        return [
            ProductionRule("AGE-RF08", r_age_to_rf08),
            ProductionRule("VITAL-SPO2", r_vital_spo2),
            ProductionRule("VITAL-BP", r_vital_bp),
            ProductionRule("VITAL-HR", r_vital_hr),
            ProductionRule("VITAL-SIRS", r_vital_sirs),
            ProductionRule("VITAL-RR", r_vital_rr),
            ProductionRule("CHAIN-VITAL-ESI", r_chain_vital_to_esi),
            ProductionRule("MP-RED-SYM", r_mp_red_flag_symptom),
            ProductionRule("CHAIN-RED-ESI", r_chain_red_flag_to_block_and_esi),
            ProductionRule("MP-COND-MATCH", r_mp_candidate_condition),
            ProductionRule("CHAIN-RISK-AMP", r_chain_risk_amplification),
            ProductionRule("CHAIN-SCORE", r_chain_score_condition),
            ProductionRule("CHAIN-COND-ESI", r_chain_condition_to_esi),
        ]

    # ------------------------------------------------------------------
    # Evaluation Entry Points
    # ------------------------------------------------------------------
    def evaluate_patient(self, patient_id: str) -> TriageTrace:
        patient, symptom_ids, risk_ids = self.get_patient_case(patient_id)
        return self.evaluate_custom_case(
            patient_id=patient["patient_id"],
            patient_name=patient["name"],
            age=int(patient["age"]),
            vitals={
                "hr_bpm": int(patient["hr_bpm"]),
                "bp_sys": int(patient["bp_sys"]),
                "bp_dia": int(patient["bp_dia"]),
                "spo2_pct": int(patient["spo2_pct"]),
                "temp_c": float(patient["temp_c"]),
                "rr_bpm": int(patient["rr_bpm"]),
            },
            symptom_ids=symptom_ids,
            risk_ids=risk_ids,
        )

    def evaluate_custom_case(
        self,
        patient_id: str,
        patient_name: str,
        age: int,
        vitals: Dict[str, Any],
        symptom_ids: List[str],
        risk_ids: List[str],
    ) -> TriageTrace:
        trace = TriageTrace(patient_id, patient_name, vitals)

        all_symptoms = self.get_all_symptoms()
        all_risks = self.get_all_risk_factors()
        effective_symptoms = [sid for sid in dict.fromkeys(symptom_ids) if sid in all_symptoms]
        effective_risks = [rid for rid in dict.fromkeys(risk_ids) if rid in all_risks]

        conditions_map, cond_syms_map, risk_links_map, protocols_map = (
            self._fetch_graph_reasoning_context(effective_symptoms, effective_risks)
        )

        # 1. Seed Working Memory with Base Facts (Cycle 0)
        wm = WorkingMemory()
        wm.assert_fact(("Age", patient_id, int(age)), cycle=0)
        wm.assert_fact(("SpO2", patient_id, int(vitals.get("spo2_pct", 98))), cycle=0)
        wm.assert_fact(("SystolicBP", patient_id, int(vitals.get("bp_sys", 120))), cycle=0)
        wm.assert_fact(("HeartRate", patient_id, int(vitals.get("hr_bpm", 80))), cycle=0)
        wm.assert_fact(("TempC", patient_id, float(vitals.get("temp_c", 37.0))), cycle=0)
        wm.assert_fact(("RespRate", patient_id, int(vitals.get("rr_bpm", 16))), cycle=0)

        for sid in effective_symptoms:
            wm.assert_fact(("PresentsSymptom", patient_id, sid), cycle=0)
            if all_symptoms[sid]["is_red_flag"]:
                wm.assert_fact(("IsRedFlag", sid), cycle=0)

        for rid in effective_risks:
            wm.assert_fact(("HasRiskFactor", patient_id, rid), cycle=0)

        # Assert KB Graph Facts into Working Memory
        for cid, sym_list in cond_syms_map.items():
            for item in sym_list:
                wm.assert_fact(("Indicates", cid, item["symptom_id"], item["role"], item["weight"]), cycle=0)

        for rid, links in risk_links_map.items():
            for link in links:
                wm.assert_fact(("Escalates", rid, link["condition_id"], link["escalation_points"], link["clinical_rationale"]), cycle=0)

        # 2. Run Multi-Cycle Forward-Chaining Agenda until Fixed-Point Saturation
        rules = self._build_production_rules(all_symptoms, all_risks, conditions_map, cond_syms_map)
        fired_rule_signatures: Set[Tuple[str, Fact]] = set()
        cycle = 0

        while True:
            cycle += 1
            pending_derivations = []
            for rule in rules:
                pending_derivations.extend(rule.evaluate(wm))

            new_assertions_in_cycle = 0
            for new_fact, specific_id, logic, consequence in pending_derivations:
                sig = (specific_id, new_fact)
                if sig not in fired_rule_signatures and wm.assert_fact(new_fact, cycle=cycle):
                    fired_rule_signatures.add(sig)
                    new_assertions_in_cycle += 1
                    trace.record_rule(specific_id, logic, consequence, cycle=cycle)
            if new_assertions_in_cycle == 0 or cycle >= 10:
                # Saturated (fixed point reached)
                trace.inference_cycles = cycle - 1
                break

        trace.working_memory_size = len(wm._facts)

        # 3. Project Derived Facts from Working Memory into TriageTrace
        trace.presented_symptoms = [all_symptoms[sid] for sid in effective_symptoms]
        inferred_risks = [f[2] for f in wm.query("HasRiskFactor", patient_id)]
        trace.active_risk_factors = [all_risks[rid] for rid in inferred_risks if rid in all_risks]

        for _, _, _param, param_str, thresh, sev_tag, meaning in wm.query("VitalAlert", patient_id):
            trace.vital_alerts.append({
                "parameter": param_str,
                "threshold": thresh,
                "severity": f"{sev_tag} ALERT",
                "meaning": meaning,
            })

        for _, _, sid in wm.query("RedFlagDetected", patient_id):
            s_info = all_symptoms[sid]
            trace.red_flag_alerts.append({
                "symptom_id": sid,
                "symptom_name": s_info["name"],
                "body_system": s_info["body_system"],
                "action": "Outpatient clinic blocked; immediate emergency triage required",
            })

        for _, _, cid, rid, pts, rationale in wm.query("RiskAmplified", patient_id):
            trace.risk_escalations.append({
                "risk_id": rid,
                "risk_name": all_risks.get(rid, {}).get("name", rid),
                "condition_id": cid,
                "condition_name": conditions_map[cid]["name"],
                "points": pts,
                "rationale": rationale,
            })

        sym_set = set(effective_symptoms)
        scored_conditions: List[Dict[str, Any]] = []
        for _, _, cid, base_pct, bonus, total_score, has_rf, cond_esi in wm.query("ScoredCondition", patient_id):
            cond = conditions_map[cid]
            req_syms = cond_syms_map.get(cid, [])
            matched_names = []
            missing_primary = []
            for item in req_syms:
                sname = item.get("symptom_name") or all_symptoms.get(item["symptom_id"], {}).get("name", item["symptom_id"])
                if item["symptom_id"] in sym_set:
                    matched_names.append(sname)
                elif item["role"] in ("RED_FLAG_TRIGGER", "PRIMARY_INDICATOR"):
                    missing_primary.append(sname)
            risk_notes = [
                f"{all_risks.get(f[3], {}).get('name', f[3])} (+{f[4]})"
                for f in wm.query("RiskAmplified", patient_id, cid)
            ]
            scored_conditions.append({
                "condition_id": cid,
                "name": cond["name"],
                "triage_level": cond_esi,
                "urgency_label": cond["urgency_label"],
                "department": cond["department"],
                "max_wait_minutes": cond["max_wait_minutes"],
                "clinical_summary": cond["clinical_summary"],
                "base_match_pct": base_pct,
                "risk_bonus": bonus,
                "confidence_score": total_score,
                "matched_symptoms": matched_names,
                "missing_primary": missing_primary,
                "risk_notes": risk_notes,
                "has_red_flag_match": has_rf,
            })

        scored_conditions.sort(
            key=lambda x: (x["confidence_score"], -ESI_METADATA[x["triage_level"]]["rank"]),
            reverse=True,
        )
        trace.suspected_conditions = scored_conditions

        # Determine final ESI from all RequireMinESI facts derived in Working Memory
        best_esi = "ESI-5"
        best_rank = 5
        for _, _, tier, _src in wm.query("RequireMinESI", patient_id):
            r = ESI_METADATA[tier]["rank"]
            if r < best_rank:
                best_rank = r
                best_esi = tier

        strong_matches = [c for c in scored_conditions if c["confidence_score"] >= 45.0 or c["has_red_flag_match"]]
        if strong_matches:
            trace.recommended_department = strong_matches[0]["department"]
        elif scored_conditions:
            top_cond = scored_conditions[0]
            if ESI_METADATA[top_cond["triage_level"]]["rank"] < best_rank:
                best_esi = top_cond["triage_level"]
                best_rank = ESI_METADATA[best_esi]["rank"]
            trace.recommended_department = top_cond["department"]

        meta = ESI_METADATA[best_esi]
        trace.triage_level = best_esi
        trace.urgency_label = meta["label"]
        trace.disposition = meta["disposition"]
        trace.max_wait_minutes = meta["max_wait_minutes"]
        trace.requires_urgent_care = meta["rank"] <= 3

        seen_proto_ids = set()
        for c in (strong_matches[:2] if strong_matches else scored_conditions[:1]):
            for p in protocols_map.get(c["condition_id"], []):
                pid_p = p["protocol_id"]
                if pid_p not in seen_proto_ids:
                    seen_proto_ids.add(pid_p)
                    trace.protocols.append({
                        "protocol_id": pid_p,
                        "condition_name": c["name"],
                        "action_type": p["action_type"],
                        "instruction": p["instruction"],
                        "timeframe": p["timeframe"],
                    })

        # Populate Executive Audit Summary
        if trace.requires_urgent_care:
            trace.add_audit(
                "Triage Decision",
                f"URGENT / EMERGENCY CARE REQUIRED ({trace.urgency_label}) after {trace.inference_cycles} forward-chaining cycles.",
                best_esi,
            )
        else:
            trace.add_audit(
                "Triage Decision",
                f"No life-threatening red flags detected ({trace.urgency_label}) across {trace.inference_cycles} forward-chaining cycles.",
                best_esi,
            )

        if trace.red_flag_alerts:
            rf_names = ", ".join(r["symptom_name"] for r in trace.red_flag_alerts)
            trace.add_audit(
                "Red-Flag Symptoms",
                f"Modus Ponens derived RedFlagDetected for {len(trace.red_flag_alerts)} symptom(s): {rf_names}. Outpatient discharge blocked.",
                "RED_FLAG",
            )
        else:
            trace.add_audit("Red-Flag Symptoms", "Zero red-flag emergency symptoms reported.", "CLEAR")

        if trace.vital_alerts:
            v_names = "; ".join(v["parameter"] for v in trace.vital_alerts)
            trace.add_audit("Vital Signs Status", f"Physiological instability derived ({v_names}).", "VITAL_ALERT")
        else:
            trace.add_audit("Vital Signs Status", "All vital signs within stable triage thresholds.", "STABLE")

        if scored_conditions:
            top = scored_conditions[0]
            trace.add_audit(
                "Primary Differential",
                f"Top matched condition: {top['name']} ({top['confidence_score']:.0f}% evidence) -> Route to {trace.recommended_department}.",
                top["triage_level"],
            )

        return trace
