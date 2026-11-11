"""Datos sintéticos; la autoridad clínica permanece desactivada en el perfil."""

from uuid import uuid4
from .helpers import iso


def prepare(p):
    confirm = dict(
        human_confirmation=True,
        reason="Preparación técnica sintética, sin autorización clínica",
    )
    unit = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data=dict(
            folio="ORG-WEB-" + uuid4().hex[:8],
            kind="ORGAN",
            component="KIDNEY",
            blood_group="O+",
            expires_at=iso(days=2),
        ),
    )
    references = p.ok(
        "compatibilidad", "GET", "/api/v1/laboratory/reference-sources", user="medical1"
    )
    ids = [r["id"] for r in references["rules"] if r["kind"] == "ORGAN"]
    profile = p.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/profiles",
        user="medical1",
        data=dict(
            name="Completitud HLA de ensayo",
            kind="ORGAN",
            component="KIDNEY",
            version=1,
            required_tests=["HLA"],
            required_loci=["A"],
            evidence_rules=ids[:1],
            source="Perfil exclusivamente sintético; referencias documentales de etapa 02",
            synthetic=True,
            effective_at=iso(),
        ),
    )
    p.ok(
        "inventario",
        "POST",
        f"/api/v1/resources/{unit['id']}/controls",
        user="medical1",
        data=dict(confirm, version=1, lab_profile_id=profile["id"]),
    )
    sample = p.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/samples",
        user="operator1",
        data=dict(
            resource_id=unit["id"],
            profile_id=profile["id"],
            identifier="SYN-" + uuid4().hex,
            collected_at=iso(minutes=-5),
        ),
    )
    p.ok(
        "compatibilidad",
        "POST",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        user="operator1",
        data=dict(confirm, version=1, decision="RECEIVED"),
    )
    result = p.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/results",
        user="operator1",
        data=dict(
            sample_id=sample["id"],
            test_code="HLA",
            result_state="REPORTED",
            method="Técnica ficticia",
            laboratory="Laboratorio de prueba",
            reference="Resultado sintético",
            measured_at=iso(minutes=-2),
            issued_at=iso(minutes=-1),
            hla=dict(
                nomenclature="HLA-colon-2010",
                nomenclature_version="2010",
                resolution="Dos campos",
                loci=[dict(locus="A", alleles=["A*01:01"], ambiguous=False)],
            ),
        ),
    )
    # La revisión y liberación se realizan en formularios con MFA, no en el seed.
    return dict(unit=unit, result=result, sample=sample, profile=profile)
