"""Sieben nie benutzte Tabellen aus dem Prisma-Vorgaenger entfernen.

Role, User, UserFacility, AppTicket, AppStep, WorkflowDefinition, CareerPath.
Keine Zeile Anwendungscode hat sie je gelesen oder geschrieben; sie waren nur
im Django-Admin registriert - und Registrierung ist keine Nutzung. Genau dieser
Fehlschluss hat einen frueheren Aufraeum-Durchgang zu dem Schluss "kein toter
Code" gefuehrt.

Nicht bloss unnuetz, sondern schaedlich: Der Fremdschluessel von ApprovalStep
auf das tote User-Modell hat den Urheber jeder Freigabe unbefuellbar gemacht
(behoben in U6) und beim Umhaengen eine PostgreSQL-Migration zerlegt.

Datenverlust ist ausgeschlossen: Die Tabellen konnten nur ueber den ebenfalls
entfernten Prisma-Importbefehl gefuellt werden, dessen Quell-Stack seit dem
Aufraeumen der Express-/Next.js-Altlasten nicht mehr im Repo liegt.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ats', '0005_alter_approvalstep_actiontakenby'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appstep',
            name='appTicket',
        ),
        migrations.RemoveField(
            model_name='appstep',
            name='assignedUser',
        ),
        migrations.RemoveField(
            model_name='appticket',
            name='application',
        ),
        migrations.RemoveField(
            model_name='appticket',
            name='workflow',
        ),
        migrations.DeleteModel(
            name='CareerPath',
        ),
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        # Reihenfolge von Hand korrigiert: Der Autodetector wollte erst das
        # Feld `user` entfernen und danach das unique_together aufloesen, das
        # genau dieses Feld nennt - SQLite baut die Tabelle dabei neu und
        # stolpert ueber den Verweis ins Leere.
        migrations.AlterUniqueTogether(
            name='userfacility',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='userfacility',
            name='user',
        ),
        migrations.RemoveField(
            model_name='userfacility',
            name='facility',
        ),
        migrations.RemoveField(
            model_name='workflowdefinition',
            name='facility',
        ),
        migrations.DeleteModel(
            name='AppStep',
        ),
        migrations.DeleteModel(
            name='AppTicket',
        ),
        migrations.DeleteModel(
            name='Role',
        ),
        migrations.DeleteModel(
            name='User',
        ),
        migrations.DeleteModel(
            name='UserFacility',
        ),
        migrations.DeleteModel(
            name='WorkflowDefinition',
        ),
    ]
