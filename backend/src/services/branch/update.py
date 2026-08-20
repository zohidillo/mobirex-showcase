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


class BranchUpdateService:
    @staticmethod
    def update_branch(branch, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(branch)
            for attr, value in validated_data.items():
                setattr(branch, attr, value)
            branch.save()
            JournalService.log_update(
                user=updated_by,
                instance=branch,
                old_data=old_data,
                new_data=_snapshot(branch),
            )
            return branch
