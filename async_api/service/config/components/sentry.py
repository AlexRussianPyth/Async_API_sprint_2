import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn= os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate= float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 1.0)),
    send_default_pii=True,
)