import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.support.password_helper import get_password_hash
from config.database import settings

async def main():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        hashed = get_password_hash('admin')
        await session.execute(text("""
            INSERT INTO users (id, username, nickname, password, cellphone, state, gender, avatar, is_admin)
            VALUES (gen_random_uuid(), 'admin', '管理员', :password, '13800000000', 'enabled', 'unknown', '', true)
            ON CONFLICT (username) DO UPDATE SET password = :password, cellphone = '13800000000', is_admin = true
        """), {"password": hashed})
        await session.commit()
        print("✅ 管理员账号创建成功！用户名: admin  密码: admin")

asyncio.run(main())