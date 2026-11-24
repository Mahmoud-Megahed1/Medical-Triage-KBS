"""
CSV-to-Neo4j Knowledge Graph Loader
Reads local CSV files in data/ and populates Neo4j via parameterized UNWIND/MERGE Cypher queries.
No manual copying into Neo4j's import/ directory required.
"""

import os
import csv
from typing import List, Dict
from neo4j import GraphDatabase


def _read_csv(data_dir: str, filename: str) -> List[Dict[str, str]]:
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing CSV file: {path}")
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed_neo4j_from_csv(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password123",
    data_dir: str = None,
    clear_existing: bool = False,
) -> Dict[str, int]:
    data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()

    symptoms = _read_csv(data_dir, "symptoms.csv")
    conditions = _read_csv(data_dir, "conditions.csv")
    cond_syms = _read_csv(data_dir, "condition_symptoms.csv")
    risks = _read_csv(data_dir, "risk_factors.csv")
    risk_links = _read_csv(data_dir, "risk_condition_links.csv")
    protocols = _read_csv(data_dir, "action_protocols.csv")
    patients = _read_csv(data_dir, "patients.csv")
    pat_syms = _read_csv(data_dir, "patient_symptoms.csv")
    pat_risks = _read_csv(data_dir, "patient_risk_factors.csv")

    with driver.session() as session:
        if clear_existing:
            session.run("MATCH (n) DETACH DELETE n")

        # Constraints
        for cypher in [
            "CREATE CONSTRAINT unique_patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",
            "CREATE CONSTRAINT unique_symptom_id IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
            "CREATE CONSTRAINT unique_condition_id IF NOT EXISTS FOR (c:MedicalCondition) REQUIRE c.condition_id IS UNIQUE",
            "CREATE CONSTRAINT unique_risk_id IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.risk_id IS UNIQUE",
            "CREATE CONSTRAINT unique_protocol_id IF NOT EXISTS FOR (pr:ClinicalProtocol) REQUIRE pr.protocol_id IS UNIQUE",
        ]:
            session.run(cypher)

        session.run(
            """
            UNWIND $rows AS row
            MERGE (s:Symptom {symptom_id: row.symptom_id})
            SET s.name = row.name,
                s.body_system = row.body_system,
                s.is_red_flag = (row.is_red_flag = 'True'),
                s.severity_weight = toInteger(row.severity_weight)
            """,
            rows=symptoms,
        )

        session.run(
            """
            UNWIND $rows AS row
            MERGE (c:MedicalCondition {condition_id: row.condition_id})
            SET c.name = row.name,
                c.triage_level = row.triage_level,
                c.urgency_label = row.urgency_label,
                c.department = row.department,
                c.max_wait_minutes = toInteger(row.max_wait_minutes),
                c.clinical_summary = row.clinical_summary
            """,
            rows=conditions,
        )

        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:MedicalCondition {condition_id: row.condition_id})
            MATCH (s:Symptom {symptom_id: row.symptom_id})
            MERGE (c)-[rel:INDICATED_BY]->(s)
            SET rel.role = row.role,
                rel.weight = toInteger(row.weight)
            """,
            rows=cond_syms,
        )

        session.run(
            """
            UNWIND $rows AS row
            MERGE (r:RiskFactor {risk_id: row.risk_id})
            SET r.name = row.name,
                r.category = row.category,
                r.escalation_note = row.escalation_note
            """,
            rows=risks,
        )

        session.run(
            """
            UNWIND $rows AS row
            MATCH (r:RiskFactor {risk_id: row.risk_id})
            MATCH (c:MedicalCondition {condition_id: row.condition_id})
            MERGE (r)-[rel:ESCALATES_RISK_OF]->(c)
            SET rel.escalation_points = toInteger(row.escalation_points),
                rel.clinical_rationale = row.clinical_rationale
            """,
            rows=risk_links,
        )

        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:MedicalCondition {condition_id: row.condition_id})
            MERGE (pr:ClinicalProtocol {protocol_id: row.protocol_id})
            SET pr.action_type = row.action_type,
                pr.instruction = row.instruction,
                pr.timeframe = row.timeframe
            MERGE (c)-[:REQUIRES_PROTOCOL]->(pr)
            """,
            rows=protocols,
        )

        session.run(
            """
            UNWIND $rows AS row
            MERGE (p:Patient {patient_id: row.patient_id})
            SET p.name = row.name,
                p.age = toInteger(row.age),
                p.gender = row.gender,
                p.hr_bpm = toInteger(row.hr_bpm),
                p.bp_sys = toInteger(row.bp_sys),
                p.bp_dia = toInteger(row.bp_dia),
                p.spo2_pct = toInteger(row.spo2_pct),
                p.temp_c = toFloat(row.temp_c),
                p.rr_bpm = toInteger(row.rr_bpm),
                p.chief_complaint = row.chief_complaint
            """,
            rows=patients,
        )

        session.run(
            """
            UNWIND $rows AS row
            MATCH (p:Patient {patient_id: row.patient_id})
            MATCH (s:Symptom {symptom_id: row.symptom_id})
            MERGE (p)-[:PRESENTS_SYMPTOM]->(s)
            """,
            rows=pat_syms,
        )

        session.run(
            """
            UNWIND $rows AS row
            MATCH (p:Patient {patient_id: row.patient_id})
            MATCH (r:RiskFactor {risk_id: row.risk_id})
            MERGE (p)-[:HAS_RISK_FACTOR]->(r)
            """,
            rows=pat_risks,
        )

    driver.close()
    return {
        "symptoms": len(symptoms),
        "conditions": len(conditions),
        "risk_factors": len(risks),
        "protocols": len(protocols),
        "patients": len(patients),
    }


if __name__ == "__main__":
    try:
        counts = seed_neo4j_from_csv(clear_existing=True)
        print("Neo4j seeded successfully:", counts)
    except Exception as exc:
        print(f"Could not connect to Neo4j ({exc}). Ensure Neo4j Desktop is running on bolt://localhost:7687.")
