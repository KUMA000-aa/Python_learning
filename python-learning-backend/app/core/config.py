from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # 微信小程序配置：真实 code2session 用，留空时 wx-login 会回退到 mock
    WX_APPID: str = ""
    WX_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()