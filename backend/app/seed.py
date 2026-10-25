from sqlalchemy.orm import Session
from .models import Product, User
from .security import hash_password
import os

SAMPLE_PRODUCTS = [
("Rosewood Kantha Story Saree","rosewood-kantha-story-saree","Kantha",2890,3290,"https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=900&q=85","Handcrafted-inspired print with a warm, earthy palette.",True),
("Ivory Mulmul Everyday Drape","ivory-mulmul-everyday-drape","Cotton",1890,2190,"https://images.unsplash.com/photo-1610189012906-4c4c7f8f7b5c?auto=format&fit=crop&w=900&q=85","An airy everyday drape with understated charm.",True),
("Indigo Khadi Heritage Saree","indigo-khadi-heritage-saree","Khadi",2490,2790,"https://images.unsplash.com/photo-1610030469668-8e9f641aaf16?auto=format&fit=crop&w=900&q=85","Texture-led styling inspired by timeless Indian weaves.",True),
("Marigold Festive Saree","marigold-festive-saree","Festive",3590,3990,"https://images.unsplash.com/photo-1583391733956-6c78276477e8?auto=format&fit=crop&w=900&q=85","A celebratory colour story for meaningful occasions.",True),
("Blue Motif Cotton Saree","blue-motif-cotton-saree","Cotton",1690,1990,"https://images.unsplash.com/photo-1590736969955-71cc94901144?auto=format&fit=crop&w=900&q=85","A versatile cotton-inspired look for everyday wear.",False),
("Terracotta Folk Art Saree","terracotta-folk-art-saree","Kantha",2790,3190,"https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=900&q=85","A folk-art inspired statement in earthy tones.",False),
("Natural Texture Khadi Saree","natural-texture-khadi-saree","Khadi",2290,2590,"https://images.unsplash.com/photo-1609748340478-9f9e9b8b4c6d?auto=format&fit=crop&w=900&q=85","Quiet, versatile styling with natural-texture inspiration.",False),
("Ruby Evening Saree","ruby-evening-saree","Festive",3890,4490,"https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=900&q=85","An elegant occasion-inspired drape in rich colour.",False),
]

def seed_data(db: Session):
    if db.query(Product).count() == 0:
        for name,slug,cat,price,old,img,desc,featured in SAMPLE_PRODUCTS:
            db.add(Product(name=name,slug=slug,category=cat,price=price,compare_at_price=old,image_url=img,description=desc,stock=12,featured=featured,active=True))
    admin_email = os.getenv("ADMIN_EMAIL", "admin@ayukta.local").lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
    if not db.query(User).filter(User.email == admin_email).first():
        db.add(User(name="Ayukta Admin",email=admin_email,password_hash=hash_password(admin_password),is_admin=True))
    db.commit()
