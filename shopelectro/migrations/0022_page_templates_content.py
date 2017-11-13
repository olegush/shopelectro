# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-17 07:36
from __future__ import unicode_literals

from django.db import migrations, models
from pages.models import PageTemplate

FROM_TAG = 'tags.titles'
TO_TAG = 'tag_titles'
PAGE_TEMPLATE_FIELDS = [
    'name', 'h1', 'keywords',
    'description', 'title', 'seo_text'
]


def migrate_forward(apps, schema_editor):
    # pycharm inspection settings:
    # noinspection PyUnresolvedReferences
    for template in PageTemplate.objects.all():
        for field in PAGE_TEMPLATE_FIELDS:
            new_value = getattr(template, field).replace(FROM_TAG, TO_TAG)
            setattr(template, field, new_value)
            template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shopelectro', '0021_order_comment'),
    ]

    operations = [
        migrations.RunPython(migrate_forward),
    ]
