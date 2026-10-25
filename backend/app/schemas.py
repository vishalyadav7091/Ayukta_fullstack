from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)

class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = ""
    category: str = Field(min_length=2, max_length=80)
    price: float = Field(gt=0)
    compare_at_price: Optional[float] = Field(default=None, gt=0)
    image_url: str = Field(min_length=5)
    stock: int = Field(default=10, ge=0)
    featured: bool = False
    active: bool = True

class ProductOut(ProductIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OrderLineIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=20)

class OrderIn(BaseModel):
    items: list[OrderLineIn] = Field(min_length=1, max_length=30)
    customer_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=30)
    address: str = Field(min_length=5, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=4, max_length=20)

class OrderStatusIn(BaseModel):
    status: str = Field(pattern=r"^(pending|confirmed|shipped|delivered|cancelled)$")

class NewsletterIn(BaseModel):
    email: EmailStr
