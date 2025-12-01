"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.db import migrations, models
import uuid

def generate_public_ids(apps, schema_editor):
    Reservation = apps.get_model('web', 'Reservation')

    for r in Reservation.objects.filter(public_id__isnull=True):
        r.public_id = "MBL-" + uuid.uuid4().hex[:8].upper()
        r.save(update_fields=["public_id"])

class Migration(migrations.Migration):

    dependencies = [
        ('web', '0005_reservation_public_id'),
    ]

    operations = [
        migrations.RunPython(generate_public_ids),
        migrations.AlterField(
            model_name='reservation',
            name='public_id',
            field=models.CharField(editable=False, help_text='Public-facing reservation ID.', max_length=12, unique=True),
        ),
    ]
