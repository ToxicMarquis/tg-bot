from aiogram import Router
from handlers import admin, application, common


def get_router() -> Router:
    router = Router(name="main")
    router.include_router(common.router)
    router.include_router(admin.router)
    router.include_router(application.router)
    return router


__all__ = ["get_router"]
