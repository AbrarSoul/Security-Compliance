"""Generate NIST AI RMF control catalog JSON for ComplianceGuard."""

from __future__ import annotations

import json
from pathlib import Path


def c(
    cid: str,
    fn: str,
    cat_id: str,
    cat_title: str,
    text: str,
    evidence_type: str,
    coverage: str,
    modules: list[str],
    evaluator: str | None = None,
    tw: list[str] | None = None,
    notes: str = "",
) -> dict:
    return {
        "id": cid,
        "function": fn,
        "category_id": cat_id,
        "category_title": cat_title,
        "text": text,
        "evidence_type": evidence_type,
        "coverage": coverage,
        "modules": modules,
        "evaluator": evaluator,
        "trustworthiness": tw or [],
        "notes": notes,
    }


def build_controls() -> list[dict]:
    G1 = (
        "Policies, processes, procedures, and practices across the organization "
        "related to the mapping, measuring, and managing of AI risks are in place, "
        "transparent, and implemented effectively."
    )
    G2 = (
        "Accountability structures are in place so that the appropriate teams and "
        "individuals are empowered, responsible, and trained for mapping, measuring, "
        "and managing AI risks."
    )
    G3 = (
        "Workforce diversity, equity, inclusion, and accessibility processes are "
        "prioritized in the mapping, measuring, and managing of AI risks throughout "
        "the lifecycle."
    )
    G4 = (
        "Organizational teams are committed to a culture that considers and "
        "communicates AI risk."
    )
    G5 = "Processes are in place for robust engagement with relevant AI actors."
    G6 = (
        "Policies and procedures are in place to address AI risks and benefits "
        "arising from third-party software and data and other supply chain issues."
    )
    M1 = "Context is established and understood."
    M2 = "Categorization of the AI system is performed."
    M3 = (
        "AI capabilities, targeted usage, goals, and expected benefits and costs "
        "compared with appropriate benchmarks are understood."
    )
    M4 = (
        "Risks and benefits are mapped for all components of the AI system "
        "including third-party software and data."
    )
    M5 = (
        "Impacts to individuals, groups, communities, organizations, and society "
        "are characterized."
    )
    MS1 = "Appropriate methods and metrics are identified and applied."
    MS2 = "AI systems are evaluated for trustworthy characteristics."
    MS3 = "Mechanisms for tracking identified AI risks over time are in place."
    MS4 = "Feedback about efficacy of measurement is gathered and assessed."
    MG1 = (
        "AI risks based on assessments and other analytical output from the MAP "
        "and MEASURE functions are prioritized, responded to, and managed."
    )
    MG2 = (
        "Strategies to maximize AI benefits and minimize negative impacts are "
        "planned, prepared, implemented, documented, and informed by input from "
        "relevant AI actors."
    )
    MG3 = "AI risks and benefits from third-party entities are managed."
    MG4 = (
        "Risk treatments, including response and recovery, and communication plans "
        "for the identified and measured AI risks are documented and monitored regularly."
    )

    controls: list[dict] = []

    govern1 = [
        (
            "1.1",
            "Legal and regulatory requirements involving AI are understood, managed, and documented.",
            "hybrid",
            "partial",
            ["gaira"],
            None,
            "GAIRA EU AI Act module supports legal applicability; formal legal register is organizational.",
        ),
        (
            "1.2",
            "The characteristics of trustworthy AI are integrated into organizational policies, processes, procedures, and practices.",
            "hybrid",
            "partial",
            ["policies", "rules"],
            "org_has_enabled_rules",
            "Atomic rules and policy bundles encode privacy/security trustworthiness checks.",
        ),
        (
            "1.3",
            "Processes are in place to determine the needed level of risk management activities based on organizational risk tolerance.",
            "manual",
            "partial",
            ["gaira", "scoring"],
            None,
            "GAIRA risk levels and scoring thresholds; org risk appetite is manual config.",
        ),
        (
            "1.4",
            "The risk management process and its outcomes are established through transparent policies, procedures, and other controls.",
            "automated",
            "partial",
            ["policies", "rules", "audit"],
            "org_has_active_controls",
            "Active policies, enabled rules, and audit trail provide operational controls.",
        ),
        (
            "1.5",
            "Ongoing monitoring and periodic review of the risk management process and its outcomes are planned and roles defined.",
            "automated",
            "partial",
            ["audit", "gaps", "rbac"],
            "org_has_audit_and_gaps",
            "RBAC roles, audit logs, and gap analysis runs support periodic review.",
        ),
        (
            "1.6",
            "Mechanisms are in place to inventory AI systems and are resourced according to organizational risk priorities.",
            "automated",
            "partial",
            ["gaira", "models"],
            "roaia_inventory",
            "ROAIA (AI applications) and model registry provide inventory.",
        ),
        (
            "1.7",
            "Processes are in place for decommissioning and phasing out AI systems safely.",
            "manual",
            "none",
            [],
            None,
            "Not automated; requires org lifecycle process.",
        ),
    ]
    for sub, text, et, cov, mods, ev, notes in govern1:
        controls.append(c(f"GOVERN-{sub}", "GOVERN", "GOVERN1", G1, text, et, cov, mods, ev, notes=notes))

    for sub, text, et, cov, mods, ev, notes in [
        (
            "2.1",
            "Roles and responsibilities related to mapping, measuring, and managing AI risks are documented and clear.",
            "automated",
            "partial",
            ["rbac"],
            "rbac_roles_configured",
            "RBAC permissions map to Admin/User/Auditor responsibilities.",
        ),
        (
            "2.2",
            "Personnel and partners receive AI risk management training consistent with policies and procedures.",
            "manual",
            "none",
            [],
            None,
            "Training is organizational; not tracked in platform.",
        ),
        (
            "2.3",
            "Executive leadership takes responsibility for decisions about AI system development and deployment risks.",
            "hybrid",
            "partial",
            ["gaira"],
            "gaira_leadership_decisions",
            "GAIRA submit records proceed/no-go decisions; executive attestation is manual.",
        ),
    ]:
        controls.append(c(f"GOVERN-{sub}", "GOVERN", "GOVERN2", G2, text, et, cov, mods, ev, notes=notes))

    for sub, text in [
        (
            "3.1",
            "Decision-making is informed by a diverse team (demographics, disciplines, experience, expertise, backgrounds).",
        ),
        (
            "3.2",
            "Policies define roles and responsibilities for human-AI configurations and oversight of AI systems.",
        ),
    ]:
        controls.append(
            c(
                f"GOVERN-{sub}",
                "GOVERN",
                "GOVERN3",
                G3,
                text,
                "manual",
                "none",
                ["guard"],
                notes="DEI and human-AI oversight processes are organizational.",
            )
        )

    for sub, text, et, cov, mods, ev, notes in [
        (
            "4.1",
            "Policies foster a critical thinking and safety-first mindset in AI design, development, deployment, and use.",
            "hybrid",
            "partial",
            ["policies", "guard"],
            None,
            "Block/warn policies and guard enforce safety-first execution.",
        ),
        (
            "4.2",
            "Teams document risks and potential impacts of AI technology and communicate about impacts.",
            "hybrid",
            "partial",
            ["gaira", "reports"],
            "gaira_documentation",
            "GAIRA assessments and scan/report artifacts document impacts.",
        ),
        (
            "4.3",
            "Practices enable AI testing, identification of incidents, and information sharing.",
            "automated",
            "partial",
            ["threats", "guard", "audit"],
            "incident_detection",
            "Threat detection, guard violations, and audit logs support incident identification.",
        ),
    ]:
        controls.append(c(f"GOVERN-{sub}", "GOVERN", "GOVERN4", G4, text, et, cov, mods, ev, notes=notes))

    for sub, text in [
        (
            "5.1",
            "Policies collect, consider, prioritize, and integrate feedback from external parties on AI risks and impacts.",
        ),
        (
            "5.2",
            "Mechanisms incorporate adjudicated feedback from relevant AI actors into system design and implementation.",
        ),
    ]:
        controls.append(
            c(
                f"GOVERN-{sub}",
                "GOVERN",
                "GOVERN5",
                G5,
                text,
                "hybrid",
                "partial",
                ["gaira"],
                notes="GAIRA 2nd-line review for flagged answers; broader engagement is manual.",
            )
        )

    for sub, text, et, cov, mods, ev, notes in [
        (
            "6.1",
            "Policies address AI risks associated with third-party entities including IP infringement.",
            "automated",
            "partial",
            ["models"],
            "no_unapproved_external_models",
            "Model registry approval workflow for external/cloud models.",
        ),
        (
            "6.2",
            "Contingency processes handle failures or incidents in third-party data or high-risk AI systems.",
            "automated",
            "partial",
            ["executions", "guard"],
            "execution_blocking",
            "Pre-execution validation and guard block/warn on risky third-party use.",
        ),
    ]:
        controls.append(c(f"GOVERN-{sub}", "GOVERN", "GOVERN6", G6, text, et, cov, mods, ev, notes=notes))

    map_specs: list[tuple[str, str, str, str, str, list[str], str | None, str]] = [
        ("1.1", "MAP1", M1, "Intended purposes, context-specific laws, norms, deployment settings are documented.", "hybrid", ["gaira"], "gaira_context_documented", ""),
        ("1.2", "MAP1", M1, "Interdisciplinary diverse AI actors for establishing context are documented.", "manual", [], None, "Organizational process not tracked in platform."),
        ("1.3", "MAP1", M1, "Organization mission and relevant AI goals are understood and documented.", "manual", ["gaira"], None, ""),
        ("1.4", "MAP1", M1, "Business value or context of business use is clearly defined or re-evaluated.", "hybrid", ["gaira"], "gaira_context_documented", ""),
        ("1.5", "MAP1", M1, "Organizational risk tolerances are determined and documented.", "hybrid", ["scoring", "gaira"], None, ""),
        ("1.6", "MAP1", M1, "System requirements (e.g., privacy of users) are elicited and understood.", "hybrid", ["rules", "policies"], "org_has_enabled_rules", ""),
        ("2.1", "MAP2", M2, "Tasks and methods the AI system will support are defined.", "automated", ["models", "gaira"], "models_registry_populated", ""),
        ("2.2", "MAP2", M2, "Knowledge limits and human oversight of system output are documented.", "hybrid", ["gaira", "models"], None, ""),
        ("2.3", "MAP2", M2, "Scientific integrity and TEVV considerations are identified and documented.", "manual", ["scans"], None, ""),
        ("3.1", "MAP3", M3, "Potential benefits of intended AI functionality are examined and documented.", "hybrid", ["gaira"], None, ""),
        ("3.2", "MAP3", M3, "Potential costs from AI errors or trustworthiness issues are examined and documented.", "hybrid", ["gaira", "analytics"], None, ""),
        ("3.3", "MAP3", M3, "Targeted application scope is specified based on capability and context.", "hybrid", ["gaira"], "gaira_context_documented", ""),
        ("3.4", "MAP3", M3, "Operator proficiency processes with AI performance and trustworthiness are defined.", "manual", [], None, "Organizational process not tracked in platform."),
        ("3.5", "MAP3", M3, "Human oversight processes are defined per GOVERN policies.", "hybrid", ["guard", "executions"], None, ""),
        ("4.1", "MAP4", M4, "Approaches for mapping third-party component risks are in place and documented.", "automated", ["models"], "no_unapproved_external_models", ""),
        ("4.2", "MAP4", M4, "Internal risk controls for AI components including third-party technologies are documented.", "automated", ["policies", "rules", "models"], "org_has_active_controls", ""),
        ("5.1", "MAP5", M5, "Likelihood and magnitude of identified impacts are documented.", "hybrid", ["gaira"], "gaira_risk_assessed", ""),
        ("5.2", "MAP5", M5, "Practices for engaging AI actors and integrating feedback on impacts are in place.", "manual", ["gaira"], None, ""),
    ]
    for sub, cat_id, cat_title, text, et, mods, ev, notes in map_specs:
        cov = "none" if et == "manual" and not mods else "partial"
        controls.append(c(f"MAP-{sub}", "MAP", cat_id, cat_title, text, et, cov, mods, ev, notes=notes))

    measure2_tw = {
        "2.1": [],
        "2.2": [],
        "2.3": ["valid_and_reliable"],
        "2.4": ["valid_and_reliable", "safe"],
        "2.5": ["valid_and_reliable"],
        "2.6": ["safe"],
        "2.7": ["secure_and_resilient"],
        "2.8": ["accountable_and_transparent"],
        "2.9": ["explainable_and_interpretable"],
        "2.10": ["privacy_enhanced"],
        "2.11": ["fair_with_harmful_bias_managed"],
        "2.12": [],
        "2.13": [],
    }
    measure_specs: list[tuple[str, str, str, str, str, list[str], str | None, list[str], str]] = [
        ("1.1", "MEASURE1", MS1, "Approaches and metrics for MAP risks are selected; unmeasurable risks documented.", "hybrid", ["gaps"], None, [], ""),
        ("1.2", "MEASURE1", MS1, "Appropriateness of AI metrics and control effectiveness are regularly assessed.", "automated", ["gaps", "analytics"], "gap_analysis_recent", [], ""),
        ("1.3", "MEASURE1", MS1, "Independent assessors and domain experts are involved in regular assessments.", "manual", [], None, [], "Independent TEVV not automated in platform."),
        ("2.4", "MEASURE2", MS2, "AI system functionality and behavior are monitored in production.", "automated", ["guard", "monitoring"], "production_monitoring", ["valid_and_reliable", "safe"], ""),
        ("2.7", "MEASURE2", MS2, "AI system security and resilience are evaluated and documented.", "automated", ["scans", "executions", "gaps"], "security_controls_active", ["secure_and_resilient"], ""),
        ("2.8", "MEASURE2", MS2, "Transparency and accountability risks are examined and documented.", "automated", ["audit", "reports"], "org_has_audit_and_gaps", ["accountable_and_transparent"], ""),
        ("2.10", "MEASURE2", MS2, "Privacy risk of the AI system is examined and documented.", "automated", ["scans", "guard"], "privacy_scanning_active", ["privacy_enhanced"], ""),
        ("3.1", "MEASURE3", MS3, "Approaches track existing, unanticipated, and emergent AI risks over time.", "automated", ["analytics", "threats", "gaps"], "risk_tracking_active", [], ""),
        ("3.3", "MEASURE3", MS3, "Feedback processes for end users to report problems are established.", "manual", [], None, [], "User appeal workflows not yet in platform."),
        ("4.1", "MEASURE4", MS4, "Measurement approaches are connected to deployment contexts and documented.", "hybrid", ["executions", "models"], None, [], ""),
    ]
    for sub, cat_id, cat_title, text, et, mods, ev, tw, notes in measure_specs:
        controls.append(c(f"MEASURE-{sub}", "MEASURE", cat_id, cat_title, text, et, "partial", mods, ev, tw=tw, notes=notes))

    for sub, text, tw, cov, ev, notes in [
        ("2.1", "Test sets, metrics, and TEVV tools are documented.", [], "partial", None, ""),
        ("2.2", "Evaluations involving human subjects meet applicable requirements.", [], "none", None, "Human subjects research not in scope."),
        ("2.3", "Performance or assurance criteria are measured for deployment-like conditions.", ["valid_and_reliable"], "partial", None, ""),
        ("2.5", "AI system is demonstrated valid and reliable; generalization limits documented.", ["valid_and_reliable"], "partial", None, ""),
        ("2.6", "AI system is evaluated for safety risks with fail-safe behavior.", ["safe"], "partial", "execution_blocking", ""),
        ("2.9", "AI model is explained, validated, and output interpreted in context.", ["explainable_and_interpretable"], "none", None, "Explainability not implemented."),
        ("2.11", "Fairness and bias are evaluated and documented.", ["fair_with_harmful_bias_managed"], "none", None, "Bias evaluation not implemented."),
        ("2.12", "Environmental impact of AI training and management is assessed.", [], "none", None, "Sustainability not tracked."),
        ("2.13", "Effectiveness of TEVV metrics and processes is evaluated.", [], "partial", "gap_analysis_recent", ""),
        ("3.2", "Risk tracking for hard-to-measure settings is considered.", [], "partial", None, ""),
        ("4.2", "Measurement results are validated with domain expert input.", [], "partial", None, ""),
        ("4.3", "Performance improvements or declines from field data are documented.", [], "partial", None, ""),
    ]:
        controls.append(
            c(
                f"MEASURE-{sub}",
                "MEASURE",
                f"MEASURE{sub.split('.')[0]}",
                MS2 if sub.startswith("2.") else (MS3 if sub.startswith("3.") else MS4),
                text,
                "manual" if cov == "none" and not ev else "hybrid",
                cov,
                ["scans"] if sub.startswith("2.") else ["analytics"],
                ev,
                tw=tw,
                notes=notes,
            )
        )

    manage_specs = [
        ("1.1", "MANAGE1", MG1, "Determination whether AI system should proceed based on intended purposes.", "hybrid", ["gaira"], "gaira_leadership_decisions", ""),
        ("1.2", "MANAGE1", MG1, "Treatment of documented AI risks is prioritized by impact and likelihood.", "automated", ["gaps"], "gap_analysis_recent", ""),
        ("1.3", "MANAGE1", MG1, "Responses to high-priority MAP risks are developed, planned, and documented.", "hybrid", ["gaps", "gaira"], None, ""),
        ("1.4", "MANAGE1", MG1, "Negative residual risks to acquirers and end users are documented.", "hybrid", ["gaira", "reports"], None, ""),
        ("2.1", "MANAGE2", MG2, "Resources to manage AI risks and non-AI alternatives are considered.", "manual", [], None, "Resource planning is organizational."),
        ("2.2", "MANAGE2", MG2, "Mechanisms sustain value of deployed AI systems.", "hybrid", ["models", "monitoring"], "production_monitoring", ""),
        ("2.3", "MANAGE2", MG2, "Procedures respond to and recover from previously unknown risks.", "automated", ["threats", "gaps"], "incident_detection", ""),
        ("2.4", "MANAGE2", MG2, "Mechanisms supersede or deactivate AI systems with inconsistent outcomes.", "automated", ["executions", "guard"], "execution_blocking", ""),
        ("3.1", "MANAGE3", MG3, "Third-party AI risks and benefits are monitored with controls applied.", "automated", ["models"], "no_unapproved_external_models", ""),
        ("3.2", "MANAGE3", MG3, "Pre-trained models are monitored as part of regular maintenance.", "automated", ["models", "monitoring"], "production_monitoring", ""),
        ("4.1", "MANAGE4", MG4, "Post-deployment monitoring plans include incident response and decommissioning.", "automated", ["monitoring", "audit"], "production_monitoring", ""),
        ("4.2", "MANAGE4", MG4, "Continual improvement activities are integrated into AI system updates.", "hybrid", ["gaps"], "gap_analysis_recent", ""),
        ("4.3", "MANAGE4", MG4, "Incidents and errors are communicated; tracking and recovery are documented.", "automated", ["threats", "audit", "notifications"], "incident_detection", ""),
    ]
    for sub, cat_id, cat_title, text, et, mods, ev, notes in manage_specs:
        cov = "none" if et == "manual" and not mods else "partial"
        controls.append(c(f"MANAGE-{sub}", "MANAGE", cat_id, cat_title, text, et, cov, mods, ev, notes=notes))

    return controls


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    controls = build_controls()
    payload = {
        "version": "1.0",
        "source": "NIST AI RMF 1.0",
        "source_document": "Frameworks/NIST_AI_RMF.md",
        "source_url": "https://doi.org/10.6028/NIST.AI.100-1",
        "playbook_url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "profile": {
            "id": "complianceguard-operational-v1",
            "name": "ComplianceGuard Operational AI RMF Profile",
            "description": (
                "Cross-sectoral profile for LLM and data-pipeline AI use: GAIRA governance, "
                "model registry, dataset scanning, execution validation, and runtime guard."
            ),
            "type": "cross-sectoral",
        },
        "trustworthiness_characteristics": [
            "valid_and_reliable",
            "safe",
            "secure_and_resilient",
            "accountable_and_transparent",
            "explainable_and_interpretable",
            "privacy_enhanced",
            "fair_with_harmful_bias_managed",
        ],
        "control_count": len(controls),
        "controls": controls,
    }

    backend_path = root / "backend" / "app" / "data" / "nist_ai_rmf" / "controls_v1.json"
    frameworks_path = root / "Frameworks" / "nist_ai_rmf_controls.json"
    backend_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    backend_path.write_text(text, encoding="utf-8")
    frameworks_path.write_text(text, encoding="utf-8")
    print(f"Wrote {len(controls)} controls to {backend_path}")
    print(f"Wrote {len(controls)} controls to {frameworks_path}")


if __name__ == "__main__":
    main()
