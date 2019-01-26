# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-10 16:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import vedm.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField()),
                ('subtitle', models.TextField()),
                ('summary', vedm.models.MarkupField()),
                ('ingress', vedm.models.MarkupField()),
                ('body', vedm.models.MarkupField()),
                ('date_created', models.DateField()),
                ('date_updated', models.DateField()),
                ('scripts', models.TextField()),
                ('parent_object', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='vedm.Document')),
            ],
            options={
                'ordering': ['date_created', 'title'],
            },
            bases=(models.Model, vedm.models.UploadableMixin),
        ),
    ]
