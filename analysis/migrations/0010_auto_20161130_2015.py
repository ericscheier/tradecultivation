# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-30 20:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0009_auto_20161130_1957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chainpair',
            name='pair',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.Pair'),
        ),
    ]
