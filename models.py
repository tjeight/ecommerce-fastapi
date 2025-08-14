from datetime import datetime
from database import Base
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    password = Column(String)
    role = Column(String, default="user")

    cart = relationship("Cart", back_populates="user")
    wishlist = relationship("WishList", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Brand(Base):
    __tablename__ = "brands"
    brand_id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, nullable=False, unique=True)
    short_name = Column(String, nullable=True)
    short_description = Column(String(50), nullable=True)
    long_description = Column(String(50), nullable=True)
    image = Column(String, nullable=True)

    products = relationship("Product", back_populates="brand")


class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(50), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))

    brand = relationship("Brand", backref="categories")
    products = relationship("Product", back_populates="category")


class SubCategory(Base):
    __tablename__ = "subcategories"
    sub_category_id = Column(Integer, primary_key=True, index=True)
    sub_category_name = Column(String(50), nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))

    brand = relationship("Brand", backref="subcategories")
    category = relationship("Category", backref="subcategories")
    products = relationship("Product", back_populates="sub_category")


class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(50), nullable=False, unique=True)
    prod_image = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    product_description = Column(Text, nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))
    sub_category_id = Column(Integer, ForeignKey("subcategories.sub_category_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    brand = relationship("Brand", back_populates="products")
    sub_category = relationship("SubCategory", back_populates="products")
    category = relationship("Category", back_populates="products")


class Attribute(Base):
    __tablename__ = "attributes"
    attribute_id = Column(Integer, primary_key=True, index=True)
    attribute_name = Column(String, nullable=False)  # e.g., Color, Size


class Term(Base):
    __tablename__ = "terms"
    term_id = Column(Integer, primary_key=True, index=True)
    value = Column(String, nullable=False)  # e.g., Black, Pro
    attribute_id = Column(Integer, ForeignKey("attributes.attribute_id"))


class ProductAssignment(Base):
    __tablename__ = "product_assignments"
    assignment_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    term_id = Column(Integer, ForeignKey("terms.term_id"), nullable=False)


class Variant(Base):
    __tablename__ = "variants"
    variant_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    name = Column(String, nullable=False)  # e.g., "Black Pro 128GB"
    sku = Column(String, unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    available = Column(Boolean, default=True)


# '''
# class Attribute(Base):
#     __tablename__ = "attributes"
#     attribute_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)   # e.g., Color, Version
#     value = Column(String, nullable=False)  # e.g., Black, Pro


# class Product(Base):
#     __tablename__ = "products"
#     product_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)


# class ProductAssignment(Base):
#     __tablename__ = "product_assignments"
#     assignment_id = Column(Integer, primary_key=True, index=True)
#     product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
#     attribute_id = Column(Integer, ForeignKey("attributes.attribute_id"), nullable=False)
#     stock = Column(Integer, default=0)
#     available = Column(Boolean, default=True)


# class Variant(Base):
#     __tablename__ = "variants"
#     variant_id = Column(Integer, primary_key=True, index=True)
#     product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
#     # This could be many-to-many if you want multiple assignments per variant
#     assignment_id = Column(Integer, ForeignKey("product_assignments.assignment_id"), nullable=False)
# '''


class Cart(Base):
    __tablename__ = "carts"
    cart_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.variant_id"), nullable=False)
    quantity = Column(Integer, default=1)

    user = relationship("Users", back_populates="cart")
    product = relationship("Product")
    variant = relationship("Variant")


class WishList(Base):
    __tablename__ = "wishlist"
    wishlist_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"))

    user = relationship("Users", back_populates="wishlist")
    product = relationship("Product")


class Coupon(Base):
    __tablename__ = "coupons"
    coupon_id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    discount_type = Column(String, nullable=False)  # percentage/fixed
    discount_value = Column(Float, nullable=False)
    min_order_amount = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    usage_limit = Column(Integer, default=None)
    usage_per_user = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="coupon")


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    coupon_id = Column(Integer, ForeignKey("coupons.coupon_id"), nullable=True)
    totol_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="orders")
    coupon = relationship("Coupon", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    variant_id = Column(Integer, ForeignKey("variants.variant_id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # price at time of purchase

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("Variant")


class BlackListedToken(Base):
    __tablename__ = "blacklisted_token"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, nullable=False, unique=True)
    black_listed_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    token = Column(String, nullable=False)  # JWT or random session token
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("Users")


class UserAddress(Base):
    __tablename__ = "user_address"
    address_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    address = Column(String)

    user = relationship("Users")
