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


class ScreeningAnswersAtRestTestCase(TestCase):
    """Die Antworten der Person auf Screening-Fragen - bei Freitext-Fragen
    ihre eigenen Worte, dieselbe Kategorie wie das Anschreiben. Als JSONField
    lagen sie im Klartext, waehrend `coverLetterTxt` daneben verschluesselt
    war: Der Waechter prueft(e) nur Char-/Textfelder, und ein JSONField ist
    keins von beiden."""

    ANTWORTEN = {
        "Warum wechseln Sie?": "Konflikt mit der aktuellen Leitung.",
        "Examen?": "ja",
    }

    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Ines", lastName="R",
                                          email="ines@example.invalid")
        self.app = Application.objects.create(
            applicant=person, jobPosting=job, status="NEW",
            screeningAnswersJson=self.ANTWORTEN)

    def test_the_application_still_reads_the_dict(self):
        frisch = Application.objects.get(id=self.app.id)
        self.assertEqual(frisch.screeningAnswersJson, self.ANTWORTEN)

    def test_values_list_also_reads_the_dict(self):
        """`insights.py` liest das Feld ueber values_list - der Weg muss
        genauso entschluesseln wie der Attributzugriff."""
        (wert,) = Application.objects.filter(id=self.app.id).values_list(
            'screeningAnswersJson', flat=True)
        self.assertEqual(wert, self.ANTWORTEN)

    def test_the_database_holds_no_plain_text(self):
        roh = _roh('ats_application', 'screeningAnswersJson')
        self.assertTrue(roh)
        self.assertNotIn("Konflikt", roh)
        self.assertNotIn("Warum wechseln", roh)

    def test_clearing_still_works(self):
        """`data_retention` leert das Feld mit `{}` - das muss auch ueber die
        Verschluesselung hinweg ankommen."""
        self.app.screeningAnswersJson = {}
        self.app.save(update_fields=['screeningAnswersJson'])
        self.assertEqual(
            Application.objects.get(id=self.app.id).screeningAnswersJson, {})


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
    """Personenbezogene Felder in ALLEN Modellen — nicht in einer Liste.

    Die erste Fassung dieses Wächters prüfte sechs namentlich genannte Modelle.
    Er kodierte damit die Fälle, die ich gefunden hatte, nicht die Fehlerklasse
    — und übersah prompt `JobAlertSubscription.email`: dieselbe Art Angabe
    derselben Art Person wie im Talent-Pool, nur ein Modell weiter.

    Jetzt läuft er über jedes Modell der Anwendung und erkennt Felder am Namen
    (E-Mail, Telefon, Vor-/Nachname, Anschrift). Jedes davon muss verschlüsselt
    sein — oder hier mit Begründung stehen.
    """

    #: Muster fuer Feldnamen, die auf eine Person zeigen.
    MUSTER = r"(email|phone|mobil|telefon|firstname|lastname|address|anschrift)"

    #: Feld -> warum es NICHT verschluesselt gehoert.
    UNBEDENKLICH = {
        'Applicant.emailHash': 'Blind-Index, kein lesbarer Inhalt',
        'TalentPoolSubscription.emailHash': 'Blind-Index',
        'JobAlertSubscription.emailHash': 'Blind-Index',
        'Location.address': 'Anschrift einer EINRICHTUNG, kein Personendatum - '
                            'steht auf jeder Stellenanzeige',
        # Die Kontaktperson wird auf der Stellenanzeige VEROEFFENTLICHT
        # (Name, E-Mail, Telefon stehen dort im Klartext im HTML). Sie hinter
        # eine Verschluesselung zu legen schuetzt nichts, was nicht ohnehin
        # oeffentlich ist - kostet aber die alphabetische Sortierung der
        # Kontaktliste, weil dann Ciphertext sortiert wuerde.
        'ContactPerson.firstName': 'auf der Stellenanzeige veroeffentlicht',
        'ContactPerson.lastName': 'auf der Stellenanzeige veroeffentlicht; '
                                  'order_by wuerde sonst Ciphertext sortieren',
        'ContactPerson.email': 'auf der Stellenanzeige veroeffentlicht',
        'ContactPerson.phone': 'auf der Stellenanzeige veroeffentlicht',
    }

    def test_every_personal_field_is_encrypted_or_justified(self):
        import re

        from django.apps import apps as django_apps
        from django.db import models as djm

        from ..models.base import (
            EncryptedCharField,
            EncryptedJSONField,
            EncryptedTextField,
        )

        muster = re.compile(self.MUSTER, re.I)
        offen = []
        for modell in django_apps.get_app_config('ats').get_models():
            for feld in modell._meta.get_fields():
                if not isinstance(feld, djm.Field) or feld.is_relation:
                    continue
                if isinstance(feld, (EncryptedCharField, EncryptedTextField,
                                     EncryptedJSONField)):
                    continue
                # JSONField gehoert MIT geprueft: `screeningAnswersJson` lag
                # unverschluesselt, weil die erste Fassung nur Char/Text sah.
                if not isinstance(feld, (djm.CharField, djm.TextField,
                                         djm.EmailField, djm.JSONField)):
                    continue
                if not muster.search(feld.name):
                    continue
                schluessel = f"{modell.__name__}.{feld.name}"
                if schluessel not in self.UNBEDENKLICH:
                    offen.append(schluessel)
        self.assertEqual(
            offen, [],
            "Personenbezogenes Feld, weder verschluesselt noch begruendet. "
            "Bitte EncryptedCharField/-TextField verwenden oder mit "
            "Begruendung in UNBEDENKLICH eintragen: " + ", ".join(offen))

    def test_the_exception_list_has_no_dead_entries(self):
        """Eine Begruendung fuer ein Feld, das es nicht mehr gibt, ist eine
        stehen gebliebene Erlaubnis: Legt jemand spaeter ein gleichnamiges
        Feld an, laesst der Waechter es wortlos durch."""
        from django.apps import apps as django_apps
        vorhanden = {f"{m.__name__}.{f.name}"
                     for m in django_apps.get_app_config('ats').get_models()
                     for f in m._meta.get_fields() if hasattr(f, 'name')}
        tot = sorted(set(self.UNBEDENKLICH) - vorhanden)
        self.assertEqual(tot, [], f"Begruendung ohne zugehoeriges Feld: {tot}")


class GuardrailApplicationDomainTextFieldsTestCase(TestCase):
    """Neue Textfelder an personenbezogenen Modellen brauchen eine Entscheidung.

    Der Anlass: Name, Anschrift und E-Mail lagen verschlüsselt, die Sätze über
    dieselbe Person nicht — interne Notizen, Schriftwechsel, Interview-Urteile,
    die Talent-Pool-Adresse, der Dateiname des Lebenslaufs. Das war kein
    Versäumnis an einer Stelle, sondern acht Felder, die über Jahre einzeln
    dazukamen, ohne dass jemand die Frage stellte.

    Der Wächter stellt sie jetzt: An diesen Modellen muss jedes Text- UND
    JSON-Feld entweder verschlüsselt sein oder hier mit Begründung stehen.
    JSONField gehört dazu, seit `screeningAnswersJson` — die eigenen Worte
    der Person auf Freitext-Fragen — genau durch diese Lücke rutschte:
    Der Wächter sah nur Char/Text, und ein JSONField ist keins von beiden.
    """

    #: Modelle, die Daten ÜBER eine bewerbende Person tragen.
    MODELLE = ('Applicant', 'Application', 'Message', 'InterviewFeedback',
               'ApplicationDocument', 'TalentPoolSubscription',
               'JobAlertSubscription')

    #: Feld -> warum es KEIN personenbezogener Freitext ist.
    UNBEDENKLICH = {
        'Applicant.emailHash': 'Blind-Index, kein lesbarer Inhalt',
        'Application.status': 'Zustand der Bewerbung, kein Personenmerkmal',
        'Application.source': 'Herkunftskanal (DIRECT, STEPSTONE, ...)',
        'Application.aiScore': 'A/B/C/D - Einordnung, kein Freitext',
        'Application.cvStorageId': 'Ablagepfad, nur Zufalls-ID plus Endung. '
                                   'Der Anzeigename steht verschluesselt in '
                                   'cvFileName; Altbestand raeumt '
                                   '`manage.py anonymize_upload_names` auf.',
        'Message.direction': 'INBOUND/OUTBOUND',
        'InterviewFeedback.recommendation': 'Empfehlungs-Code, kein Freitext',
        'ApplicationDocument.docType': 'CV/CERTIFICATE/... - Kategorie',
        'ApplicationDocument.file': 'FileField auf den namenlosen Ablagepfad',
        'TalentPoolSubscription.emailHash': 'Blind-Index',
        'TalentPoolSubscription.consentId': 'Einwilligungs-Referenz, kein Inhalt',
        'TalentPoolSubscription.criteria': 'JSON aus Jobfamilien- und Standort-IDs',
        # Zahlenwerte 1..4 je Leitfaden-Kriterium - Einordnung wie aiScore,
        # kein Freitext. Die Freitext-Urteile derselben Rueckmeldung
        # (strengths/concerns/comment) sind verschluesselt.
        'InterviewFeedback.ratingsJson': 'Zahlenwerte 1..4 je Kriterium',
        'InterviewFeedback.guideCoverageJson':
            'welche Leitfaden-Themen das Gespraech behandelt hat - '
            'beschreibt das Gespraech, nicht die Person',
        'JobAlertSubscription.emailHash': 'Blind-Index',
        'JobAlertSubscription.status': 'PENDING/ACTIVE/INACTIVE - Zustand',
        'JobAlertSubscription.categories': 'JSON-Liste von Jobfamilien-IDs',
        'JobAlertSubscription.locations': 'JSON-Liste von Standort-IDs',
        'JobAlertSubscription.confirmationToken': 'Zufalls-Token, kein Inhalt',
        'JobAlertSubscription.managementToken': 'Zufalls-Token, kein Inhalt',
    }

    def test_every_text_field_is_encrypted_or_justified(self):
        from django.apps import apps as django_apps
        from django.db import models as djm

        from ..models.base import (
            EncryptedCharField,
            EncryptedJSONField,
            EncryptedTextField,
        )

        offen = []
        for name in self.MODELLE:
            modell = django_apps.get_model('ats', name)
            for feld in modell._meta.get_fields():
                if not isinstance(feld, djm.Field) or feld.is_relation:
                    continue
                if isinstance(feld, (EncryptedCharField, EncryptedTextField,
                                     EncryptedJSONField)):
                    continue
                if not isinstance(feld, (djm.CharField, djm.TextField,
                                         djm.EmailField, djm.FileField,
                                         djm.JSONField)):
                    continue
                schluessel = f"{name}.{feld.name}"
                if schluessel not in self.UNBEDENKLICH:
                    offen.append(schluessel)
        self.assertEqual(
            offen, [],
            "Textfeld an einem personenbezogenen Modell, weder verschluesselt "
            "noch begruendet. Bitte EncryptedCharField/-TextField verwenden "
            "oder mit Begruendung in UNBEDENKLICH eintragen: " + ", ".join(offen))

    def test_neither_list_has_dead_entries(self):
        from django.apps import apps as django_apps
        modelle = {m.__name__ for m
                   in django_apps.get_app_config('ats').get_models()}
        tote_modelle = sorted(set(self.MODELLE) - modelle)
        self.assertEqual(tote_modelle, [],
                         f"Modell in der Liste existiert nicht mehr: {tote_modelle}")
        vorhanden = {f"{m.__name__}.{f.name}"
                     for m in django_apps.get_app_config('ats').get_models()
                     for f in m._meta.get_fields() if hasattr(f, 'name')}
        tot = sorted(set(self.UNBEDENKLICH) - vorhanden)
        self.assertEqual(tot, [], f"Begruendung ohne zugehoeriges Feld: {tot}")


class JobAlertAtRestTestCase(TestCase):
    """Die Adresse einer interessierten Person - nirgends veröffentlicht."""

    def setUp(self):
        from ..models import JobAlertSubscription
        self.adresse = "alert-person@example.invalid"
        JobAlertSubscription.objects.create(
            email=self.adresse, status="ACTIVE",
            confirmationToken="c-1", managementToken="m-1")

    def test_the_address_is_encrypted(self):
        roh = _roh('ats_jobalertsubscription', 'email')
        self.assertTrue(roh)
        self.assertNotIn("alert-person", roh)

    def test_the_keyword_is_encrypted(self):
        """Das Suchwort ist frei getippt und sagt etwas ueber die Person
        ("Teilzeit Nachtdienst") - es gehoert zur Adresse, nicht daneben."""
        from ..models import JobAlertSubscription
        sub = JobAlertSubscription.objects.get()
        sub.keyword = "Teilzeit Nachtdienst"
        sub.save(update_fields=['keyword'])
        roh = _roh('ats_jobalertsubscription', 'keyword')
        self.assertTrue(roh)
        self.assertNotIn("Nachtdienst", roh)
        self.assertEqual(JobAlertSubscription.objects.get().keyword,
                         "Teilzeit Nachtdienst")

    def test_one_subscription_per_address_still_holds(self):
        """Die Eindeutigkeit haengt jetzt am Blind-Index, nicht an der Spalte."""
        from ..models import JobAlertSubscription
        sub, angelegt = JobAlertSubscription.objects.get_or_create_by_email(
            self.adresse.upper(),
            defaults={'status': 'PENDING', 'confirmationToken': 'c-2',
                      'managementToken': 'm-2'})
        self.assertFalse(angelegt, "Gross-/Kleinschreibung legte ein zweites "
                                   "Abo an - das Double-Opt-in waere damit "
                                   "umgangen.")
        self.assertEqual(JobAlertSubscription.objects.count(), 1)
