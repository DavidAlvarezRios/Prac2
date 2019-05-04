# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-04-28 21:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forkilla', '0004_auto_20190424_1822'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.CharField(default='Anonymous', max_length=100),
        ),
        migrations.AlterField(
            model_name='review',
            name='stars',
            field=models.IntegerField(),
        ),
    ]