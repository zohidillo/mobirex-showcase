from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_alter_phone_imei"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="accessory",
            index=models.Index(fields=["branch"], name="accessory_branch_idx"),
        ),
        migrations.AddIndex(
            model_name="accessory",
            index=models.Index(fields=["category"], name="accessory_category_idx"),
        ),
        migrations.AddIndex(
            model_name="accessory",
            index=models.Index(fields=["added_at"], name="accessory_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="accessory",
            index=models.Index(fields=["is_deleted"], name="accessory_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="accessorycategory",
            index=models.Index(fields=["is_deleted"], name="accessory_category_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="accessorycapital",
            index=models.Index(
                fields=["branch", "month"], name="accessory_capital_branch_month_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="accessorycapital",
            index=models.Index(fields=["is_deleted"], name="accessory_capital_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="accessorysale",
            index=models.Index(fields=["is_deleted"], name="accessorysale_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["owner"], name="branch_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["added_at"], name="branch_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["is_deleted"], name="branch_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="branchuser",
            index=models.Index(fields=["branch"], name="branch_user_branch_idx"),
        ),
        migrations.AddIndex(
            model_name="branchuser",
            index=models.Index(fields=["user"], name="branch_user_user_idx"),
        ),
        migrations.AddIndex(
            model_name="branchuser",
            index=models.Index(fields=["role"], name="branch_user_role_idx"),
        ),
        migrations.AddIndex(
            model_name="branchuser",
            index=models.Index(fields=["is_deleted"], name="branch_user_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="branchuser",
            index=models.Index(fields=["added_at"], name="branch_user_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["direction"], name="debt_direction_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["f_name"], name="debt_f_name_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["added_at"], name="debt_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["is_deleted"], name="debt_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["branch", "added_at"], name="debt_branch_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="debtpayment",
            index=models.Index(fields=["added_at"], name="debtpayment_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="debtpayment",
            index=models.Index(fields=["is_deleted"], name="debtpayment_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["type"], name="expense_type_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["added_at"], name="expense_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["is_deleted"], name="expense_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["branch", "added_at"], name="expense_branch_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="extraprofit",
            index=models.Index(fields=["created_by"], name="extra_profit_created_by_idx"),
        ),
        migrations.AddIndex(
            model_name="extraprofit",
            index=models.Index(fields=["added_at"], name="extra_profit_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="extraprofit",
            index=models.Index(fields=["is_deleted"], name="extra_profit_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="extraprofit",
            index=models.Index(fields=["branch", "added_at"], name="extra_profit_branch_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="journal",
            index=models.Index(fields=["action"], name="journal_action_idx"),
        ),
        migrations.AddIndex(
            model_name="journal",
            index=models.Index(fields=["added_at"], name="journal_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="phone",
            index=models.Index(fields=["is_deleted"], name="phone_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="phone",
            index=models.Index(fields=["branch", "added_at"], name="phone_branch_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="phonecategory",
            index=models.Index(fields=["is_deleted"], name="phone_category_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="phonecapital",
            index=models.Index(fields=["is_deleted"], name="phone_capital_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="salary",
            index=models.Index(fields=["branch"], name="salary_branch_idx"),
        ),
        migrations.AddIndex(
            model_name="salary",
            index=models.Index(fields=["employee"], name="salary_employee_idx"),
        ),
        migrations.AddIndex(
            model_name="salary",
            index=models.Index(fields=["created_by"], name="salary_created_by_idx"),
        ),
        migrations.AddIndex(
            model_name="salary",
            index=models.Index(fields=["added_at"], name="salary_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="salary",
            index=models.Index(fields=["is_deleted"], name="salary_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["user"], name="subscription_user_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["status"], name="subscription_status_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["end_date"], name="subscription_end_date_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["added_at"], name="subscription_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["is_deleted"], name="subscription_is_deleted_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["user"], name="subpay_user_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["subscription"], name="subpay_subscription_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["paid_at"], name="subpay_paid_at_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["added_at"], name="subpay_added_at_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["added_by"], name="subpay_added_by_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionpayment",
            index=models.Index(fields=["is_deleted"], name="subpay_is_deleted_idx"),
        ),
    ]
