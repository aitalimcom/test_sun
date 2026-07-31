"""Mock IoT device data — ported from sure_agritoolkit.

Realistic Nepal-based IoT devices with bilingual names.
"""

IOT_DEVICES = [
    {
        "id": "device-1",
        "name": "Gundu NPK Probe",
        "name_np": "गुण्डु NPK प्रोब",
        "status": "active",
        "deviceType": "NPK",
        "battery": 88,
        "metrics": [
            {"label": "Nitrogen (N)", "label_np": "नाइट्रोजन (N)", "value": "45", "unit": "mg/kg"},
            {"label": "Phosphorus (P)", "label_np": "फस्फोरस (P)", "value": "32", "unit": "mg/kg"},
            {"label": "Potassium (K)", "label_np": "पोटासियम (K)", "value": "60", "unit": "mg/kg"},
        ],
        "landId": "land-1",
        "landName": "गुण्डु भेडेखुर्सानी हरितगृह",
        "lastSync": "2026-07-30T10:30:00",
    },
    {
        "id": "device-2",
        "name": "Lubhu Soil Probe",
        "name_np": "लुभु माटो प्रोब",
        "status": "warning",
        "deviceType": "Moisture",
        "battery": 42,
        "metrics": [
            {"label": "Soil Moisture", "label_np": "माटोको चिस्यान", "value": "24", "unit": "%"},
            {"label": "Soil Temp", "label_np": "माटोको तापक्रम", "value": "26.8", "unit": "°C"},
        ],
        "landId": "land-2",
        "landName": "पाटन गोलभेडा खेत",
        "lastSync": "2026-07-30T10:25:00",
    },
    {
        "id": "device-3",
        "name": "Chobhar Valve Controller",
        "name_np": "चोभर भल्भ कन्ट्रोलर",
        "status": "offline",
        "deviceType": "Irrigation",
        "battery": 0,
        "metrics": [
            {"label": "Flow Rate", "label_np": "प्रवाह दर", "value": "0.0", "unit": "L/min"},
            {"label": "Valve State", "label_np": "भल्भ अवस्था", "value": "Closed", "unit": ""},
        ],
        "landId": "land-3",
        "landName": "कीर्तिपुर आलु बारी",
        "lastSync": "2026-07-30T08:00:00",
    },
    {
        "id": "device-4",
        "name": "Gundu Weather Station",
        "name_np": "गुण्डु मौसम केन्द्र",
        "status": "active",
        "deviceType": "Weather",
        "battery": 95,
        "metrics": [
            {"label": "Air Temp", "label_np": "वायु तापक्रम", "value": "28.5", "unit": "°C"},
            {"label": "Humidity", "label_np": "आर्द्रता", "value": "68", "unit": "%"},
            {"label": "Light", "label_np": "प्रकाश", "value": "45000", "unit": "Lux"},
        ],
        "landId": "land-1",
        "landName": "गुण्डु भेडेखुर्सानी हरितगृह",
        "lastSync": "2026-07-30T10:30:00",
    },
]

IOT_ALERTS = [
    {
        "id": "alert-1",
        "title": "Low Soil Moisture / माटोमा कम चिस्यान",
        "title_np": "माटोमा कम चिस्यान",
        "message": "Lubhu Soil Probe reports moisture at 24%, which is below the threshold of 30%.",
        "message_np": "लुभु माटो सेन्सरले २४% चिस्यान रिपोर्ट गर्छ, जुन ३०% को न्यूनतम आवश्यकता भन्दा कम छ।",
        "severity": "warning",
        "timestamp": "2026-07-30T10:20:00",
        "read": False,
        "deviceId": "device-2",
        "landId": "land-2",
        "action": "irrigate",
    },
    {
        "id": "alert-2",
        "title": "Greenhouse Temperature Alert / हरितगृह तापक्रम चेतावनी",
        "title_np": "हरितगृह तापक्रम चेतावनी",
        "message": "Gundu Weather Station reports temperature of 32.5°C in Greenhouse 1. Ventilation suggested.",
        "message_np": "गुण्डु मौसम केन्द्रले हरितगृह १ मा ३२.५ डिग्री सेल्सियस तापक्रम रिपोर्ट गर्दछ। भेन्टिलेसन सुझाव दिइन्छ।",
        "severity": "danger",
        "timestamp": "2026-07-30T09:45:00",
        "read": False,
        "deviceId": "device-4",
        "landId": "land-1",
        "action": "ventilate",
    },
    {
        "id": "alert-3",
        "title": "Device Battery Critically Low / उपकरण ब्याट्री न्यून",
        "title_np": "उपकरण ब्याट्री न्यून",
        "message": "Lubhu Soil Probe battery is at 42%. Weather sensor offline warnings triggered.",
        "message_np": "लुभु माटो सेन्सरको ब्याट्री ४२% छ। मौसम सेन्सर अफलाइन चेतावनी सक्रिय गरियो।",
        "severity": "info",
        "timestamp": "2026-07-30T08:30:00",
        "read": True,
        "deviceId": "device-2",
        "landId": "land-2",
        "action": None,
    },
]

# Mock telemetry history for charts
IOT_TELEMETRY = {
    "device-2": [
        {"timestamp": "2026-07-30T00:00:00", "moisture": 35, "temp": 22},
        {"timestamp": "2026-07-30T02:00:00", "moisture": 33, "temp": 21},
        {"timestamp": "2026-07-30T04:00:00", "moisture": 30, "temp": 20},
        {"timestamp": "2026-07-30T06:00:00", "moisture": 28, "temp": 22},
        {"timestamp": "2026-07-30T08:00:00", "moisture": 26, "temp": 25},
        {"timestamp": "2026-07-30T10:00:00", "moisture": 24, "temp": 27},
    ],
    "device-4": [
        {"timestamp": "2026-07-30T00:00:00", "temp": 22, "humidity": 75, "light": 0},
        {"timestamp": "2026-07-30T02:00:00", "temp": 21, "humidity": 78, "light": 0},
        {"timestamp": "2026-07-30T04:00:00", "temp": 20, "humidity": 80, "light": 500},
        {"timestamp": "2026-07-30T06:00:00", "temp": 23, "humidity": 72, "light": 15000},
        {"timestamp": "2026-07-30T08:00:00", "temp": 26, "humidity": 65, "light": 35000},
        {"timestamp": "2026-07-30T10:00:00", "temp": 28.5, "humidity": 68, "light": 45000},
    ],
}
