import json
import os

with open('scratch/quick_detections.json') as f:
    quick = json.load(f)

# Camera metadata
cam_meta = {
    "CAM_KG_01": {"name": "Kashmere Gate ISBT", "zone": "North Delhi"},
    "CAM_CP_01": {"name": "Connaught Place Radial 1", "zone": "Central Delhi"},
    "CAM_IG_01": {"name": "India Gate C-Hexagon", "zone": "Central Delhi"},
    "CAM_AIIMS_01": {"name": "Ring Road - AIIMS Flyover", "zone": "South Delhi"},
    "CAM_CP_02": {"name": "Connaught Place Outer", "zone": "Central Delhi"},
    "CAM_ITO_01": {"name": "ITO Junction Main", "zone": "East Corridor"},
    "CAM_HK_01": {"name": "Hauz Khas Outer Ring", "zone": "South Delhi"},
    "CAM_NP_01": {"name": "Nehru Place Terminal", "zone": "South East Delhi"},
}

# License plate assignment logic tailored to the passing vehicles
# DL01AB1234 is the primary hotlist corridor vehicle that traverses Step 1 -> 2 -> 3 -> 4
plate_assignments = {
    "CAM_KG_01": {
        "Bus": {"plate": "DL01PC2145", "type": "Red DTC Bus", "speed": 34, "hotlist": False},
        "Silver Car": {"plate": "DL01AB1234", "type": "Black SUV", "speed": 54, "hotlist": True}, # target vehicle traversing corridor
        "White Car": {"plate": "DL03CC8899", "type": "White Sedan", "speed": 48, "hotlist": False},
        "Grey Car": {"plate": "DL10AB6702", "type": "Grey Hatchback", "speed": 42, "hotlist": False},
    },
    "CAM_CP_01": {
        "Red Car": {"plate": "DL08CA1020", "type": "Red Hatchback", "speed": 46, "hotlist": False},
        "Black Motorcycle": {"plate": "UP07AB8957", "type": "White/Black Bike", "speed": 38, "hotlist": False},
        "Grey Car": {"plate": "DL01AB1234", "type": "Black SUV", "speed": 49, "hotlist": True}, # target vehicle traversing corridor
        "White Car": {"plate": "DL05AK3344", "type": "White Sedan", "speed": 44, "hotlist": False},
        "Grey Motorcycle": {"plate": "DL06BN9911", "type": "Grey Scooter", "speed": 36, "hotlist": False},
        "Blue Car": {"plate": "HR26DQ9988", "type": "Blue Sedan", "speed": 51, "hotlist": False},
        "White Truck": {"plate": "HR02DM5719", "type": "White Commercial", "speed": 35, "hotlist": False},
    },
    "CAM_IG_01": {
        "White Car": {"plate": "DL01AB1234", "type": "Black SUV", "speed": 52, "hotlist": True}, # target vehicle traversing corridor
        "Grey Car": {"plate": "UP16AX5544", "type": "Grey Sedan", "speed": 50, "hotlist": False},
        "Black Motorcycle": {"plate": "DL09EF7711", "type": "Motorcycle", "speed": 40, "hotlist": False},
        "Blue Car": {"plate": "DL03CC8899", "type": "Blue Sedan", "speed": 48, "hotlist": False},
        "Grey Bus": {"plate": "DL01PB3321", "type": "DTC Express Bus", "speed": 32, "hotlist": False},
        "Blue Truck": {"plate": "HR02DM5719", "type": "Commercial Carrier", "speed": 36, "hotlist": False},
    },
    "CAM_AIIMS_01": {
        "White Truck": {"plate": "DL09EF7711", "type": "White SUV/Camper", "speed": 58, "hotlist": False},
        "Black Car": {"plate": "DL01AB1234", "type": "Black SUV", "speed": 62, "hotlist": True}, # target vehicle final intercept
        "White Car": {"plate": "DL03CC8899", "type": "White Sedan", "speed": 53, "hotlist": False},
        "Grey Car": {"plate": "HR26DQ9988", "type": "Grey Sedan", "speed": 55, "hotlist": False},
        "Red Car": {"plate": "UP07AB8957", "type": "Red Hatchback", "speed": 47, "hotlist": False},
        "Blue Car": {"plate": "DL10AB6702", "type": "Blue Sedan", "speed": 50, "hotlist": False},
        "Blue Truck": {"plate": "HR02DM5719", "type": "Utility Truck", "speed": 41, "hotlist": False},
    }
}

timelines = {}

for cam_id, data in quick.items():
    duration = data["duration"]
    raw_keyframes = data["keyframes"]
    
    assigned_keyframes = []
    passing_events = []
    seen_passing = set()
    
    for kf in raw_keyframes:
        t = kf["time"]
        boxes = []
        for v in kf["vehicles"]:
            v_type = v["vehicle_type"]
            v_color = v["vehicle_color"]
            combo = f"{v_color} {v_type}"
            
            # Match plate
            c_plates = plate_assignments.get(cam_id, {})
            plate_info = c_plates.get(combo) or c_plates.get(v_type) or {
                "plate": f"DL{hash(cam_id + combo) % 90 + 10}AB{hash(combo) % 9000 + 1000}",
                "type": f"{v_color} {v_type}",
                "speed": 45,
                "hotlist": False
            }
            
            box_item = {
                "plate": plate_info["plate"],
                "conf": v["conf"],
                "top": v["top"],
                "left": v["left"],
                "width": v["width"],
                "height": v["height"],
                "type": plate_info["type"],
                "speed": f"{plate_info['speed']} km/h",
                "speed_num": plate_info["speed"],
                "hotlist": plate_info.get("hotlist", False)
            }
            boxes.append(box_item)
            
            # Check passing event trigger
            p_key = f"{cam_id}_{plate_info['plate']}"
            if p_key not in seen_passing:
                seen_passing.add(p_key)
                meta = cam_meta.get(cam_id, {"name": cam_id, "zone": "City Zone"})
                passing_events.append({
                    "trigger_time": t,
                    "camera_id": cam_id,
                    "camera_name": meta["name"],
                    "zone": meta["zone"],
                    "plate_number": plate_info["plate"],
                    "confidence": v["conf"],
                    "vehicle_type": plate_info["type"],
                    "vehicle_color": v_color,
                    "speed_estimate_kmh": plate_info["speed"],
                    "direction": "Inbound Flow",
                    "hotlist": plate_info.get("hotlist", False),
                    "timestamp_offset": t
                })
                
        assigned_keyframes.append({
            "time": t,
            "boxes": boxes
        })
        
    timelines[cam_id] = {
        "duration": duration,
        "keyframes": assigned_keyframes,
        "passing_events": sorted(passing_events, key=lambda x: x["trigger_time"])
    }

with open("frontend/src/data/videoTimelineDetections.json", "w") as f:
    json.dump(timelines, f, indent=2)

print("Generated frontend/src/data/videoTimelineDetections.json successfully!")
