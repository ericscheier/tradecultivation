# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-17 15:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('length', models.IntegerField()),
                ('courtage', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('is_eligible', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ChainPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField()),
                ('chain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.Chain')),
            ],
            options={
                'ordering': ('chain', 'index'),
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('altname', models.CharField(max_length=100)),
                ('decimals', models.IntegerField()),
                ('display_decimals', models.IntegerField()),
                ('is_eligible', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Pair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('altname', models.CharField(max_length=100)),
                ('is_eligible', models.BooleanField(default=False)),
                ('base_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_currency', to='analysis.Currency')),
                ('quote_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quote_currency', to='analysis.Currency')),
            ],
        ),
        migrations.AddField(
            model_name='chainpair',
            name='pair',
            field=models.ManyToManyField(to='analysis.Pair'),
        ),
    ]
