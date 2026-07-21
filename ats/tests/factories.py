"""Fabrik-Funktionen für den immer gleichen Welt-Aufbau in den Tests.

Fast jeder Test braucht dieselbe Grundausstattung: Organisation, Einrichtung,
Standort, Jobfamilie, den published-Zustand und ein Entgeltband. Statt sie je
Modul über kopierte _world-Helfer zu bauen, liefern die Fabriken hier
sinnvolle Defaults; alles Abweichende kommt per Schlüsselwort-Argument.
Kollisionsanfällige Werte (Jobfamilien-Name, Bewerber-E-Mail) bekommen ein
uuid-Suffix, damit sich Tests innerhalb einer Transaktion nicht treffen.

Bewusst OHNE test_-Präfix im Dateinamen: das Modul soll vom Test-Discovery
nicht als Testmodul eingesammelt werden.
"""
import uuid
from typing import Any, NamedTuple

from ..models import (
    Applicant,
    Application,
    Facility,
    JobFamily,
    JobPosting,
    Location,
    Organization,
    PayBand,
    WorkflowState,
)


class World(NamedTuple):
    """Die Grundausstattung; Feld-Reihenfolge passt zum Tuple-Unpacking."""

    org: Organization
    facility: Facility
    location: Location
    job_family: JobFamily
    published: WorkflowState
    band: PayBand


def make_world() -> World:
    """Standard-Welt: Träger, Klinik, Standort, Jobfamilie, published-Zustand
    und ein tarif-natives Entgeltband.

    Die Band-Werte sind bewusst konkret (TVöD-P 7 samt Tarifhinweis) — Tests,
    die veröffentlichte Spannen prüfen, können sich darauf verlassen.
    """
    org = Organization.objects.create(name="Träger")
    facility = Facility.objects.create(name="Klinik", organization=org)
    location = Location.objects.create(name="Hamburg", city="Hamburg")
    job_family = JobFamily.objects.create(name=f"Pflege-{uuid.uuid4().hex[:6]}")
    published, _ = WorkflowState.objects.get_or_create(
        name="published", defaults={"description": "Öffentlich"})
    band = PayBand.objects.create(
        name="TVöD-P 7 (Stufe 2–6)", tariffSystem="TVOED",
        minAmount=3304, maxAmount=4106, period="MONTH",
        collectiveAgreement="TVöD-P, Entgeltgruppe P7",
        note="zzgl. Schichtzulagen")
    return World(org, facility, location, job_family, published, band)


def make_job(world: World, **overrides: Any) -> JobPosting:
    """JobPosting mit Welt-Defaults: veröffentlicht und mit Entgeltband.

    Abweichungen per Modellfeld-Name, z. B.
    make_job(w, workflowState=draft, payBand=None).
    """
    fields: dict[str, Any] = {
        "title": "Pflegefachkraft (m/w/d)",
        "organization": world.org,
        "facility": world.facility,
        "location": world.location,
        "jobFamily": world.job_family,
        "workflowState": world.published,
        "payBand": world.band,
    }
    fields.update(overrides)
    return JobPosting.objects.create(**fields)


def make_application(job: JobPosting, *, first_name: str = "Mira",
                     last_name: str = "Muster", email: str | None = None,
                     phone: str | None = None,
                     **overrides: Any) -> Application:
    """Applicant + Application (Status NEW, Bewerber via app.applicant).

    Ohne `email` wird eine eindeutige Adresse erzeugt (der E-Mail-Blind-Index
    ist unique). Weitere Schlüsselwort-Argumente gehen an die Application,
    z. B. status="IN_REVIEW".
    """
    applicant = Applicant.objects.create(
        firstName=first_name, lastName=last_name, phone=phone,
        email=email or f"bewerber-{uuid.uuid4().hex[:10]}@beispiel.example")
    fields: dict[str, Any] = {"applicant": applicant, "jobPosting": job,
                              "status": "NEW"}
    fields.update(overrides)
    return Application.objects.create(**fields)
