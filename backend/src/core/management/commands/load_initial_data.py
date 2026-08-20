from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from src.core import models


class Command(BaseCommand):
    help = "Load initial admin user and seed category data."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[2]
        seed_dir = base_dir / "seed_data"
        phone_path = seed_dir / "phone_categories.json"
        accessory_path = seed_dir / "accessory_categories.json"

        admin_created = False
        phone_added = 0
        accessory_added = 0

        try:
            with transaction.atomic():
                if not models.User.objects.filter(is_superuser=True).exists():
                    models.User.objects.create_superuser(
                        username="admin",
                        password="321",
                        is_staff=True,
                        is_active=True,
                    )
                    admin_created = True

                if phone_path.exists():
                    phone_data = json.loads(phone_path.read_text(encoding="utf-8"))
                    for name in phone_data:
                        obj, created = models.PhoneCategory.objects.get_or_create(name=name)
                        if created:
                            phone_added += 1
                else:
                    self.stderr.write(f"Phone categories file not found: {phone_path}")

                if accessory_path.exists():
                    accessory_data = json.loads(accessory_path.read_text(encoding="utf-8"))
                    for name in accessory_data:
                        obj, created = models.AccessoryCategory.objects.get_or_create(name=name)
                        if created:
                            accessory_added += 1
                else:
                    self.stderr.write(f"Accessory categories file not found: {accessory_path}")
        except (OSError, json.JSONDecodeError) as exc:
            self.stderr.write(f"Failed to load initial data: {exc}")
            return

        if admin_created:
            self.stdout.write("Admin created")
        else:
            self.stdout.write("Admin already exists")

        self.stdout.write(f"{phone_added} phone categories added")
        self.stdout.write(f"{accessory_added} accessory categories added")
