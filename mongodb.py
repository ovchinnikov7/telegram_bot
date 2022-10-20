from datetime import datetime
from aiogram.types import Message


def create_user(db, message: Message):
    user_obj = {
        "id": message.from_user.id,
        "username": message.from_user.username,
        "is_bot": message.from_user.is_bot,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "full_name": message.from_user.full_name,
        "created_at": datetime.now(),
        "chat_id": message.chat.id,
    }
    user = db.users.find_one({'id': user_obj['id']})
    if not user:
        user = user_obj
        db.users.insert_one(user_obj)
        return user
