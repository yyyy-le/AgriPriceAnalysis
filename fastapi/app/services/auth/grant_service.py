#
# OAuth2 授权业务逻辑
#
# 实现用户名密码授权的业务逻辑，包括用户验证和令牌颁发。
#

from pydantic import ConfigDict, validate_call
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    InvalidPasswordError,
    InvalidUserError,
    UserNotFoundError,
)
from app.models.user import UserModel
from app.schemas.oauth2 import OAuth2PasswordSc
from app.services.auth.token_service import create_token_response_from_user
from app.support import password_helper


class PasswordGrant:
    """用户名密码授权"""

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(self, session: AsyncSession, client_ip: str, request_data: OAuth2PasswordSc):
        self.session = session
        self.client_ip = client_ip
        self.request_data = request_data

    async def respond(self):
        user = await UserModel.get_one(
            self.session,
            ((UserModel.username == self.request_data.username) | (UserModel.cellphone == self.request_data.username))
            & UserModel.exist_filter(),
        )
        if not user:
            raise UserNotFoundError(message='没有此用户')

        # 用户密码校验
        if not (user.password and password_helper.verify_password(self.request_data.password, user.password)):
            raise InvalidPasswordError(message='用户名或密码错误')

        # 用户状态校验
        if not user.is_enabled():
            raise InvalidUserError(message='该账号已被禁用')

        return create_token_response_from_user(user)
