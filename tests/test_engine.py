import unittest
from engine import analyze_incident, load_manual_chunks, retrieve_evidence


class EngineTests(unittest.TestCase):
    def test_normal_case_has_no_flags(self):
        incident = {"readings": {"vibration_mm_s": 3.1, "temperature_c": 68, "pressure_bar": 4.2, "current_a": 11.4}}
        self.assertEqual(sum(x["status"] == "FLAG" for x in analyze_incident(incident)), 0)

    def test_high_vibration_flags(self):
        incident = {"readings": {"vibration_mm_s": 8.2, "temperature_c": 67, "pressure_bar": 4.1, "current_a": 12}}
        checks = analyze_incident(incident)
        flagged = [x["key"] for x in checks if x["status"] == "FLAG"]
        self.assertIn("vibration_mm_s", flagged)

    def test_low_pressure_flags(self):
        incident = {"readings": {"vibration_mm_s": 2.8, "temperature_c": 71, "pressure_bar": 1.2, "current_a": 10.2}}
        checks = analyze_incident(incident)
        flagged = [x["key"] for x in checks if x["status"] == "FLAG"]
        self.assertIn("pressure_bar", flagged)

    def test_manual_chunks_load(self):
        from pathlib import Path
        chunks = load_manual_chunks(Path(__file__).parents[1] / "data" / "sample_manual.txt")
        self.assertGreaterEqual(len(chunks), 4)
        self.assertTrue(any("fictional" in x["text"].lower() for x in chunks))

    def test_evidence_returns_passages(self):
        incident = {"readings": {"vibration_mm_s": 8.2, "temperature_c": 67, "pressure_bar": 4.1, "current_a": 12}}
        checks = analyze_incident(incident)
        chunks = load_manual_chunks(__import__("pathlib").Path(__file__).parents[1] / "data" / "sample_manual.txt")
        evidence = retrieve_evidence(checks, chunks)
        self.assertTrue(evidence)
        self.assertTrue(all("text" in x for x in evidence))


if __name__ == "__main__":
    unittest.main()
