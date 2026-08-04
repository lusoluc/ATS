"""Freigabe-Urheber auf den echten Anmelde-Benutzer umstellen.

Warum Entfernen + Neuanlegen statt AlterField: Die alte Spalte zeigte auf das
Prisma-Alt-Modell `User` und war damit eine UUID; das Django-Benutzermodell hat
eine Integer-ID. PostgreSQL verweigert diesen Cast zu Recht ("cannot cast type
uuid to integer") - SQLite haette ihn klaglos geschluckt und den Fehler bis in
die Produktion getragen.

Kein Datenverlust: Das Feld war strukturell nicht befuellbar (mit dem
Alt-Modell meldet sich in dieser Anwendung niemand an) und in jeder Zeile NULL.
Wer bei Altbestand entschieden hat, steht im verketteten Audit-Log
(APPROVAL_APPROVED/-REJECTED/-RETURNED mit Benutzernamen).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0004_interviewfeedback_guidecoveragejson_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='approvalstep',
            name='actionTakenBy',
        ),
        migrations.AddField(
            model_name='approvalstep',
            name='actionTakenBy',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='approvalSteps',
                                    to=settings.AUTH_USER_MODEL),
        ),
    ]
