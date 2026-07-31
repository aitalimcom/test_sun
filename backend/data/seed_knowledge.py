"""Seeds the flat-file markdown knowledge base and triggers RAG indexing."""

import logging
from pathlib import Path
from config import settings
from services.rag.indexer import document_indexer

logger = logging.getLogger(__name__)

# Sample documents content
DISEASES = {
    "rice_blast": (
        "# धान ब्लास्ट (Rice Blast)\n\n"
        "धान ब्लास्ट म्याग्नापोर्थे ओरिजाए (Magnaporthe oryzae) ढुसीको कारणले लाग्ने धानको प्रमुख रोग हो।\n"
        "यसले पात, काण्ड, र बालामा आक्रमण गर्छ। पातमा हिरा आकारका दागहरू देखा पर्छन्।\n\n"
        "## रासायनिक उपचार (Chemical Treatment):\n"
        "१. ट्राइसाइक्लाजोल ७५% WP (Tricyclazole) - ०.६ ग्राम प्रति लिटर पानीमा मिसाएर छर्कने।\n"
        "२. कासुगामाइसिन (Kasugamycin) - २ एमएल प्रति लिटर पानीमा हालेर छर्कने।\n\n"
        "## जैविक उपचार (Organic Treatment):\n"
        "१. गाईको गहुँत १० गुणा पानीमा मिसाएर छर्कने।\n"
        "२. जैविक ढुसीनाशक ट्राइकोडर्मा (Trichoderma viride) १ केजी प्रति रोपनी माटोमा मिसाउने।"
    ),
    "tomato_late_blight": (
        "# गोलभेडा डढुवा (Tomato Late Blight)\n\n"
        "गोलभेडा डढुवा फाइटोफ्थोरा इन्फेस्टान्स (Phytophthora infestans) ढुसीका कारण लाग्ने खतरनाक रोग हो।\n"
        "यसले पातमा पानीले भिजेको जस्तो गाढा दाग बनाउँछ र डाँठ कालो भएर कुहिन्छ।\n\n"
        "## रासायनिक उपचार:\n"
        "१. मेटलक्सिल ८% + म्यान्कोजेब ६४% (Metalaxyl + Mancozeb) - २ ग्राम प्रति लिटर पानीमा मिसाएर ७-१० दिनको अन्तरालमा स्प्रे गर्ने।\n\n"
        "## जैविक उपचार:\n"
        "१. बोर्डो मिश्रण (Bordeaux mixture 1%) पातमा छर्कने।\n"
        "२. निमको पातको रस मिसाएर छर्कने।"
    )
}

PRACTICES = {
    "organic_fertilizer": (
        "# कम्पोस्ट र जैविक मल प्रबन्ध (Organic Fertilizer Management)\n\n"
        "बाली उत्पादन बढाउन र माटोको स्वास्थ्य सुधार गर्न जैविक मलको ठूलो भूमिका हुन्छ।\n"
        "कम्पोस्ट बनाउँदा सुकेको पात, गोबर, र हरियो झारपातको सन्तुलित तह मिलाएर कुहाउनुपर्छ।\n"
        "एक रोपनी जग्गाका लागि सामान्यतया ५०० केजी देखि १००० केजी कम्पोस्ट मल आवश्यक पर्छ।"
    )
}

GUIDES = {
    "rice_cultivation": (
        "# धान खेती निर्देशिका (Rice Cultivation Guide)\n\n"
        "नेपालमा धान प्रमुख खाद्यान्न बाली हो। यसको खेतीका लागि २५-३० डिग्री सेल्सियस तापक्रम उपयुक्त मानिन्छ।\n"
        "रोपाइँ गर्दा लाइन देखि लाइनको दुरी २० सेन्टिमिटर र बोट देखि बोटको दुरी १५ सेन्टिमिटर राख्नुपर्छ।\n"
        "मल प्रति रोपनी: ६ केजी यूरिया, ४ केजी डीएपी र २.५ केजी पोटास धान रोप्नु अघि र पछि टप-ड्रेसिङ गर्नुपर्छ।"
    )
}


async def seed_and_index_knowledge() -> None:
    """Create directory structure, populate markdown files, and index into vector store."""
    knowledge_dir = Path(settings.database_root) / "knowledge"
    
    # Create subfolders
    (knowledge_dir / "diseases").mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "practices").mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "guides").mkdir(parents=True, exist_ok=True)

    logger.info("Writing knowledge base Markdown documents...")
    # Write diseases
    for filename, content in DISEASES.items():
        path = knowledge_dir / "diseases" / f"{filename}.md"
        path.write_text(content, encoding="utf-8")
        
    # Write practices
    for filename, content in PRACTICES.items():
        path = knowledge_dir / "practices" / f"{filename}.md"
        path.write_text(content, encoding="utf-8")
        
    # Write guides
    for filename, content in GUIDES.items():
        path = knowledge_dir / "guides" / f"{filename}.md"
        path.write_text(content, encoding="utf-8")

    logger.info("Triggering vector index indexing...")
    # Now run indexing
    indexed_count = await document_indexer.index_all()
    logger.info(f"Indexed {indexed_count} total document chunks in vector store.")
