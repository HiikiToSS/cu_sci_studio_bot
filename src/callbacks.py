from aiogram.filters import callback_data


class StartingCallback(callback_data.CallbackData, prefix="start"):
    pass


class LinkCallback(callback_data.CallbackData, prefix="link"):
    username_to: str
    rating: int


class SexCallback(callback_data.CallbackData, prefix="sex"):
    sex: str


class CourseCallback(callback_data.CallbackData, prefix="course"):
    course: int


class LivingCallback(callback_data.CallbackData, prefix="living"):
    living: str


class TypeInfoCallback(callback_data.CallbackData, prefix="typeinfo"):
    pass
