from fastapi import Depends

from app.core.config import Settings, get_settings


def get_current_settings(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
