from pydantic import BaseModel


class MockLoginRequest(BaseModel):
    """临时假登录：只要传个昵称就创建一个新用户"""
    nickname: str


class WxLoginRequest(BaseModel):
    """微信小程序登录：前端 wx.login() 拿到的 code"""
    code: str


class LoginResponse(BaseModel):
    token: str
    user_id: int
    nickname: str | None = None
    avatar_url: str | None = None