from pydantic import BaseModel


class ProductsList(BaseModel):
    product_name: str
    prod_image: str
    product_price: float
    product_description: str


class AddCart(BaseModel):
    product_id: int
    variant_id: int
    quantity: int


class CartOut(BaseModel):
    product_name: str


class WishListOut:
    pass


class OrderSchemaOut(BaseModel):
    order_id: int
    user_id: int
    coupon_id: int
    totol_amount: int
    discount_amount: float
    status: str


class OrderUpdateStatusSchema(BaseModel):
    status: str
