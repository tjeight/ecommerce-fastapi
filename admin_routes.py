from datetime import datetime
from jose import jwt
from typing import Optional
from fastapi import (
    Depends,
    APIRouter,
    File,
    Header,
    UploadFile,
    status,
    HTTPException,
    Form,
)
from auth import get_current_user, o_auth_schemes
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from admin_schemas import (
    AttributeCreate,
    Brands,
    BrandOut,
    CategoryCreate,
    CategoryOut,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    ProductAssignOut,
    ProductAssignmentCreate,
    SubCategoryCreate,
    TermOut,
    Variants,
    TermCreate,
)
from database import get_db
from models import (
    Brand,
    Coupon,
    UserSession,
    Users,
    Category,
    SubCategory,
    Variant,
    Attribute,
    ProductAssignment,
    Product,
    Term,
    BlackListedToken,
)
from auth import create_access_token, admin_required
import os

# from utils import save_uploaded_files
from pathlib import Path
from uuid import uuid4


UPLOAD_DIR = "/uploads/brand_images/"

admin_router = APIRouter(tags=["admin"])

pw_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_BRAND_DIR = "uploads/product/images"


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_BRAND_DIR, exist_ok=True)


def save_uploaded_files(image: UploadFile) -> str:
    file_ext = Path(image.filename).suffix.lower()
    unique_filename = f"{uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    # Save file - simpler way
    with open(file_path, "wb") as f:
        f.write(image.file.read())
    return file_path


def save_product_uploaded_files(image: UploadFile) -> str:
    file_ext = Path(image.filename).suffix.lower()
    unique_file_name = f"{uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_BRAND_DIR, unique_file_name)
    with open(file_path, "wb") as f:
        f.write(image.file.read())
    return file_path


@admin_router.post("/signup")
def create_user(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    username = request.username
    hashed_password = pw_context.hash(request.password)

    # Check if user already exists
    found_user = db.query(Users).filter(Users.email == username).first()
    if found_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Check if this is the first user → make admin
    is_first_user = db.query(Users).count() == 0
    role = "admin" if is_first_user else "user"

    # Create new user
    new_user = Users(email=username, password=hashed_password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "role": role}


@admin_router.post("/login")
def login_user(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    user_agent: str = Header(None),
    x_forwarded_for: str = Header(None),
):
    username = request.username
    password = request.password

    found_user = db.query(Users).filter(Users.email == username).first()
    if not found_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found, create one"
        )

    if not pw_context.verify(password, found_user.password):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Incorrect password"
        )

    token = create_access_token({"sub": found_user.email, "role": found_user.role})

    # Extract IP (if behind proxy use x-forwarded-for)
    ip_address = x_forwarded_for.split(",")[0] if x_forwarded_for else None

    # Create session record
    new_session = UserSession(
        user_id=found_user.user_id,
        token=token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(new_session)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}


@admin_router.post("/logout")
def logout(
    token: str = Depends(o_auth_schemes),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1️⃣ Find the active session
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user.user_id,
            UserSession.is_active,
            UserSession.token == token,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # 2️⃣ Mark as logged out
    session.is_active = False
    session.logout_at = datetime.utcnow()
    db.commit()

    # 3️⃣ Blacklist the JWT (optional security step)
    expires_at = datetime.utcfromtimestamp(
        jwt.decode(token, options={"verify_signature": False})["exp"]
    )
    blacklist_entry = BlackListedToken(token=token, expires_at=expires_at)
    db.add(blacklist_entry)
    db.commit()

    return {"message": "Successfully logged out"}


# CRUD operations of the brand
@admin_router.post("/brand", response_model=Brands, tags=["brands"])
def add_brand(
    brand_name: str = Form(...),
    short_name: str = Form(None),
    short_description: str = Form(None),
    long_description: str = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_brand = db.query(Brand).filter(Brand.brand_name == brand_name).first()
    if found_brand:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Brand already exists"},
        )

    image_path = None
    if image and image.filename:
        image_path = save_uploaded_files(image)

    new_brand = Brand(
        brand_name=brand_name,
        short_name=short_name,
        short_description=short_description,
        long_description=long_description,
        image=image_path,
    )
    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)
    return new_brand


@admin_router.get("/brand", response_model=list[BrandOut])
def get_all_brands(db: Session = Depends(get_db), cuurent_user=Depends(admin_required)):
    brands = db.query(Brand).all()
    return brands


@admin_router.get("/brand/{id}", response_model=BrandOut)
def get_brand_by_id(
    id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)
):
    found_brand = db.query(Brand).filter(Brand.brand_id == id).first()
    if not found_brand:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Brand not found"},
        )
    return found_brand


@admin_router.put("/brand/{id}")
def update_brand(
    id: int,
    brand_name: str = Form(...),
    short_name: str = Form(None),
    short_description: str = Form(None),
    long_description: str = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_brand = db.query(Brand).filter(Brand.brand_id == id).first()
    if not found_brand:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Brand not found"},
        )

    if image and image.filename:
        image_path = save_uploaded_files(image)
        found_brand.image = image_path

    found_brand.brand_name = brand_name
    found_brand.short_name = short_name
    found_brand.short_description = short_description
    found_brand.long_description = long_description

    db.commit()
    return {"message": "Updated sucessfully", "brand": found_brand.brand_name}


@admin_router.delete("/brand/{id}")
def delete_brand(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_brand = db.query(Brand).filter(Brand.brand_id == id).first()
    if not found_brand:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Brand not found"},
        )
    db.delete(found_brand)
    db.commit()
    return {"message": "Brand Deleted Successfully"}


# CRUD operations of the category
# give name category and call all the requests on same name


@admin_router.post("/category")
def add_category(
    request: CategoryCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_category = (
        db.query(Category)
        .filter(Category.category_name == request.category_name)
        .first()
    )
    if found_category:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Category Already Exists"},
        )

    new_category = Category(
        brand_id=request.brand_id, category_name=request.category_name
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Category added successfully",
            "category": {
                "id": new_category.category_id,
                "brand_id": new_category.brand_id,
                "category_name": new_category.category_name,
            },
        },
    )


@admin_router.get("/category", response_model=list[CategoryOut])
def get_all_categories(
    current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    all_categories = db.query(Category).all()
    return all_categories


@admin_router.get("/category/{id}", response_model=CategoryOut)
def get_category_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_category = db.query(Category).filter(Category.category_id == id).first()
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Category does not exist"},
        )
    return found_category


@admin_router.put("/category/{id}")
def update_category(
    id: int,
    request: CategoryCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_category = db.query(Category).filter(Category.category_id == id).first()
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Category not found"},
        )

    found_category.brand_id = request.brand_id
    found_category.category_name = request.category_name
    db.commit()
    db.refresh(found_category)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Updated Successfully",
            "category": found_category.category_name,
        },
    )


@admin_router.delete("/category/{id}")
def delete_category(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_category = db.query(Category).filter(Category.category_id == id).first()
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Category not found"},
        )

    db.delete(found_category)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Category deleted successfully"},
    )


# +++++++++++++++++++++++++++++++++++++++
#   |
# +++++++++++++++++++++++++++++++++++++++


@admin_router.post("/subcategory")
def add_sub_category(
    request: SubCategoryCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_sub = (
        db.query(SubCategory)
        .filter(SubCategory.sub_category_name == request.sub_category_name)
        .first()
    )
    if found_sub:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Sub Category Exists"},
        )

    new_sub_category = SubCategory(
        sub_category_name=request.sub_category_name,
        category_id=request.category_id,
        brand_id=request.brand_id,
    )
    db.add(new_sub_category)
    db.commit()
    db.refresh(new_sub_category)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Sub Category added successfully",
            "subcategory": {
                "id": new_sub_category.sub_category_id,
                "name": new_sub_category.sub_category_name,
                "category_id": new_sub_category.category_id,
                "brand_id": new_sub_category.brand_id,
            },
        },
    )


@admin_router.get("/subcategory")
def get_all_subcategories(
    current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    subcategories = db.query(SubCategory).all()
    return subcategories


@admin_router.get("/subcategory/{id}")
def get_subcategory_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_category = (
        db.query(SubCategory).filter(SubCategory.sub_category_id == id).first()
    )
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Sub Category not found"},
        )
    return found_category


@admin_router.put("/subcategory/{id}")
def update_subcategory(
    id: int,
    request: SubCategoryCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_category = (
        db.query(SubCategory).filter(SubCategory.sub_category_id == id).first()
    )
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Sub Category not found"},
        )

    found_category.sub_category_name = request.sub_category_name
    found_category.category_id = request.category_id
    found_category.brand_id = request.brand_id
    db.commit()
    db.refresh(found_category)

    return found_category


@admin_router.delete("/subcategory/{id}")
def delete_subcategory(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_category = (
        db.query(SubCategory).filter(SubCategory.sub_category_id == id).first()
    )
    if not found_category:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Sub Category not found"},
        )

    db.delete(found_category)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Sub category deleted successfully"},
    )


@admin_router.post("/product")
def add_product(
    product_name: str = Form(...),
    prod_image: UploadFile = File(...),
    product_price: float = Form(...),
    product_description: str = Form(...),
    brand_id: int = Form(...),
    sub_category_id: int = Form(...),
    category_id: int = Form(...),
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_product = (
        db.query(Product).filter(Product.product_name == product_name).first()
    )
    if found_product:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Product Already Exists"},
        )

    image_path = None
    if prod_image and prod_image.filename:
        image_path = save_product_uploaded_files(image=prod_image)

    new_product = Product(
        product_name=product_name,
        prod_image=image_path,
        product_price=product_price,
        product_description=product_description,
        brand_id=brand_id,
        sub_category_id=sub_category_id,
        category_id=category_id,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Product added successfully",
            "product": {
                "id": new_product.product_id,
                "name": new_product.product_name,
                "price": new_product.product_price,
                "description": new_product.product_description,
                "image": new_product.prod_image,
                "brand_id": new_product.brand_id,
                "subcategory_id": new_product.sub_category_id,
                "category_id": new_product.category_id,
            },
        },
    )


@admin_router.get("/product")
def get_all_products(
    current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    all_products = db.query(Product).all()
    return all_products


@admin_router.get("/product/{id}")
def get_product_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_product = db.query(Product).filter(Product.product_id == id).first()
    if not found_product:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Product Not Found"},
        )
    return found_product


@admin_router.put("/product/{id}")
def update_product(
    id: int,
    product_name: str = Form(...),
    prod_image: UploadFile = File(None),
    product_price: float = Form(...),
    product_description: str = Form(...),
    brand_id: int = Form(...),
    sub_category_id: int = Form(...),
    category_id: int = Form(...),
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_product = db.query(Product).filter(Product.product_id == id).first()

    if not found_product:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Product Not Found"},
        )

    if prod_image and prod_image.filename:
        image_path = save_product_uploaded_files(prod_image)
        found_product.prod_image = image_path

    found_product.product_name = product_name
    found_product.brand_id = brand_id
    found_product.product_price = product_price
    found_product.product_description = product_description
    found_product.sub_category_id = sub_category_id
    found_product.category_id = category_id

    db.commit()
    db.refresh(found_product)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Product Updated Successfully",
            "product": {
                "id": found_product.product_id,
                "name": found_product.product_name,
            },
        },
    )


@admin_router.delete("/product/{id}")
def delete_product(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_product = db.query(Product).filter(Product.product_id == id).first()

    if not found_product:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Product Not Found"},
        )

    db.delete(found_product)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Product Deleted Successfully"},
    )


@admin_router.post("/attribute")
def add_attributes(
    request: AttributeCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_attribute = (
        db.query(Attribute)
        .filter(Attribute.attribute_name == request.attribute_name)
        .first()
    )
    if found_attribute:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Attribute Already Exists"},
        )

    new_attribute = Attribute(attribute_name=request.attribute_name)
    db.add(new_attribute)
    db.commit()
    db.refresh(new_attribute)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Attribute added successfully",
            "attribute": {
                "id": new_attribute.attribute_id,
                "name": new_attribute.attribute_name,
            },
        },
    )


@admin_router.get("/attribute")
def get_all_attributes(
    current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    all_attributes = db.query(Attribute).all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "attributes": [
                {"id": attr.attribute_id, "name": attr.attribute_name}
                for attr in all_attributes
            ]
        },
    )


@admin_router.get("/attribute/{id}")
def get_attribute_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    attribute = db.query(Attribute).filter(Attribute.attribute_id == id).first()
    if not attribute:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Attribute not found"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"id": attribute.attribute_id, "name": attribute.attribute_name},
    )


@admin_router.put("/attribute/{id}")
def update_attribute(id: int, request: AttributeCreate, db: Session = Depends(get_db)):
    attribute = db.query(Attribute).filter(Attribute.attribute_id == id).first()
    if not attribute:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Attribute not found"},
        )

    attribute.attribute_name = request.attribute_name
    db.commit()
    db.refresh(attribute)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Attribute updated successfully",
            "attribute": {
                "id": attribute.attribute_id,
                "name": attribute.attribute_name,
            },
        },
    )


@admin_router.delete("/attribute/{id}")
def delete_attribute(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    attribute = db.query(Attribute).filter(Attribute.attribute_id == id).first()
    if not attribute:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Attribute not found"},
        )

    db.delete(attribute)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Attribute deleted successfully"},
    )


@admin_router.post("/term")
def create_term(
    request: TermCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_term = db.query(Term).filter(Term.value == request.value).first()
    if found_term:
        return JSONResponse(
            content={"detail": "Term Already Exists"}, status_code=status.HTTP_302_FOUND
        )

    new_term = Term(value=request.value, attribute_id=request.attribute_id)
    db.add(new_term)
    db.commit()
    db.refresh(new_term)

    return new_term


@admin_router.get("/term", response_model=list[TermOut])
def get_all_terms(current_user=Depends(admin_required), db: Session = Depends(get_db)):
    all_terms = db.query(Term).all()
    return all_terms


@admin_router.get("/term/{id}", response_model=TermOut)
def get_term_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    term = db.query(Term).filter(Term.term_id == id).first()
    if not term:
        return JSONResponse(
            content={"detail": "Term not found"}, status_code=status.HTTP_404_NOT_FOUND
        )

    return term


@admin_router.put("/term/{id}")
def update_term(
    id: int,
    request: TermCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    term = db.query(Term).filter(Term.term_id == id).first()
    if not term:
        return JSONResponse(
            content={"detail": "Term not found"}, status_code=status.HTTP_404_NOT_FOUND
        )

    term.attribute_id = request.attribute_id
    term.value = request.value
    db.commit()
    db.refresh(term)

    return JSONResponse(
        content={"detail": "Term updated succesfully"}, status_code=status.HTTP_200_OK
    )


@admin_router.delete("/term/{id}")
def delete_term(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    term = db.query(Term).filter(Term.term_id == id).first()
    if not term:
        return JSONResponse(
            content={"detail": "Term not found"}, status_code=status.HTTP_404_NOT_FOUND
        )

    db.delete(term)
    db.commit()

    return JSONResponse(
        content={"message": "Term deleted successfully"}, status_code=status.HTTP_200_OK
    )


@admin_router.post("/productassign")
def assign_product(
    request: ProductAssignmentCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    new_assignment = ProductAssignment(
        product_id=request.product_id, term_id=request.term_id
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return JSONResponse(
        content={"message": "Product assigned    successfully"},
        status_code=status.HTTP_201_CREATED,
    )


@admin_router.get("/productassign", response_model=list[ProductAssignOut])
def get_all_product_assignments(
    current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    all_assignment = db.query(ProductAssignment).all()
    return all_assignment


@admin_router.get("/productassign/{id}", response_model=ProductAssignOut)
def get_product_assignment_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    assignment = (
        db.query(ProductAssignment)
        .filter(ProductAssignment.assignment_id == id)
        .first()
    )
    if not assignment:
        return JSONResponse(
            content={"detail": "Not Found"}, status_code=status.HTTP_404_NOT_FOUND
        )
    return assignment


@admin_router.put("/productassign/{id}")
def update_product_assignment(
    id: int,
    request: ProductAssignmentCreate,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(ProductAssignment)
        .filter(ProductAssignment.assignment_id == id)
        .first()
    )
    if not assignment:
        return JSONResponse(
            content={"detail": "Not Found"}, status_code=status.HTTP_404_NOT_FOUND
        )

    assignment.product_id = request.product_id
    assignment.term_id = request.term_id
    db.commit()
    db.refresh(assignment)

    return JSONResponse(
        content={"message": "Updated succesfully"}, status_code=status.HTTP_200_OK
    )


@admin_router.delete("/productassign/{id}")
def delete_product_assignment(
    id: int,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(ProductAssignment)
        .filter(ProductAssignment.assignment_id == id)
        .first()
    )
    if not assignment:
        return JSONResponse(
            content={"detail": "Not Found"}, status_code=status.HTTP_404_NOT_FOUND
        )

    db.delete(assignment)
    db.commit()
    return JSONResponse(
        content={"message": "Product Assignment Deleted successfully"},
        status_code=status.HTTP_200_OK,
    )


@admin_router.post("/variants")
def add_variant(
    request: Variants,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    found_variant = db.query(Variant).filter(Variant.name == request.name).first()
    if found_variant:
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"detail": "Variant Already Exists"},
        )
    new_variant = Variant(
        product_id=request.product_id,
        name=request.name,
        sku=request.sku,
        price=request.price,
        stock=request.stock,
        available=request.available,
    )
    db.add(new_variant)
    db.commit()
    db.refresh(new_variant)
    return new_variant


@admin_router.get("/variants")
def get_variants(current_user=Depends(admin_required), db: Session = Depends(get_db)):
    found_variant = db.query(Variant).all()
    return found_variant


@admin_router.get("/variants/{id}")
def get_variant_by_id(
    id: int, current_user=Depends(admin_required), db: Session = Depends(get_db)
):
    found_variant = db.query(Variant).filter(Variant.variant_id == id).first()
    if not found_variant:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"}
        )
    return found_variant


@admin_router.put("/variants/{id}")
def update_variant(
    id: int,
    request: Variants,  # Assuming Variants is your Pydantic schema for incoming data
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    # 1. Find the variant
    variant = db.query(Variant).filter(Variant.variant_id == id).first()
    if not variant:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Variant not found"},
        )

    # 2. Update fields
    variant.product_id = request.product_id
    variant.name = request.name
    variant.sku = request.sku
    variant.price = request.price
    variant.stock = request.stock
    variant.available = request.available

    # 3. Commit changes
    db.commit()
    db.refresh(variant)

    return variant


@admin_router.delete("/variants/{id}")
def delete_variant(
    id: int,
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
):
    # 1. Find the variant
    variant = db.query(Variant).filter(Variant.variant_id == id).first()
    if not variant:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Variant not found"},
        )

    # 2. Delete it
    db.delete(variant)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Variant deleted successfully"},
    )


# CREATE Coupon
@admin_router.post("/coupons", response_model=CouponResponse)
def create_coupon(coupon_data: CouponCreate, db: Session = Depends(get_db)):
    existing_coupon = db.query(Coupon).filter(Coupon.code == coupon_data.code).first()
    if existing_coupon:
        return JSONResponse(
            status_code=400, content={"detail": "Coupon code already exists"}
        )

    new_coupon = Coupon(**coupon_data.dict())
    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return JSONResponse(status_code=201, content={"message": "Created successfully"})


# READ All Coupons
@admin_router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(db: Session = Depends(get_db)):
    coupons = db.query(Coupon).all()
    return coupons


# READ Single Coupon
@admin_router.get("/coupons/{coupon_id}", response_model=CouponResponse)
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()
    if not coupon:
        return JSONResponse(status_code=404, content={"detail": "Coupon not found"})
    return coupon


# UPDATE Coupon
@admin_router.put("/coupons/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int, coupon_data: CouponUpdate, db: Session = Depends(get_db)
):
    coupon = db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()
    if not coupon:
        return JSONResponse(status_code=404, content={"detail": "Coupon not found"})

    for key, value in coupon_data.dict(exclude_unset=True).items():
        setattr(coupon, key, value)

    db.commit()
    db.refresh(coupon)
    return JSONResponse(status_code=200, content={"message": "Updates sucessfully"})


# DELETE Coupon
@admin_router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()
    if not coupon:
        return JSONResponse(status_code=404, content={"detail": "Coupon not found"})

    db.delete(coupon)
    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Coupon deleted successfully"}
    )
