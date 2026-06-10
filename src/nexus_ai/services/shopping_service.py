import logging
import json
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from google import genai
from google.genai import types

from nexus_ai.config import get_settings
from nexus_ai.db.models import CartItem, Notification
from nexus_ai.adapters.notifications import MockNotificationAdapter
from nexus_ai.utils.url_router import ProductUrlRouter

logger = logging.getLogger(__name__)

SHOPPING_AGENT_SYSTEM_INSTRUCTION = """\
You are an expert product analyst assistant integrated into the nexus_ai platform.
Your task is to analyze the text content of a retailer's product page and extract the product's availability, price, and any applicable discount coupons/deals.

You must return a JSON object with exactly these keys:
{
  "status": "<string: one of 'in_stock', 'out_of_stock', or 'price_drop'>",
  "price": <float or null>,
  "original_price": <float or null>,
  "coupon_code": "<string or null>",
  "confidence": <integer 0-100>
}

Guidelines:
- "status" should be:
  - "in_stock" if the item is available for purchase/add-to-cart.
  - "out_of_stock" if the text explicitly states the item is out of stock, unavailable, sold out, or backordered.
  - "price_drop" if the text indicates a discount, a price reduction, sale price, or active deal.
- "price" should be the current active price of the item as a float (e.g. 12.99).
- "original_price" should be the original price before discount/sale (if present, else null).
- "coupon_code" should be any visible promo code or coupon code for additional discounts (if present, else null).
- ALWAYS respond with valid JSON only – no markdown fences, no extra text.
"""

class ShoppingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.google_api_key
        self.model_id = self.settings.gemini_fast_model_id or "gemini-2.0-flash"
        self.notification_adapter = MockNotificationAdapter()

    def check_cart_availability(self, db: Session, patient_id: int) -> list[CartItem]:
        """Check availability for all items in a patient's cart and trigger notifications for changes."""
        stmt = select(CartItem).where(CartItem.patient_id == patient_id)
        items = list(db.scalars(stmt).all())
        
        updated_items = []
        for item in items:
            old_status = item.status
            
            url_to_check = item.source_url or ProductUrlRouter.get_search_url(item.item_name, item.item_type)
            if url_to_check:
                # Real/Simulated URL check
                checked_info = self._check_url_availability(url_to_check)
            else:
                # Name-based fallback lookup
                checked_info = self._get_mock_availability_for_name(item.item_name)
            
            # Apply changes
            item.status = checked_info.get("status", "in_stock")
            item.price = checked_info.get("price")
            item.original_price = checked_info.get("original_price")
            item.coupon_code = checked_info.get("coupon_code")
            item.last_checked = datetime.utcnow()
            
            # Save if status changed to trigger notifications
            if item.status != old_status:
                self._trigger_cart_notifications(db, patient_id, item, old_status)
                
            db.add(item)
            updated_items.append(item)
            
        db.commit()
        return updated_items

    def checkout_item(self, db: Session, patient_id: int, item_id: int) -> dict[str, Any]:
        """Perform a simulated Agentic Checkout for a cart item."""
        item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.patient_id == patient_id))
        if not item:
            raise ValueError("Cart item not found.")
            
        if item.status == "out_of_stock":
            return {"success": False, "message": "Cannot purchase an out-of-stock item."}
            
        # Success checkout path
        item.status = "purchased"
        db.add(item)
        
        # Fire checkout success notifications
        message = f"Checkout complete! Your order for {item.item_name} has been processed via Google Pay. Total charged: ${item.price or 0.0:.2f}."
        
        # 1. SMS Alert
        self.notification_adapter.send(channel="sms", message_body=message)
        
        # 2. Gmail Alert
        self.notification_adapter.send(channel="gmail", message_body=message)
        
        # 3. Web Notification
        web_notif = Notification(
            patient_id=patient_id,
            channel="web",
            message_type="cart_checkout",
            body=message,
            delivery_status="sent"
        )
        db.add(web_notif)
        db.commit()
        
        return {
            "success": True,
            "message": "Agentic checkout successful.",
            "order_id": f"CQ-ORD-{item.id}-{int(datetime.utcnow().timestamp())}",
            "item_name": item.item_name,
            "price": item.price,
        }

    def _check_url_availability(self, url: str) -> dict[str, Any]:
        """Fetch URL content and parse availability using the Gemini Subagent."""
        if not url.startswith("http"):
            return self._get_mock_availability_for_name(url)
            
        # Try fetching the URL
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            # Fetch with a reasonable timeout
            response = httpx.get(url, headers=headers, timeout=8.0, follow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch cart URL {url}, status code: {response.status_code}")
                return self._get_mock_availability_for_name(url)
                
            page_text = response.text[:12000] # Limit size for token constraints
            
            # Delegate parsing to Gemini Subagent
            return self._parse_html_with_gemini(page_text)
        except Exception as e:
            logger.exception(f"Scraper error fetching {url}: {e}")
            # Fallback to mock behavior if site blocks us or is down
            return self._get_mock_availability_for_name(url)

    def _parse_html_with_gemini(self, page_content: str) -> dict[str, Any]:
        """Delegate text parsing to a Gemini model to ensure layout changes don't break the system."""
        if not self.api_key:
            logger.warning("Google API Key not configured; using fallback mock parsing.")
            return {"status": "in_stock", "price": 15.00, "confidence": 100}
            
        try:
            client = genai.Client(api_key=self.api_key)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"Analyze this raw page source:\n\n{page_content}")
                    ]
                )
            ]
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=[types.Part.from_text(text=SHOPPING_AGENT_SYSTEM_INSTRUCTION)],
            )
            response = client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=config,
            )
            
            raw_text = response.text.strip() if response.text else ""
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[-1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()
            
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Gemini page parsing failed: {e}")
            return {"status": "in_stock", "price": 15.00, "confidence": 50}

    def _get_mock_availability_for_name(self, name: str) -> dict[str, Any]:
        """Generate smart fallback mock data for testing and when scraping is blocked."""
        name_lower = name.lower()
        
        # Default mock items
        status = "in_stock"
        price = 12.50
        original_price = None
        coupon_code = None
        
        # Control UI states via name keywords
        if "out of stock" in name_lower or "out_of_stock" in name_lower:
            status = "out_of_stock"
            price = None
        elif "price drop" in name_lower or "discount" in name_lower or "deal" in name_lower:
            status = "price_drop"
            price = 9.99
            original_price = 14.99
            coupon_code = "CQDEAL15"
        elif "aspirin" in name_lower:
            status = "in_stock"
            price = 4.99
        elif "levetiracetam" in name_lower:
            status = "out_of_stock"
            price = None
        elif "hydrocortisone" in name_lower:
            status = "price_drop"
            price = 6.80
            original_price = 8.50
            coupon_code = "SKINCARE20"
        elif "moisturex" in name_lower:
            status = "in_stock"
            price = 11.20
        elif "upma" in name_lower or "rava" in name_lower or "semolina" in name_lower:
            status = "in_stock"
            price = 3.50
        elif "eczema" in name_lower:
            status = "price_drop"
            price = 22.00
            original_price = 28.00
            coupon_code = "ECZEMA15"
            
        return {
            "status": status,
            "price": price,
            "original_price": original_price,
            "coupon_code": coupon_code,
            "confidence": 100
        }

    def _trigger_cart_notifications(self, db: Session, patient_id: int, item: CartItem, old_status: str) -> None:
        """Fire notifications when a cart item's availability changes."""
        status_labels = {
            "in_stock": "In Stock",
            "out_of_stock": "Out of Stock",
            "price_drop": "Price Drop Deal Available",
        }
        
        new_label = status_labels.get(item.status, item.status)
        
        if item.status == "in_stock":
            body = f"Good news! Your tracked product '{item.item_name}' is back in stock! Buy it now: {item.source_url or 'nexus_ai Cart'}"
        elif item.status == "price_drop":
            body = f"Price drop alert! '{item.item_name}' is now available for ${item.price:.2f} (originally ${item.original_price:.2f}). Use code {item.coupon_code}."
        else:
            body = f"Status update: '{item.item_name}' is currently {new_label}."
            
        # Fire alerts through notifications channels
        # 1. SMS
        self.notification_adapter.send(channel="sms", message_body=body)
        
        # 2. Gmail
        self.notification_adapter.send(channel="gmail", message_body=body)
        
        # 3. Web notification inside app
        web_notif = Notification(
            patient_id=patient_id,
            channel="web",
            message_type="cart_alert",
            body=body,
            delivery_status="sent"
        )
        db.add(web_notif)
