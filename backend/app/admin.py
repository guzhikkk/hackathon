from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.models.user import User
from app.services.auth import verify_password, create_access_token, decode_token
from app.database import async_session_maker
from app.services.user import get_user_by_email
from app.config import get_settings

settings = get_settings()

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        async with async_session_maker() as session:
            user = await get_user_by_email(session, str(username))
            if not user or not user.hashed_password:
                return False
            if not verify_password(str(password), user.hashed_password):
                return False
            if not user.is_admin:
                return False

            token = create_access_token(str(user.id))
            request.session.update({"token": token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        payload = decode_token(token)
        if not payload:
            return False
        return True

from app.models.user import UserData
from app.models.file import FileRecord

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_admin, User.is_active, User.created_at]
    column_searchable_list = [User.email]
    column_sortable_list = [User.created_at, User.email]
    column_default_sort = ("created_at", True)
    form_excluded_columns = [User.id, User.created_at, User.updated_at]
    icon = "fa-solid fa-user"
    name = "User"
    name_plural = "Users"
    category = "Accounts"

class UserDataAdmin(ModelView, model=UserData):
    column_list = [UserData.id, UserData.user_id, UserData.full_name, UserData.avatar_url]
    column_searchable_list = [UserData.full_name]
    icon = "fa-solid fa-id-card"
    name = "User Data"
    name_plural = "User Data"
    category = "Accounts"

class FileRecordAdmin(ModelView, model=FileRecord):
    column_list = [FileRecord.id, FileRecord.key, FileRecord.owner_id, FileRecord.created_at]
    column_searchable_list = [FileRecord.key]
    icon = "fa-solid fa-file"
    name = "File"
    name_plural = "Files"
    category = "Storage"
