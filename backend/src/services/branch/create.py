from django.db import transaction

from src.core.models import Branch
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class BranchCreateService:
    @staticmethod
    def create_branch(validated_data, created_by):
        with transaction.atomic():
            branch = Branch.objects.create(**validated_data)
            JournalService.log_create(
                user=created_by,
                instance=branch,
                new_data=_snapshot(branch),
            )
            return branch
