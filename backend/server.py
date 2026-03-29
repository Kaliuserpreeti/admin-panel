from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncpg
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database connection pools
db_pools = {}

# Database configurations
DB_CONFIGS = {
    "neondb": "postgresql://neondb_owner:npg_hW0AyxRbrD9I@ep-solitary-sunset-a8uvikxx-pooler.eastus2.azure.neon.tech/neondb?sslmode=require",
    "pmfby": "postgresql://neondb_owner:npg_hW0AyxRbrD9I@ep-solitary-sunset-a8uvikxx-pooler.eastus2.azure.neon.tech/pmfby_idpass?sslmode=require",
    "krp": "postgresql://neondb_owner:npg_hW0AyxRbrD9I@ep-solitary-sunset-a8uvikxx-pooler.eastus2.azure.neon.tech/krp_idpass?sslmode=require",
    "byajanudan": "postgresql://neondb_owner:npg_hW0AyxRbrD9I@ep-solitary-sunset-a8uvikxx-pooler.eastus2.azure.neon.tech/byajanudan_idpass?sslmode=require",
    "idpass": "postgresql://neondb_owner:npg_hW0AyxRbrD9I@ep-solitary-sunset-a8uvikxx-pooler.eastus2.azure.neon.tech/IDPass?sslmode=require"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create connection pools
    for db_key, db_url in DB_CONFIGS.items():
        try:
            db_pools[db_key] = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"✅ Connected to {db_key} database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to {db_key}: {str(e)}")
    
    yield
    
    # Shutdown: Close all pools
    for db_key, pool in db_pools.items():
        await pool.close()
        logger.info(f"Closed {db_key} connection pool")

# Create the main app
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class PendingUser(BaseModel):
    sr: int
    userid: str
    user_pass_hash: str
    created_on: Optional[datetime]
    pacs_name: Optional[str]

class AppUser(BaseModel):
    sr: int
    userid: str
    user_pass_hash: str
    active: bool
    approved_on: Optional[datetime]
    pacs_name: Optional[str]
    last_access_time: Optional[datetime]

class PendingIPWS(BaseModel):
    sr: int
    user_id: Optional[str] = None
    user_name: Optional[str] = None  # For IDPass database
    pass_: str
    name: str
    pacs_name: Optional[str]
    branch: Optional[str]
    dist: Optional[str]
    state: Optional[str]
    mobile: Optional[int]

class IPWS(BaseModel):
    sr: int
    user_id: Optional[str] = None
    user_name: Optional[str] = None  # For IDPass database
    pass_: str
    name: str
    pacs_name: Optional[str]
    branch: Optional[str]
    dist: Optional[str]
    state: Optional[str]
    mobile: Optional[int]
    approved_on: Optional[datetime]
    last_access_time: Optional[datetime]

# ==================== HELPER FUNCTIONS ====================

def get_pool(dbkey: str):
    """Get database pool for given dbkey"""
    if dbkey not in db_pools:
        raise HTTPException(status_code=400, detail=f"Invalid database key: {dbkey}")
    return db_pools[dbkey]

# ==================== DB1 (neondb) ENDPOINTS ====================

@api_router.get("/{dbkey}/pending")
async def get_pending(dbkey: str):
    """Get all pending users/requests"""
    try:
        pool = get_pool(dbkey)
        
        if dbkey == "neondb":
            query = "SELECT * FROM pending_users ORDER BY sr DESC"
        else:
            query = "SELECT * FROM pending_ipws ORDER BY sr DESC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            result = [dict(row) for row in rows]
            
            # Convert pass field to pass_ for consistency
            if dbkey != "neondb":
                for item in result:
                    if 'pass' in item:
                        item['pass_'] = item.pop('pass')
            
            return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pending for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/{dbkey}/approved")
async def get_approved(dbkey: str):
    """Get all approved/active users"""
    try:
        pool = get_pool(dbkey)
        
        if dbkey == "neondb":
            query = "SELECT * FROM app_users WHERE active = true ORDER BY sr DESC"
        else:
            query = "SELECT * FROM ipws ORDER BY sr DESC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            result = [dict(row) for row in rows]
            
            # Convert pass field to pass_ for consistency
            if dbkey != "neondb":
                for item in result:
                    if 'pass' in item:
                        item['pass_'] = item.pop('pass')
            
            return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching approved for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/neondb/inactive")
async def get_inactive():
    """Get all inactive users (DB1 only)"""
    try:
        pool = get_pool("neondb")
        query = "SELECT * FROM app_users WHERE active = false ORDER BY sr DESC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            result = [dict(row) for row in rows]
            return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error fetching inactive users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/{dbkey}/approve/{sr}")
async def approve_user(dbkey: str, sr: int):
    """Approve a pending user/request"""
    try:
        pool = get_pool(dbkey)
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                if dbkey == "neondb":
                    # Get pending user
                    pending = await conn.fetchrow(
                        "SELECT * FROM pending_users WHERE sr = $1", sr
                    )
                    if not pending:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    # Insert into app_users
                    await conn.execute("""
                        INSERT INTO app_users (sr, userid, user_pass_hash, active, approved_on, pacs_name)
                        VALUES ($1, $2, $3, true, NOW(), $4)
                    """, pending['sr'], pending['userid'], pending['user_pass_hash'], pending['pacs_name'])
                    
                    # Delete from pending_users
                    await conn.execute("DELETE FROM pending_users WHERE sr = $1", sr)
                else:
                    # Get pending ipws
                    pending = await conn.fetchrow(
                        "SELECT * FROM pending_ipws WHERE sr = $1", sr
                    )
                    if not pending:
                        raise HTTPException(status_code=404, detail="Request not found")
                    
                    # Determine user field name
                    user_field = "user_name" if dbkey == "idpass" else "user_id"
                    user_value = pending.get('user_name') or pending.get('user_id')
                    
                    # Insert into ipws
                    if dbkey == "idpass":
                        await conn.execute("""
                            INSERT INTO ipws (sr, user_name, pass, name, pacs_name, branch, dist, state, mobile, approved_on)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                        """, pending['sr'], user_value, pending['pass'], pending['name'],
                           pending['pacs_name'], pending['branch'], pending['dist'], 
                           pending['state'], pending['mobile'])
                    else:
                        await conn.execute("""
                            INSERT INTO ipws (sr, user_id, pass, name, pacs_name, branch, dist, state, mobile, approved_on)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                        """, pending['sr'], user_value, pending['pass'], pending['name'],
                           pending['pacs_name'], pending['branch'], pending['dist'], 
                           pending['state'], pending['mobile'])
                    
                    # Delete from pending_ipws
                    await conn.execute("DELETE FROM pending_ipws WHERE sr = $1", sr)
        
        return {"success": True, "message": "Approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/{dbkey}/reject/{sr}")
async def reject_user(dbkey: str, sr: int):
    """Reject a pending user/request"""
    try:
        pool = get_pool(dbkey)
        
        async with pool.acquire() as conn:
            if dbkey == "neondb":
                result = await conn.execute("DELETE FROM pending_users WHERE sr = $1", sr)
            else:
                result = await conn.execute("DELETE FROM pending_ipws WHERE sr = $1", sr)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Record not found")
        
        return {"success": True, "message": "Rejected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/{dbkey}/deactivate/{sr}")
async def deactivate_user(dbkey: str, sr: int):
    """Deactivate an approved user (move back to pending)"""
    try:
        pool = get_pool(dbkey)
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                if dbkey == "neondb":
                    # Get from app_users
                    user = await conn.fetchrow(
                        "SELECT * FROM app_users WHERE sr = $1", sr
                    )
                    if not user:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    # Set active to false
                    await conn.execute(
                        "UPDATE app_users SET active = false WHERE sr = $1", sr
                    )
                    
                    # Insert into pending_users
                    # Check if already exists in pending
                    existing = await conn.fetchval(
                        "SELECT COUNT(*) FROM pending_users WHERE sr = $1", user['sr']
                    )
                    if existing == 0:
                        await conn.execute("""
                            INSERT INTO pending_users (sr, userid, user_pass_hash, created_on, pacs_name)
                            VALUES ($1, $2, $3, NOW(), $4)
                        """, user['sr'], user['userid'], user['user_pass_hash'], user['pacs_name'])
                else:
                    # Get from ipws
                    ipws = await conn.fetchrow(
                        "SELECT * FROM ipws WHERE sr = $1", sr
                    )
                    if not ipws:
                        raise HTTPException(status_code=404, detail="Record not found")
                    
                    # Determine user field name
                    user_field = "user_name" if dbkey == "idpass" else "user_id"
                    user_value = ipws.get('user_name') or ipws.get('user_id')
                    
                    # Insert back into pending_ipws
                    # Check if already exists
                    existing = await conn.fetchval(
                        "SELECT COUNT(*) FROM pending_ipws WHERE sr = $1", ipws['sr']
                    )
                    if existing == 0:
                        if dbkey == "idpass":
                            await conn.execute("""
                                INSERT INTO pending_ipws (sr, user_name, pass, name, pacs_name, branch, dist, state, mobile)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            """, ipws['sr'], user_value, ipws['pass'], ipws['name'],
                               ipws['pacs_name'], ipws['branch'], ipws['dist'], 
                               ipws['state'], ipws['mobile'])
                        else:
                            await conn.execute("""
                                INSERT INTO pending_ipws (sr, user_id, pass, name, pacs_name, branch, dist, state, mobile)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            """, ipws['sr'], user_value, ipws['pass'], ipws['name'],
                               ipws['pacs_name'], ipws['branch'], ipws['dist'], 
                               ipws['state'], ipws['mobile'])
                    
                    # Delete from ipws
                    await conn.execute("DELETE FROM ipws WHERE sr = $1", sr)
        
        return {"success": True, "message": "Deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/{dbkey}/delete/{sr}")
async def delete_user(dbkey: str, sr: int):
    """Permanently delete an approved user"""
    try:
        pool = get_pool(dbkey)
        
        async with pool.acquire() as conn:
            if dbkey == "neondb":
                result = await conn.execute("DELETE FROM app_users WHERE sr = $1", sr)
            else:
                result = await conn.execute("DELETE FROM ipws WHERE sr = $1", sr)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Record not found")
        
        return {"success": True, "message": "Deleted permanently"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting for {dbkey}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/neondb/reactivate/{sr}")
async def reactivate_user(sr: int):
    """Reactivate an inactive user (DB1 only)"""
    try:
        pool = get_pool("neondb")
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE app_users 
                SET active = true, approved_on = NOW() 
                WHERE sr = $1 AND active = false
            """, sr)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="User not found or already active")
        
        return {"success": True, "message": "Reactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/counts")
async def get_all_counts():
    """Get counts for all databases and statuses"""
    try:
        counts = {}
        
        for dbkey in DB_CONFIGS.keys():
            pool = get_pool(dbkey)
            
            async with pool.acquire() as conn:
                if dbkey == "neondb":
                    pending_count = await conn.fetchval("SELECT COUNT(*) FROM pending_users")
                    active_count = await conn.fetchval("SELECT COUNT(*) FROM app_users WHERE active = true")
                    inactive_count = await conn.fetchval("SELECT COUNT(*) FROM app_users WHERE active = false")
                    counts[dbkey] = {
                        "pending": pending_count,
                        "approved": active_count,
                        "inactive": inactive_count
                    }
                else:
                    pending_count = await conn.fetchval("SELECT COUNT(*) FROM pending_ipws")
                    approved_count = await conn.fetchval("SELECT COUNT(*) FROM ipws")
                    counts[dbkey] = {
                        "pending": pending_count,
                        "approved": approved_count
                    }
        
        return {"success": True, "data": counts}
    except Exception as e:
        logger.error(f"Error fetching counts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Admin Panel API is running", "databases": list(DB_CONFIGS.keys())}

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = {}
    for dbkey in DB_CONFIGS.keys():
        try:
            pool = db_pools.get(dbkey)
            if pool:
                db_status[dbkey] = "connected"
            else:
                db_status[dbkey] = "disconnected"
        except Exception:
            db_status[dbkey] = "error"
    
    return {
        "status": "healthy",
        "databases": db_status,
        "total_databases": len(DB_CONFIGS)
    }
