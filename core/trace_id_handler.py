import threading
import uuid
from contextlib import asynccontextmanager


class TraceIdHandler:
    _thread_local = threading.local()

    @staticmethod
    @asynccontextmanager
    async def logging_scope():
        TraceIdHandler._thread_local.trace_id = uuid.uuid4()
        try:
            yield
        finally:
            del TraceIdHandler._thread_local.trace_id

    @staticmethod
    def get_current_trace_id() -> uuid.UUID | None:
        return getattr(TraceIdHandler._thread_local, "trace_id", None)
