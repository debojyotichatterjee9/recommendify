import uuid
from app.models import Product
from app.schemas import ProductOut

def test_product_out_from_orm_product():
    product_id = uuid.uuid4()
    # Create an instance of the Product ORM model
    p = Product(
        id=product_id,
        external_id="ext-123",
        business_id="bus-456",
        product_type="item",
        name="Test Item",
        description=None,  # Testing the `p.description or ""` fallback
    )
    p.attributes = {"color": "blue"}
    
    # Use the classmethod to convert to the Pydantic model
    p_out = ProductOut.from_orm_product(p)
    
    # Verify the Pydantic model is correctly formed
    assert p_out.id == product_id
    assert p_out.external_id == "ext-123"
    assert p_out.business_id == "bus-456"
    assert p_out.product_type == "item"
    assert p_out.name == "Test Item"
    assert p_out.description == ""  # Should default to empty string if None
    assert p_out.attributes == {"color": "blue"}
