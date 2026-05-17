import os
import sys
import types

sys.path.insert(0, "apps")

os.environ.setdefault("MAXKB_LOG_DIR", os.path.abspath("data/logs"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
os.environ.setdefault("MAXKB_CONFIG_TYPE", "ENV")
os.environ.setdefault("PGSQL_HOST", "172.16.2.103")
os.environ.setdefault("PGSQL_PORT", "5432")
os.environ.setdefault("PGSQL_DB", "maxkb")
os.environ.setdefault("PGSQL_USER", "root")
os.environ.setdefault("PGSQL_PASSWORD", "Password123@postgres")
os.environ.setdefault("MAXKB_EXTERNAL_REDIS", "false")
os.environ.setdefault("REDIS_HOST", "172.16.2.103")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "Password123@redis")
os.environ.setdefault("MAXKB_DB_NAME", os.environ["PGSQL_DB"])
os.environ.setdefault("MAXKB_DB_HOST", os.environ["PGSQL_HOST"])
os.environ.setdefault("MAXKB_DB_PORT", os.environ["PGSQL_PORT"])
os.environ.setdefault("MAXKB_DB_USER", os.environ["PGSQL_USER"])
os.environ.setdefault("MAXKB_DB_PASSWORD", os.environ["PGSQL_PASSWORD"])
os.environ.setdefault("MAXKB_REDIS_HOST", os.environ["REDIS_HOST"])
os.environ.setdefault("MAXKB_REDIS_PORT", os.environ["REDIS_PORT"])
os.environ.setdefault("MAXKB_REDIS_PASSWORD", os.environ["REDIS_PASSWORD"])
os.environ.setdefault("MAXKB_REDIS_DB", os.environ["REDIS_DB"])
os.environ.setdefault("MAXKB_DEBUG", "True")

from django.core.management.commands import runserver

runserver.Command.check_migrations = lambda self: None

from django.core.wsgi import get_wsgi_application

module = types.ModuleType("maxkb_debug_wsgi")
module.application = get_wsgi_application()
sys.modules[module.__name__] = module

from django.conf import settings
from django.core.management import execute_from_command_line

settings.WSGI_APPLICATION = "maxkb_debug_wsgi.application"

execute_from_command_line(
    ["manage.py", "runserver", "0.0.0.0:8080", "--noreload", "--skip-checks"]
)
