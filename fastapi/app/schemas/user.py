from pydantic import Field

from app.schemas.base import BaseSc


class UserCreateReqSc(BaseSc):
    """用户创建请求模型"""

    username: str = Field(description='用户名', example='admin')
    cellphone: str = Field(description='手机号', example='12345678901')
    password: str = Field(description='密码', example='123456')
