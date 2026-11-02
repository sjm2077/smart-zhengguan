import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    return int(raw_value)


def float_env(name: str, default=None):
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    return float(raw_value)


SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-dev-secret-key")
DEBUG = bool_env("DEBUG", True)
ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "apps.common",
    "apps.accounts",
    "apps.graduate",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

CORS_ALLOWED_ORIGINS = csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DEFAULT_PREDICTION_KNOWLEDGE_DIRS = "knowledge/prediction,../\u7814\u7a76\u751f\u6587\u4ef6\u89c4\u5b9a"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "smartzhengguan-default",
    }
}

PREDICTION_LLM_ENABLED = bool_env("PREDICTION_LLM_ENABLED", False)
PREDICTION_LLM_PROVIDER = os.getenv("PREDICTION_LLM_PROVIDER", "openai")
PREDICTION_LLM_API_STYLE = os.getenv("PREDICTION_LLM_API_STYLE", "responses").strip().lower() or "responses"
PREDICTION_LLM_API_KEY = os.getenv("PREDICTION_LLM_API_KEY", "")
PREDICTION_LLM_BASE_URL = os.getenv("PREDICTION_LLM_BASE_URL", "https://api.openai.com/v1")
PREDICTION_LLM_MODEL = os.getenv("PREDICTION_LLM_MODEL", "gpt-5-mini")
# 智能预测 Agent（工具调用循环）。关闭时回落到原来的单次 pipeline。
PREDICTION_AGENT_ENABLED = bool_env("PREDICTION_AGENT_ENABLED", False)
# 最多工具调用轮数，防止模型反复检索打转。
PREDICTION_AGENT_MAX_STEPS = int_env("PREDICTION_AGENT_MAX_STEPS", 3)
# 整轮 Agent 的时间预算，超限立即收尾，避免前端长时间挂住。
PREDICTION_AGENT_TIME_BUDGET_SECONDS = int_env("PREDICTION_AGENT_TIME_BUDGET_SECONDS", 120)

# 开启 thinking 后单次回复常需 600+ reasoning token，45s 容易超时。
PREDICTION_LLM_TIMEOUT_SECONDS = int_env("PREDICTION_LLM_TIMEOUT_SECONDS", 90)
# 网络抖动/超时的重试次数（HTTP 4xx/5xx 不重试）。
PREDICTION_LLM_MAX_RETRIES = int_env("PREDICTION_LLM_MAX_RETRIES", 2)
# 留空则直连模型 API（忽略系统/环境变量代理）；填写则强制走该代理。
PREDICTION_LLM_PROXY = os.getenv("PREDICTION_LLM_PROXY", "").strip()
# 置为 True 才让请求沿用环境变量/系统代理设置。
PREDICTION_LLM_TRUST_ENV_PROXY = bool_env("PREDICTION_LLM_TRUST_ENV_PROXY", False)
PREDICTION_LLM_THINKING_TYPE = os.getenv("PREDICTION_LLM_THINKING_TYPE", "")
PREDICTION_LLM_REASONING_EFFORT = os.getenv("PREDICTION_LLM_REASONING_EFFORT", "medium")
PREDICTION_LLM_TEMPERATURE = float_env("PREDICTION_LLM_TEMPERATURE")
PREDICTION_EXPOSE_DEBUG = bool_env("PREDICTION_EXPOSE_DEBUG", False)
PREDICTION_KNOWLEDGE_DIRS = csv_env(
    "PREDICTION_KNOWLEDGE_DIRS",
    DEFAULT_PREDICTION_KNOWLEDGE_DIRS,
)
PREDICTION_KNOWLEDGE_TOP_K = int_env("PREDICTION_KNOWLEDGE_TOP_K", 4)
PREDICTION_ALLOW_RUNTIME_OVERRIDES = bool_env("PREDICTION_ALLOW_RUNTIME_OVERRIDES", False)
PREDICTION_ALLOWED_MODELS = csv_env("PREDICTION_ALLOWED_MODELS", "")
PREDICTION_MAX_REQUEST_BYTES = int_env("PREDICTION_MAX_REQUEST_BYTES", 16384)
PREDICTION_RATE_LIMIT_WINDOW_SECONDS = int_env("PREDICTION_RATE_LIMIT_WINDOW_SECONDS", 60)
PREDICTION_RATE_LIMIT_DATA = int_env("PREDICTION_RATE_LIMIT_DATA", 60)
PREDICTION_RATE_LIMIT_CONTEXT = int_env("PREDICTION_RATE_LIMIT_CONTEXT", 30)
PREDICTION_RATE_LIMIT_ANALYZE = int_env("PREDICTION_RATE_LIMIT_ANALYZE", 20)
PREDICTION_RATE_LIMIT_CHAT = int_env("PREDICTION_RATE_LIMIT_CHAT", 12)
PUBLIC_API_RATE_LIMIT_READ = int_env("PUBLIC_API_RATE_LIMIT_READ", 120)
PUBLIC_API_RATE_LIMIT_SEARCH = int_env("PUBLIC_API_RATE_LIMIT_SEARCH", 40)
PUBLIC_API_RATE_LIMIT_QUERY = int_env("PUBLIC_API_RATE_LIMIT_QUERY", 40)
PUBLIC_API_RATE_LIMIT_META = int_env("PUBLIC_API_RATE_LIMIT_META", 120)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"
