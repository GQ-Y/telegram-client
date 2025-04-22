# API package initialization 
from fastapi import APIRouter
from app.api import auth

api_router = APIRouter()

# 注册认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"]) 