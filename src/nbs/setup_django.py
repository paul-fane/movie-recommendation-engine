import os
import sys


DJANGO_SETTINGS_MODULE = "netflix.settings"

# Ensure 'PWD' is set for compatibility
# if os.name == 'nt':  # Windows
#     os.environ['PWD'] = os.getcwd()

# PWD = os.getenv("PWD")

PWD = os.path.dirname(os.getcwd())


def init():
    os.chdir(PWD)
    # sys.path.insert(0, os.getenv("PWD"))
    sys.path.insert(0, PWD)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django
    django.setup()