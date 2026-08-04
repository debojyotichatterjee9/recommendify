import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models import Base, User, Product
import uuid

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_multi_tenancy_constraints(db_session):
    # Same email, different business_id -> Should pass
    u1 = User(name="User 1", email="test@example.com", external_id="ext1", business_id="biz1")
    u2 = User(name="User 2", email="test@example.com", external_id="ext2", business_id="biz2")
    db_session.add(u1)
    db_session.add(u2)
    db_session.commit()

    # Same email, same business_id -> Should fail
    u3 = User(name="User 3", email="test@example.com", external_id="ext3", business_id="biz1")
    db_session.add(u3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Same external_id, different business_id -> Should pass
    u4 = User(name="User 4", email="other1@example.com", external_id="ext1", business_id="biz2")
    db_session.add(u4)
    db_session.commit()

    # Same external_id, same business_id -> Should fail
    u5 = User(name="User 5", email="other2@example.com", external_id="ext1", business_id="biz1")
    db_session.add(u5)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_product_multi_tenancy_constraints(db_session):
    # Same name, different business_id -> Should pass
    p1 = Product(name="Product A", external_id="p1", business_id="biz1", product_type="t")
    p2 = Product(name="Product A", external_id="p2", business_id="biz2", product_type="t")
    db_session.add(p1)
    db_session.add(p2)
    db_session.commit()

    # Same name, same business_id -> Should fail
    p3 = Product(name="Product A", external_id="p3", business_id="biz1", product_type="t")
    db_session.add(p3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Same external_id, different business_id -> Should pass
    p4 = Product(name="Product B", external_id="p1", business_id="biz2", product_type="t")
    db_session.add(p4)
    db_session.commit()

    # Same external_id, same business_id -> Should fail
    p5 = Product(name="Product C", external_id="p1", business_id="biz1", product_type="t")
    db_session.add(p5)
    with pytest.raises(IntegrityError):
        db_session.commit()
