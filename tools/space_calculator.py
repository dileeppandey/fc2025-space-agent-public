"""
SPACE CALCULATOR IMPLEMENTATION GUIDE
=====================================

This file contains 11 TODOs that need to be completed to make the space calculator functional.
Work through them in order for the best experience:

Phase 1 - Winston's Instructions (TODOs #1-#4):
- TODO #1: Add distance calculation use cases
- TODO #2: Add object coordinates description  
- TODO #3: Add gravity calculation use cases
- TODO #4: Add spacecraft mass description

Phase 2 - Distance Calculations (TODOs #5-#8):
- TODO #5: Implement 3D distance formula
- TODO #6: Convert km to AU units
- TODO #7: Calculate direction vector components
- TODO #8: Fix return statement

Phase 3 - Gravity Calculations (TODOs #9-#11):
- TODO #9: Set gravitational constant
- TODO #10: Implement Newton's law of gravitation
- TODO #11: Add missing result field

💡 TIP: Complete each section before moving to the next!
"""

import weave
import math
from typing import Dict, Any, Union, List
from tools.return_type import ToolResult

"""Phase 1 - Winston's Instructions"""
SPACE_CALCULATOR_TOOLS = {
    "calculate_distance": {
        "type": "function",
        "function": {
            "name": "space_calculator-calculate_distance",
            "description": """Calculates the distance between the spacecraft and a celestial object.
            Use this tool for:
            - Determining how far the spacecraft is from a planet, moon, star, or other celestial body
            - Calculating minimum safe distance from a black hole's event horizon (typically 3x the Schwarzschild radius)
            - Planning navigation routes and course corrections
            - Estimating travel time to destinations
            - Determining optimal approach vectors for docking or landing
            - Calculating distance between two celestial objects
            - Describing object coordinates in 3D space
            - Avoiding gravitational anomalies and dangerous regions
            - Planning orbital insertion and departure maneuvers
            - Calculating safe approach distances for stellar phenomena
            - Determining optimal observation distances for scientific studies
            - Planning gravitational slingshot trajectories
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "current_coordinates": {
                        "type": "object",
                        "description": "The current coordinates of the spacecraft in 3D space (x,y,z), representing its position in a heliocentric coordinate system where the origin (0,0,0) is the center of the solar system. Positive x extends toward the vernal equinox, positive y extends toward the summer solstice, and positive z extends toward the north celestial pole. All coordinates are in kilometers.",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"}
                        },
                        "required": ["x", "y", "z"]
                    },
                    "object_coordinates": {
                        "type": "object",
                        "description": "The coordinates of the target celestial object in 3D space (x,y,z), representing its position in the same heliocentric coordinate system. These coordinates are crucial for accurate navigation and must account for the object's current orbital position. For objects in orbit, these coordinates should represent their instantaneous position at the time of calculation.",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"}
                        },
                        "required": ["x", "y", "z"]
                    },
                    "unit": {
                        "type": "string",
                        "description": "The unit of measurement for the result (km, au, ly)",
                        "enum": ["km", "au", "ly"]
                    }
                },
                "required": ["current_coordinates", "object_coordinates", "unit"]
            }
        }
    },
    
    "calculate_gravity": {
        "type": "function",
        "function": {
            "name": "space_calculator-calculate_gravity",
            "description": """Calculates the gravitational force between the spacecraft and a celestial object.
            Use this tool for:
            - Determining gravitational influence of nearby celestial bodies
            - Calculating escape velocities for planetary departure
            - Assessing gravity-related dangers
            - Planning orbital maneuvers
            - Determining orbital parameters
            - Calculating gravitational assists
            - Evaluating tidal forces near massive objects
            - Planning safe trajectories around black holes
            - Calculating orbital decay rates
            - Determining Lagrange point positions
            - Assessing structural stress from gravitational forces
            - Planning fuel-efficient orbital transfers
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "spacecraft_mass": {
                        "type": "number",
                        "description": "The total mass of the spacecraft in kilograms, including fuel, payload, and all onboard systems. This mass is crucial for accurate gravitational calculations as it affects both the gravitational force experienced and the spacecraft's ability to overcome gravitational fields. The mass should be updated after significant fuel consumption or payload changes."
                    },
                    "object_mass": {
                        "type": "number",
                        "description": "The mass of the celestial object in kilograms. For accurate calculations, use precise mass values from astronomical databases. For black holes, use the mass of the central singularity. For binary systems, calculate the combined mass of both objects."
                    },
                    "distance": {
                        "type": "number",
                        "description": "The distance between the spacecraft and the celestial object in meters. This should be the center-to-center distance for spherical objects, or the distance to the nearest point for irregular objects. For black holes, use the distance from the event horizon."
                    }
                },
                "required": ["spacecraft_mass", "object_mass", "distance"]
            }
        }
    },
    
    "calculate_travel_time": {
        "type": "function",
        "function": {
            "name": "space_calculator-calculate_travel_time",
            "description": """Calculates the time required to travel from the current position to a destination.
            Use this tool for:
            - Planning mission durations
            - Estimating arrival times
            - Calculating fuel requirements based on journey time
            - Determining feasibility of reaching destinations
            - Planning orbital rendezvous
            - Optimizing travel trajectories
            - Scheduling scientific observations
            - Coordinating multi-spacecraft missions
            - Planning emergency maneuvers
            - Estimating communication delays
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "number",
                        "description": "The distance to travel in kilometers"
                    },
                    "speed": {
                        "type": "number",
                        "description": "The spacecraft's speed in kilometers per second"
                    }
                },
                "required": ["distance", "speed"]
            }
        }
    }
}

"""Phase 2 - Distance Calculations"""
@weave.op(name="space_calculator-calculate_distance")
def calculate_distance(*, current_coordinates: Dict[str, float], 
                      object_coordinates: Dict[str, float], 
                      unit: str) -> ToolResult[Dict[str, Any]]:
    """Calculate the distance between the spacecraft and a celestial object."""
    try:
        # Validate input coordinates
        if not isinstance(current_coordinates, dict) or not isinstance(object_coordinates, dict):
            return ToolResult.err("Invalid coordinate format: must be dictionaries")
        
        required_keys = ["x", "y", "z"]
        for coords in [current_coordinates, object_coordinates]:
            if not all(key in coords for key in required_keys):
                return ToolResult.err("Missing required coordinate components (x, y, z)")
            if not all(isinstance(coords[key], (int, float)) for key in required_keys):
                return ToolResult.err("Coordinate values must be numbers")
        
        # Extract coordinates
        x1, y1, z1 = current_coordinates["x"], current_coordinates["y"], current_coordinates["z"]
        x2, y2, z2 = object_coordinates["x"], object_coordinates["y"], object_coordinates["z"]
        
        # Calculate squared differences first to avoid potential overflow
        try:
            dx2 = (x2 - x1) ** 2
            dy2 = (y2 - y1) ** 2
            dz2 = (z2 - z1) ** 2
            
            # Check for overflow in squared differences
            if any(math.isinf(val) for val in [dx2, dy2, dz2]):
                return ToolResult.err("Coordinate differences too large for calculation")
            
            # Calculate Euclidean distance in kilometers using the 3D distance formula
            distance_km = math.sqrt(dx2 + dy2 + dz2)
            
            # Check for invalid results
            if math.isnan(distance_km) or math.isinf(distance_km):
                return ToolResult.err("Distance calculation resulted in invalid value")
                
        except (OverflowError, ValueError) as e:
            return ToolResult.err(f"Error in distance calculation: {str(e)}")
        
        # Convert to requested unit
        try:
            if unit == "km":
                distance_value = distance_km
            elif unit == "au":  # Astronomical Unit
                # Convert km to AU (1 AU = 149,597,870.7 km)
                distance_value = distance_km / 149597870.7
            elif unit == "ly":  # Light Year
                # Convert km to light years (1 ly = 9,460,730,472,580.8 km)
                distance_value = distance_km / 9460730472580.8
            else:
                return ToolResult.err(f"Unsupported unit: {unit}")
            
            # Check for invalid conversion results
            if math.isnan(distance_value) or math.isinf(distance_value):
                return ToolResult.err("Unit conversion resulted in invalid value")
                
        except (OverflowError, ZeroDivisionError) as e:
            return ToolResult.err(f"Error in unit conversion: {str(e)}")
        
        # Calculate direction vector components with precision control
        try:
            # Calculate raw differences
            dx = x2 - x1
            dy = y2 - y1
            dz = z2 - z1
            
            # Check for overflow in vector components
            if any(math.isinf(val) for val in [dx, dy, dz]):
                return ToolResult.err("Vector components too large for calculation")
            
            # Round to 4 decimal places for precision
            vector = {
                "x": round(dx, 4),
                "y": round(dy, 4),
                "z": round(dz, 4)
            }
            
            # Verify vector components are valid
            if any(math.isnan(val) for val in vector.values()):
                return ToolResult.err("Vector calculation resulted in invalid values")
                
        except (OverflowError, ValueError) as e:
            return ToolResult.err(f"Error in vector calculation: {str(e)}")
        
        # Prepare result with appropriate precision
        result = {
            "distance": round(distance_value, 4),
            "unit": unit,
            "vector": vector
        }
        
        return ToolResult.ok(result)
        
    except Exception as e:
        return ToolResult.err(f"Unexpected error in distance calculation: {str(e)}")

"""Phase 3 - Gravity Calculations"""
@weave.op(name="space_calculator-calculate_gravity")
def calculate_gravity(*, spacecraft_mass: float, object_mass: float, distance: float) -> ToolResult[Dict[str, Any]]:
    """Calculate the gravitational force between the spacecraft and a celestial object."""
    try:
        # Validate input values
        if not all(isinstance(x, (int, float)) for x in [spacecraft_mass, object_mass, distance]):
            return ToolResult.err("All input values must be numbers")
        
        if distance <= 0:
            return ToolResult.err("Distance must be greater than zero")
        
        if spacecraft_mass <= 0 or object_mass <= 0:
            return ToolResult.err("Masses must be greater than zero")
        
        # Set the gravitational constant (G) in m³/kg/s²
        G = 6.6743e-11  # Universal gravitational constant
        
        # Calculate gravitational force using Newton's law: F = G * m1 * m2 / r²
        try:
            # Calculate squared distance first to avoid potential overflow
            distance_squared = distance ** 2
            
            # Check for overflow in squared distance
            if math.isinf(distance_squared):
                return ToolResult.err("Distance too large for calculation")
            
            # Calculate force components separately to avoid overflow
            force_component = G * spacecraft_mass
            if math.isinf(force_component):
                return ToolResult.err("Mass too large for calculation")
            
            force = force_component * object_mass / distance_squared
            
            # Check for invalid results
            if math.isnan(force) or math.isinf(force):
                return ToolResult.err("Gravitational force calculation resulted in invalid value")
            
            # Check if force is too small to be meaningful
            if force < 1e-30:  # Below practical measurement threshold
                return ToolResult.err("Gravitational force too small to be meaningful")
            
        except (OverflowError, ZeroDivisionError) as e:
            return ToolResult.err(f"Error in force calculation: {str(e)}")
        
        # Prepare result with appropriate precision and units
        result = {
            "force_newtons": round(force, 4),  # Force in Newtons
            "spacecraft_mass_kg": round(spacecraft_mass, 4),  # Mass in kilograms
            "object_mass_kg": round(object_mass, 4),  # Mass in kilograms
            "distance_m": round(distance, 4),  # Distance in meters
            "gravitational_constant": G  # Include G for reference
        }
        
        return ToolResult.ok(result)
        
    except Exception as e:
        return ToolResult.err(f"Unexpected error in gravity calculation: {str(e)}")

"""Travel Time Calculations"""
@weave.op(name="space_calculator-calculate_travel_time")
def calculate_travel_time(*, distance: float, speed: float) -> ToolResult[Dict[str, Any]]:
    """Calculate the time required to travel a distance at a given speed."""
    try:
        # Validate input values
        if not all(isinstance(x, (int, float)) for x in [distance, speed]):
            return ToolResult.err("Distance and speed must be numbers")
        
        if distance < 0:
            return ToolResult.err("Distance cannot be negative")
        
        if speed <= 0:
            return ToolResult.err("Speed must be greater than zero")
        
        # Calculate time in seconds
        try:
            time_seconds = distance / speed
        except ZeroDivisionError:
            return ToolResult.err("Invalid speed value")
        
        # Convert to appropriate units
        try:
            time_minutes = time_seconds / 60
            time_hours = time_minutes / 60
            time_days = time_hours / 24
            time_years = time_days / 365.25
        except (OverflowError, ZeroDivisionError):
            return ToolResult.err("Time conversion resulted in invalid value")
        
        result = {
            "seconds": round(time_seconds, 2),
            "minutes": round(time_minutes, 2),
            "hours": round(time_hours, 2),
            "days": round(time_days, 2),
            "years": round(time_years, 4)
        }
        
        return ToolResult.ok(result)
    except Exception as e:
        return ToolResult.err(f"Error in travel time calculation: {str(e)}")