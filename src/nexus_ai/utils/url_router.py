import urllib.parse
from typing import Optional

class ProductUrlRouter:
    # Supported Indian and Global platforms
    DOMAINS = {
        "1mg": "https://www.1mg.com/search/all?name={query}",
        "apollo": "https://www.apollopharmacy.in/search-medicines/{query}",
        "pharmeasy": "https://pharmeasy.in/search/all?searchTextField={query}",
        "blinkit": "https://blinkit.com/s/?q={query}",
        "amazon": "https://www.amazon.in/s?k={query}",
        "bigbasket": "https://www.bigbasket.com/ps/?q={query}",
        "zepto": "https://zepto.cash/search?query={query}"
    }

    @classmethod
    def get_search_url(cls, item_name: str, item_type: str, platform_preference: Optional[str] = None) -> str:
        """
        Generates a direct, real-world search URL based on item characteristics and preferences.
        """
        encoded_query = urllib.parse.quote_plus(item_name)
        
        # 1. Determine platform if not explicitly requested
        if not platform_preference:
            item_type_lower = item_type.lower() if item_type else ""
            if "medicine" in item_type_lower or "medication" in item_type_lower or "drug" in item_type_lower:
                platform_preference = "1mg"        # Standard for medicines
            elif "device" in item_type_lower or "hardware" in item_type_lower or "meditech" in item_type_lower:
                platform_preference = "amazon"     # Standard for oximeters, monitors, hardware
            else:
                platform_preference = "blinkit"    # Standard for quick grocery ingredients

        # 2. Extract standard format string
        url_format = cls.DOMAINS.get(platform_preference.lower(), cls.DOMAINS["amazon"])
        
        # Special-case formatting if required by certain APIs
        if platform_preference.lower() == "apollo":
            hyphen_query = item_name.lower().replace(" ", "-")
            return f"https://www.apollopharmacy.in/search-medicines/{hyphen_query}"

        return url_format.format(query=encoded_query)
