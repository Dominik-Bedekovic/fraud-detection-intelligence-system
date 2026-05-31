import time
import logging
from fastapi import Request
from contextlib import contextmanager
from pathlib import Path


logger = logging.getLogger("profiling")

LOG_FILE = Path(__file__).parent / "profiling.log"

def setup_profiling(app):
    #clear old logs on startup
    LOG_FILE.write_text("")

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        force=True,
    )

    @app.middleware("http")
    async def profiling_middleware(request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        total = (time.perf_counter() - start) * 1000

        logger.info(
            f"[TOTAL] {request.method} {request.url.path} = {total:.2f}ms"
        )

        return response


class Timer:
    def __init__(self):
        self.sections = {}

    @contextmanager
    def time(self, name: str):
        start = time.perf_counter()
        yield
        self.sections[name] = (time.perf_counter() - start) * 1000

    def log(self, request_info=""):
        parts = " | ".join(
            f"{k}: {v:.2f}ms" for k, v in self.sections.items()
        )
        logger.info(f"[DETAIL] {request_info} | {parts}")