import unittest
import json
from tools.space_calculator import (
    calculate_distance,
    calculate_gravity,
    calculate_travel_time
)
from tools.return_type import ToolResult

class TestSpaceCalculatorHidden(unittest.TestCase):
    def setUp(self):
        # Load test cases from eval_calculator.jsonl
        self.test_cases = []
        with open('objects/datasets/eval_calculator.jsonl', 'r') as f:
            for line in f:
                if line.strip():
                    self.test_cases.append(json.loads(line))

    def test_distance_calculations(self):
        # Test all distance calculation cases
        for case in self.test_cases:
            if "distance" in case["answer"]:
                # Extract coordinates from the question
                # This is a simplified version - in practice, you'd need to parse the question text
                # to extract the actual coordinates
                coords = self._extract_coordinates(case["question"])
                if coords:
                    result = calculate_distance(
                        current_coordinates=coords["current"],
                        object_coordinates=coords["object"],
                        unit=case["answer"]["unit"]
                    )
                    self.assertTrue(result.success)
                    self.assertAlmostEqual(
                        result.data["distance"],
                        case["answer"]["distance"],
                        places=4
                    )
                    self.assertEqual(result.data["unit"], case["answer"]["unit"])
                    self.assertAlmostEqual(
                        result.data["vector"]["x"],
                        case["answer"]["vector"]["x"],
                        places=4
                    )
                    self.assertAlmostEqual(
                        result.data["vector"]["y"],
                        case["answer"]["vector"]["y"],
                        places=4
                    )
                    self.assertAlmostEqual(
                        result.data["vector"]["z"],
                        case["answer"]["vector"]["z"],
                        places=4
                    )

    def test_gravity_calculations(self):
        # Test all gravity calculation cases
        for case in self.test_cases:
            if "force_newtons" in case["answer"]:
                # Extract masses and distance from the question
                # This is a simplified version - in practice, you'd need to parse the question text
                # to extract the actual values
                values = self._extract_gravity_values(case["question"])
                if values:
                    result = calculate_gravity(
                        spacecraft_mass=values["spacecraft_mass"],
                        object_mass=values["object_mass"],
                        distance=values["distance"]
                    )
                    self.assertTrue(result.success)
                    self.assertAlmostEqual(
                        result.data["force_newtons"],
                        case["answer"]["force_newtons"],
                        places=4
                    )
                    self.assertEqual(
                        result.data["spacecraft_mass_kg"],
                        case["answer"]["spacecraft_mass_kg"]
                    )
                    self.assertEqual(
                        result.data["object_mass_kg"],
                        case["answer"]["object_mass_kg"]
                    )
                    self.assertEqual(
                        result.data["distance_m"],
                        case["answer"]["distance_m"]
                    )

    def _extract_coordinates(self, question):
        """Extract coordinates from the question text."""
        try:
            # Find coordinates in the format (x:value, y:value, z:value)
            import re
            
            # Pattern for coordinates like (x:100, y:250, z:-50)
            coord_pattern = r'\(x:([-\d.e+]+),\s*y:([-\d.e+]+),\s*z:([-\d.e+]+)\)'
            coords = re.findall(coord_pattern, question)
            
            if len(coords) >= 2:
                # Convert string values to float, handling scientific notation
                current = {
                    "x": float(coords[0][0]),
                    "y": float(coords[0][1]),
                    "z": float(coords[0][2])
                }
                object_coords = {
                    "x": float(coords[1][0]),
                    "y": float(coords[1][1]),
                    "z": float(coords[1][2])
                }
                return {
                    "current": current,
                    "object": object_coords
                }
        except Exception as e:
            print(f"Error extracting coordinates: {str(e)}")
        return None

    def _extract_gravity_values(self, question):
        """Extract mass and distance values from the question text."""
        try:
            import re
            
            # Pattern for mass values like "mass of 1200 kg" or "mass of $1.898 \times 10^{27}$ kg"
            mass_pattern = r'mass of (?:\\?\$)?([\d.e+]+)(?:\s*\\?\times\s*10\^\{?(\d+)\}?)?\s*kg'
            masses = re.findall(mass_pattern, question)
            
            # Pattern for distance values like "distance of 700,000,000 meters" or "distance of $1.496 \times 10^{11}$ meters"
            distance_pattern = r'distance of (?:\\?\$)?([\d.e+]+)(?:\s*\\?\times\s*10\^\{?(\d+)\}?)?\s*meters'
            distances = re.findall(distance_pattern, question)
            
            if len(masses) >= 2 and len(distances) >= 1:
                # Convert string values to float, handling scientific notation
                def parse_scientific(value, exponent):
                    if exponent:
                        return float(value) * (10 ** int(exponent))
                    return float(value)
                
                spacecraft_mass = parse_scientific(masses[0][0], masses[0][1])
                object_mass = parse_scientific(masses[1][0], masses[1][1])
                distance = parse_scientific(distances[0][0], distances[0][1])
                
                return {
                    "spacecraft_mass": spacecraft_mass,
                    "object_mass": object_mass,
                    "distance": distance
                }
        except Exception as e:
            print(f"Error extracting gravity values: {str(e)}")
        return None

if __name__ == '__main__':
    unittest.main() 