from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    JSON,
    Boolean,
    BigInteger,
    DateTime,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from datetime import datetime


class Client(BaseModel):
    """客户端表"""

    __tablename__ = "client"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(
        String(32), unique=True, nullable=False, comment="客户端唯一标识"
    )
    name = Column(String(50), nullable=False, comment="客户端名称")
    status = Column(Integer, default=0, comment="状态：0-离线，1-在线")
    ip_address = Column(String(15), comment="客户端IP地址")
    last_online_time = Column(DateTime, comment="最后在线时间")

    # 关联关系
    controllers = relationship("Controller", back_populates="client")


class Controller(BaseModel):
    """控制器表"""

    __tablename__ = "controller"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    controller_id = Column(
        String(32), unique=True, nullable=False, comment="控制器唯一标识"
    )
    client_id = Column(
        String(32),
        ForeignKey("client.client_id"),
        nullable=False,
        comment="所属客户端ID",
    )
    name = Column(String(50), nullable=False, comment="控制器名称")
    status = Column(Integer, default=0, comment="状态：0-停止，1-运行中")
    login_status = Column(Integer, default=0, comment="登录状态：0-未登录，1-已登录")
    qr_code_url = Column(Text, comment="登录二维码URL")

    # 关联关系
    client = relationship("Client", back_populates="controllers")
    messages = relationship("Message", back_populates="controller")
    tasks = relationship("ScheduledTask", back_populates="controller")


class Message(BaseModel):
    """消息记录表"""

    __tablename__ = "message"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    controller_id = Column(
        String(32),
        ForeignKey("controller.controller_id"),
        nullable=False,
        comment="控制器ID",
    )
    message_type = Column(
        Integer, nullable=False, comment="消息类型：1-文本，2-图片，3-文件"
    )
    content = Column(Text, nullable=False, comment="消息内容")
    sender_id = Column(String(32), nullable=False, comment="发送者ID")
    receiver_id = Column(String(32), nullable=False, comment="接收者ID")
    chat_type = Column(
        Integer, nullable=False, comment="聊天类型：1-私聊，2-群聊，3-频道"
    )
    status = Column(Integer, default=0, comment="状态：0-待发送，1-已发送，2-发送失败")

    # 关联关系
    controller = relationship("Controller", back_populates="messages")


class ScheduledTask(BaseModel):
    """定时任务表"""

    __tablename__ = "scheduled_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name = Column(String(50), nullable=False, comment="任务名称")
    controller_id = Column(
        String(32),
        ForeignKey("controller.controller_id"),
        nullable=False,
        comment="控制器ID",
    )
    task_type = Column(
        Integer, nullable=False, comment="任务类型：1-消息推送，2-好友添加，3-频道检索"
    )
    cron_expression = Column(String(100), nullable=False, comment="Cron表达式")
    task_data = Column(JSON, comment="任务数据")
    status = Column(Integer, default=1, comment="状态：0-禁用，1-启用")

    # 关联关系
    controller = relationship("Controller", back_populates="tasks")


class User(BaseModel):
    """用户表"""

    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    email = Column(String(100), unique=True, comment="邮箱")
    full_name = Column(String(100), comment="全名")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_superuser = Column(
        Boolean, default=False, nullable=False, comment="是否超级管理员"
    )
    last_login = Column(DateTime, comment="最后登录时间")

    # 关联关系
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    login_logs = relationship("LoginLog", back_populates="user")


class Role(BaseModel):
    """角色表"""

    __tablename__ = "role"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    description = Column(String(255), comment="角色描述")

    # 关联关系
    users = relationship("User", secondary="user_roles", back_populates="roles")


class UserRole(BaseModel):
    """用户角色关联表"""

    __tablename__ = "user_roles"

    user_id = Column(BigInteger, ForeignKey("user.id"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("role.id"), primary_key=True)


class LoginLog(BaseModel):
    """登录日志表"""

    __tablename__ = "login_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    login_time = Column(DateTime, default=datetime.now, comment="登录时间")
    ip_address = Column(String(45), comment="登录IP地址")
    user_agent = Column(Text, comment="用户代理信息")
    status = Column(
        Integer, default=1, nullable=False, comment="登录状态：0-失败，1-成功"
    )

    # 关联关系
    user = relationship("User", back_populates="login_logs")
