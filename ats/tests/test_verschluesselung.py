"""Was über einen Menschen geschrieben wird, gehört zu seinen Daten.

Name, Anschrift und E-Mail der bewerbenden Person lagen längst verschlüsselt —
die Sätze **über** sie nicht: interne Notizen, KI-Begründung, Rücktrittsgrund,
der gesamte Schriftwechsel und die drei Freitextfelder des
Interview-Feedbacks. Dazu die Talent-Pool-Adresse: dieselbe Angabe derselben
Person wie `Applicant.email`, nur ohne Schutz.

Geprüft wird hier nicht, ob die Anwendung den Klartext zurückgibt — das tut
sie ohnehin. Geprüft wird, was **in der Datenbank steht**: Wer die Tabelle
sichert, kopiert oder ein Backup verliert, darf die Sätze nicht lesen können.
"""
from django.db import connection
from django.test import TestCase

from ..models import (
    Applicant,
    Application,
    Interview,
    InterviewFeedback,
    Message,
    TalentPoolSubscription,
)
from .factories import make_job, make_world
from .utils import make_user


def _roh(tabelle: str, spalte: str):
    """Der Wert, wie er wirklich in der Spalte liegt.

    Spalte quoten: PostgreSQL faltet unquotierte Bezeichner klein
    (internalNotes -> internalnotes = existiert nicht).
    """
    q = connection.ops.quote_name
    with connection.cursor() as cur:
        cur.execute(f"SELECT {q(spalte)} FROM {tabelle}")
        zeile = cur.fetchone()
    return zeile[0] if zeile else None


class ApplicationFieldsAtRestTestCase(TestCase):
    KLARTEXT = {
        'internalNotes': "Wirkte im Gespräch unsicher, zweite Meinung einholen.",
        'withdrawReason': "Ich habe eine Stelle näher am Wohnort angenommen.",
        'aiRationale': "Erfüllt drei von vier Muss-Kriterien.",
    }

    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Mara", lastName="K",
                                          email="mara@example.invalid")
        self.app = Application.objects.create(
            applicant=person, jobPosting=job, status="IN_REVIEW",
            **self.KLARTEXT)

    def test_the_application_still_reads_plain_text(self):
        frisch = Application.objects.get(id=self.app.id)
        for feld, wert in self.KLARTEXT.items():
            self.assertEqual(getattr(frisch, feld), wert)

    def test_the_database_holds_no_plain_text(self):
        for feld, wert in self.KLARTEXT.items():
            roh = _roh('ats_application', feld)
            self.assertTrue(roh, f"{feld}: leer")
            self.assertNotEqual(roh, wert, f"{feld} liegt im Klartext")
            self.assertNotIn(wert[:20], roh, f"{feld} enthaelt Klartext")


class MessageAtRestTestCase(TestCase):
    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Timo", lastName="L",
                                          email="timo@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="IN_REVIEW")
        self.text = "Ich bin in Therapie und brauche einen späteren Termin."
        Message.objects.create(application=app, direction="INBOUND",
                               content=self.text)

    def test_the_correspondence_is_not_readable_in_the_table(self):
        """Der Schriftwechsel ist oft der offenherzigste Teil einer Bewerbung."""
        roh = _roh('ats_message', 'content')
        self.assertTrue(roh)
        self.assertNotIn("Therapie", roh)
        self.assertEqual(Message.objects.get().content, self.text)


class InterviewFeedbackAtRestTestCase(TestCase):
    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Nora", lastName="P",
                                          email="nora@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="INVITED")
        from django.utils import timezone
        iv = Interview.objects.create(application=app,
                                      scheduledAt=timezone.now())
        InterviewFeedback.objects.create(
            interview=iv, application=app, author=make_user("fb-autor"),
            recommendation="HIRE",
            strengths="Sehr ruhig im Umgang mit Angehörigen.",
            concerns="Wenig Erfahrung mit Wunddokumentation.",
            comment="Aus meiner Sicht einstellen.")

    def test_judgements_about_a_person_are_encrypted(self):
        for feld, wort in (('strengths', 'Angehörigen'),
                           ('concerns', 'Wunddokumentation'),
                           ('comment', 'einstellen')):
            roh = _roh('ats_interviewfeedback', feld)
            self.assertTrue(roh, feld)
            self.assertNotIn(wort, roh, f"{feld} liegt im Klartext")


class TalentPoolAtRestTestCase(TestCase):
    """Dieselbe Adresse derselben Person war je nach Tabelle geschützt oder nicht."""

    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone
        self.adresse = "pool-person@example.invalid"
        TalentPoolSubscription.objects.create(
            email=self.adresse, consentId="test",
            expiresAt=timezone.now() + timedelta(days=365))

    def test_the_address_is_encrypted(self):
        roh = _roh('ats_talentpoolsubscription', 'email')
        self.assertTrue(roh)
        self.assertNotIn("pool-person", roh)

    def test_lookup_still_works_through_the_blind_index(self):
        """Ohne Blind-Index wäre die Adresse zwar geschützt, aber unauffindbar —
        und `filter(email=...)` gäbe still null Treffer statt eines Fehlers."""
        gefunden = TalentPoolSubscription.objects.get_by_email(self.adresse)
        self.assertEqual(gefunden.email, self.adresse)
        self.assertTrue(
            TalentPoolSubscription.objects.filter_by_email(
                self.adresse.upper()).exists(),
            "Gross-/Kleinschreibung darf den Index nicht auseinanderbringen")

    def test_the_index_is_not_the_address(self):
        roh = _roh('ats_talentpoolsubscription', 'emailHash')
        self.assertTrue(roh)
        self.assertNotIn("pool-person", roh)
        self.assertEqual(len(roh), 64)      # HMAC-SHA256, hex


class GuardrailPersonalFieldsEncryptedTestCase(TestCase):
    """Neue Textfelder an personenbezogenen Modellen brauchen eine Entscheidung.

    Der Anlass: Name, Anschrift und E-Mail lagen verschlüsselt, die Sätze über
    dieselbe Person nicht — interne Notizen, Schriftwechsel, Interview-Urteile,
    die Talent-Pool-Adresse, der Dateiname des Lebenslaufs. Das war kein
    Versäumnis an einer Stelle, sondern acht Felder, die über Jahre einzeln
    dazukamen, ohne dass jemand die Frage stellte.

    Der Wächter stellt sie jetzt: An diesen Modellen muss jedes Text-Feld
    entweder verschlüsselt sein oder hier mit Begründung stehen.
    """

    #: Modelle, die Daten ÜBER eine bewerbende Person tragen.
    MODELLE = ('Applicant', 'Application', 'Message', 'InterviewFeedback',
               'ApplicationDocument', 'TalentPoolSubscription')

    #: Feld -> warum es KEIN personenbezogener Freitext ist.
    UNBEDENKLICH = {
        'Applicant.emailHash': 'Blind-Index, kein lesbarer Inhalt',
        'Application.status': 'Zustand der Bewerbung, kein Personenmerkmal',
        'Application.source': 'Herkunftskanal (DIRECT, STEPSTONE, ...)',
        'Application.aiScore': 'A/B/C/D - Einordnung, kein Freitext',
        'Application.cvStorageId': 'Ablagepfad; seit dem Verschluesselungs-Paket '
                                   'nur noch Zufalls-ID plus Endung. ALTBESTAND '
                                   'traegt weiterhin den Originalnamen - eigene '
                                   'Aufgabe (Umbenennen der vorhandenen Dateien).',
        'Message.direction': 'INBOUND/OUTBOUND',
        'InterviewFeedback.recommendation': 'Empfehlungs-Code, kein Freitext',
        'ApplicationDocument.docType': 'CV/CERTIFICATE/... - Kategorie',
        'ApplicationDocument.file': 'FileField auf den namenlosen Ablagepfad',
        'TalentPoolSubscription.emailHash': 'Blind-Index',
        'TalentPoolSubscription.consentId': 'Einwilligungs-Referenz, kein Inhalt',
        'TalentPoolSubscription.criteria': 'JSON aus Jobfamilien- und Standort-IDs',
    }

    def test_every_text_field_is_encrypted_or_justified(self):
        from django.apps import apps as django_apps
        from django.db import models as djm

        from ..models.base import EncryptedCharField, EncryptedTextField

        offen = []
        for name in self.MODELLE:
            modell = django_apps.get_model('ats', name)
            for feld in modell._meta.get_fields():
                if not isinstance(feld, djm.Field) or feld.is_relation:
                    continue
                if isinstance(feld, (EncryptedCharField, EncryptedTextField)):
                    continue
                if not isinstance(feld, (djm.CharField, djm.TextField,
                                         djm.EmailField, djm.FileField)):
                    continue
                schluessel = f"{name}.{feld.name}"
                if schluessel not in self.UNBEDENKLICH:
                    offen.append(schluessel)
        self.assertEqual(
            offen, [],
            "Textfeld an einem personenbezogenen Modell, weder verschluesselt "
            "noch begruendet. Bitte EncryptedCharField/-TextField verwenden "
            "oder mit Begruendung in UNBEDENKLICH eintragen: " + ", ".join(offen))
