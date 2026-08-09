"""Das Job-Alert-Suchwort at rest verschluesseln.

`JobAlertSubscription.keyword` ist von der abonnierenden Person frei getippt
("Teilzeit Nachtdienst") - anders als die ID-Listen `categories`/`locations`
echter Freitext, der etwas ueber sie aussagt. Die E-Mail derselben Zeile lag
laengst verschluesselt, das Suchwort daneben im Klartext.

Hier reicht ein `AlterField`: varchar nach TEXT braucht auf PostgreSQL kein
`USING` (anders als jsonb in 0013). Die Datenmigration ist idempotent - das
Lesen liefert bei Klartext-Zeilen den Rohwert, bei bereits verschluesselten
den Klartext; das Speichern verschluesselt so oder so.
"""
from django.db import migrations

import ats.models.base


def _verschluesseln(apps, schema_editor):
    JobAlertSubscription = apps.get_model('ats', 'JobAlertSubscription')
    for sub in JobAlertSubscription.objects.all().iterator(chunk_size=500):
        sub.save(update_fields=['keyword'])


def _zurueck(apps, schema_editor):
    """Bewusst ohne Wirkung - ein Rueckbau wuerde den Schutz aktiv abbauen."""


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0013_screening_antworten_verschluesselt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobalertsubscription',
            name='keyword',
            field=ats.models.base.EncryptedCharField(
                blank=True, default='', max_length=120),
        ),
        migrations.RunPython(_verschluesseln, _zurueck),
    ]
