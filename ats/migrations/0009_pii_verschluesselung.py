"""Personenbezogene Freitexte und die Talent-Pool-Adresse at rest verschluesseln.

Name, Anschrift und E-Mail der bewerbenden Person lagen laengst verschluesselt -
die Saetze UEBER sie nicht: interne Notizen, KI-Begruendung, Ruecktrittsgrund,
der gesamte Schriftwechsel und die drei Freitextfelder des Interview-Feedbacks.
Dazu die Talent-Pool-Adresse: dieselbe Angabe derselben Person wie
`Applicant.email`, nur ohne Schutz.

Die Datenmigration ist von Natur aus idempotent: Das Lesen liefert in beiden
Faellen Klartext - bei bereits verschluesselten Zeilen durch Entschluesseln,
bei Klartext-Zeilen, weil `from_db_value` bei fehlgeschlagener Entschluesselung
den Rohwert zurueckgibt. Das anschliessende Speichern verschluesselt so oder so.
"""
from django.db import migrations, models

import ats.models.base


def _verschluesseln(apps, schema_editor):
    """Bestandszeilen nachziehen - in Haeppchen, damit grosse Tabellen halten."""
    from ats.models.base import email_blind_index

    def durchgehen(modell, felder, extra=None):
        for obj in modell.objects.all().iterator(chunk_size=500):
            if extra:
                extra(obj, email_blind_index)
            obj.save(update_fields=felder)

    durchgehen(apps.get_model('ats', 'Application'),
               ['internalNotes', 'withdrawReason', 'aiRationale'])
    durchgehen(apps.get_model('ats', 'Message'), ['content'])
    durchgehen(apps.get_model('ats', 'InterviewFeedback'),
               ['strengths', 'concerns', 'comment'])

    # Der Blind-Index wird hier ausdruecklich gesetzt: Historische Modelle in
    # Migrationen tragen die eigenen `save()`-Methoden NICHT, die ihn sonst
    # berechnen wuerden.
    def mit_index(obj, blind):
        obj.email = (obj.email or '').strip().lower()
        obj.emailHash = blind(obj.email)

    durchgehen(apps.get_model('ats', 'TalentPoolSubscription'),
               ['email', 'emailHash'], extra=mit_index)


def _zurueck(apps, schema_editor):
    """Bewusst ohne Wirkung.

    Ein Rueckbau muesste entschluesseln und im Klartext ablegen - also den
    Schutz aktiv wieder abbauen. Wer eine Migration zurueckdreht, will die
    Struktur zurueck, nicht die Daten offenlegen. Gelesen wird auch danach
    korrekt, weil `from_db_value` bei fehlgeschlagener Entschluesselung den
    Rohwert liefert.
    """


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0008_auditlog_userid_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='talentpoolsubscription',
            name='emailHash',
            field=models.CharField(editable=False, max_length=64, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='aiRationale',
            field=ats.models.base.EncryptedTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='internalNotes',
            field=ats.models.base.EncryptedTextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='application',
            name='withdrawReason',
            field=ats.models.base.EncryptedTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='comment',
            field=ats.models.base.EncryptedTextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='concerns',
            field=ats.models.base.EncryptedTextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='strengths',
            field=ats.models.base.EncryptedTextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='message',
            name='content',
            field=ats.models.base.EncryptedTextField(),
        ),
        migrations.AlterField(
            model_name='talentpoolsubscription',
            name='email',
            field=ats.models.base.EncryptedCharField(max_length=254),
        ),
        migrations.RunPython(_verschluesseln, _zurueck),
    ]
