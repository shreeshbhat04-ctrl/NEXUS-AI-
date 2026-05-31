import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from nexus_ai.db.models import Base, CartItem, Patient, Notification
from nexus_ai.services.shopping_service import ShoppingService

def test_shopping_service_flow() -> None:
    # Set up in-memory SQLite database for self-contained testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        # Create a mock patient
        patient = Patient(id=999, full_name="Test Patient", preferred_language="en")
        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Create cart items
        item_in_stock = CartItem(
            patient_id=999,
            item_name="Metformin price drop test",
            item_type="medicine",
            price=15.00,
            status="checking"
        )
        item_out_of_stock = CartItem(
            patient_id=999,
            item_name="Levetiracetam out of stock test",
            item_type="medicine",
            price=None,
            status="checking"
        )
        db.add(item_in_stock)
        db.add(item_out_of_stock)
        db.commit()

        service = ShoppingService()

        # Run check availability
        service.check_cart_availability(db, patient_id=999)

        # Retrieve items
        db.refresh(item_in_stock)
        db.refresh(item_out_of_stock)

        # Verify fallback states assigned by mock helper
        assert item_in_stock.status == "price_drop"
        assert item_in_stock.price == 9.99
        assert item_out_of_stock.status == "out_of_stock"

        # Verify notification created
        notifications = db.query(Notification).filter(Notification.patient_id == 999).all()
        assert len(notifications) > 0

        # Perform checkout on in_stock / price_drop item
        checkout_res = service.checkout_item(db, patient_id=999, item_id=item_in_stock.id)
        assert checkout_res["success"] is True
        assert checkout_res["item_name"] == "Metformin price drop test"

        # Verify item status updated to purchased
        db.refresh(item_in_stock)
        assert item_in_stock.status == "purchased"
