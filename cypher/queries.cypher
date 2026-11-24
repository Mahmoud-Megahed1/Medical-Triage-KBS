// ============================================================================
// Sample Cypher Reasoning Queries for Neo4j Browser Demonstration (IS438)
// ============================================================================

// Q1: Visualize a patient's full clinical subgraph (Symptoms, Risks, Suspected Conditions & Protocols)
MATCH (p:Patient {patient_id: 'P01'})-[:PRESENTS_SYMPTOM]->(s:Symptom)<-[ind:INDICATED_BY]-(c:MedicalCondition)
OPTIONAL MATCH (p)-[:HAS_RISK_FACTOR]->(rf:RiskFactor)-[esc:ESCALATES_RISK_OF]->(c)
OPTIONAL MATCH (c)-[:REQUIRES_PROTOCOL]->(pr:ClinicalProtocol)
RETURN p, s, c, rf, pr;

// Q2: Red-Flag Emergency Detection Query (Find patients presenting any Red-Flag Symptom)
MATCH (p:Patient)-[:PRESENTS_SYMPTOM]->(s:Symptom {is_red_flag: true})
RETURN p.patient_id AS PatientID, p.name AS Name, collect(s.name) AS RedFlagSymptoms;

// Q3: Differential Diagnosis Scoring via Graph Traversal (Symptoms + Risk Escalation)
MATCH (p:Patient {patient_id: 'P01'})-[:PRESENTS_SYMPTOM]->(s:Symptom)<-[ind:INDICATED_BY]-(c:MedicalCondition)
WITH p, c, sum(ind.weight) AS symptom_score, collect(s.name) AS matched_symptoms
OPTIONAL MATCH (p)-[:HAS_RISK_FACTOR]->(rf:RiskFactor)-[esc:ESCALATES_RISK_OF]->(c)
WITH c, symptom_score, matched_symptoms, coalesce(sum(esc.escalation_points), 0) AS risk_bonus, collect(rf.name) AS active_risks
RETURN c.condition_id AS ID,
       c.name AS Condition,
       c.triage_level AS ESI_Tier,
       (symptom_score + risk_bonus) AS TotalEvidenceScore,
       matched_symptoms,
       active_risks
ORDER BY TotalEvidenceScore DESC;
