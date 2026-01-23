import contextvars

user_context = contextvars.ContextVar("user", default="anonymous")