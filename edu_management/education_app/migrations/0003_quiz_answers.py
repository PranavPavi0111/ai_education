# Generated by Django 5.1 on 2025-01-07 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education_app', '0002_student_batch_student_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='answers',
            field=models.JSONField(default=''),
            preserve_default=False,
        ),
    ]
