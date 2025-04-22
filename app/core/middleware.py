from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
import uuid
import time
import json
from typing import Union, Dict, Any

class ErrorCode:
    SUCCESS = 200
    PARAM_ERROR = 400
    AUTH_ERROR = 401
    PERMISSION_ERROR = 403
    RESOURCE_NOT_FOUND = 404
    INTERNAL_ERROR = 500

    @classmethod
    def from_http_status(cls, status_code: int) -> int:
        """将HTTP状态码转换为业务错误码"""
        if status_code < 400:
            return cls.SUCCESS
        elif status_code == 400:
            return cls.PARAM_ERROR
        elif status_code == 401:
            return cls.AUTH_ERROR
        elif status_code == 403:
            return cls.PERMISSION_ERROR
        elif status_code == 404:
            return cls.RESOURCE_NOT_FOUND
        else:
            return cls.INTERNAL_ERROR

class ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 如果不是JSON响应，直接返回
            if not isinstance(response, JSONResponse):
                return response
            
            # 获取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            try:
                # 解析响应内容
                response_data = json.loads(response_body.decode())
            except json.JSONDecodeError:
                # 如果无法解析为JSON，使用原始响应
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            
            # 构建统一响应格式
            unified_response = {
                "request_id": request_id,
                "path": str(request.url.path),
                "code": response.status_code,
                "status": "success" if response.status_code < 400 else "error",
                "data": response_data.get("data") if isinstance(response_data, dict) else response_data,
                "message": response_data.get("message", "success" if response.status_code < 400 else "error"),
                "timestamp": int(time.time() * 1000),
                "duration": int((time.time() - start_time) * 1000)  # 毫秒
            }
            
            # 返回统一响应
            return JSONResponse(
                content=unified_response,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            # 处理异常情况
            return JSONResponse(
                content={
                    "request_id": request_id,
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