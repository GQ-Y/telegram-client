from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uuid
import time
import json

class ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 获取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # 解析响应内容
            response_data = json.loads(response_body.decode())
            
            # 构建统一响应格式
            unified_response = {
                "request_id": request_id,
                "path": str(request.url.path),
                "code": response.status_code,
                "status": "success" if response.status_code == 200 else "error",
                "data": response_data.get("data", {}),
                "message": response_data.get("message", ""),
                "timestamp": int(time.time() * 1000),
                "duration": int((time.time() - start_time) * 1000)  # 毫秒
            }
            
            # 返回统一响应
            return JSONResponse(
                content=unified_response,
                status_code=response.status_code,
                headers=response.headers
            )
            
        except Exception as e:
            # 处理异常情况
            return JSONResponse(
                content={
                    "request_id": request_id,
                    "path": str(request.url.path),
                    "code": 500,
                    "status": "error",
                    "data": {},
                    "message": str(e),
                    "timestamp": int(time.time() * 1000),
                    "duration": int((time.time() - start_time) * 1000)
                },
                status_code=500
            ) 