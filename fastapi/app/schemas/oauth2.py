from pydantic import Field

from app.schemas.base import BaseSc


class OAuth2PasswordSc(BaseSc):
    """OAuth2 密码登录请求"""

    grant_type: str = Field('password', description='授权类型', pattern='^password$', example='password')
    username: str = Field(description='用户名', example='admin')
    password: str = Field(description='密码', example='123456')
    scope: str = Field('', description='授权范围')
    client_id: str | None = Field(None, description='客户端ID')
    client_secret: str | None = Field(None, description='客户端密钥')
