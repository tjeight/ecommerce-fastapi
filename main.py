from fastapi import FastAPI
from database import Base,db_engine
from admin_routes import admin_router
from users_routes import user_router


app =  FastAPI()


Base.metadata.create_all(db_engine)



app.include_router(router= admin_router,prefix="/admin")
app.include_router(router=user_router)



# from typing import List, Optional
# from datetime import datetime

# from fastapi import FastAPI, Depends, HTTPException, status
# from pydantic import BaseModel, Field
# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     Text,
#     ForeignKey,
#     Numeric,
#     Boolean,
#     Table,
#     create_engine,
# )
# from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base

# # --------------------
# # Database / ORM setup
# # --------------------
# DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/ecom_db"

# engine = create_engine(DATABASE_URL, echo=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # --------------------
# # Association tables
# # --------------------
# product_attributes_table = Table(
#     "product_attributes",
#     Base.metadata,
#     Column("product_id", Integer, ForeignKey("products.product_id"), primary_key=True),
#     Column("attribute_id", Integer, ForeignKey("attributes.attribute_id"), primary_key=True),
# )

# variant_attributes_table = Table(
#     "variant_attributes",
#     Base.metadata,
#     Column("variant_id", Integer, ForeignKey("variants.variant_id"), primary_key=True),
#     Column("attribute_id", Integer, ForeignKey("attributes.attribute_id"), primary_key=True),
# )

# # --------------------
# # Models ------------
# # --------------------
# class Brand(Base):
#     __tablename__ = "brands"
#     brand_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False, unique=True)
#     short_name = Column(String, nullable=True)
#     short_desc = Column(String, nullable=True)
#     long_desc = Column(Text, nullable=True)
#     image = Column(String, nullable=True)

#     categories = relationship("Category", back_populates="brand", cascade="all, delete-orphan")


# class Category(Base):
#     __tablename__ = "categories"
#     cat_id = Column(Integer, primary_key=True, index=True)
#     brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
#     cname = Column(String, nullable=False)

#     brand = relationship("Brand", back_populates="categories")
#     subcategories = relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")


# class SubCategory(Base):
#     __tablename__ = "sub_categories"
#     subcat_id = Column(Integer, primary_key=True, index=True)
#     cat_id = Column(Integer, ForeignKey("categories.cat_id"), nullable=False)
#     brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
#     name = Column(String, nullable=False)

#     category = relationship("Category", back_populates="subcategories")
#     brand = relationship("Brand")
#     products = relationship("Product", back_populates="sub_category", cascade="all, delete-orphan")


# class Product(Base):
#     __tablename__ = "products"
#     product_id = Column(Integer, primary_key=True, index=True)
#     subcat_id = Column(Integer, ForeignKey("sub_categories.subcat_id"), nullable=False)
#     brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
#     name = Column(String, nullable=False)
#     price = Column(Numeric(10, 2), nullable=False)
#     description = Column(Text, nullable=True)

#     sub_category = relationship("SubCategory", back_populates="products")
#     brand = relationship("Brand")

#     attributes = relationship("Attribute", secondary=product_attributes_table, back_populates="products")
#     variants = relationship("Variant", back_populates="product", cascade="all, delete-orphan")


# class Attribute(Base):
#     __tablename__ = "attributes"
#     attribute_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)    # e.g. Color, Size
#     value = Column(String, nullable=False)   # e.g. Blue, M

#     products = relationship("Product", secondary=product_attributes_table, back_populates="attributes")
#     variants = relationship("Variant", secondary=variant_attributes_table, back_populates="attributes")


# class Variant(Base):
#     __tablename__ = "variants"
#     variant_id = Column(Integer, primary_key=True, index=True)
#     product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
#     sku = Column(String, nullable=True, unique=True)
#     price = Column(Numeric(10, 2), nullable=False)

#     product = relationship("Product", back_populates="variants")
#     attributes = relationship("Attribute", secondary=variant_attributes_table, back_populates="variants")
#     assignments = relationship("ProductAssignment", back_populates="variant", cascade="all, delete-orphan")


# class ProductAssignment(Base):
#     __tablename__ = "product_assignments"
#     assignment_id = Column(Integer, primary_key=True, index=True)
#     product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
#     variant_id = Column(Integer, ForeignKey("variants.variant_id"), nullable=False)
#     stock = Column(Integer, nullable=False, default=0)
#     available = Column(Boolean, default=True)
#     location = Column(String, nullable=True)  # optional store/location

#     variant = relationship("Variant", back_populates="assignments")
#     product = relationship("Product")


# # Create tables
# Base.metadata.create_all(bind=engine)

# # --------------------
# # Pydantic Schemas
# # --------------------
# class BrandCreate(BaseModel):
#     name: str
#     short_name: Optional[str]
#     short_desc: Optional[str]
#     long_desc: Optional[str]
#     image: Optional[str]


# class BrandOut(BaseModel):
#     brand_id: int
#     name: str

#     class Config:
#         orm_mode = True


# class CategoryCreate(BaseModel):
#     brand_id: int
#     cname: str


# class SubCategoryCreate(BaseModel):
#     cat_id: int
#     brand_id: int
#     name: str


# class ProductCreate(BaseModel):
#     subcat_id: int
#     brand_id: int
#     name: str
#     price: float
#     description: Optional[str]


# class AttributeCreate(BaseModel):
#     name: str
#     value: str


# class VariantCreate(BaseModel):
#     attribute_ids: List[int] = Field(..., description="List of attribute_id that form this variant")
#     price: float
#     sku: Optional[str]


# class AssignmentCreate(BaseModel):
#     variant_id: int
#     product_id: int
#     stock: int
#     available: Optional[bool] = True
#     location: Optional[str]


# # Response schemas
# class AttributeOut(BaseModel):
#     attribute_id: int
#     name: str
#     value: str

#     class Config:
#         orm_mode = True


# class VariantOut(BaseModel):
#     variant_id: int
#     sku: Optional[str]
#     price: float
#     attributes: List[AttributeOut]

#     class Config:
#         orm_mode = True


# class ProductOut(BaseModel):
#     product_id: int
#     name: str
#     price: float
#     description: Optional[str]
#     attributes: List[AttributeOut] = []
#     variants: List[VariantOut] = []

#     class Config:
#         orm_mode = True


# # --------------------
# # FastAPI + Dependencies
# # --------------------
# app = FastAPI(title="E-Commerce Admin Backend (Postgres + SQLAlchemy)")


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # --------------------
# # Admin CRUD Endpoints
# # --------------------
# @app.post("/brands", response_model=BrandOut)
# def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
#     existing = db.query(Brand).filter(Brand.name == payload.name).first()
#     if existing:
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Brand already exists")
#     b = Brand(**payload.dict())
#     db.add(b)
#     db.commit()
#     db.refresh(b)
#     return b


# @app.post("/categories")
# def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
#     brand = db.query(Brand).filter(Brand.brand_id == payload.brand_id).first()
#     if not brand:
#         raise HTTPException(status_code=404, detail="Brand not found")
#     c = Category(**payload.dict())
#     db.add(c)
#     db.commit()
#     db.refresh(c)
#     return {"cat_id": c.cat_id, "cname": c.cname}


# @app.post("/subcategories")
# def create_subcategory(payload: SubCategoryCreate, db: Session = Depends(get_db)):
#     cat = db.query(Category).filter(Category.cat_id == payload.cat_id).first()
#     if not cat:
#         raise HTTPException(status_code=404, detail="Category not found")
#     sc = SubCategory(**payload.dict())
#     db.add(sc)
#     db.commit()
#     db.refresh(sc)
#     return {"subcat_id": sc.subcat_id, "name": sc.name}


# @app.post("/products", response_model=ProductOut)
# def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
#     sc = db.query(SubCategory).filter(SubCategory.subcat_id == payload.subcat_id).first()
#     if not sc:
#         raise HTTPException(status_code=404, detail="SubCategory not found")
#     p = Product(**payload.dict())
#     db.add(p)
#     db.commit()
#     db.refresh(p)
#     return p


# @app.post("/attributes", response_model=AttributeOut)
# def create_attribute(payload: AttributeCreate, db: Session = Depends(get_db)):
#     # Prevent exact duplicates (name+value)
#     existing = db.query(Attribute).filter(Attribute.name == payload.name, Attribute.value == payload.value).first()
#     if existing:
#         return existing
#     a = Attribute(**payload.dict())
#     db.add(a)
#     db.commit()
#     db.refresh(a)
#     return a


# @app.post("/products/{product_id}/attributes")
# def map_product_attributes(product_id: int, attribute_ids: List[int], db: Session = Depends(get_db)):
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
#     for aid in attribute_ids:
#         attr = db.query(Attribute).filter(Attribute.attribute_id == aid).first()
#         if not attr:
#             raise HTTPException(status_code=404, detail=f"Attribute {aid} not found")
#         if attr not in product.attributes:
#             product.attributes.append(attr)
#     db.commit()
#     db.refresh(product)
#     return {"product_id": product.product_id, "attribute_ids": [a.attribute_id for a in product.attributes]}


# @app.post("/products/{product_id}/variants", response_model=VariantOut)
# def create_variant(product_id: int, payload: VariantCreate, db: Session = Depends(get_db)):
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     # ensure provided attributes exist and belong to product (optional business rule)
#     attrs = []
#     for aid in payload.attribute_ids:
#         a = db.query(Attribute).filter(Attribute.attribute_id == aid).first()
#         if not a:
#             raise HTTPException(status_code=404, detail=f"Attribute {aid} not found")
#         # optional: ensure attribute is allowed for product
#         if a not in product.attributes:
#             raise HTTPException(status_code=400, detail=f"Attribute {aid} is not assigned to product {product_id}")
#         attrs.append(a)

#     v = Variant(product_id=product_id, price=payload.price, sku=payload.sku if payload.sku else None)
#     v.attributes = attrs
#     db.add(v)
#     db.commit()
#     db.refresh(v)
#     out = VariantOut.from_orm(v)
#     return out


# @app.post("/assignments")
# def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
#     # validate product and variant
#     p = db.query(Product).filter(Product.product_id == payload.product_id).first()
#     v = db.query(Variant).filter(Variant.variant_id == payload.variant_id).first()
#     if not p or not v:
#         raise HTTPException(status_code=404, detail="Product or Variant not found")
#     assign = ProductAssignment(**payload.dict())
#     db.add(assign)
#     db.commit()
#     db.refresh(assign)
#     return {"assignment_id": assign.assignment_id, "stock": assign.stock}


# @app.get("/products/{product_id}", response_model=ProductOut)
# def get_product(product_id: int, db: Session = Depends(get_db)):
#     p = db.query(Product).filter(Product.product_id == product_id).first()
#     if not p:
#         raise HTTPException(status_code=404, detail="Product not found")
#     # eager load attributes and variants
#     return p


# @app.get("/products", response_model=List[ProductOut])
# def list_products(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
#     products = db.query(Product).offset(skip).limit(limit).all()
#     return products


# --------------------
# Notes for running
# --------------------
# 1) Update DATABASE_URL with your Postgres credentials
# 2) pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
# 3) Run: uvicorn ecom_fastapi_sqlalchemy:app --reload

# This implementation follows Approach 2: a global attributes table, mapping
# table product_attributes linking products to allowed attributes, and
# variant_attributes linking concrete variant SKUs to their attribute values.
# It provides admin endpoints to create brands, categories, products, global
# attributes, map product->attributes, create variants (combination of attrs),
# and assign stock/availability via ProductAssignment.




