from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.image import Image
from app.models.building import Building
from app.services.ai.rag import get_embedding, cosine_similarity


async def classify_image_building(
    db: AsyncSession,
    image: Image,
    project_id: UUID,
) -> dict:
    """Suggest which building an image belongs to based on visual features."""
    
    # Get all buildings for the project (through site)
    from app.models.site import Site
    
    result = await db.execute(
        select(Building)
        .join(Site)
        .where(Site.project_id == project_id)
    )
    buildings = result.scalars().all()
    
    if not buildings:
        return {
            "suggested_building_id": None,
            "confidence": 0.0,
            "message": "No buildings found for this project"
        }
    
    # If image has AI analysis, use it for classification
    if not image.ai_analysis:
        return {
            "suggested_building_id": None,
            "confidence": 0.0,
            "message": "Image not yet analyzed. Run image analysis first."
        }
    
    analysis = image.ai_analysis
    
    # Build a feature string from the image analysis
    image_features = []
    if analysis.get("building_type"):
        image_features.append(f"Building type: {analysis['building_type']}")
    if analysis.get("materials"):
        image_features.append(f"Materials: {', '.join(analysis['materials'])}")
    if analysis.get("location_clues"):
        image_features.append(f"Location: {', '.join(analysis['location_clues'])}")
    if analysis.get("description"):
        image_features.append(analysis["description"][:200])
    
    image_feature_str = " ".join(image_features)
    
    if not image_feature_str:
        return {
            "suggested_building_id": None,
            "confidence": 0.0,
            "message": "Insufficient image analysis data for classification"
        }
    
    # Get embedding for image features
    image_embedding = await get_embedding(image_feature_str)
    
    # Compare with each building
    best_match = None
    best_similarity = 0.0
    all_matches = []
    
    for building in buildings:
        # Build building feature string
        building_features = [f"Building: {building.name}"]
        if building.building_type:
            building_features.append(f"Type: {building.building_type}")
        if building.description:
            building_features.append(building.description)
        
        # Check extra_data for learned features
        if building.extra_data and building.extra_data.get("learned_features"):
            learned = building.extra_data["learned_features"]
            if learned.get("materials"):
                building_features.append(f"Materials: {', '.join(learned['materials'])}")
            if learned.get("characteristics"):
                building_features.append(f"Characteristics: {', '.join(learned['characteristics'])}")
        
        building_feature_str = " ".join(building_features)
        building_embedding = await get_embedding(building_feature_str)
        
        similarity = cosine_similarity(image_embedding, building_embedding)
        
        all_matches.append({
            "building_id": str(building.id),
            "building_name": building.name,
            "similarity": round(similarity, 4)
        })
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = building
    
    # Sort matches by similarity
    all_matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Only suggest if confidence is above threshold
    confidence_threshold = 0.75
    
    if best_similarity >= confidence_threshold and best_match:
        return {
            "suggested_building_id": best_match.id,
            "suggested_building_name": best_match.name,
            "confidence": round(best_similarity, 4),
            "all_matches": all_matches[:3],
            "message": f"Image likely belongs to {best_match.name}"
        }
    else:
        return {
            "suggested_building_id": None,
            "confidence": round(best_similarity, 4),
            "all_matches": all_matches[:3],
            "message": "Low confidence - manual selection recommended"
        }


async def learn_building_features(
    db: AsyncSession,
    building: Building,
    image: Image,
):
    """Update building's learned features based on confirmed image assignment."""
    
    if not image.ai_analysis:
        return
    
    analysis = image.ai_analysis
    
    # Get or initialize extra_data
    extra_data = building.extra_data or {}
    learned = extra_data.get("learned_features", {
        "materials": [],
        "characteristics": [],
        "typical_areas": [],
    })
    
    # Add new materials
    if analysis.get("materials"):
        for material in analysis["materials"]:
            if material not in learned["materials"]:
                learned["materials"].append(material)
    
    # Add location clues as characteristics
    if analysis.get("location_clues"):
        for clue in analysis["location_clues"]:
            if clue not in learned["characteristics"]:
                learned["characteristics"].append(clue)
    
    # Add area if specified
    if image.area and image.area not in learned["typical_areas"]:
        learned["typical_areas"].append(image.area)
    
    # Update extra_data
    extra_data["learned_features"] = learned
    building.extra_data = extra_data
    
    await db.commit()
