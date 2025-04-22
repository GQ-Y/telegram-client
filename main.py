from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import ResponseMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict

# 创建FastAPI应用
app = FastAPI(
    title="Telegram Client Manager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=JSONResponse
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from app.api import auth

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])

# 最后添加响应中间件
app.add_middleware(ResponseMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 