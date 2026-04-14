import os
import django
from django.conf import settings
from django.db import connection

# Manually configure Django if needed, or just rely on env vars
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easycert_django.settings')
django.setup()

print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default']['NAME']}")
print(f"Host: {settings.DATABASES['default'].get('HOST')}")

try:
    tables = connection.introspection.table_names()
    print(f"Tables: {tables}")
    if 'users' in tables:
        from apps.accounts.models import User
        print(f"User count: {User.objects.count()}")
    else:
        print("Table 'users' NOT found.")
except Exception as e:
    print(f"Error: {e}")
