import redis
from app.core.config import settings

# 创建Redis连接池
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=True
)

# 获取Redis连接
def get_redis():
    return redis.Redis(connection_pool=redis_pool) 