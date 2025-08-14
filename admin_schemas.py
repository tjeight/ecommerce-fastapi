from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    token: str


class Brands(BaseModel):
    brand_name: str
    short_name: str
    short_description: str
    long_description: str
    image: str


class BrandOut(BaseModel):
    brand_name: str

    class Config:
        from_attributes = True


class User(BaseModel):
    user_id: int
    email: str
    role: str


class CategoryCreate(BaseModel):
    category_name: str
    brand_id: int


class CategoryOut(BaseModel):
    category_name: str


class SubCategoryCreate(BaseModel):
    sub_category_name: str
    category_id: int
    brand_id: int


class SubCategoryOut(BaseModel):
    sub_category_name: str


class ProductOut(BaseModel):
    product_name: str


class AttributeOut(BaseModel):
    attribute_name: str


class ProductCreate(BaseModel):
    product_name: str
    prod_image: str
    product_price: float
    product_description: str
    brand_id: int
    sub_category_id: int
    category_id: int


class AttributeCreate(BaseModel):
    attribute_name: str


class ProductAssignmentCreate(BaseModel):
    product_id: int
    term_id: int


class TermCreate(BaseModel):
    value: str
    attribute_id: int


class Variants(BaseModel):
    product_id: int
    name: str  # e.g., "Black Pro 128GB"
    sku: str
    price: float
    stock: int
    available: bool


class TermOut(BaseModel):
    value: str


class ProductAssignOut(BaseModel):
    assignment_id: int
    product_id: int
    term_id: int


class VariantOut(BaseModel):
    name: str


class CouponBase(BaseModel):
    code: str
    discount_type: str  # "percentage" or "fixed"
    discount_value: float
    min_order_amount: Optional[float] = 0.0
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = None
    usage_per_user: Optional[int] = 1
    is_active: Optional[bool] = True


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    usage_limit: Optional[int] = None
    usage_per_user: Optional[int] = None
    is_active: Optional[bool] = None


class CouponResponse(CouponBase):
    coupon_id: int

    class Config:
        from_attributes = True


class AddressBase(BaseModel):
    address: str


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address: Optional[str] = None


class AddressOut(AddressBase):
    address_id: int
    user_id: int

    class Config:
        from_attributes = True
