import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from inference_engine import MedicalTriageEngine


class TestMedicalTriageEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = MedicalTriageEngine(uri="bolt://localhost:7687", user="neo4j", password="password123")

    def test_p01_cardiac_emergency_esi1(self):
        trace = self.engine.evaluate_patient("P01")
        self.assertEqual(trace.triage_level, "ESI-1")
        self.assertTrue(trace.requires_urgent_care)
        self.assertGreater(len(trace.red_flag_alerts), 0)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND01")
        self.assertGreater(len(trace.risk_escalations), 0)

    def test_p02_mild_viral_uri_esi5(self):
        trace = self.engine.evaluate_patient("P02")
        self.assertEqual(trace.triage_level, "ESI-5")
        self.assertFalse(trace.requires_urgent_care)
        self.assertEqual(len(trace.red_flag_alerts), 0)
        self.assertEqual(len(trace.vital_alerts), 0)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND13")

    def test_p03_sepsis_shock_hypoxia_esi1(self):
        trace = self.engine.evaluate_patient("P03")
        self.assertEqual(trace.triage_level, "ESI-1")
        self.assertTrue(trace.requires_urgent_care)
        # Verify SpO2 < 90 and BP < 90 vital alerts fired
        rule_ids = {r["rule_id"] for r in trace.fired_rules}
        self.assertIn("VITAL-SPO2-CRIT", rule_ids)
        self.assertIn("VITAL-BP-SHOCK", rule_ids)
        self.assertIn("RISK-RF08-COND05", rule_ids)

    def test_age_risk_factor_auto_inferred(self):
        trace = self.engine.evaluate_custom_case(
            patient_id="CUSTOM-AGE",
            patient_name="Elderly Patient",
            age=72,
            vitals={"hr_bpm": 88, "bp_sys": 125, "bp_dia": 78, "spo2_pct": 97, "temp_c": 37.8, "rr_bpm": 18},
            symptom_ids=["SYM13", "SYM09"],
            risk_ids=[],
        )
        rule_ids = {r["rule_id"] for r in trace.fired_rules}
        self.assertIn("AGE-RF08", rule_ids)

    def test_p04_anaphylaxis_airway_esi1(self):
        trace = self.engine.evaluate_patient("P04")
        self.assertEqual(trace.triage_level, "ESI-1")
        self.assertTrue(trace.requires_urgent_care)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND03")

    def test_p05_appendicitis_esi3(self):
        trace = self.engine.evaluate_patient("P05")
        self.assertEqual(trace.triage_level, "ESI-3")
        self.assertTrue(trace.requires_urgent_care)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND09")

    def test_p07_severe_asthma_esi2(self):
        trace = self.engine.evaluate_patient("P07")
        self.assertEqual(trace.triage_level, "ESI-2")
        self.assertTrue(trace.requires_urgent_care)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND08")

    def test_p06_migraine_esi4(self):
        trace = self.engine.evaluate_patient("P06")
        self.assertEqual(trace.triage_level, "ESI-4")
        self.assertFalse(trace.requires_urgent_care)
        self.assertEqual(trace.suspected_conditions[0]["condition_id"], "COND12")

    def test_vital_sign_escalation_overrides_mild_symptoms(self):
        trace = self.engine.evaluate_custom_case(
            patient_id="CUSTOM01",
            patient_name="Test Patient",
            age=30,
            vitals={"hr_bpm": 85, "bp_sys": 120, "bp_dia": 80, "spo2_pct": 85, "temp_c": 37.0, "rr_bpm": 20},
            symptom_ids=["SYM15"],
            risk_ids=[],
        )
        self.assertEqual(trace.triage_level, "ESI-1")
        self.assertTrue(trace.requires_urgent_care)

    def test_missing_patient_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.evaluate_patient("P999")

    def test_forward_chaining_multi_cycle_saturation(self):
        trace = self.engine.evaluate_patient("P01")
        self.assertGreaterEqual(trace.inference_cycles, 3)
        cycles_seen = {r.get("cycle") for r in trace.fired_rules}
        self.assertIn("Cycle 1", cycles_seen)
        self.assertIn("Cycle 2", cycles_seen)
        self.assertIn("Cycle 3", cycles_seen)
        self.assertGreater(trace.working_memory_size, 10)


if __name__ == "__main__":
    unittest.main()
