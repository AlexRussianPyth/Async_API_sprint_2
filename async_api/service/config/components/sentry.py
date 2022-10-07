import dotenv
import pathlib
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=float(os.environ.get("SENTRY_DSN", 1.0)),
    send_default_pii=bool(os.environ.get("SENTRY_SEND_DEFAULT_PII", True)),
)
