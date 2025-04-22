from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Form, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_superuser
from app.models.models import User
from app.schemas.auth import Token, TokenData, UserInDB, UserCreate
from app.core.middleware import ErrorCode
from pydantic import BaseModel, Field, ConfigDict
from fastapi.responses import JSONResponse
import uuid
import time
import secrets

router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 客户端配置
CLIENTS = {
    "swagger": {
        "client_id": "swagger",
        "client_secret": "swagger",  # 开发环境使用简单密码
        "allowed_scopes": ["me", "items"],
        "redirect_uris": ["http://localhost:8000/docs/oauth2-redirect"]
    }
}

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
    scopes={
        "me": "Read information about the current user.",
        "items": "Read items."
    }
)

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名", example="admin")
    password: str = Field(..., description="密码", example="admin123")
    grant_type: str = Field("password", description="授权类型", example="password")
    scope: str = Field("", description="授权范围", example="me items")
    client_id: Optional[str] = Field(None, description="客户端ID")
    client_secret: Optional[str] = Field(None, description="客户端密钥")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "admin123",
                "grant_type": "password",
                "scope": "me items",
                "client_id": "swagger",
                "client_secret": "swagger"
            }
        }
    )

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    scope: str = Field(..., description="授权范围")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "scope": "me items"
            }
        }
    )

class LoginResponse(BaseModel):
    """登录响应模型"""
    data: TokenResponse = Field(..., description="令牌数据")
    message: str = Field(..., description="响应消息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "scope": "me items"
                },
                "message": "登录成功"
            }
        }
    )

class ClientCreate(BaseModel):
    """客户端创建模型"""
    client_name: str = Field(..., description="客户端名称")
    allowed_scopes: List[str] = Field(..., description="允许的授权范围")
    redirect_uris: List[str] = Field(..., description="重定向URI列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_name": "测试客户端",
                "allowed_scopes": ["me", "items"],
                "redirect_uris": ["http://localhost:8000/docs/oauth2-redirect"]
            }
        }
    )

class ClientResponse(BaseModel):
    """客户端响应模型"""
    client_id: str = Field(..., description="客户端ID")
    client_secret: str = Field(..., description="客户端密钥")
    client_name: str = Field(..., description="客户端名称")
    allowed_scopes: List[str] = Field(..., description="允许的授权范围")
    redirect_uris: List[str] = Field(..., description="重定向URI列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "test_client",
                "client_secret": "your_client_secret",
                "client_name": "测试客户端",
                "allowed_scopes": ["me", "items"],
                "redirect_uris": ["http://localhost:8000/docs/oauth2-redirect"]
            }
        }
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_client(client_id: str, client_secret: str) -> bool:
    """验证客户端身份"""
    if client_id not in CLIENTS:
        return False
    return secrets.compare_digest(CLIENTS[client_id]["client_secret"], client_secret)

def verify_scopes(client_id: str, requested_scopes: List[str]) -> bool:
    """验证请求的scope是否合法"""
    if client_id not in CLIENTS:
        return False
    allowed_scopes = set(CLIENTS[client_id]["allowed_scopes"])
    return all(scope in allowed_scopes for scope in requested_scopes)

@router.post("/register", response_model=UserInDB)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """注册新用户（仅超级管理员可用）"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if user_in.email:
        db_email = db.query(User).filter(User.email == user_in.email).first()
        if db_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 创建新用户
    db_user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        email=user_in.email,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    
    Args:
        request (Request): FastAPI请求对象
        form_data (OAuth2PasswordRequestForm): OAuth2登录表单数据
        db (Session): 数据库会话
        
    Returns:
        JSONResponse: 统一格式的响应
    """
    # 记录请求开始时间
    start_time = time.time()
    
    try:
        # 处理客户端凭据
        client_id = form_data.client_id or "swagger"
        client_secret = form_data.client_secret or "swagger"
        
        # 验证客户端
        if not verify_client(client_id, client_secret):
            return JSONResponse(
                content={
                    "request_id": str(uuid.uuid4()),
                    "path": str(request.url.path),
                    "code": status.HTTP_401_UNAUTHORIZED,
                    "status": "error",
                    "data": None,
                    "message": "无效的客户端凭据",
                    "timestamp": int(time.time() * 1000),
                    "duration": int((time.time() - start_time) * 1000)
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # 处理 scope
        requested_scopes = form_data.scopes if form_data.scopes else ["me"]
        
        # 验证scope
        if not verify_scopes(client_id, requested_scopes):
            return JSONResponse(
                content={
                    "request_id": str(uuid.uuid4()),
                    "path": str(request.url.path),
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "data": None,
                    "message": "无效的授权范围",
                    "timestamp": int(time.time() * 1000),
                    "duration": int((time.time() - start_time) * 1000)
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            return JSONResponse(
                content={
                    "request_id": str(uuid.uuid4()),
                    "path": str(request.url.path),
                    "code": status.HTTP_401_UNAUTHORIZED,
                    "status": "error",
                    "data": None,
                    "message": "用户名或密码错误",
                    "timestamp": int(time.time() * 1000),
                    "duration": int((time.time() - start_time) * 1000)
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        if not user.is_active:
            return JSONResponse(
                content={
                    "request_id": str(uuid.uuid4()),
                    "path": str(request.url.path),
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "data": None,
                    "message": "用户已被禁用",
                    "timestamp": int(time.time() * 1000),
                    "duration": int((time.time() - start_time) * 1000)
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "scopes": requested_scopes,
                "client_id": client_id
            }, 
            expires_delta=access_token_expires
        )
        
        # 返回统一响应格式
        return JSONResponse(
            content={
                "request_id": str(uuid.uuid4()),
                "path": str(request.url.path),
                "code": status.HTTP_200_OK,
                "status": "success",
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "scope": " ".join(requested_scopes),
                    "expires_in": int(access_token_expires.total_seconds())
                },
                "message": "登录成功",
                "timestamp": int(time.time() * 1000),
                "duration": int((time.time() - start_time) * 1000)
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "request_id": str(uuid.uuid4()),
                "path": str(request.url.path),
                "code": ErrorCode.INTERNAL_ERROR,
                "status": "error",
                "data": None,
                "message": str(e),
                "timestamp": int(time.time() * 1000),
                "duration": int((time.time() - start_time) * 1000)
            },
            status_code=500
        )

@router.get("/me")
async def read_users_me(
    security_scopes: SecurityScopes,
    current_user: User = Security(get_current_user, scopes=["me"])
):
    """获取当前用户信息"""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    return current_user 

@router.post("/register-client", response_model=ClientResponse)
async def register_client(
    client: ClientCreate,
    current_user: User = Depends(get_current_superuser)
):
    """
    注册新的OAuth2客户端
    
    Args:
        client: 客户端信息
        current_user: 当前用户（需要超级管理员权限）
        
    Returns:
        ClientResponse: 客户端注册信息
    """
    # 生成客户端ID和密钥
    client_id = secrets.token_urlsafe(16)
    client_secret = secrets.token_urlsafe(32)
    
    # 存储客户端信息
    CLIENTS[client_id] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": client.client_name,
        "allowed_scopes": client.allowed_scopes,
        "redirect_uris": client.redirect_uris
    }
    
    return ClientResponse(
        client_id=client_id,
        client_secret=client_secret,
        client_name=client.client_name,
        allowed_scopes=client.allowed_scopes,
        redirect_uris=client.redirect_uris
    ) 