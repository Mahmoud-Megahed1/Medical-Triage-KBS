// ============================================================================
// Medical Triage & Emergency Knowledge Graph Schema (IS438)
// Neo4j Constraints, Indexes & CSV Import Pipeline
// Course: New Trends in Information Systems (IS438) - Damietta University
// Supervisor: Dr. Aya Gamal | TA: Eng. Amal
// ============================================================================

// 1. Constraints & Indexes
CREATE CONSTRAINT unique_patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT unique_symptom_id IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE;
CREATE CONSTRAINT unique_condition_id IF NOT EXISTS FOR (c:MedicalCondition) REQUIRE c.condition_id IS UNIQUE;
CREATE CONSTRAINT unique_risk_id IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.risk_id IS UNIQUE;
CREATE CONSTRAINT unique_protocol_id IF NOT EXISTS FOR (pr:ClinicalProtocol) REQUIRE pr.protocol_id IS UNIQUE;

CREATE INDEX idx_symptom_red_flag IF NOT EXISTS FOR (s:Symptom) ON (s.is_red_flag);
CREATE INDEX idx_condition_esi IF NOT EXISTS FOR (c:MedicalCondition) ON (c.triage_level);

// 2. Load Symptoms
LOAD CSV WITH HEADERS FROM 'file:///symptoms.csv' AS row
MERGE (s:Symptom {symptom_id: row.symptom_id})
SET s.name = row.name,
    s.body_system = row.body_system,
    s.is_red_flag = (row.is_red_flag = 'True'),
    s.severity_weight = toInteger(row.severity_weight);

// 3. Load Medical Conditions
LOAD CSV WITH HEADERS FROM 'file:///conditions.csv' AS row
MERGE (c:MedicalCondition {condition_id: row.condition_id})
SET c.name = row.name,
    c.triage_level = row.triage_level,
    c.urgency_label = row.urgency_label,
    c.department = row.department,
    c.max_wait_minutes = toInteger(row.max_wait_minutes),
    c.clinical_summary = row.clinical_summary;

// 4. Load Condition -> Symptom Indications
LOAD CSV WITH HEADERS FROM 'file:///condition_symptoms.csv' AS row
MATCH (c:MedicalCondition {condition_id: row.condition_id})
MATCH (s:Symptom {symptom_id: row.symptom_id})
MERGE (c)-[rel:INDICATED_BY]->(s)
SET rel.role = row.role,
    rel.weight = toInteger(row.weight);

// 5. Load Risk Factors
LOAD CSV WITH HEADERS FROM 'file:///risk_factors.csv' AS row
MERGE (r:RiskFactor {risk_id: row.risk_id})
SET r.name = row.name,
    r.category = row.category,
    r.escalation_note = row.escalation_note;

// 6. Load Risk Factor -> Condition Escalations
LOAD CSV WITH HEADERS FROM 'file:///risk_condition_links.csv' AS row
MATCH (r:RiskFactor {risk_id: row.risk_id})
MATCH (c:MedicalCondition {condition_id: row.condition_id})
MERGE (r)-[rel:ESCALATES_RISK_OF]->(c)
SET rel.escalation_points = toInteger(row.escalation_points),
    rel.clinical_rationale = row.clinical_rationale;

// 7. Load Action Protocols & Contraindications
LOAD CSV WITH HEADERS FROM 'file:///action_protocols.csv' AS row
MATCH (c:MedicalCondition {condition_id: row.condition_id})
MERGE (pr:ClinicalProtocol {protocol_id: row.protocol_id})
SET pr.action_type = row.action_type,
    pr.instruction = row.instruction,
    pr.timeframe = row.timeframe
MERGE (c)-[:REQUIRES_PROTOCOL]->(pr);

// 8. Load Patients
LOAD CSV WITH HEADERS FROM 'file:///patients.csv' AS row
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
    p.chief_complaint = row.chief_complaint;

// 9. Load Patient -> Symptom Relationships
LOAD CSV WITH HEADERS FROM 'file:///patient_symptoms.csv' AS row
MATCH (p:Patient {patient_id: row.patient_id})
MATCH (s:Symptom {symptom_id: row.symptom_id})
MERGE (p)-[:PRESENTS_SYMPTOM]->(s);

// 10. Load Patient -> Risk Factor Relationships
LOAD CSV WITH HEADERS FROM 'file:///patient_risk_factors.csv' AS row
MATCH (p:Patient {patient_id: row.patient_id})
MATCH (r:RiskFactor {risk_id: row.risk_id})
MERGE (p)-[:HAS_RISK_FACTOR]->(r);
