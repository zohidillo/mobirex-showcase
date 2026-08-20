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


class BranchDeleteService:
    @staticmethod
    def delete_branch(branch, deleted_by):
        with transaction.atomic():
            old_data = _snapshot(branch)
            branch.is_deleted = True
            branch.save()
            JournalService.log_delete(
                user=deleted_by,
                instance=branch,
                old_data=old_data,
            )
            return branch
