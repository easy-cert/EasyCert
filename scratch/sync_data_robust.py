import os
import json
import django
from django.core import serializers
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easycert_django.settings')

FIXTURE_PATH = 'datadump_sync.json'

def sync():
    print(f"Reading fixture from {FIXTURE_PATH}...")
    with open(FIXTURE_PATH, 'r', encoding='utf-8') as f:
        data = f.read()

    print("Deserializing and saving objects...")
    objects = serializers.deserialize('json', data)
    
    count = 0
    # We do NOT use transaction.atomic() here because if one object fails 
    # (e.g. contenttype already exists), we want to continue.
    for obj in objects:
        try:
            obj.save()
            count += 1
            if count % 10 == 0:
                print(f"Saved {count} objects...")
        except Exception as e:
            # Silently skip errors (like UNIQUE constraints if data already exists)
            # but print if it's something unexpected.
            if "duplicate key value" not in str(e).lower():
                print(f"Skipping {obj}: {e}")
    
    print(f"Done! Successfully handled {count} objects.")

if __name__ == "__main__":
    print("Script started...")
    django.setup()
    print("Django setup complete.")
    sync()
