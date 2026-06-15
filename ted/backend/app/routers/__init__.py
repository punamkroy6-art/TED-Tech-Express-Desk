from app.routers.auth import router as auth
from app.routers.diagnose import router as diagnose
from app.routers.ocr import router as ocr
from app.routers.ticket import router as ticket
from app.routers.loaner import router as loaner
from app.routers.health import router as health
from app.routers.autofix import router as autofix
from app.routers.diagnostic import router as diagnostic

__all__ = ["auth", "diagnose", "ocr", "ticket", "loaner", "health", "autofix", "diagnostic"]
