# 多客户端多控制器管理系统架构设计文档

## 1. 系统概述

本系统是一个基于 Python 开发的多客户端多控制器管理系统，主要用于管理和控制多个客户端及其下属的控制器。系统采用 WebSocket 进行实时通信，使用 MySQL 存储核心数据，Redis 处理定时任务。

### 1.1 核心功能
- 客户端管理与控制
- 控制器生命周期管理
- 实时消息通信
- 定时任务处理
- 数据存储与管理

## 2. 系统架构

### 2.1 整体架构
系统采用分层架构设计，主要包含以下组件：

1. **服务端**
   - WebSocket 服务器
   - RESTful API 服务
   - 定时任务调度器
   - 数据访问层

2. **客户端**
   - C# 启动器
   - WebSocket 客户端
   - 控制器管理模块

3. **控制器**
   - 业务逻辑处理
   - 消息收发模块
   - 状态管理

### 2.2 技术栈选型

1. **后端服务**
   - 编程语言：Python 3.8+
   - Web 框架：FastAPI（提供高性能异步支持）
   - WebSocket：FastAPI WebSocket
   - 数据库：MySQL 8.0
   - 缓存与任务队列：Redis 6.0+
   - 定时任务：APScheduler
   - ORM：SQLAlchemy

2. **客户端**
   - 编程语言：C# (.NET 6.0+)
   - WebSocket 客户端：WebSocketSharp
   - UI 框架：WPF

## 3. 数据库设计

### 3.1 核心表设计

#### 客户端表 (clients)
```sql
CREATE TABLE clients (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    client_id VARCHAR(32) UNIQUE NOT NULL COMMENT '客户端唯一标识',
    name VARCHAR(50) NOT NULL COMMENT '客户端名称',
    status TINYINT DEFAULT 0 COMMENT '状态：0-离线，1-在线',
    ip_address VARCHAR(15) COMMENT '客户端IP地址',
    last_online_time DATETIME COMMENT '最后在线时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 控制器表 (controllers)
```sql
CREATE TABLE controllers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    controller_id VARCHAR(32) UNIQUE NOT NULL COMMENT '控制器唯一标识',
    client_id VARCHAR(32) NOT NULL COMMENT '所属客户端ID',
    name VARCHAR(50) NOT NULL COMMENT '控制器名称',
    status TINYINT DEFAULT 0 COMMENT '状态：0-停止，1-运行中',
    login_status TINYINT DEFAULT 0 COMMENT '登录状态：0-未登录，1-已登录',
    qr_code_url TEXT COMMENT '登录二维码URL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
```

#### 消息记录表 (messages)
```sql
CREATE TABLE messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    controller_id VARCHAR(32) NOT NULL COMMENT '控制器ID',
    message_type TINYINT NOT NULL COMMENT '消息类型：1-文本，2-图片，3-文件',
    content TEXT NOT NULL COMMENT '消息内容',
    sender_id VARCHAR(32) NOT NULL COMMENT '发送者ID',
    receiver_id VARCHAR(32) NOT NULL COMMENT '接收者ID',
    chat_type TINYINT NOT NULL COMMENT '聊天类型：1-私聊，2-群聊，3-频道',
    status TINYINT DEFAULT 0 COMMENT '状态：0-待发送，1-已发送，2-发送失败',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 定时任务表 (scheduled_tasks)
```sql
CREATE TABLE scheduled_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(50) NOT NULL COMMENT '任务名称',
    controller_id VARCHAR(32) NOT NULL COMMENT '控制器ID',
    task_type TINYINT NOT NULL COMMENT '任务类型：1-消息推送，2-好友添加，3-频道检索',
    cron_expression VARCHAR(100) NOT NULL COMMENT 'Cron表达式',
    task_data JSON COMMENT '任务数据',
    status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 4. 通信协议设计

### 4.1 WebSocket 消息格式
```json
{
    "type": "string",    // 消息类型
    "action": "string",  // 操作类型
    "data": {},         // 消息数据
    "timestamp": "number" // 时间戳
}
```

### 4.2 主要消息类型
1. 客户端连接消息
2. 控制器操作消息
3. 业务消息
4. 心跳消息
5. 错误消息

## 8. 数据库迁移设计

### 8.1 迁移工具
- 使用 Alembic 进行数据库迁移管理
- 支持版本控制和回滚
- 自动生成迁移脚本

### 8.2 迁移文件结构
```
migrations/
├── versions/           # 迁移脚本目录
├── env.py             # 迁移环境配置
├── script.py.mako     # 迁移脚本模板
└── README             # 迁移说明文档
```

### 8.3 迁移命令
```bash
# 初始化迁移环境
alembic init migrations

# 创建迁移脚本
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 9. API 接口设计

### 9.1 接口规范
- 所有接口使用 POST 和 GET 方法
- 请求参数统一放在请求体中
- 响应格式统一为 JSON
- 使用 Swagger UI 文档
- 接口版本控制：/api/v1/

### 9.2 认证设计
```python
# 认证模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    disabled: bool | None = None
```

### 9.3 接口列表

#### 9.3.1 认证接口
```python
# 登录接口
POST /api/v1/auth/login
Request Body:
{
    "username": "string",
    "password": "string"
}
Response:
{
    "access_token": "string",
    "token_type": "bearer"
}

# 获取当前用户信息
GET /api/v1/auth/me
Headers:
{
    "Authorization": "Bearer {token}"
}
```

#### 9.3.2 客户端管理接口
```python
# 创建客户端
POST /api/v1/clients
Request Body:
{
    "name": "string",
    "ip_address": "string"
}

# 获取客户端列表
GET /api/v1/clients
Query Parameters:
{
    "page": 1,
    "page_size": 10,
    "status": 0
}

# 获取客户端详情
GET /api/v1/clients/{client_id}

# 更新客户端
POST /api/v1/clients/{client_id}
Request Body:
{
    "name": "string",
    "status": 0
}

# 删除客户端
POST /api/v1/clients/{client_id}/delete
```

#### 9.3.3 控制器管理接口
```python
# 创建控制器
POST /api/v1/controllers
Request Body:
{
    "client_id": "string",
    "name": "string"
}

# 获取控制器列表
GET /api/v1/controllers
Query Parameters:
{
    "client_id": "string",
    "page": 1,
    "page_size": 10,
    "status": 0
}

# 获取控制器详情
GET /api/v1/controllers/{controller_id}

# 更新控制器
POST /api/v1/controllers/{controller_id}
Request Body:
{
    "name": "string",
    "status": 0
}

# 删除控制器
POST /api/v1/controllers/{controller_id}/delete

# 启动控制器
POST /api/v1/controllers/{controller_id}/start

# 停止控制器
POST /api/v1/controllers/{controller_id}/stop
```

#### 9.3.4 定时任务管理接口
```python
# 创建定时任务
POST /api/v1/tasks
Request Body:
{
    "task_name": "string",
    "controller_id": "string",
    "task_type": 1,
    "cron_expression": "string",
    "task_data": {}
}

# 获取定时任务列表
GET /api/v1/tasks
Query Parameters:
{
    "controller_id": "string",
    "page": 1,
    "page_size": 10,
    "status": 1
}

# 获取定时任务详情
GET /api/v1/tasks/{task_id}

# 更新定时任务
POST /api/v1/tasks/{task_id}
Request Body:
{
    "task_name": "string",
    "cron_expression": "string",
    "task_data": {},
    "status": 1
}

# 删除定时任务
POST /api/v1/tasks/{task_id}/delete

# 启用/禁用定时任务
POST /api/v1/tasks/{task_id}/toggle
Request Body:
{
    "status": 1
}
```

### 9.4 响应格式
```json
{
    "code": 0,          // 状态码：0-成功，非0-失败
    "message": "string", // 响应消息
    "data": {}          // 响应数据
}
```

### 9.5 错误码定义
```python
class ErrorCode:
    SUCCESS = 0
    PARAM_ERROR = 1001
    AUTH_ERROR = 1002
    PERMISSION_ERROR = 1003
    RESOURCE_NOT_FOUND = 1004
    INTERNAL_ERROR = 1005
```

## 10. 项目结构
```
project/
├── app/
│   ├── api/           # API 接口层
│   ├── controllers/   # 控制器逻辑
│   ├── core/         # 核心配置
│   ├── db/           # 数据库相关
│   ├── middlewares/  # 中间件
│   ├── models/       # 数据模型
│   ├── routes/       # 路由定义
│   ├── schemas/      # Pydantic 模型
│   ├── services/     # 业务服务层
│   ├── templates/    # 模板文件
│   └── utils/        # 工具函数
├── docker/          # Docker 相关配置
│   ├── mysql/       # MySQL 配置
│   │   ├── init/    # 初始化脚本
│   │   └── data/    # 数据存储
│   └── redis/       # Redis 配置
│       └── data/    # 数据存储
├── migrations/      # 数据库迁移
├── tests/          # 测试代码
├── venv/           # Python 虚拟环境
├── .env            # 环境变量配置
├── .gitignore      # Git 忽略文件
├── alembic.ini     # Alembic 配置
├── docker-compose.yml # Docker 编排配置
├── main.py         # 应用入口
├── requirements.txt # 依赖管理
└── system-architecture.md # 系统架构文档
```

## 11. 开发规范

### 11.1 代码规范
- 遵循 PEP 8 规范
- 使用类型注解
- 编写单元测试
- 添加必要的注释

### 11.2 提交规范
- 使用 Conventional Commits
- 提交前进行代码格式化
- 提交前运行测试

### 11.3 文档规范
- 保持文档及时更新
- 使用 Markdown 格式
- 添加必要的示例

## 12. 中间件设计

### 12.1 响应中间件
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uuid
import time

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
```

### 12.2 响应格式
```json
{
    "request_id": "string",      // 请求唯一标识
    "path": "string",           // 请求路径
    "code": 200,                // HTTP状态码：200-成功，其他-失败
    "status": "string",         // 响应状态：success/error
    "data": {},                // 响应数据
    "message": "string",        // 响应消息
    "timestamp": 0,            // 响应时间戳（毫秒）
    "duration": 0              // 请求处理时长（毫秒）
}
```

### 12.3 中间件配置
```python
from fastapi import FastAPI

app = FastAPI()

# 添加响应中间件
app.add_middleware(ResponseMiddleware)
```

### 12.4 使用示例
```python
# 正常响应示例
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "path": "/api/v1/clients",
    "code": 200,
    "status": "success",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 10
    },
    "message": "获取客户端列表成功",
    "timestamp": 1677648000000,
    "duration": 150
}

# 错误响应示例
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "path": "/api/v1/clients/123",
    "code": 404,
    "status": "error",
    "data": {},
    "message": "客户端不存在",
    "timestamp": 1677648000000,
    "duration": 50
}
```

### 12.5 中间件特性
1. 自动生成请求ID，便于请求追踪
2. 记录请求处理时长，用于性能监控
3. 统一响应格式，便于前端处理
4. 异常捕获和统一处理
5. 支持自定义响应头
6. 支持异步处理
7. 使用标准 HTTP 状态码
