"""Screening-Antworten at rest verschluesseln.

`Application.screeningAnswersJson` traegt die Antworten der bewerbenden Person
auf die Screening-Fragen - bei Freitext-Fragen ihre eigenen Worte, dieselbe
Kategorie wie das Anschreiben (`coverLetterTxt`), das eine Zeile drueber laengst
verschluesselt liegt. Als JSONField stand es im Klartext in der Datenbank.

WARUM NICHT einfach `AlterField`: Auf PostgreSQL ist die Spalte `jsonb`. Ein
Typwechsel nach TEXT braeuchte dort `ALTER COLUMN ... USING`, das Djangos
AlterField nicht erzeugt - die Migration braeche genau auf dem System, auf dem
sie in Produktion laeuft (die 0005-Lehre). Deshalb in vier Schritten:
neue TEXT-Spalte anlegen, Daten verschluesselt hinueberkopieren, alte
jsonb-Spalte entfernen, neue Spalte auf den alten Namen umbenennen.

Die Datenmigration ist idempotent: Beim Wiederholen liest der Kopierschritt
die noch unveraenderte jsonb-Spalte und ueberschreibt die Kopie.
"""
from django.db import migrations

import ats.models.base


def _kopieren(apps, schema_editor):
    """Bestand aus der jsonb-Spalte verschluesselt in die neue Spalte legen."""
    Application = apps.get_model('ats', 'Application')
    for app in Application.objects.all().iterator(chunk_size=500):
        # Lesen liefert das dict aus der alten JSONField-Spalte; das Speichern
        # ueber das neue EncryptedJSONField verschluesselt es.
        app.screeningAnswersNeu = app.screeningAnswersJson or {}
        app.save(update_fields=['screeningAnswersNeu'])


def _zurueck(apps, schema_editor):
    """Bewusst ohne Wirkung.

    Ein Rueckbau muesste entschluesseln und im Klartext ablegen - also den
    Schutz aktiv wieder abbauen. Wer die Migration zurueckdreht, will die
    Struktur zurueck, nicht die Daten offenlegen.
    """


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0012_jobalert_adresse'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='screeningAnswersNeu',
            field=ats.models.base.EncryptedJSONField(default=dict),
        ),
        migrations.RunPython(_kopieren, _zurueck),
        migrations.RemoveField(
            model_name='application',
            name='screeningAnswersJson',
        ),
        migrations.RenameField(
            model_name='application',
            old_name='screeningAnswersNeu',
            new_name='screeningAnswersJson',
        ),
    ]
