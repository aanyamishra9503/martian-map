targets = [
    {"name": "Target A", "latitude": 18.4, "longitude": 77.6, "science_value": 8},
    {"name": "Target B", "latitude": 18.6, "longitude": 77.9, "science_value": 5},
    {"name": "Target C", "latitude": 18.3, "longitude": 77.7, "science_value": 9}
]

for target in targets:
    if target["science_value"] >= 8:
        print(target["name"], target["science_value"])