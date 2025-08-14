# 🛒 E-Commerce Backend API (FastAPI + PostgreSQL + SQLAlchemy)

A robust, scalable **backend API** for an e-commerce platform built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.  
Includes authentication, user management, product catalog, cart system, orders, and address management with JWT-based security.

---

## 🚀 Features

- **Authentication & Authorization**
  - JWT-based login/signup
  - Role-based access (User, Seller, Admin)
- **User Management**
  - Profile management
  - Address CRUD with user-level ownership checks
- **Product Management**
  - Add, update, delete products (seller/admin)
  - Product listing with filtering and search
- **Cart & Order System**
  - Add to cart, update quantities, remove items
  - Create orders from cart
- **Address Management**
  - Add, update, delete multiple addresses
  - User-specific address retrieval
- **Secure & Modular**
  - SQLAlchemy ORM
  - Pydantic for validation
  - Follows industry-standard folder structure

---

## 🗂 Project Structure

ecommerce-backend/
│── app/
│ ├── main.py # FastAPI entry point
│ ├── database.py # DB connection
│ ├── models.py # SQLAlchemy models
│ ├── schemas.py # Pydantic schemas
│ ├── routes/
│ │ ├── auth.py # Authentication routes
│ │ ├── products.py # Product routes
│ │ ├── cart.py # Cart routes
│ │ ├── orders.py # Order routes
│ │ ├── address.py # Address CRUD routes
│ ├── auth/ # JWT helper functions
│ ├── utils/ # Helper utilities
