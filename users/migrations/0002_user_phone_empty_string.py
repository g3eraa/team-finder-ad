from django.db import migrations, models


def replace_null_phones(apps, schema_editor):
    users = apps.get_model("users", "User").objects.using(schema_editor.connection.alias)
    users.filter(phone__isnull=True).update(phone="")


def restore_null_phones(apps, schema_editor):
    users = apps.get_model("users", "User").objects.using(schema_editor.connection.alias)
    users.filter(phone="").update(phone=None)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                "телефон", max_length=12, blank=True, default="", null=True
            ),
        ),
        migrations.RunPython(replace_null_phones, restore_null_phones),
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField("телефон", max_length=12, blank=True, default=""),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                fields=("phone",),
                condition=~models.Q(phone=""),
                name="unique_nonempty_user_phone",
                violation_error_message="Этот номер телефона уже используется.",
            ),
        ),
    ]
