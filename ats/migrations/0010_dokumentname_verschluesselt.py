"""Anzeigename hochgeladener Nachweise verschluesseln.

Der Anzeigename ist meist der Originaldateiname - und der heisst haeufig
"Lebenslauf_Maria_Schmidt.pdf". Er beschreibt also die Person und gehoert
hinter dieselbe Schranke wie ihr Name.

Wie in 0009 ist die Datenmigration idempotent: Lesen liefert in beiden Faellen
Klartext, Speichern verschluesselt.
"""

from django.db import migrations

import ats.models.base


def _verschluesseln(apps, schema_editor):
    modell = apps.get_model('ats', 'ApplicationDocument')
    for obj in modell.objects.all().iterator(chunk_size=500):
        obj.save(update_fields=['name'])


def _zurueck(apps, schema_editor):
    """Ohne Wirkung - siehe 0009: Ein Rueckbau hiesse, den Schutz abzubauen."""


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0009_pii_verschluesselung'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationdocument',
            name='name',
            field=ats.models.base.EncryptedCharField(max_length=255),
        ),
        migrations.RunPython(_verschluesseln, _zurueck),
    ]
