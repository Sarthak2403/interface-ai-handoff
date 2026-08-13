import logging
import re

SENSITIVE = re.compile(r'(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')

class RedactFilter(logging.Filter):
    def filter(self, record):
        record.msg = SENSITIVE.sub("[REDACTED]", str(record.msg))
        return True

def configure(path: str | None = None):
    handlers = [logging.StreamHandler()]
    if path:
        handlers.append(logging.FileHandler(path))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )
    for h in handlers:
        h.addFilter(RedactFilter())
    return logging.getLogger("cua")
