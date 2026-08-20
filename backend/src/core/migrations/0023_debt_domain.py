from django.db import migrations, models


BATCH_SIZE = 500

ROLE_PRIORITY = {
    "OWNER": 1,
    "ACCESSORY_SELLER": 2,
    "PHONE_SELLER": 3,
}

ROLE_DOMAIN = {
    "OWNER": "PHONE",
    "ACCESSORY_SELLER": "ACCESSORY",
    "PHONE_SELLER": "PHONE",
}


def populate_debt_domain(apps, schema_editor):
    Debt = apps.get_model("core", "Debt")
    Branch = apps.get_model("core", "Branch")
    BranchUser = apps.get_model("core", "BranchUser")
    db_alias = schema_editor.connection.alias

    branch_owner_map = dict(
        Branch._base_manager.using(db_alias).values_list("id", "owner_id")
    )

    role_map = {}
    role_rows = BranchUser._base_manager.using(db_alias).filter(is_deleted=False).values_list(
        "user_id",
        "branch_id",
        "role",
    )
    for user_id, branch_id, role in role_rows.iterator():
        priority = ROLE_PRIORITY.get(role)
        domain = ROLE_DOMAIN.get(role)
        if not priority or not domain:
            continue
        key = (user_id, branch_id)
        current = role_map.get(key)
        if current is None or priority > current[0]:
            role_map[key] = (priority, domain)

    debts = Debt._base_manager.using(db_alias).filter(domain__isnull=True).only(
        "id",
        "created_by_id",
        "branch_id",
        "domain",
    )

    batch = []
    for debt in debts.iterator():
        domain = None
        role_data = role_map.get((debt.created_by_id, debt.branch_id))
        if role_data:
            domain = role_data[1]
        elif branch_owner_map.get(debt.branch_id) == debt.created_by_id:
            domain = "PHONE"

        if not domain:
            continue

        debt.domain = domain
        batch.append(debt)
        if len(batch) >= BATCH_SIZE:
            Debt._base_manager.using(db_alias).bulk_update(batch, ["domain"])
            batch = []

    if batch:
        Debt._base_manager.using(db_alias).bulk_update(batch, ["domain"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_monthclosingrecord_status_phone_for_month_close"),
    ]

    operations = [
        migrations.AddField(
            model_name="debt",
            name="domain",
            field=models.CharField(
                blank=True,
                choices=[("PHONE", "Telefon"), ("ACCESSORY", "Aksessuar")],
                help_text="Qarz tegishli savdo yo‘nalishi.",
                max_length=16,
                null=True,
                verbose_name="Yo‘nalish turi",
            ),
        ),
        migrations.RunPython(populate_debt_domain, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["domain"], name="debt_domain_idx"),
        ),
    ]
