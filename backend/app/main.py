import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, get_db, SessionLocal
from .models import User, Product, Order, OrderItem, NewsletterSubscriber
from .schemas import RegisterIn, LoginIn, UserOut, ProductIn, ProductOut, OrderIn, OrderStatusIn, NewsletterIn
from .security import hash_password, verify_password, create_access_token, get_current_user, require_admin
from .seed import seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield

app = FastAPI(title="Ayukta API", version="1.0.0", description="API for the Ayukta saree storefront", lifespan=lifespan)
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"message":"Welcome to Ayukta API","docs":"/docs","health":"/api/health"}

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    return {"status":"ok","service":"ayukta-api"}

@app.post("/api/auth/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), is_admin=False)
    db.add(user)
    try:
        db.commit(); db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    return user

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token":create_access_token(user),"token_type":"bearer","user":UserOut.model_validate(user)}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@app.get("/api/products", response_model=list[ProductOut])
def list_products(category: str | None = None, q: str | None = Query(default=None, max_length=100), featured: bool | None = None, limit: int = Query(default=100, ge=1, le=200), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.active.is_(True))
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like), Product.category.ilike(like)))
    if featured is not None:
        query = query.filter(Product.featured.is_(featured))
    return query.order_by(Product.created_at.desc(), Product.id.desc()).offset(offset).limit(limit).all()

@app.get("/api/products/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.active.is_(True)).first()
    if not product: raise HTTPException(404, "Product not found")
    return product

@app.post("/api/orders", status_code=201)
def create_order(data: OrderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Never trust client-provided prices; calculate from current database product prices.
    quantities = {}
    for item in data.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
    products = {p.id:p for p in db.query(Product).filter(Product.id.in_(quantities.keys()), Product.active.is_(True)).all()}
    if len(products) != len(quantities): raise HTTPException(400, "One or more products are unavailable")
    total = 0.0
    order_lines = []
    for product_id, qty in quantities.items():
        p = products[product_id]
        if p.stock < qty: raise HTTPException(409, f"Insufficient stock for {p.name}")
        total += p.price * qty
        order_lines.append((p,qty))
    order = Order(user_id=user.id,status="pending",total=round(total,2),customer_name=data.customer_name.strip(),phone=data.phone.strip(),address=data.address.strip(),city=data.city.strip(),postal_code=data.postal_code.strip())
    db.add(order); db.flush()
    for p,qty in order_lines:
        db.add(OrderItem(order_id=order.id,product_id=p.id,product_name=p.name,unit_price=p.price,quantity=qty))
        p.stock -= qty
    db.commit(); db.refresh(order)
    return {"id":order.id,"status":order.status,"total":order.total,"message":"Order created. Payment integration is not enabled in this starter."}

@app.get("/api/orders/mine")
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.query(Order).options(joinedload(Order.items)).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return [{"id":o.id,"status":o.status,"total":o.total,"created_at":o.created_at,"customer_name":o.customer_name,"items":[{"product_id":i.product_id,"name":i.product_name,"price":i.unit_price,"quantity":i.quantity} for i in o.items]} for o in orders]

@app.post("/api/newsletter", status_code=201)
def subscribe(data: NewsletterIn, db: Session = Depends(get_db)):
    email=data.email.lower()
    if db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email==email).first():
        return {"message":"You are already subscribed."}
    db.add(NewsletterSubscriber(email=email))
    try: db.commit()
    except IntegrityError:
        db.rollback()
        return {"message":"You are already subscribed."}
    return {"message":"Thanks for subscribing to Ayukta."}

@app.get("/api/admin/orders")
def admin_orders(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    orders=db.query(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc()).all()
    return [{"id":o.id,"status":o.status,"total":o.total,"created_at":o.created_at,"customer_name":o.customer_name,"phone":o.phone,"address":o.address,"city":o.city,"postal_code":o.postal_code,"email":o.user.email if o.user else None,"items":[{"name":i.product_name,"price":i.unit_price,"quantity":i.quantity} for i in o.items]} for o in orders]

@app.patch("/api/admin/orders/{order_id}")
def update_order(order_id: int, data: OrderStatusIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    order=db.get(Order,order_id)
    if not order: raise HTTPException(404,"Order not found")
    order.status=data.status; db.commit()
    return {"id":order.id,"status":order.status}

@app.post("/api/admin/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(Product).filter(Product.slug==data.slug).first(): raise HTTPException(409,"Product slug already exists")
    p=Product(**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@app.patch("/api/admin/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,"Product not found")
    if data.slug != p.slug and db.query(Product).filter(Product.slug==data.slug).first(): raise HTTPException(409,"Product slug already exists")
    for key,value in data.model_dump().items(): setattr(p,key,value)
    db.commit(); db.refresh(p); return p

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,"Product not found")
    p.active=False; db.commit()
    return {"message":"Product hidden from storefront"}

@app.get("/api/admin/summary")
def admin_summary(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {"products":db.query(Product).filter(Product.active.is_(True)).count(),"orders":db.query(Order).count(),"customers":db.query(User).filter(User.is_admin.is_(False)).count(),"subscribers":db.query(NewsletterSubscriber).count(),"revenue":round(sum(o.total for o in db.query(Order).filter(Order.status!="cancelled").all()),2)}
