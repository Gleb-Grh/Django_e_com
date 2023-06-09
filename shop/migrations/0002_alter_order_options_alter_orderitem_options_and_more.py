# Generated by Django 4.2 on 2023-04-26 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='orderitem',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='payment',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['pk']},
        ),
        migrations.RemoveField(
            model_name='product',
            name='image_url',
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(null=True, upload_to=''),
        ),
    ]
