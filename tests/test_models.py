import json
from app.models import Product

def test_product_attributes_getter_setter():
    product = Product(name="Test Product", external_id="p1", business_id="b1", product_type="item")
    
    # Initial state
    assert product.attributes == {}
    
    # Test setting attributes
    test_dict = {"color": "red", "size": "M"}
    product.attributes = test_dict
    
    # Verify getter returns the exact same dict
    assert product.attributes == test_dict
    
    # Verify the underlying JSON string column is updated
    assert json.loads(product._attributes) == test_dict
    
    # Test getting attributes when only _attributes string is set (e.g. from DB)
    product_from_db = Product()
    product_from_db._attributes = json.dumps({"weight": 10})
    
    # The property should parse and cache the JSON
    assert product_from_db.attributes == {"weight": 10}
