"""Vorlagen bekommen einen Zweck - und die bestehenden werden einmalig zugeordnet.

Bis hierher suchte die Automatik ihre Vorlage ueber den Namen
(`name__icontains='absage'`). Wer sie "Ablehnung" nannte oder umbenannte, bekam
keinen Fehler: Die Absage fiel still auf einen fest einprogrammierten Text
zurueck, den niemand im Haus je freigegeben hatte - und den Bewerbende lasen.

Die Zuordnung hier ist die EINZIGE Stelle, an der noch geraten wird, und sie
laeuft genau einmal. Was nicht sicher zuzuordnen ist, bleibt bewusst ohne
Zweck: Eine falsch zugeordnete Vorlage waere schlimmer als eine offene Luecke,
weil sie unbemerkt an Bewerbende ginge. Die Verwaltungsseite zeigt danach, was
noch zu setzen ist.
"""
from django.db import migrations, models

# Bewusst hier dupliziert statt importiert: Eine Migration muss auch dann noch
# laufen, wenn der Anwendungscode sich weiterentwickelt hat.
NAME_HINTS = {
    "CONFIRMATION": ("eingangsbest", "bestätigung", "bestaetigung", "eingang"),
    "INVITATION": ("einladung", "gespräch", "gespraech", "interview"),
    "REJECTION": ("absage", "ablehnung"),
}


def assign_purposes(apps, schema_editor):
    EmailTemplate = apps.get_model("ats", "EmailTemplate")
    taken = set()
    for tpl in EmailTemplate.objects.order_by("name"):
        lowered = (tpl.name or "").lower()
        for purpose, hints in NAME_HINTS.items():
            # Je Zweck nur die ERSTE passende Vorlage - bei zwei Kandidaten
            # waere die Wahl geraten, und Raten ist genau das Problem.
            if purpose in taken:
                continue
            if any(hint in lowered for hint in hints):
                tpl.purpose = purpose
                tpl.save(update_fields=["purpose"])
                taken.add(purpose)
                break


def clear_purposes(apps, schema_editor):
    EmailTemplate = apps.get_model("ats", "EmailTemplate")
    EmailTemplate.objects.update(purpose="")


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0006_remove_appstep_appticket_remove_appstep_assigneduser_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtemplate',
            name='purpose',
            field=models.CharField(blank=True, choices=[('CONFIRMATION', 'Eingangsbestätigung'), ('INVITATION', 'Einladung zum Gespräch'), ('REJECTION', 'Absage'), ('', 'Freier Textbaustein (keine Automatik)')], default='', max_length=20),
        ),
        migrations.RunPython(assign_purposes, clear_purposes),
    ]
