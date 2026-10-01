import certifi
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import uuid
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict, Any
import bcrypt
import jwt
from lib.amount_words import amount_in_words
from bson import ObjectId

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query
from routers.auth import router as auth_router
from routers.subscriptions import router as subscriptions_router
from routers.analytics import router as analytics_router
from routers.team import router as team_router
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, EmailStr

from lib import plans as plans_lib
from lib import razorpay_client
from lib.features import require_feature
from lib.features import resolve_entitlements
from lib.business_scope import get_business_data_owner_id
from lib import ai_assistant as ai_svc
from lib import ai_data as ai_data_svc

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
# from routers.auth import router as auth_router

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
# client = AsyncIOMotorClient(mongo_url)
client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
db = client[os.environ.get('DB_NAME', 'test_database')]

JWT_SECRET = os.environ.get("JWT_SECRET", "vyastha_jwt_secret_key_2026_default_99")
JWT_ALGORITHM = "HS256"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vyastha Billing & Invoicing API")
api_router = APIRouter(prefix="/api")


# ==========================================
# Auth Helpers & Password Hashing
# ==========================================
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            user = await db.users.find_one({"id": user_id})
        if not user:
            user = await db.users.find_one({"email": payload.get("email")})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")




# ==========================================
# Pydantic Models
# ==========================================
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: Optional[str] = ""
    phone: Optional[str] = ""

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    company_name: Optional[str] = ""
    role: str = "business_owner"

class BankDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bank_name: str = ""
    account_holder_name: str = ""
    account_number: str = ""
    ifsc: str = ""
    branch: str = ""
    upi_id: str = ""

class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company_name: str = "Vyastha Enterprise"
    pan_number: str = ""
    gstin_number: str = ""
    state_code: str = ""  
    phone: str = ""
    email: str = ""
    company_logo: str = ""
    tagline: str = ""
    address: str = ""
    bank_details: BankDetails = Field(default_factory=BankDetails)
    signature_image: str = ""
    default_terms: str = "1. Payment is due within 15 days of invoice date.\n2. Goods once sold will not be taken back.\n3. All disputes are subject to local jurisdiction."
    invoice_prefix: str = "INV"
    quotation_prefix: str = "QUO"

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""  # e.g. CUST-001
    company_name: str
    contact_person: str = ""
    gstin_number: str = ""
    state_code: str = "" 
    pan_number: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    user_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CustomerCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = ""
    gstin_number: Optional[str] = ""
    pan_number: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    customer_id: Optional[str] = ""

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    sku: str = ""
    category: str = "General"
    unit: str = "pc"  # pc, kg, box, mtr, set, etc.
    unit_price: float = 0.0
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    description: str = ""
    user_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = ""
    category: Optional[str] = "General"
    unit: Optional[str] = "pc"
    unit_price: float = 0.0
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    description: Optional[str] = ""

class StockAdjustment(BaseModel):
    quantity: int  # positive to add (IN), negative to deduct (OUT)
    type: str = "IN"  # IN, OUT, ADJUSTMENT
    reason: str = "Stock adjustment"
    reference: Optional[str] = ""

class LineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_id: Optional[str] = None
    description: str
    quantity: float = 1.0
    unit: str = "pc"
    pieces: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0

class InvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: str = Field(default_factory=lambda: date.today().isoformat())
    shipping_date: Optional[str] = ""
    customer_id: Optional[str] = ""
    vehicle_number: Optional[str] = ""
    reference_quotation_number: Optional[str] = ""
    seller_details: Dict[str, Any] = Field(default_factory=dict)
    buyer_details: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax_rate: float = 18.0
    tax_amount: float = 0.0
    discount_type: str = "amount"  # amount or percentage
    discount_value: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    terms_and_conditions: Optional[str] = ""
    bank_details: Dict[str, Any] = Field(default_factory=dict)
    signature_url: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "finalized"  # draft, finalized, sent, paid, cancelled
    payment_status: str = "unpaid"  # unpaid, partially_paid, paid
    amount_paid: float = 0.0
    auto_deduct_inventory: bool = True

class QuotationCreate(BaseModel):
    quotation_number: Optional[str] = None
    quotation_date: str = Field(default_factory=lambda: date.today().isoformat())
    valid_until: Optional[str] = ""
    customer_id: Optional[str] = ""
    vehicle_number: Optional[str] = ""
    seller_details: Dict[str, Any] = Field(default_factory=dict)
    buyer_details: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax_rate: float = 18.0
    tax_amount: float = 0.0
    discount_type: str = "amount"
    discount_value: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    terms_and_conditions: Optional[str] = ""
    bank_details: Dict[str, Any] = Field(default_factory=dict)
    signature_url: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "draft"  # draft, sent, accepted, rejected, converted

class PaymentCreate(BaseModel):
    invoice_id: Optional[str] = None
    invoice_number: str = ""
    customer_name: str = ""
    amount: float
    payment_date: str = Field(default_factory=lambda: date.today().isoformat())
    payment_method: str = "UPI"  # UPI, Bank Transfer, Cash, Card, Cheque
    transaction_ref: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "successful"  # successful, pending, failed


# ==========================================
# Helper Functions for Sequences & Stock
# ==========================================
def build_upi_qr_string(upi_id: str, company_name: str, amount: float, ref: str) -> str:
    if not upi_id:
        upi_id = "business@upi"
    clean_name = "".join(c for c in company_name if c.isalnum() or c in " _-") or "VyasthaPay"
    clean_ref = "".join(c for c in ref if c.isalnum() or c in "-_") or "Bill"
    formatted_amt = f"{amount:.2f}"
    return f"upi://pay?pa={upi_id}&pn={clean_name}&am={formatted_amt}&cu=INR&tn={clean_ref}"

def calculate_gst_split(tax_amount: float, seller_state: str, buyer_state: str):
    """Same state → CGST+SGST split; different state → IGST."""
    if seller_state and buyer_state and seller_state.strip() == buyer_state.strip():
        half = round(tax_amount / 2, 2)
        return {"cgst_amount": half, "sgst_amount": tax_amount - half, "igst_amount": 0.0}
    else:
        return {"cgst_amount": 0.0, "sgst_amount": 0.0, "igst_amount": round(tax_amount, 2)}

async def get_next_sequence(user_id: str, seq_type: str, prefix: str) -> str:
    year = date.today().year
    seq_doc = await db.counters.find_one_and_update(
        {"user_id": user_id, "type": seq_type, "year": year},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    seq_num = seq_doc.get("sequence", 1) if seq_doc else 1
    return f"{prefix}-{year}-{seq_num:04d}"

async def get_daily_draft_count(user_id: str) -> int:
    today_str = date.today().isoformat()
    invoice_drafts = await db.invoices.count_documents({
        "user_id": user_id,
        "status": "draft",
        "created_date_str": today_str
    })
    quotation_drafts = await db.quotations.count_documents({
        "user_id": user_id,
        "status": "draft",
        "created_date_str": today_str
    })
    return invoice_drafts + quotation_drafts

async def deduct_inventory_for_items(user_id: str, line_items: List[dict], reference: str):
    for item in line_items:
        p_id = item.get("product_id")
        qty = float(item.get("quantity", 0))
        if not qty or qty <= 0:
            continue
        
        product = None
        if p_id:
            product = await db.products.find_one({"id": p_id, "user_id": user_id})
        if not product and item.get("description"):
            # match by name if product_id not provided
            product = await db.products.find_one({
                "name": {"$regex": f"^{item.get('description')}$", "$options": "i"},
                "user_id": user_id
            })
        
        if product:
            new_qty = max(0, product.get("stock_quantity", 0) - int(qty))
            await db.products.update_one(
                {"id": product["id"], "user_id": user_id},
                {"$set": {"stock_quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            # Record transaction
            await db.inventory_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": -int(qty),
                "type": "OUT_INVOICE",
                "reason": f"Deducted for Invoice {reference}",
                "reference": reference,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

async def restore_inventory_for_items(user_id: str, line_items: List[dict], reference: str):
    for item in line_items:
        p_id = item.get("product_id")
        qty = float(item.get("quantity", 0))
        if not qty or qty <= 0:
            continue
        
        product = None
        if p_id:
            product = await db.products.find_one({"id": p_id, "user_id": user_id})
        if not product and item.get("description"):
            product = await db.products.find_one({
                "name": {"$regex": f"^{item.get('description')}$", "$options": "i"},
                "user_id": user_id
            })
        
        if product:
            new_qty = product.get("stock_quantity", 0) + int(qty)
            await db.products.update_one(
                {"id": product["id"], "user_id": user_id},
                {"$set": {"stock_quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            await db.inventory_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": int(qty),
                "type": "IN_RESTORE",
                "reason": f"Restored from cancelled invoice {reference}",
                "reference": reference,
                "created_at": datetime.now(timezone.utc).isoformat()
            })


# ==========================================
# Auth Endpoints
# ==========================================

@api_router.post("/auth/demo-login")
async def demo_login(response: Response):
    demo_email = "demo@vyastha.com"
    user = await db.users.find_one({"email": demo_email})
    if not user:
        user_id = str(uuid.uuid4())
        hashed = hash_password("demopassword123")
        user_doc = {
            "id": user_id,
            "email": demo_email,
            "name": "Rajesh Sharma",
            "company_name": "Vyastha Enterprise Solutions Ltd",
            "phone": "+91 98765 43210",
            "password_hash": hashed,
            "role": "business_owner",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    
    user_id = user.get("id") or str(user["_id"])
    access_token = create_access_token(user_id, demo_email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400 * 7, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=86400 * 30, path="/")
    
    return {
        "token": access_token,
        "user": {
            "id": user_id,
            "email": demo_email,
            "name": user.get("name", "Rajesh Sharma"),
            "company_name": user.get("company_name", "Vyastha Enterprise Solutions Ltd"),
            "role": "business_owner"
        }
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    return {
        "id": user_id,
        "email": user.get("email"),
        "name": user.get("name"),
        "company_name": user.get("company_name", ""),
        "role": user.get("role", "business_owner")
    }

@api_router.get("/auth/entitlements")
async def get_auth_entitlements(
    user: dict = Depends(get_current_user),
):
    business_id = user.get("business_id")

    if not business_id:
        raise HTTPException(
            status_code=401,
            detail="Business context is missing.",
        )

    return await resolve_entitlements(business_id)

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}


# ==========================================
# Company Profile / Settings Module
# ==========================================
@api_router.get("/company-profile")
async def get_company_profile(user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    profile = await db.company_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        profile = {
            "user_id": user_id,
            "company_name": user.get("company_name") or "Vyastha Enterprise",
            "pan_number": "ABCDE1234F",
            "gstin_number": "27ABCDE1234F1Z5",
            "phone": "+91 98765 43210",
            "email": user.get("email") or "billing@vyastha.com",
            "company_logo": "",
            "tagline": "Excellence in Enterprise Solutions",
            "address": "402, Business Hub, MG Road, Mumbai, Maharashtra 400001",
            "bank_details": {
                "bank_name": "HDFC Bank",
                "account_holder_name": user.get("company_name") or "Vyastha Enterprise",
                "account_number": "50200012345678",
                "ifsc": "HDFC0000240",
                "branch": "Fort Mumbai",
                "upi_id": "vyastha@hdfcbank"
            },
            "signature_image": "",
            "default_terms": "1. Payment is due within 15 days of invoice date.\n2. Goods once sold will not be taken back.\n3. All disputes are subject to Mumbai jurisdiction.",
            "invoice_prefix": "INV",
            "quotation_prefix": "QUO"
        }
        await db.company_profiles.insert_one(dict(profile))
    return profile

@api_router.put("/company-profile")
async def update_company_profile(profile_data: dict, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    profile_data["user_id"] = user_id
    profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.company_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile_data},
        upsert=True
    )
    # Update user's company_name as well
    if "company_name" in profile_data:
        await db.users.update_one(
            {"$or": [{"id": user_id}, {"_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else None}]},
            {"$set": {"company_name": profile_data["company_name"]}}
        )
    
    return {"message": "Company profile updated successfully", "profile": profile_data}


# ==========================================
# Customers Module
# ==========================================
@api_router.get("/customers")
async def get_customers(user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    customers = await db.customers.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return customers

@api_router.post("/customers")
async def create_customer(data: CustomerCreate, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    cust_count = await db.customers.count_documents({"user_id": user_id})
    cust_code = data.customer_id or f"CUST-{cust_count + 1:03d}"
    
    cust_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "customer_id": cust_code,
        "company_name": data.company_name,
        "contact_person": data.contact_person or "",
        "gstin_number": data.gstin_number or "",
        "pan_number": data.pan_number or "",
        "phone": data.phone or "",
        "email": data.email or "",
        "address": data.address or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customers.insert_one(cust_doc)
    cust_doc.pop("_id", None)
    return cust_doc

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, data: CustomerCreate, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    update_dict = data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    res = await db.customers.update_one(
        {"id": customer_id, "user_id": user_id},
        {"$set": update_dict}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    updated = await db.customers.find_one({"id": customer_id, "user_id": user_id}, {"_id": 0})
    return updated

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    await db.customers.delete_one({"id": customer_id, "user_id": user_id})
    return {"message": "Customer deleted successfully"}


# ==========================================
# Products & Inventory Module
# ==========================================
@api_router.get("/products")
async def get_products(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("products")),
):
    data_owner_id = await get_business_data_owner_id(user)

    products = await db.products.find(
        {"user_id": data_owner_id},
        {"_id": 0}
    ).sort(
        "name", 1
    ).to_list(1000)

    return products

@api_router.post("/products")
async def create_product(
    data: ProductCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("products")),
):
    user_id = user.get("id") or str(user["_id"])
    prod_count = await db.products.count_documents({"user_id": user_id})
    sku = data.sku or f"SKU-{prod_count + 1:04d}"
    
    prod_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": data.name,
        "sku": sku,
        "category": data.category or "General",
        "unit": data.unit or "pc",
        "unit_price": float(data.unit_price),
        "stock_quantity": int(data.stock_quantity),
        "low_stock_threshold": int(data.low_stock_threshold),
        "description": data.description or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.products.insert_one(prod_doc)
    prod_doc.pop("_id", None)
    
    # Initial stock log if initial stock > 0
    if prod_doc["stock_quantity"] > 0:
        await db.inventory_transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "product_id": prod_doc["id"],
            "product_name": prod_doc["name"],
            "quantity": prod_doc["stock_quantity"],
            "type": "IN_INITIAL",
            "reason": "Initial stock opening balance",
            "reference": "OPENING_BALANCE",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
    return prod_doc

@api_router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    data: ProductCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("products")),
):
    user_id = user.get("id") or str(user["_id"])
    update_dict = data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    res = await db.products.update_one(
        {"id": product_id, "user_id": user_id},
        {"$set": update_dict}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.products.find_one({"id": product_id, "user_id": user_id}, {"_id": 0})
    return updated

@api_router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("products")),
):
    user_id = user.get("id") or str(user["_id"])
    await db.products.delete_one({"id": product_id, "user_id": user_id})
    return {"message": "Product deleted"}

@api_router.post("/products/{product_id}/adjust-stock")
async def adjust_stock(
    product_id: str,
    adjustment: StockAdjustment,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("advanced_inventory")),
):
    user_id = user.get("id") or str(user["_id"])
    product = await db.products.find_one({"id": product_id, "user_id": user_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    current_stock = product.get("stock_quantity", 0)
    change = adjustment.quantity
    if adjustment.type.upper() == "OUT":
        change = -abs(change)
    else:
        change = abs(change)
        
    new_stock = max(0, current_stock + change)
    await db.products.update_one(
        {"id": product_id, "user_id": user_id},
        {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    txn_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product.get("name"),
        "quantity": change,
        "type": adjustment.type.upper(),
        "reason": adjustment.reason,
        "reference": adjustment.reference or "MANUAL_ADJUSTMENT",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.inventory_transactions.insert_one(txn_doc)
    txn_doc.pop("_id", None)
    
    return {
        "product_id": product_id,
        "previous_stock": current_stock,
        "new_stock": new_stock,
        "transaction": txn_doc
    }

@api_router.get("/inventory/alerts")
async def get_inventory_alerts(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("advanced_inventory")),
):
    user_id = user.get("id") or str(user["_id"])
    products = await db.products.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    low_stock_items = [p for p in products if p.get("stock_quantity", 0) <= p.get("low_stock_threshold", 10)]
    return {
        "count": len(low_stock_items),
        "items": low_stock_items
    }

@api_router.get("/inventory/transactions")
async def get_inventory_transactions(user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    txns = await db.inventory_transactions.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return txns


# ==========================================
# Drafts Management & Stats Endpoint
# ==========================================
@api_router.get("/drafts/stats")
async def get_drafts_stats(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    today_str = date.today().isoformat()
    
    invoice_drafts = await db.invoices.find({
        "user_id": user_id,
        "status": "draft"
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    quotation_drafts = await db.quotations.find({
        "user_id": user_id,
        "status": "draft"
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    today_draft_count = sum(1 for d in invoice_drafts if d.get("created_date_str") == today_str) + \
                        sum(1 for d in quotation_drafts if d.get("created_date_str") == today_str)
    
    return {
        "today_drafts_count": today_draft_count,
        "max_daily_limit": 50,
        "remaining_drafts_today": max(0, 50 - today_draft_count),
        "total_active_drafts": len(invoice_drafts) + len(quotation_drafts),
        "invoice_drafts": invoice_drafts,
        "quotation_drafts": quotation_drafts
    }


# ==========================================
# Invoices Module
# ==========================================
@api_router.get("/invoices")
async def get_invoices(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    data_owner_id = await get_business_data_owner_id(user)

    query: Dict[str, Any] = {"user_id": data_owner_id}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
        
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice_by_id(invoice_id: str, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or str(user["_id"])
    invoice = await db.invoices.find_one({"$or": [{"id": invoice_id}, {"invoice_number": invoice_id}], "user_id": user_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    
    # Check Draft Limit if status is draft
    today_str = date.today().isoformat()
    if data.status == "draft":
        today_count = await get_daily_draft_count(user_id)
        if today_count >= 50:
            raise HTTPException(status_code=400, detail="Daily draft limit reached (50 drafts/day maximum). Please finalize or delete existing drafts.")
            
    # Fetch Company Profile for Prefix & Defaults if needed
    profile = await db.company_profiles.find_one({"user_id": user_id}, {"_id": 0}) or {}
    prefix = profile.get("invoice_prefix") or "INV"
    
    inv_number = data.invoice_number
    if not inv_number:
        inv_number = await get_next_sequence(user_id, "invoice", prefix)

    # Real-time calculation integrity check
    line_items_data = [item.model_dump() for item in data.line_items]

    calc_subtotal = sum(
        float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        for item in line_items_data
    )

    discount_amt = 0.0

    if data.discount_type == "percentage":
        discount_amt = (calc_subtotal * data.discount_value) / 100.0
    else:
        discount_amt = data.discount_value

    discount_amt = max(0.0, min(discount_amt, calc_subtotal))

    taxable = max(0.0, calc_subtotal - discount_amt)

    calc_tax_amt = (taxable * data.tax_rate) / 100.0

    calc_total = taxable + calc_tax_amt

    gst_split = {
        "cgst_amount": round(calc_tax_amt / 2, 2),
        "sgst_amount": round(calc_tax_amt / 2, 2),
        "igst_amount": 0.0,
    }

    calc_amount_in_words = amount_in_words(calc_total)

    seller_state = (data.seller_details or profile).get("state_code", "")
    buyer_state = (data.buyer_details or {}).get("state_code", "")

    gst_split = calculate_gst_split(
        calc_tax_amt,
        seller_state,
        buyer_state
)
        
    # Generate Dynamic UPI Payment QR Data
    seller = data.seller_details or profile
    upi_id = seller.get("bank_details", {}).get("upi_id") or profile.get("bank_details", {}).get("upi_id") or "business@upi"
    company_name = seller.get("company_name") or profile.get("company_name") or "Vyastha Business"
    upi_qr_data = build_upi_qr_string(upi_id, company_name, calc_total, f"Invoice {inv_number}")
    
    # Auto-save buyer to customers collection if requested or non-empty
    buyer = data.buyer_details or {}
    if buyer.get("company_name"):
        existing_cust = await db.customers.find_one({"company_name": buyer.get("company_name"), "user_id": user_id})
        if not existing_cust:
            cust_count = await db.customers.count_documents({"user_id": user_id})
            await db.customers.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "customer_id": buyer.get("customer_id") or f"CUST-{cust_count+1:03d}",
                "company_name": buyer.get("company_name"),
                "contact_person": buyer.get("contact_person", ""),
                "gstin_number": buyer.get("gstin_number", ""),
                "phone": buyer.get("phone", ""),
                "email": buyer.get("email", ""),
                "address": buyer.get("address", ""),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
    inv_id = str(uuid.uuid4())
    inv_doc = {
        "id": inv_id,
        "user_id": user_id,
        "invoice_number": inv_number,
        "invoice_date": data.invoice_date,
        "shipping_date": data.shipping_date or "",
        "customer_id": data.customer_id or buyer.get("customer_id", ""),
        "vehicle_number": data.vehicle_number or "",
        "reference_quotation_number": data.reference_quotation_number or "",
        "seller_details": data.seller_details or profile,
        "buyer_details": data.buyer_details,
        "line_items": line_items_data,
        "subtotal": round(calc_subtotal, 2),
        "tax_rate": data.tax_rate,
        "tax_amount": round(calc_tax_amt, 2),
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "discount_amount": round(discount_amt, 2),
        "total_amount": round(calc_total, 2),
        "terms_and_conditions": data.terms_and_conditions or profile.get("default_terms", ""),
        "bank_details": data.bank_details or profile.get("bank_details", {}),
        "signature_url": data.signature_url or profile.get("signature_image", ""),
        "notes": data.notes or "",
        "status": data.status,
        "payment_status": data.payment_status,
        "amount_paid": float(data.amount_paid),
        "balance_due": max(0.0, round(calc_total - float(data.amount_paid), 2)),
        "upi_qr_data": upi_qr_data,
        "created_date_str": today_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(inv_doc)
    inv_doc.pop("_id", None)
    
    # Deduct stock if invoice finalized or sent and auto_deduct_inventory is true
    if data.status in ["finalized", "sent", "paid"] and data.auto_deduct_inventory:
        await deduct_inventory_for_items(user_id, line_items_data, inv_number)
        
    return inv_doc

@api_router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    data: InvoiceCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    existing = await db.invoices.find_one({"id": invoice_id, "user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    line_items_data = [item.model_dump() for item in data.line_items]
    calc_subtotal = sum(float(item.get("quantity", 0)) * float(item.get("unit_price", 0)) for item in line_items_data)
    
    discount_amt = 0.0
    if data.discount_type == "percentage":
        discount_amt = (calc_subtotal * data.discount_value) / 100.0
    else:
        discount_amt = data.discount_value
    discount_amt = max(0.0, min(discount_amt, calc_subtotal))
    
    taxable = max(0.0, calc_subtotal - discount_amt)
    calc_tax_amt = (taxable * data.tax_rate) / 100.0
    calc_total = taxable + calc_tax_amt
    calc_amount_in_words = amount_in_words(calc_total)
    seller_state = data.seller_details.get("state_code", "")
    buyer_state = data.buyer_details.get("state_code", "")
    gst_split = calculate_gst_split(calc_tax_amt, seller_state, buyer_state)
    
    upi_id = data.seller_details.get("bank_details", {}).get("upi_id") or "business@upi"
    company_name = data.seller_details.get("company_name") or "Vyastha Business"
    upi_qr_data = build_upi_qr_string(upi_id, company_name, calc_total, f"Invoice {existing.get('invoice_number')}")
    
    # Check stock transition
    old_status = existing.get("status")
    new_status = data.status
    if old_status == "draft" and new_status in ["finalized", "sent", "paid"] and data.auto_deduct_inventory:
        await deduct_inventory_for_items(user_id, line_items_data, existing.get("invoice_number"))
    elif old_status in ["finalized", "sent", "paid"] and new_status == "cancelled":
        await restore_inventory_for_items(user_id, existing.get("line_items", []), existing.get("invoice_number"))
        
    update_doc = {
        "invoice_date": data.invoice_date,
        "shipping_date": data.shipping_date or "",
        "customer_id": data.customer_id or "",
        "vehicle_number": data.vehicle_number or "",
        "reference_quotation_number": data.reference_quotation_number or "",
        "seller_details": data.seller_details,
        "buyer_details": data.buyer_details,
        "line_items": line_items_data,
        "subtotal": round(calc_subtotal, 2),
        "tax_rate": data.tax_rate,
        "tax_amount": round(calc_tax_amt, 2),
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "discount_amount": round(discount_amt, 2),
        "total_amount": round(calc_total, 2),
        "amount_in_words": calc_amount_in_words,
        "cgst_amount": gst_split["cgst_amount"],
        "sgst_amount": gst_split["sgst_amount"],
        "igst_amount": gst_split["igst_amount"],
        "terms_and_conditions": data.terms_and_conditions,
        "bank_details": data.bank_details,
        "signature_url": data.signature_url,
        "notes": data.notes or "",
        "status": data.status,
        "payment_status": data.payment_status,
        "amount_paid": float(data.amount_paid),
        "balance_due": max(0.0, round(calc_total - float(data.amount_paid), 2)),
        "upi_qr_data": upi_qr_data,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.update_one({"id": invoice_id, "user_id": user_id}, {"$set": update_doc})
    updated = await db.invoices.find_one({"id": invoice_id, "user_id": user_id}, {"_id": 0})
    return updated

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    existing = await db.invoices.find_one({"id": invoice_id, "user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.invoices.delete_one({"id": invoice_id, "user_id": user_id})
    return {"message": "Invoice deleted successfully"}



@api_router.get("/quotations")
async def get_quotations(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    data_owner_id = await get_business_data_owner_id(user)

    query: Dict[str, Any] = {
        "user_id": data_owner_id
    }

    if status:
        query["status"] = status

    quotations = await db.quotations.find(
        query,
        {"_id": 0}
    ).sort(
        "created_at",
        -1
    ).to_list(1000)

    return quotations


@api_router.post("/quotations")
async def create_quotation(
    data: QuotationCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    today_str = date.today().isoformat()

    if data.status == "draft":
        today_count = await get_daily_draft_count(user_id)
        if today_count >= 50:
            raise HTTPException(
                status_code=400,
                detail="Daily draft limit reached (50 drafts/day maximum)."
            )

    profile = await db.company_profiles.find_one(
        {"user_id": user_id},
        {"_id": 0}
    ) or {}

    prefix = profile.get("quotation_prefix") or "QUO"

    quo_number = data.quotation_number
    if not quo_number:
        quo_number = await get_next_sequence(
            user_id,
            "quotation",
            prefix
        )

    line_items_data = [
        item.model_dump()
        for item in data.line_items
    ]

    calc_subtotal = sum(
        float(item.get("quantity", 0)) *
        float(item.get("unit_price", 0))
        for item in line_items_data
    )

    discount_amt = 0.0

    if data.discount_type == "percentage":
        discount_amt = (
            calc_subtotal * data.discount_value
        ) / 100.0
    else:
        discount_amt = data.discount_value

    discount_amt = max(
        0.0,
        min(discount_amt, calc_subtotal)
    )

    taxable = max(
        0.0,
        calc_subtotal - discount_amt
    )

    calc_tax_amt = (
        taxable * data.tax_rate
    ) / 100.0

    calc_total = taxable + calc_tax_amt

    # GST split
    gst_split = {
        "cgst_amount": round(calc_tax_amt / 2, 2),
        "sgst_amount": round(calc_tax_amt / 2, 2),
        "igst_amount": 0.0,
    }

    # Amount in words
    calc_amount_in_words = amount_in_words(calc_total)

    seller = data.seller_details or profile

    upi_id = (
        seller.get("bank_details", {}).get("upi_id")
        or profile.get("bank_details", {}).get("upi_id")
        or "business@upi"
    )

    company_name = (
        seller.get("company_name")
        or profile.get("company_name")
        or "Vyastha Business"
    )

    upi_qr_data = build_upi_qr_string(
        upi_id,
        company_name,
        calc_total,
        f"Quote {quo_number}"
    )

    quo_id = str(uuid.uuid4())

    quo_doc = {
        "id": quo_id,
        "user_id": user_id,
        "quotation_number": quo_number,
        "quotation_date": data.quotation_date,
        "valid_until": data.valid_until or "",
        "customer_id": data.customer_id or "",
        "vehicle_number": data.vehicle_number or "",
        "seller_details": data.seller_details or profile,
        "buyer_details": data.buyer_details,
        "line_items": line_items_data,
        "subtotal": round(calc_subtotal, 2),
        "tax_rate": data.tax_rate,
        "tax_amount": round(calc_tax_amt, 2),
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "discount_amount": round(discount_amt, 2),
        "total_amount": round(calc_total, 2),
        "amount_in_words": calc_amount_in_words,
        "cgst_amount": gst_split["cgst_amount"],
        "sgst_amount": gst_split["sgst_amount"],
        "igst_amount": gst_split["igst_amount"],
        "terms_and_conditions": (
            data.terms_and_conditions
            or profile.get("default_terms", "")
        ),
        "bank_details": (
            data.bank_details
            or profile.get("bank_details", {})
        ),
        "signature_url": (
            data.signature_url
            or profile.get("signature_image", "")
        ),
        "notes": data.notes or "",
        "status": data.status,
        "upi_qr_data": upi_qr_data,
        "created_date_str": today_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.quotations.insert_one(quo_doc)

    quo_doc.pop("_id", None)

    return quo_doc
@api_router.post("/quotations/{quotation_id}/convert-to-invoice")
async def convert_quotation_to_invoice(
    quotation_id: str,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    quo = await db.quotations.find_one({"$or": [{"id": quotation_id}, {"quotation_number": quotation_id}], "user_id": user_id}, {"_id": 0})
    if not quo:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quo.get("status") == "converted":
        raise HTTPException(status_code=409, detail=f"Quotation already converted to invoice {quo.get('converted_invoice_number', '')}")
        
    profile = await db.company_profiles.find_one({"user_id": user_id}, {"_id": 0}) or {}
    prefix = profile.get("invoice_prefix") or "INV"
    inv_number = await get_next_sequence(user_id, "invoice", prefix)
    
    today_str = date.today().isoformat()
    inv_id = str(uuid.uuid4())
    
    upi_id = quo.get("seller_details", {}).get("bank_details", {}).get("upi_id") or profile.get("bank_details", {}).get("upi_id") or "business@upi"
    company_name = quo.get("seller_details", {}).get("company_name") or profile.get("company_name") or "Vyastha Business"
    upi_qr = build_upi_qr_string(upi_id, company_name, quo.get("total_amount", 0), f"Invoice {inv_number}")
    
    inv_doc = {
        "id": inv_id,
        "user_id": user_id,
        "invoice_number": inv_number,
        "invoice_date": today_str,
        "shipping_date": "",
        "customer_id": quo.get("customer_id", ""),
        "vehicle_number": quo.get("vehicle_number", ""),
        "reference_quotation_number": quo.get("quotation_number"),
        "seller_details": quo.get("seller_details", {}),
        "buyer_details": quo.get("buyer_details", {}),
        "line_items": quo.get("line_items", []),
        "subtotal": quo.get("subtotal", 0),
        "tax_rate": quo.get("tax_rate", 18.0),
        "tax_amount": quo.get("tax_amount", 0),
        "discount_type": quo.get("discount_type", "amount"),
        "discount_value": quo.get("discount_value", 0),
        "discount_amount": quo.get("discount_amount", 0),
        "total_amount": quo.get("total_amount", 0),
        "terms_and_conditions": quo.get("terms_and_conditions", ""),
        "bank_details": quo.get("bank_details", {}),
        "signature_url": quo.get("signature_url", ""),
        "notes": quo.get("notes", ""),
        "status": "finalized",
        "payment_status": "unpaid",
        "amount_paid": 0.0,
        "balance_due": quo.get("total_amount", 0),
        "upi_qr_data": upi_qr,
        "created_date_str": today_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(inv_doc)
    # Deduct stock
    await deduct_inventory_for_items(user_id, quo.get("line_items", []), inv_number)
    # Update quotation status
    await db.quotations.update_one({"id": quo["id"], "user_id": user_id}, {"$set": {"status": "converted", "converted_invoice_number": inv_number}})
    
    inv_doc.pop("_id", None)
    return {
        "message": f"Successfully converted {quo.get('quotation_number')} to {inv_number}",
        "invoice": inv_doc
    }

@api_router.delete("/quotations/{quotation_id}")
async def delete_quotation(
    quotation_id: str,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("invoicing")),
):
    user_id = user.get("id") or str(user["_id"])
    await db.quotations.delete_one({"id": quotation_id, "user_id": user_id})
    return {"message": "Quotation deleted"}

## ==========================================
# Payments Module
# ==========================================
@api_router.get("/payments")
async def get_payments(
    filter: str = Query(
        "today",
        description="Filter payments by 'today' or 'all'"
    ),
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("payment_due_management")),
):
    # Staff users should see payments belonging to
    # the business owner's existing data.
    data_owner_id = await get_business_data_owner_id(user)

    query: Dict[str, Any] = {
        "user_id": data_owner_id
    }

    if filter == "today":
        today_str = date.today().isoformat()
        query["payment_date"] = today_str

    payments = await db.payments.find(
        query,
        {"_id": 0}
    ).sort(
        "created_at",
        -1
    ).to_list(1000)

    # Summary calculation
    total_collected = sum(
        p.get("amount", 0)
        for p in payments
        if p.get("status") == "successful"
    )

    return {
        "filter": filter,
        "total_amount": round(total_collected, 2),
        "count": len(payments),
        "payments": payments
    }

@api_router.post("/payments")
async def record_payment(
    data: PaymentCreate,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("payment_due_management")),
):
    user_id = user.get("id") or str(user["_id"])

    if float(data.amount) <= 0:
        raise HTTPException(
            status_code=422,
            detail="Payment amount must be greater than 0"
        )

    # -------------------------------------------------
    # Find linked invoice
    # -------------------------------------------------
    linked_invoice = None

    if data.invoice_id:
        linked_invoice = await db.invoices.find_one({
            "id": data.invoice_id,
            "user_id": user_id
        })

    if not linked_invoice and data.invoice_number:
        linked_invoice = await db.invoices.find_one({
            "invoice_number": data.invoice_number,
            "user_id": user_id
        })

    # -------------------------------------------------
    # Verify payment amount is not greater than balance
    # -------------------------------------------------
    if linked_invoice:
        balance_due = float(
            linked_invoice.get(
                "balance_due",
                linked_invoice.get("total_amount", 0)
            )
        )

        if float(data.amount) > balance_due + 0.01:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Payment amount ₹{data.amount} "
                    f"exceeds invoice balance due ₹{balance_due:.2f}"
                )
            )

    # -------------------------------------------------
    # Create payment record
    # -------------------------------------------------
    pay_id = str(uuid.uuid4())

    pay_doc = {
        "id": pay_id,
        "user_id": user_id,
        "invoice_id": data.invoice_id or "",
        "invoice_number": data.invoice_number,
        "customer_name": data.customer_name,
        "amount": round(float(data.amount), 2),
        "payment_date": data.payment_date,
        "payment_method": data.payment_method,
        "transaction_ref": (
            data.transaction_ref
            or f"TXN-{uuid.uuid4().hex[:8].upper()}"
        ),
        "notes": data.notes or "",
        "status": data.status,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.payments.insert_one(pay_doc)
    pay_doc.pop("_id", None)

    # -------------------------------------------------
    # If payment is linked to an invoice and successful,
    # update invoice balance + payment status + QR amount
    # -------------------------------------------------
    if data.status == "successful" and linked_invoice:

        invoice = linked_invoice

        # Existing paid amount
        old_paid = float(invoice.get("amount_paid", 0))

        # Add new payment
        new_paid = old_paid + float(data.amount)

        # Invoice total
        total_amt = float(invoice.get("total_amount", 0))

        # Remaining balance
        new_balance = max(0.0, total_amt - new_paid)

        # Determine payment status
        new_status = (
            "paid"
            if new_balance <= 0.01
            else "partially_paid"
        )

        # -------------------------------------------------
        # Generate NEW UPI QR for remaining balance
        # -------------------------------------------------
        seller = invoice.get("seller_details") or {}
        bank_details = invoice.get("bank_details") or {}

        upi_id = (
            bank_details.get("upi_id")
            or seller.get("bank_details", {}).get("upi_id")
            or "business@upi"
        )

        company_name = (
            seller.get("company_name")
            or "Vyastha Business"
        )

        updated_upi_qr_data = build_upi_qr_string(
            upi_id,
            company_name,
            new_balance,
            f"Invoice {invoice.get('invoice_number', '')}"
        )

        # -------------------------------------------------
        # Update invoice
        # -------------------------------------------------
        await db.invoices.update_one(
            {
                "id": invoice["id"],
                "user_id": user_id
            },
            {
                "$set": {
                    "amount_paid": round(new_paid, 2),
                    "balance_due": round(new_balance, 2),
                    "payment_status": new_status,
                    "upi_qr_data": updated_upi_qr_data,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

    return {
        "success": True,
        "message": "Payment recorded successfully",
        "payment": pay_doc
    }


# ==========================================
# Vyastha AI Business Assistant
# ==========================================

class AskBody(BaseModel):
    question: str
    language: str = "hinglish"
    session_id: Optional[str] = None


@api_router.get("/ai/suggestions")
async def ai_suggestions(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("ai_business_assistant")),
):
    data_owner_id = await get_business_data_owner_id(user)
    return await ai_svc.suggested_questions(data_owner_id)


@api_router.get("/ai/alerts")
async def ai_alerts(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("ai_business_assistant")),
):
    data_owner_id = await get_business_data_owner_id(user)
    return await ai_data_svc.get_business_alerts(data_owner_id)


@api_router.post("/ai/ask")
async def ai_ask(
    body: AskBody,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("ai_business_assistant")),
):
    if not body.question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty"
        )

    data_owner_id = await get_business_data_owner_id(user)

    result = await ai_svc.ask(
        user_id=data_owner_id,
        question=body.question.strip()[:1000],
        language=body.language,
        business_name=user.get("company_name", "your business"),
        session_id=body.session_id,
    )

    return result



# ==========================================
# Dashboard Statistics & Overview
# ==========================================
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("basic_analytics")),
):
    data_owner_id = await get_business_data_owner_id(user)
    today_str = date.today().isoformat()
        
    all_invoices = await db.invoices.find(
        {"user_id": data_owner_id},
        {"_id": 0}
    ).to_list(1000)

    all_payments = await db.payments.find(
        {"user_id": data_owner_id},
        {"_id": 0}
    ).to_list(1000)

    all_products = await db.products.find(
        {"user_id": data_owner_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_revenue = sum(inv.get("total_amount", 0) for inv in all_invoices if inv.get("status") != "cancelled")
    total_collected = sum(p.get("amount", 0) for p in all_payments if p.get("status") == "successful")
    today_collected = sum(p.get("amount", 0) for p in all_payments if p.get("status") == "successful" and p.get("payment_date") == today_str)
    
    unpaid_invoices = [inv for inv in all_invoices if inv.get("status") != "cancelled" and inv.get("payment_status") != "paid"]
    total_outstanding = sum(inv.get("balance_due", inv.get("total_amount", 0)) for inv in unpaid_invoices)
    
    low_stock_count = sum(1 for p in all_products if p.get("stock_quantity", 0) <= p.get("low_stock_threshold", 10))
    
    today_draft_count = await get_daily_draft_count(data_owner_id)
    
    recent_invoices = sorted(all_invoices, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_payments = sorted(all_payments, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_collected": round(total_collected, 2),
        "today_collected": round(today_collected, 2),
        "total_outstanding": round(total_outstanding, 2),
        "total_invoices_count": len(all_invoices),
        "unpaid_invoices_count": len(unpaid_invoices),
        "low_stock_count": low_stock_count,
        "today_drafts_count": today_draft_count,
        "max_daily_drafts": 50,
        "recent_invoices": recent_invoices,
        "recent_payments": recent_payments
    }



@api_router.get("/plans")
async def list_plans():
    """Saare active subscription plans return karo."""
    documents = await db.plans.find({"active": True}).sort("rank", 1).to_list(50)
    for doc in documents:
        doc.pop("_id", None)
    return documents


@api_router.post("/billing/create-order")
async def create_razorpay_order(
    plan_slug: str,
    billing_cycle: str = "monthly",
    user: dict = Depends(get_current_user),
):
    """Ek business ke liye Razorpay order banao (payment start karne ke liye)."""
    plan = plans_lib.get_default_plan(plan_slug)
    amount_rupees = plans_lib.get_plan_price(plan_slug, billing_cycle)
    amount_paise = plans_lib.rupees_to_paise(amount_rupees)

    if not razorpay_client.is_configured():
        raise HTTPException(status_code=500, detail="Payment gateway not configured")

    client = razorpay_client.get_client()
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "notes": {
            "user_id": user["id"],
            "plan_slug": plan_slug,
        }
    })

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "razorpay_key_id": razorpay_client.key_id(),
        "plan_name": plan["name"],
    }

    # Include all API routes
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router, prefix="/api")
app.include_router(team_router, prefix="/api")
app.include_router(auth_router, prefix="/api")