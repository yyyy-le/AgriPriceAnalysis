from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.http.deps import database_deps, request_deps, auth_deps
from app.models.user import UserModel
from app.schemas.common import BoolSc
from app.schemas.user import UserCreateReqSc
from app.services.auth import validation_service, verification_code_service
from app.services.auth.user_service import create_user
from app.exceptions import InvalidPasswordError
from app.support.password_helper import get_password_hash, verify_password

router = APIRouter(prefix='/users', tags=['用户'])


@router.post('', response_model=BoolSc, name='注册新用户')
async def register_user(
    user_create: UserCreateReqSc,
    client_ip: Annotated[str, Depends(request_deps.get_request_ip)],
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
):
    # 验证用户名
    await validation_service.validate_username_availability(session, user_create.username)
    # 验证手机号
    await validation_service.validate_cellphone_availability(session, user_create.cellphone)
    # 验证验证码
    await verification_code_service.verify_code(user_create.cellphone, user_create.cellphone_verification_code)

    await create_user(session, client_ip, user_create)
    await session.commit()
    return BoolSc(success=True)


@router.put('/password', name='修改密码')
async def change_password(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    old_password: str = Body(..., description='原密码'),
    new_password: str = Body(..., description='新密码'),
):
    # 查询数据库中存储的密码（ORM 对象可能不含密码字段）
    row = await session.execute(
        text("SELECT password FROM users WHERE id = :id"),
        {"id": str(user.id)}
    )
    result = row.fetchone()
    stored_password = result[0] if result else None

    # 校验原密码
    if not stored_password or not verify_password(old_password, stored_password):
        raise InvalidPasswordError(message='原密码不正确')

    # 更新新密码
    hashed = get_password_hash(new_password)
    await session.execute(
        text("UPDATE users SET password = :password WHERE id = :id"),
        {"password": hashed, "id": str(user.id)}
    )
    await session.commit()
    return {"success": True}