import json

with open('scratch/quick_detections.json') as f:
    data = json.load(f)

for cam in ['CAM_KG_01', 'CAM_CP_01', 'CAM_IG_01', 'CAM_AIIMS_01']:
    print(f"\n==================== {cam} ====================")
    for kf in data[cam]['keyframes']:
        v_list = [f"{v['vehicle_color']} {v['vehicle_type']}({v['top']},{v['left']})" for v in kf['vehicles']]
        print(f"t={kf['time']}s: {len(kf['vehicles'])} vehicles -> {v_list}")
