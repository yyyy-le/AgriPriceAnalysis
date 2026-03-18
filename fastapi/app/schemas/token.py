import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSc


class TokenSc(BaseSc):
    """令牌"""

    token_type: str = Field('bearer', description='令牌类型')
    expires_in: int = Field(description='过期时间（秒）')
    access_token: str = Field(description='令牌')


class TokenStatusSc(BaseSc):
    """令牌状态"""

    user_id: UUID = Field(description='用户ID')
    expires_at: datetime.datetime = Field(description='过期时间')
    issued_at: datetime.datetime = Field(description='签发时间')
    is_valid: bool = Field(description='是否有效')

class TokenSc(BaseSc):
    token_type: str = Field('bearer', description='令牌类型')
    expires_in: int = Field(description='过期时间（秒）')
    access_token: str = Field(description='令牌')
    role: str = Field(description='用户角色')  # 新增