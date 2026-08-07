"""Job-Alert-Adresse verschluesseln - wie Applicant und Talent-Pool.

Das Verschluesselungs-Paket (0009) nahm sechs Modelle mit und liess dieses
aus: Der Waechter dort pruefte eine feste LISTE von Modellen statt der
Fehlerklasse. Die Adresse gehoert einer Person, die sich fuer Stellen
interessiert - sie steht nirgends oeffentlich, anders als die Kontaktdaten auf
der Stellenanzeige.

Wie in 0009 ist die Datenmigration idempotent; der Blind-Index wird
ausdruecklich gesetzt, weil historische Modelle keine `save()`-Methoden tragen.
"""

from django.db import migrations, models

import ats.models.base


def _verschluesseln(apps, schema_editor):
    from ats.models.base import email_blind_index
    modell = apps.get_model('ats', 'JobAlertSubscription')
    for obj in modell.objects.all().iterator(chunk_size=500):
        obj.email = (obj.email or '').strip().lower()
        obj.emailHash = email_blind_index(obj.email)
        obj.save(update_fields=['email', 'emailHash'])


def _zurueck(apps, schema_editor):
    """Ohne Wirkung - siehe 0009."""


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0011_cv_anzeigename'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobalertsubscription',
            name='emailHash',
            field=models.CharField(editable=False, max_length=64, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='jobalertsubscription',
            name='email',
            field=ats.models.base.EncryptedCharField(max_length=254),
        ),
        migrations.RunPython(_verschluesseln, _zurueck),
    ]
