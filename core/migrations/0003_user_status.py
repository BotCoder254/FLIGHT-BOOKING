# Generated by Django 5.1.6 on 2025-02-18 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_hotel_image_remove_tour_image_hotelimage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('deactivated', 'Deactivated')], default='active', max_length=15),
        ),
    ]
