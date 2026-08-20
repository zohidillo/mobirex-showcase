from django.core.management.base import BaseCommand

import src.core.models as models


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in models.User.objects.all():
            user.account_status = "vip"
            user.is_vip = True
            user.save()
