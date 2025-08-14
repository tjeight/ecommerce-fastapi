from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from admin_schemas import AddressCreate, AddressOut, ProductOut
from auth import get_current_user, user_required
from database import get_db
from models import (
    Brand,
    Cart,
    Category,
    Coupon,
    Order,
    OrderItem,
    Product,
    SubCategory,
    UserAddress,
    Variant,
    WishList,
)
from users_schemas import AddCart, OrderSchemaOut, OrderUpdateStatusSchema, ProductsList


user_router = APIRouter()


@user_router.get("/", response_model=list[ProductsList])
def read_root(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@user_router.get("/getproduct/{id}", response_model=ProductOut)
def get_all_products(
    id: int, current_user=Depends(user_required), db: Session = Depends(get_db)
):
    found_product = db.query(Product).filter(Product.product_id == id).first()
    if not found_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product Not Found"
        )
    return found_product


@user_router.get("/products/filter/price", response_model=list[ProductsList])
def filter_by_price(min_price: float, max_price: float, db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .filter(Product.product_price >= min_price, Product.product_price <= max_price)
        .all()
    )
    return products


@user_router.get(
    "/products/filter/category/{category_id}", response_model=list[ProductsList]
)
def filter_by_category(category_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.category_id == category_id).all()
    return products


@user_router.get("/products/filter/brand/{brand_id}", response_model=list[ProductsList])
def filter_by_brand(brand_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.brand_id == brand_id).all()
    return products


@user_router.get("/search")
def search_product(
    query: str, db: Session = Depends(get_db), current_user=Depends(user_required)
):
    search_term = f"%{query.strip()}%"

    results = (
        db.query(Product)
        .outerjoin(Brand, Product.brand_id == Brand.brand_id)
        .outerjoin(Category, Product.category_id == Category.category_id)
        .outerjoin(SubCategory, Product.sub_category_id == SubCategory.sub_category_id)
        .filter(
            or_(
                func.lower(Product.product_name).like(search_term.lower()),
                func.lower(Product.product_description).like(search_term.lower()),
                func.lower(Brand.brand_name).like(search_term.lower()),
                func.lower(Category.category_name).like(search_term.lower()),
                func.lower(SubCategory.sub_category_name).like(search_term.lower()),
            )
        )
        .all()
    )

    return results


@user_router.post("/cart")
def add_to_cart(
    request: AddCart, current_user=Depends(user_required), db: Session = Depends(get_db)
):
    cuser_id = current_user.user_id

    found_product = (
        db.query(Product).filter(Product.product_id == request.product_id).first()
    )
    if not found_product:
        return JSONResponse(status_code=404, content={"detail": "Product Not Found"})

    found_variant = (
        db.query(Variant).filter(Variant.variant_id == request.variant_id).first()
    )
    if not found_variant:
        return JSONResponse(status_code=404, content={"detail": "Variant Not Found"})

    if found_variant.product_id != request.product_id:
        return JSONResponse(
            status_code=400, content={"detail": "Variant Not belong to the product"}
        )

    if found_variant.stock < request.quantity:
        return JSONResponse(status_code=400, content={"detail": "No stock"})

    cart_item = (
        db.query(Cart)
        .filter_by(
            user_id=cuser_id,
            variant_id=request.variant_id,
            product_id=request.product_id,
        )
        .first()
    )

    if cart_item:
        cart_item.quantity += request.quantity
    else:
        cart_item = Cart(
            user_id=cuser_id,
            product_id=request.product_id,
            variant_id=request.variant_id,
            quantity=request.quantity,
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)
    return JSONResponse(status_code=201, content={"message": "Item added to the cart"})


@user_router.get("/cart")
def show_cart(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user_id = current_user.user_id

    fetch_items = (
        db.query(Cart, Variant, Product)
        .join(Variant, Cart.variant_id == Variant.variant_id)
        .join(Product, Cart.product_id == Product.product_id)
        .filter(Cart.user_id == user_id)
        .all()
    )

    if not fetch_items:
        return JSONResponse(
            status_code=200,
            content={"message": "Cart is empty", "items": [], "total_cart_value": 0},
        )

    cart_response = []
    total_cart_value = 0

    for cart, variant, product in fetch_items:
        subtotal = float(variant.price) * cart.quantity
        total_cart_value += subtotal

        cart_response.append(
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "product_image": product.prod_image,
                "variant_id": variant.variant_id,
                "variant_name": variant.name,
                "price": float(variant.price),
                "quantity": cart.quantity,
                "subtotal": subtotal,
            }
        )

    return JSONResponse(
        status_code=200,
        content={"items": cart_response, "total_cart_value": total_cart_value},
    )


@user_router.put("/cart/{product_id}")
def update_cart(
    product_id: int,
    quantity: int,
    current_user=Depends(user_required),
    db: Session = Depends(get_db),
):
    user_id = current_user.user_id
    fetch_product = (
        db.query(Cart)
        .filter(Cart.user_id == user_id, Cart.product_id == product_id)
        .first()
    )

    if not fetch_product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})

    if quantity <= 0:
        db.delete(fetch_product)
        db.commit()
        return JSONResponse(
            status_code=200, content={"message": "Product removed from the Cart"}
        )

    fetch_product.quantity = quantity
    db.commit()
    db.refresh(fetch_product)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Cart updated successfully",
            "product_id": fetch_product.product_id,
            "quantity": fetch_product.quantity,
        },
    )


@user_router.delete("/cart/{product_id}")
def delete_product(
    product_id: int, current_user=Depends(user_required), db: Session = Depends(get_db)
):
    user_id = current_user.user_id
    fetch_product = (
        db.query(Cart)
        .filter(Cart.user_id == user_id, Cart.product_id == product_id)
        .first()
    )
    if not fetch_product:
        return JSONResponse(status_code=404, content={"detail": "Product Not Found"})

    db.delete(fetch_product)
    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Product deleted successfully"}
    )


@user_router.post("/wishlist/{product_id}")
def add_product_wishlist(
    product_id: int, current_user=Depends(user_required), db: Session = Depends(get_db)
):
    user_id = current_user.user_id

    # Validate the product
    fetch_product = db.query(Product).filter(Product.product_id == product_id).first()
    if not fetch_product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})

    # Check if already in wishlist
    existing_item = (
        db.query(WishList)
        .filter(WishList.user_id == user_id, WishList.product_id == product_id)
        .first()
    )
    if existing_item:
        return JSONResponse(
            status_code=400,
            content={"detail": "Product already in wishlist"},
        )

    # Add to wishlist
    new_wishlist_item = WishList(user_id=user_id, product_id=product_id)
    db.add(new_wishlist_item)
    db.commit()
    db.refresh(new_wishlist_item)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Product added to wishlist",
        },
    )


@user_router.get("/wishlist")
def show_wishlist(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user_id = current_user.user_id

    fetch_list = (
        db.query(Product.product_id, Product.product_name)
        .join(WishList, WishList.product_id == Product.product_id)
        .filter(WishList.user_id == user_id)
        .all()
    )

    if not fetch_list:
        return JSONResponse(status_code=404, content={"detail": "WishList not found"})

    return JSONResponse(
        status_code=200,
        content=[
            {"product_id": product.product_id, "product_name": product.product_name}
            for product in fetch_list
        ],
    )


@user_router.delete("/wishlist/{product_id}")
def remove_product(
    product_id: int, current_user=Depends(user_required), db: Session = Depends(get_db)
):
    user_id = current_user.user_id
    found_product = (
        db.query(WishList)
        .filter(WishList.user_id == user_id, WishList.product_id == product_id)
        .first()
    )
    if not found_product:
        return JSONResponse(status_code=404, content={"detail": "Product Not Found"})

    db.delete(found_product)
    db.commit()

    return JSONResponse(
        status_code=200, content={"message": "Product deleted successfully"}
    )


@user_router.post("/apply-coupon")
def apply_coupon(
    code: str,
    order_amount: float,
    db: Session = Depends(get_db),
    current_user=Depends(user_required),
):
    coupon = db.query(Coupon).filter(Coupon.code == code).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Check if coupon is active and within date
    now = datetime.utcnow()
    if not coupon.is_active or now < coupon.start_date or now > coupon.end_date:
        raise HTTPException(status_code=400, detail="Coupon is not valid right now")

    # Check minimum order amount
    if order_amount < coupon.min_order_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount should be {coupon.min_order_amount}",
        )

    # Check usage limit (overall)
    if coupon.usage_limit is not None:
        total_used = db.query(Order).filter(Order.coupon_id == coupon.coupon_id).count()
        if total_used >= coupon.usage_limit:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    # Check usage per user
    user_used = (
        db.query(Order)
        .filter(
            Order.coupon_id == coupon.coupon_id, Order.user_id == current_user.user_id
        )
        .count()
    )
    if user_used >= coupon.usage_per_user:
        raise HTTPException(
            status_code=400,
            detail="You have already used this coupon the maximum allowed times",
        )

    # Calculate discount
    if coupon.discount_type == "percentage":
        discount = (coupon.discount_value / 100) * order_amount
    else:  # fixed amount
        discount = coupon.discount_value

    return {
        "message": "Coupon applied successfully",
        "coupon_code": coupon.code,
        "discount": discount,
        "final_amount": order_amount - discount,
    }


def validate_coupon(
    coupon_code: str, user_id: int, total_amount: float, db: Session
) -> Coupon:
    # 1. Check if coupon exists
    coupon = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # 2. Check if coupon is active and within date range
    now = datetime.utcnow()
    if coupon.start_date and now < coupon.start_date:
        raise HTTPException(status_code=400, detail="Coupon not yet active")
    if coupon.end_date and now > coupon.end_date:
        raise HTTPException(status_code=400, detail="Coupon expired")
    if not coupon.is_active:
        raise HTTPException(status_code=400, detail="Coupon is inactive")

    # 3. Check min purchase requirement
    if coupon.min_purchase_amount and total_amount < coupon.min_purchase_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum purchase of {coupon.min_purchase_amount} required",
        )

    # 4. Check usage limits
    if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    # 5. Check if user already used this coupon
    user_used_coupon = (
        db.query(Order)
        .filter(Order.user_id == user_id, Order.coupon_id == coupon.coupon_id)
        .first()
    )
    if user_used_coupon:
        raise HTTPException(status_code=400, detail="You have already used this coupon")

    return coupon


@user_router.post("/order")
def create_order(
    current_user=Depends(user_required), coupon_code=None, db: Session = Depends(get_db)
):
    user_id = current_user.user_id

    # 1. Fetch cart items
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    if not cart_items:
        return JSONResponse(status_code=400, content={"detail": "Cart is empty"})

    # 2. Calculate total
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    # 3. Apply coupon if provided
    discount_amount = 0
    coupon_id = None
    if coupon_code:
        coupon = validate_coupon(coupon_code, user_id, total_amount)
        discount_amount = coupon.discount_amount
        coupon_id = coupon.coupon_id

    # 4. Create order
    order = Order(
        user_id=user_id,
        coupon_id=coupon_id,
        totol_amount=total_amount,
        discount_amount=discount_amount,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 5. Create OrderItems
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.order_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            price=item.product.price,
        )
        db.add(order_item)

    # 6. Clear cart
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    db.commit()

    return JSONResponse(status_code=201, content={"order": order.__dict__})


@user_router.get("/order", response_model=List[OrderSchemaOut])
def get_my_order(current_user=Depends(user_required), db: Session = Depends(get_db)):
    user_id = current_user.user_id
    found_order = db.query(Order).filter(Order.user_id == user_id).all()
    if not found_order:
        return JSONResponse(status_code=404, content={"detail": "Order Not Found"})
    return JSONResponse(
        status_code=200, content=[order.__dict__ for order in found_order]
    )


@user_router.get("/order/{order_id}", response_model=OrderSchemaOut)
def get_order(
    order_id: int, db: Session = Depends(get_db), current_user=Depends(user_required)
):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id, Order.user_id == current_user.user_id)
        .first()
    )
    if not order:
        return JSONResponse(status_code=404, content={"detail": "Order not found"})
    return JSONResponse(status_code=200, content=order.__dict__)


@user_router.put("/order/{order_id}")
def update_order_status(
    order_id: int, update_data: OrderUpdateStatusSchema, db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return JSONResponse(status_code=404, content={"detail": "Order not found"})

    order.status = update_data.status
    db.commit()
    return JSONResponse(
        status_code=200, content={"message": f"Order status updated to {order.status}"}
    )


@user_router.delete("/order/{order_id}")
def delete_order(
    order_id: int, db: Session = Depends(get_db), current_user=Depends(user_required)
):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id, Order.user_id == current_user.user_id)
        .first()
    )
    if not order:
        return JSONResponse(status_code=404, content={"detail": "Order not found"})

    if order.status != "pending":
        return JSONResponse(
            status_code=400, content={"detail": "Only pending orders can be deleted"}
        )

    db.delete(order)
    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Order deleted successfully"}
    )


@user_router.post("/address", response_model=AddressOut)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    new_address = UserAddress(
        user_id=current_user.user_id, address=address_data.address
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


# 📄 Get All Addresses for Current User
@user_router.get("/address", response_model=list[AddressOut])
def get_addresses(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    addresses = (
        db.query(UserAddress).filter(UserAddress.user_id == current_user.user_id).all()
    )
    return addresses


# ✏️ Update Address
@user_router.put("/address/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    address = (
        db.query(UserAddress)
        .filter(
            UserAddress.address_id == address_id,
            UserAddress.user_id == current_user.user_id,
        )
        .first()
    )

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if address_data.address is not None:
        address.address = address_data.address

    db.commit()
    db.refresh(address)
    return address


# ❌ Delete Address
@user_router.delete("/address/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    address = (
        db.query(UserAddress)
        .filter(
            UserAddress.address_id == address_id,
            UserAddress.user_id == current_user.user_id,
        )
        .first()
    )

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}
