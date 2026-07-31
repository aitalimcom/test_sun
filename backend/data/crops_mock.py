"""Mock crop and land data — ported from sure_agritoolkit.

Nepal-specific crops with bilingual names.
"""

LANDS = [
    {
        "id": "land-1",
        "name": "Gundu Capsicum Greenhouse",
        "name_np": "गुण्डु भेडेखुर्सानी हरितगृह",
        "landType": "greenhouse",
        "areaSize": 450,
        "areaUnit": "sq_m",
        "location": "Gundu, Bhaktapur",
        "status": "active",
        "notes": "Greenhouse with drip irrigation and temperature control.",
        "notes_np": "ड्रिप सिँचाइ र तापक्रम नियन्त्रण भएको हरितगृह।",
    },
    {
        "id": "land-2",
        "name": "Patan Tomato Field",
        "name_np": "पाटन गोलभेडा खेत",
        "landType": "field",
        "areaSize": 1200,
        "areaUnit": "sq_m",
        "location": "Lubhu, Lalitpur",
        "status": "active",
        "notes": "Open field cultivation. Fertile soil, prone to weeds during monsoon.",
        "notes_np": "खुला खेती। उर्वर माटो, मनसुनमा झारपात लाग्ने।",
    },
    {
        "id": "land-3",
        "name": "Kirtipur Potato Orchard",
        "name_np": "कीर्तिपुर आलु बारी",
        "landType": "garden",
        "areaSize": 800,
        "areaUnit": "sq_m",
        "location": "Chobhar, Kathmandu",
        "status": "fallow",
        "notes": "Soil resting phase. Preparing for the next sowing season.",
        "notes_np": "माटो आराम चरण। अर्को रोपाइ मौसमको लागि तयारी।",
    },
]

CROPS = [
    {
        "id": "crop-1",
        "name": "Akabare Capsicum",
        "name_np": "अकबरे भेडेखुर्सानी",
        "species": "Capsicum annuum",
        "cropFamily": "Solanaceae",
        "maturityDays": 90,
        "yieldPotential": "2.5 kg/plant",
        "status": "growing",
        "landId": "land-1",
        "plantedDate": "2026-04-10",
        "expectedHarvest": "2026-07-10",
    },
    {
        "id": "crop-2",
        "name": "Sagarmatha Hybrid Tomato",
        "name_np": "सगरमाथा उन्नत गोलभेडा",
        "species": "Solanum lycopersicum",
        "cropFamily": "Solanaceae",
        "maturityDays": 75,
        "yieldPotential": "4.2 kg/plant",
        "status": "growing",
        "landId": "land-2",
        "plantedDate": "2026-05-01",
        "expectedHarvest": "2026-07-15",
    },
    {
        "id": "crop-3",
        "name": "Janak Dev Potato",
        "name_np": "जनक देव आलु",
        "species": "Solanum tuberosum",
        "cropFamily": "Solanaceae",
        "maturityDays": 110,
        "yieldPotential": "3.0 kg/plant",
        "status": "planned",
        "landId": "land-3",
        "plantedDate": "2026-07-01",
        "expectedHarvest": "2026-10-20",
    },
]

# Crop types for diagnosis selector
CROP_TYPES = [
    {"id": "rice", "name": "Rice", "name_np": "धान", "scientific": "Oryza sativa"},
    {"id": "maize", "name": "Maize", "name_np": "मकै", "scientific": "Zea mays"},
    {"id": "wheat", "name": "Wheat", "name_np": "गहुँ", "scientific": "Triticum aestivum"},
    {"id": "tomato", "name": "Tomato", "name_np": "गोलभेडा", "scientific": "Solanum lycopersicum"},
    {"id": "potato", "name": "Potato", "name_np": "आलु", "scientific": "Solanum tuberosum"},
    {"id": "capsicum", "name": "Capsicum", "name_np": "भेडेखुर्सानी", "scientific": "Capsicum annuum"},
    {"id": "lentil", "name": "Lentil", "name_np": "मसुरो", "scientific": "Lens culinaris"},
    {"id": "mustard", "name": "Mustard", "name_np": "तोरी", "scientific": "Brassica juncea"},
    {"id": "banana", "name": "Banana", "name_np": "केरा", "scientific": "Musa acuminata"},
    {"id": "tea", "name": "Tea", "name_np": "चिया", "scientific": "Camellia sinensis"},
]
