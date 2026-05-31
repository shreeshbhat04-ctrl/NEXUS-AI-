from typing import Any

def generate_safe_ingredients(detected_ingredients: list[str], ingredients_to_avoid: list[str]) -> list[dict[str, Any]]:
    """
    Intersection Logic (The Filter).
    Compares detected_ingredients against ingredients_to_avoid.
    Returns a list of Safe Available Ingredients enriched with UI metadata.
    """
    
    # Normalize avoid list to lowercase for substring matching
    avoid_normalized = [a.lower().strip() for a in ingredients_to_avoid if a.strip()]
    
    safe_ingredients = []
    
    for idx, item in enumerate(detected_ingredients):
        item_normalized = item.lower().strip()
        if not item_normalized:
            continue
            
        # Deterministic check: if any avoid word is a substring of the detected ingredient
        is_safe = True
        reason = "Cleared for use."
        
        for avoid in avoid_normalized:
            if avoid in item_normalized or item_normalized in avoid:
                is_safe = False
                reason = f"Contraindicated due to medical history restriction on '{avoid}'."
                break
                
        # Build UI-friendly object matching the MarketplaceIngredient shape
        # In a real app we'd fetch image/price from a catalog, here we mock it
        safe_ingredients.append({
            "id": f"dyn_{idx}",
            "name": item.title(),
            "category": "Pantry", # Mocked
            "price": 2.99, # Mocked
            "status": "Safe" if is_safe else "Avoid",
            "reason": reason,
            "image": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&q=80&w=300", # Placeholder
            "is_dynamically_extracted": True
        })
        
    return safe_ingredients
