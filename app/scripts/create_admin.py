from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

def create_admin_user():
    """创建初始管理员账户"""
    db = SessionLocal()
    try:
        # 删除已存在的管理员账户
        db.query(User).filter(User.username == "admin").delete()
        db.commit()
        
        # 创建管理员账户
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),  # 默认密码
            email="admin@example.com",
            full_name="系统管理员",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("管理员账户创建成功")
    except Exception as e:
        print(f"创建管理员账户失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 