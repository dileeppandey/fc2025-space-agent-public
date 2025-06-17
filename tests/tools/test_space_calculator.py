import unittest
from unittest.mock import patch, MagicMock
from tools.space_calculator import (
    calculate_distance,
    calculate_gravity,
    calculate_travel_time
)
from tools.return_type import ToolResult

class TestSpaceCalculator(unittest.TestCase):
    def test_calculate_distance_km(self):
        # Test basic distance calculation with kilometers unit
        result = calculate_distance(
            current_coordinates={"x": 0, "y": 0, "z": 0},
            object_coordinates={"x": 3, "y": 4, "z": 0},
            unit="km"
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["distance"], 5.0)
        self.assertEqual(result.data["unit"], "km")
        self.assertEqual(result.data["vector"]["x"], 3.0)
        self.assertEqual(result.data["vector"]["y"], 4.0)
        self.assertEqual(result.data["vector"]["z"], 0.0)

    def test_calculate_distance_au(self):
        # Test with astronomical units
        result = calculate_distance(
            current_coordinates={"x": 0, "y": 0, "z": 0},
            object_coordinates={"x": 149597870.7, "y": 0, "z": 0},  # 1 AU in km
            unit="au"
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.data["distance"], 1.0, places=4)
        self.assertEqual(result.data["unit"], "au")

    def test_calculate_distance_ly(self):
        # Test with light years
        result = calculate_distance(
            current_coordinates={"x": 0, "y": 0, "z": 0},
            object_coordinates={"x": 9460730472580.8, "y": 0, "z": 0},  # 1 light year in km
            unit="ly"
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.data["distance"], 1.0, places=4)
        self.assertEqual(result.data["unit"], "ly")

    def test_calculate_distance_invalid_unit(self):
        # Test with invalid unit
        result = calculate_distance(
            current_coordinates={"x": 0, "y": 0, "z": 0},
            object_coordinates={"x": 1, "y": 1, "z": 1},
            unit="invalid"
        )
        self.assertFalse(result.success)
        self.assertIn("Unsupported unit", result.error)

    def test_calculate_gravity(self):
        # Test gravitational force calculation
        # Using Earth (5.97e24 kg) and ISS (420,000 kg) at 400 km altitude (6771000 m)
        earth_mass = 5.97e24
        iss_mass = 420000
        distance = 6771000  # Earth radius + altitude
        
        result = calculate_gravity(
            spacecraft_mass=iss_mass,
            object_mass=earth_mass,
            distance=distance
        )
        
        self.assertTrue(result.success)
        # Expected gravitational force ~3.65e6 N (using standard G)
        self.assertAlmostEqual(result.data["force_newtons"] / 3.65e6, 1.0, places=1)
        self.assertEqual(result.data["spacecraft_mass_kg"], iss_mass)
        self.assertEqual(result.data["object_mass_kg"], earth_mass)
        self.assertEqual(result.data["distance_m"], distance)

    def test_calculate_travel_time(self):
        # Test travel time calculation
        result = calculate_travel_time(
            distance=300000,  # 300,000 km
            speed=100  # 100 km/s
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["seconds"], 3000)
        self.assertEqual(result.data["minutes"], 50)
        self.assertEqual(result.data["hours"], 0.83)
        self.assertEqual(result.data["days"], 0.03)
        
    def test_calculate_travel_time_zero_speed(self):
        # Test with zero speed which should return an error
        result = calculate_travel_time(
            distance=1000,
            speed=0
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Error: Speed must be greater than zero")


if __name__ == '__main__':
    unittest.main()