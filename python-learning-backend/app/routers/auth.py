from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import MockLoginRequest, WxLoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/mock-login", response_model=LoginResponse)
def mock_login(payload: MockLoginRequest, db: Session = Depends(get_db)):
    """
    临时登录接口：用昵称当作 openid 前缀，创建或复用用户。
    等真实微信登录接好后，这个接口会保留作开发测试用。
    """
    fake_openid = f"mock_{payload.nickname}"

    user = db.query(User).filter(User.openid == fake_openid).first()
    if user is None:
        user = User(openid=fake_openid, nickname=payload.nickname)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)
    return LoginResponse(
        token=token,
        user_id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
    )


@router.post("/wx-login", response_model=LoginResponse)
def wx_login(payload: WxLoginRequest, db: Session = Depends(get_db)):
    """
    微信小程序登录：前端 wx.login() 拿到 code 后调这里，
    后端用 code 换 openid，再签发 JWT。
    如果还没配 WX_APPID/WX_SECRET，会用 code 当作假 openid，方便本地联调。
    """
    if not settings.WX_APPID or not settings.WX_SECRET:
        # 本地联调回退：没配微信密钥时直接用 code 当 openid
        openid = f"mock_{payload.code}"
    else:
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WX_APPID,
            "secret": settings.WX_SECRET,
            "js_code": payload.code,
            "grant_type": "authorization_code",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
        data = resp.json()
        openid = data.get("openid")
        if not openid:
            raise HTTPException(
                status_code=400,
                detail=f"微信登录失败: {data.get('errmsg', data)}",
            )

    user = db.query(User).filter(User.openid == openid).first()
    if user is None:
        user = User(openid=openid)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login_at = datetime.utcnow()
        db.commit()

    token = create_access_token(user.id)
    return LoginResponse(
        token=token,
        user_id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
    )