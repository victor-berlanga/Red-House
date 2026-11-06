"""Replay exclusions from recorded inputs; never query or rewrite current clinical data."""

from datetime import timedelta

from redhouse.models import utc_date


def considered(snapshot):
    from .routes import compatible

    profile = snapshot.get("execution_profile")
    manual = snapshot.get("manual_review", False)
    output = []
    for original in snapshot["considered"]:
        x = original["inputs"]
        reasons = []
        outcome = "EXCLUDED"
        if (x["kind"], x["component"]) != (snapshot["kind"], snapshot["component"]):
            reasons = ["OTHER_COMPONENT"]
        elif not manual and not (
            compatible(x["blood_group"], x["recipient_group"])
            if snapshot["kind"] == "BLOOD"
            else x["blood_group"][:-1] == x["recipient_group"][:-1]
        ):
            reasons = [
                "ABO_RHD_FILTER" if snapshot["kind"] == "BLOOD" else "ABO_FILTER"
            ]
        elif not x.get("route"):
            reasons = ["MISSING_ROUTE"]
        elif utc_date(x["expires_at"]) <= utc_date(snapshot["as_of"]) + timedelta(
            minutes=x["route"]["travel_minutes"]
        ):
            reasons = ["INSUFFICIENT_TIME"]
        else:
            lab = x.get("laboratory")
            reasons = list(lab["missing"]) if lab else ["LAB_PROFILE_NOT_LINKED"]
            outcome = (
                "REVIEW_PENDING"
                if manual or lab and not lab["complete"]
                else "PRESELECTED"
            )
            if profile:
                reasons += [
                    "PROFILE_MISSING:" + code
                    for code in profile["required_tests"]
                    if not lab or code not in lab["satisfied_tests"]
                ]
                reasons += [
                    "PROFILE_HLA_MISSING:" + code
                    for code in profile["required_loci"]
                    if not lab or code not in lab["satisfied_loci"]
                ]
                if (
                    not lab
                    or not lab["complete"]
                    or any(code.startswith("PROFILE_") for code in reasons)
                ):
                    outcome = "EXCLUDED"
        output.append(
            {
                "resource_id": original["resource_id"],
                "resource_version": original["resource_version"],
                "source": "inventario",
                "outcome": outcome,
                "reasons": reasons,
                "inputs": x,
            }
        )
    return output
