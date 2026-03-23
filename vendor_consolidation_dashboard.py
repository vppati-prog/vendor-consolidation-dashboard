import re
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vendor Consolidation Dashboard", layout="wide")

# =========================================================
# 1. BASE DATA - 10 VENDORS
# =========================================================

BASE_VENDOR_METADATA = pd.DataFrame([
    {"vendor": "V1",  "replaceability": 5, "execution_difficulty": 2, "value_potential": 5, "operational_readiness": 4, "governance_fit": 4, "vendor_health": 4, "annual_spend_m": 10.0, "business_criticality": 2},
    {"vendor": "V2",  "replaceability": 4, "execution_difficulty": 3, "value_potential": 4, "operational_readiness": 3, "governance_fit": 4, "vendor_health": 3, "annual_spend_m": 8.0,  "business_criticality": 3},
    {"vendor": "V3",  "replaceability": 3, "execution_difficulty": 3, "value_potential": 3, "operational_readiness": 3, "governance_fit": 5, "vendor_health": 4, "annual_spend_m": 6.5, "business_criticality": 4},
    {"vendor": "V4",  "replaceability": 2, "execution_difficulty": 4, "value_potential": 3, "operational_readiness": 2, "governance_fit": 4, "vendor_health": 3, "annual_spend_m": 5.5, "business_criticality": 4},
    {"vendor": "V5",  "replaceability": 1, "execution_difficulty": 5, "value_potential": 2, "operational_readiness": 1, "governance_fit": 2, "vendor_health": 3, "annual_spend_m": 4.0, "business_criticality": 5},
    {"vendor": "V6",  "replaceability": 3, "execution_difficulty": 4, "value_potential": 4, "operational_readiness": 3, "governance_fit": 4, "vendor_health": 4, "annual_spend_m": 7.0, "business_criticality": 3},
    {"vendor": "V7",  "replaceability": 2, "execution_difficulty": 4, "value_potential": 2, "operational_readiness": 2, "governance_fit": 4, "vendor_health": 3, "annual_spend_m": 3.5, "business_criticality": 4},
    {"vendor": "V8",  "replaceability": 5, "execution_difficulty": 2, "value_potential": 4, "operational_readiness": 5, "governance_fit": 4, "vendor_health": 4, "annual_spend_m": 9.0, "business_criticality": 2},
    {"vendor": "V9",  "replaceability": 1, "execution_difficulty": 5, "value_potential": 1, "operational_readiness": 1, "governance_fit": 2, "vendor_health": 2, "annual_spend_m": 2.5, "business_criticality": 5},
    {"vendor": "V10", "replaceability": 3, "execution_difficulty": 3, "value_potential": 3, "operational_readiness": 3, "governance_fit": 3, "vendor_health": 3, "annual_spend_m": 5.0, "business_criticality": 3},
])

BASE_CONTRACT_TARGETS = {
    "V1":  {"contract_flexibility": 4, "lock_in": 1},
    "V2":  {"contract_flexibility": 5, "lock_in": 2},
    "V3":  {"contract_flexibility": 5, "lock_in": 3},
    "V4":  {"contract_flexibility": 4, "lock_in": 4},
    "V5":  {"contract_flexibility": 2, "lock_in": 5},
    "V6":  {"contract_flexibility": 4, "lock_in": 3},
    "V7":  {"contract_flexibility": 3, "lock_in": 4},
    "V8":  {"contract_flexibility": 3, "lock_in": 1},
    "V9":  {"contract_flexibility": 2, "lock_in": 5},
    "V10": {"contract_flexibility": 3, "lock_in": 3},
}

# =========================================================
# 2. CONTRACT GENERATOR + PARSER
# =========================================================

def generate_contract_text(vendor_name: str, flex_score: int, lock_in_score: int) -> str:
    flex_clauses = {
        5: (
            "The client may terminate for convenience with 30 days' notice. "
            "Assignment and novation are permitted with prior written consent, not to be unreasonably withheld. "
            "The vendor will provide 90 days of transition assistance."
        ),
        4: (
            "The client may terminate for convenience with 60 days' notice. "
            "Assignment or novation may occur with mutual written consent. "
            "The vendor will provide 60 days of transition assistance."
        ),
        3: (
            "The client may terminate for convenience with 90 days' notice. "
            "Assignment requires written consent. "
            "The vendor will provide 30 days of transition assistance."
        ),
        2: (
            "The agreement may be terminated with 180 days' notice. "
            "Assignment is prohibited except with prior written approval. "
            "Transition assistance is limited to 15 business days. "
            "The agreement auto-renews annually."
        ),
        1: (
            "There is no termination for convenience. "
            "Assignment and novation are prohibited. "
            "No transition assistance is required. "
            "Early termination charges apply and the agreement auto-renews."
        ),
    }

    lock_clauses = {
        1: (
            "The client owns all deliverables. "
            "The client receives a perpetual right to use any supporting materials. "
            "No proprietary vendor tooling is required for ongoing service."
        ),
        2: (
            "The vendor grants the client a broad and perpetual license to service artefacts. "
            "Vendor tooling is replaceable with limited effort."
        ),
        3: (
            "The vendor uses vendor-owned accelerators and methods, but the client receives sufficient usage rights. "
            "Some vendor dependencies remain."
        ),
        4: (
            "The vendor retains core intellectual property and proprietary methods. "
            "The client receives limited rights of use. "
            "Several critical service components depend on vendor tooling."
        ),
        5: (
            "The vendor retains exclusive ownership of all intellectual property. "
            "The service relies on proprietary vendor tools and methods that are essential to delivery. "
            "No source access or tooling substitution rights are granted."
        ),
    }

    service_clause = (
        f"This contract governs managed services for vendor {vendor_name}. "
        "Service levels apply monthly and governance reviews are conducted quarterly. "
    )

    return service_clause + flex_clauses[flex_score] + " " + lock_clauses[lock_in_score]

def derive_contract_flexibility(contract_text: str) -> int:
    text = contract_text.lower()
    if "no termination for convenience" in text:
        return 1
    if "180 days" in text:
        return 2
    if "90 days' notice" in text:
        return 3
    if "60 days' notice" in text:
        return 4
    if "30 days' notice" in text:
        return 5
    return 3

def derive_lock_in(contract_text: str) -> int:
    text = contract_text.lower()
    if "exclusive ownership" in text and "proprietary vendor tools" in text:
        return 5
    if "retains core intellectual property" in text:
        return 4
    if "vendor-owned accelerators" in text:
        return 3
    if "broad and perpetual license" in text:
        return 2
    if "client owns all deliverables" in text:
        return 1
    return 3

def extract_contract_signals(contract_text: str) -> dict:
    text = contract_text.lower()
    return {
        "termination_signal": (
            "30 days notice" if "30 days' notice" in text else
            "60 days notice" if "60 days' notice" in text else
            "90 days notice" if "90 days' notice" in text else
            "180 days notice" if "180 days" in text else
            "no convenience termination" if "no termination for convenience" in text else
            "not found"
        ),
        "novation_signal": (
            "novation permitted" if "novation are permitted" in text or "novation may occur" in text else
            "novation prohibited" if "assignment and novation are prohibited" in text else
            "consent required / restricted"
        ),
        "transition_support_signal": (
            "90-day TSA" if "90 days of transition assistance" in text else
            "60-day TSA" if "60 days of transition assistance" in text else
            "30-day TSA" if "30 days of transition assistance" in text else
            "limited TSA" if "15 business days" in text else
            "no TSA"
        ),
        "ip_signal": (
            "client owned / low lock-in" if "client owns all deliverables" in text else
            "broad client license" if "broad and perpetual license" in text else
            "shared / medium lock-in" if "vendor-owned accelerators" in text else
            "high lock-in" if "retains core intellectual property" in text else
            "very high lock-in" if "exclusive ownership" in text else
            "not found"
        ),
    }

# =========================================================
# 3. SCORING / MODEL LOGIC
# =========================================================

TREATMENT_DIMENSIONS = [
    "replaceability",
    "contract_flexibility",
    "execution_difficulty",
    "lock_in",
    "value_potential",
]

READINESS_WEIGHTS = {
    "operational_readiness": 35,
    "governance_fit": 25,
    "vendor_health": 20,
    "execution_readiness": 20,
}

PREFERRED_BANDS = {
    "Transition": {
        "replaceability": (4, 5),
        "contract_flexibility": (4, 5),
        "execution_difficulty": (1, 2),
        "lock_in": (1, 2),
        "value_potential": (3, 5),
    },
    "Novate": {
        "replaceability": (2, 3),
        "contract_flexibility": (4, 5),
        "execution_difficulty": (3, 5),
        "lock_in": (3, 4),
        "value_potential": (2, 4),
    },
    "Managed": {
        "replaceability": (1, 2),
        "contract_flexibility": (2, 3),
        "execution_difficulty": (4, 5),
        "lock_in": (4, 5),
        "value_potential": (1, 3),
    },
    "Retain": {
        "replaceability": (1, 2),
        "contract_flexibility": (1, 2),
        "execution_difficulty": (4, 5),
        "lock_in": (4, 5),
        "value_potential": (1, 2),
    },
}

SCENARIOS = {
    "Balanced": {"replaceability": 30, "contract_flexibility": 20, "execution_difficulty": 20, "lock_in": 10, "value_potential": 20},
    "Cost Optimized": {"replaceability": 30, "contract_flexibility": 15, "execution_difficulty": 15, "lock_in": 10, "value_potential": 30},
    "Risk Averse": {"replaceability": 20, "contract_flexibility": 25, "execution_difficulty": 30, "lock_in": 15, "value_potential": 10},
    "Aggressive Consolidation": {"replaceability": 35, "contract_flexibility": 20, "execution_difficulty": 15, "lock_in": 5, "value_potential": 25},
}

def fit_score(actual_score: int, preferred_band: tuple) -> int:
    low, high = preferred_band
    if low <= actual_score <= high:
        return 5
    if actual_score == low - 1 or actual_score == high + 1:
        return 3
    return 1

def normalize_weights(weight_dict: dict) -> dict:
    total = sum(weight_dict.values())
    if total == 0:
        n = len(weight_dict)
        return {k: 100 / n for k in weight_dict}
    return {k: (v / total) * 100 for k, v in weight_dict.items()}

def build_actual_scores(metadata_df: pd.DataFrame, contracts_dict: dict) -> pd.DataFrame:
    records = []
    for _, row in metadata_df.iterrows():
        vendor = row["vendor"]
        contract_text = contracts_dict[vendor]
        records.append({
            "vendor": vendor,
            "replaceability": int(row["replaceability"]),
            "contract_flexibility": int(derive_contract_flexibility(contract_text)),
            "execution_difficulty": int(row["execution_difficulty"]),
            "lock_in": int(derive_lock_in(contract_text)),
            "value_potential": int(row["value_potential"]),
            "operational_readiness": int(row["operational_readiness"]),
            "governance_fit": int(row["governance_fit"]),
            "vendor_health": int(row["vendor_health"]),
            "annual_spend_m": float(row["annual_spend_m"]),
            "business_criticality": int(row["business_criticality"]),
            "execution_readiness": int(6 - row["execution_difficulty"]),
        })
    return pd.DataFrame(records)

def build_fit_table(actual_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in actual_df.iterrows():
        vendor = row["vendor"]
        for option, band_map in PREFERRED_BANDS.items():
            for dim in TREATMENT_DIMENSIONS:
                actual = int(row[dim])
                pref_low, pref_high = band_map[dim]
                fit = fit_score(actual, (pref_low, pref_high))
                rows.append({
                    "vendor": vendor,
                    "option": option,
                    "dimension": dim,
                    "actual_score": actual,
                    "preferred_range": f"{pref_low}-{pref_high}",
                    "fit_score": fit,
                })
    return pd.DataFrame(rows)

def build_weighted_scores(fit_df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    rows = []
    for _, row in fit_df.iterrows():
        dim = row["dimension"]
        weight = weights[dim]
        weighted_points = weight * row["fit_score"] / 5.0
        rows.append({
            **row,
            "weight": round(weight, 2),
            "weighted_points": round(weighted_points, 2),
        })
    return pd.DataFrame(rows)

def build_treatment_summary(weighted_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        weighted_df.groupby(["vendor", "option"], as_index=False)["weighted_points"]
        .sum()
        .rename(columns={"weighted_points": "option_score"})
    )

    pivot = summary.pivot(index="vendor", columns="option", values="option_score").reset_index().fillna(0)
    option_cols = ["Transition", "Novate", "Managed", "Retain"]
    pivot["recommended_treatment"] = pivot[option_cols].idxmax(axis=1)
    pivot["top_score"] = pivot[option_cols].max(axis=1)

    def score_gap(row):
        vals = sorted([row[c] for c in option_cols], reverse=True)
        return round(vals[0] - vals[1], 2)

    pivot["score_gap_vs_next_best"] = pivot.apply(score_gap, axis=1)
    return pivot

def build_readiness_summary(actual_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in actual_df.iterrows():
        operational_contribution = READINESS_WEIGHTS["operational_readiness"] * row["operational_readiness"] / 5.0
        governance_contribution = READINESS_WEIGHTS["governance_fit"] * row["governance_fit"] / 5.0
        health_contribution = READINESS_WEIGHTS["vendor_health"] * row["vendor_health"] / 5.0
        execution_contribution = READINESS_WEIGHTS["execution_readiness"] * row["execution_readiness"] / 5.0

        readiness_score = operational_contribution + governance_contribution + health_contribution + execution_contribution

        if readiness_score >= 75:
            tranche = "Tranche 1"
        elif readiness_score >= 50:
            tranche = "Tranche 2"
        else:
            tranche = "Tranche 3"

        rows.append({
            "vendor": row["vendor"],
            "operational_contribution": round(operational_contribution, 2),
            "governance_contribution": round(governance_contribution, 2),
            "health_contribution": round(health_contribution, 2),
            "execution_contribution": round(execution_contribution, 2),
            "readiness_score": round(readiness_score, 2),
            "tranche": tranche,
        })
    return pd.DataFrame(rows)

def build_readiness_breakdown(actual_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in actual_df.iterrows():
        vendor = row["vendor"]
        breakdown_map = {
            "Operational Readiness": {"actual_score": row["operational_readiness"], "weight": READINESS_WEIGHTS["operational_readiness"], "logic": "Uses the operational readiness score directly."},
            "Governance Fit": {"actual_score": row["governance_fit"], "weight": READINESS_WEIGHTS["governance_fit"], "logic": "Uses the governance fit score directly."},
            "Vendor Health": {"actual_score": row["vendor_health"], "weight": READINESS_WEIGHTS["vendor_health"], "logic": "Uses the vendor health score directly."},
            "Execution Readiness": {"actual_score": row["execution_readiness"], "weight": READINESS_WEIGHTS["execution_readiness"], "logic": "Calculated as 6 - execution difficulty."},
        }
        for dim_name, info in breakdown_map.items():
            weighted_points = info["weight"] * info["actual_score"] / 5.0
            rows.append({
                "vendor": vendor,
                "dimension": dim_name,
                "actual_score": int(info["actual_score"]),
                "weight": info["weight"],
                "weighted_points": round(weighted_points, 2),
                "logic": info["logic"],
            })
    return pd.DataFrame(rows)

# =========================================================
# 4. VALUE SIMULATION
# =========================================================

def clamp(value, low, high):
    return max(low, min(high, value))

def calculate_value_for_vendor(row, treatment):
    spend = float(row["annual_spend_m"])
    replaceability = int(row["replaceability"])
    contract_flexibility = int(row["contract_flexibility"])
    execution_difficulty = int(row["execution_difficulty"])
    lock_in = int(row["lock_in"])
    value_potential = int(row["value_potential"])
    governance_fit = int(row["governance_fit"])
    criticality = int(row["business_criticality"])

    if treatment == "Transition":
        base = 8.0
        replaceability_uplift = 2.0 * (replaceability - 3)
        value_uplift = 2.0 * (value_potential - 3)
        difficulty_penalty = 1.5 * (execution_difficulty - 3)
        lockin_penalty = 1.5 * (lock_in - 3)

        gross_pct = clamp(base + replaceability_uplift + value_uplift - difficulty_penalty - lockin_penalty, 3.0, 20.0)
        cost_pct = clamp(3.0 + 1.5 * execution_difficulty, 4.0, 12.0)

        value_type = "Hard Savings"
        gross_value = spend * gross_pct / 100.0
        one_time_cost = spend * cost_pct / 100.0
        net_value = gross_value - one_time_cost

        logic_rows = [
            ["Base Transition Savings %", base, "Baseline hard savings assumption for a replaceable vendor."],
            ["Replaceability Uplift %", replaceability_uplift, "Higher replaceability increases savings potential."],
            ["Value Potential Uplift %", value_uplift, "Higher value potential increases expected upside."],
            ["Execution Difficulty Penalty %", -difficulty_penalty, "Higher execution difficulty reduces realizable savings."],
            ["Lock-in Penalty %", -lockin_penalty, "Higher lock-in reduces savings potential."],
            ["Final Gross Savings %", gross_pct, "Estimated annual gross savings percentage."],
            ["One-Time Transition Cost %", cost_pct, "Estimated one-time cost to transition and stabilize service."],
        ]

    elif treatment == "Novate":
        base = 4.0
        contract_uplift = 1.5 * (contract_flexibility - 3)
        governance_uplift = 1.0 * (governance_fit - 3)
        lockin_penalty = 1.0 * (lock_in - 3)

        gross_pct = clamp(base + contract_uplift + governance_uplift - lockin_penalty, 2.0, 10.0)
        cost_pct = clamp(1.0 + 0.5 * execution_difficulty, 1.5, 4.0)

        value_type = "Commercial / Governance Savings"
        gross_value = spend * gross_pct / 100.0
        one_time_cost = spend * cost_pct / 100.0
        net_value = gross_value - one_time_cost

        logic_rows = [
            ["Base Novation Savings %", base, "Baseline commercial/governance gain assumption."],
            ["Contract Flexibility Uplift %", contract_uplift, "More flexible contracts improve novation value."],
            ["Governance Fit Uplift %", governance_uplift, "Better governance fit increases benefits under novation."],
            ["Lock-in Penalty %", -lockin_penalty, "Higher lock-in limits negotiable savings."],
            ["Final Gross Savings %", gross_pct, "Estimated annual gross savings percentage."],
            ["One-Time Novation Cost %", cost_pct, "Estimated one-time cost to novate and set up governance."],
        ]

    elif treatment == "Managed":
        base = 2.0
        governance_uplift = 1.0 * (governance_fit - 3)
        value_uplift = 0.5 * (value_potential - 3)

        gross_pct = clamp(base + governance_uplift + value_uplift, 1.0, 6.0)
        cost_pct = clamp(0.5 + 0.3 * execution_difficulty, 0.8, 2.5)

        value_type = "Governance / Coordination Savings"
        gross_value = spend * gross_pct / 100.0
        one_time_cost = spend * cost_pct / 100.0
        net_value = gross_value - one_time_cost

        logic_rows = [
            ["Base Managed Savings %", base, "Baseline savings from better coordination and oversight."],
            ["Governance Fit Uplift %", governance_uplift, "Higher governance fit improves managed value."],
            ["Value Potential Uplift %", value_uplift, "Some additional value can still be captured."],
            ["Final Gross Savings %", gross_pct, "Estimated annual gross savings percentage."],
            ["One-Time Managed Model Cost %", cost_pct, "Estimated setup cost for managed governance model."],
        ]

    else:
        base = 1.0
        criticality_uplift = 1.0 if criticality >= 4 else 0.0
        difficulty_uplift = 1.0 if execution_difficulty >= 4 else 0.0
        lockin_uplift = 1.0 if lock_in >= 4 else 0.0

        gross_pct = clamp(base + criticality_uplift + difficulty_uplift + lockin_uplift, 1.0, 5.0)
        cost_pct = 0.0

        value_type = "Avoided Loss / Risk Avoidance"
        gross_value = spend * gross_pct / 100.0
        one_time_cost = 0.0
        net_value = gross_value

        logic_rows = [
            ["Base Avoided Loss %", base, "Baseline avoided loss for not changing a structurally hard vendor."],
            ["Criticality Uplift %", criticality_uplift, "Higher criticality increases avoided loss value."],
            ["Execution Difficulty Uplift %", difficulty_uplift, "Very difficult vendors create higher avoided loss if retained."],
            ["Lock-in Uplift %", lockin_uplift, "Higher lock-in raises disruption risk avoided through retention."],
            ["Final Avoided Loss %", gross_pct, "Estimated avoided loss percentage."],
            ["One-Time Cost %", cost_pct, "No one-time transformation cost assumed for retain."],
        ]

    payback_months = None
    if one_time_cost > 0 and gross_value > 0:
        payback_months = round((one_time_cost / gross_value) * 12, 1)

    summary = {
        "value_type": value_type,
        "gross_value_m": round(gross_value, 2),
        "one_time_cost_m": round(one_time_cost, 2),
        "net_value_m": round(net_value, 2),
        "gross_pct": round(gross_pct, 2),
        "cost_pct": round(cost_pct, 2),
        "payback_months": payback_months,
    }

    logic_df = pd.DataFrame(logic_rows, columns=["logic_component", "value_pct", "inference"])
    return summary, logic_df

def build_value_summary(actual_df, final_df):
    rows = []
    logic_map = {}

    merged = actual_df.merge(
        final_df[["vendor", "recommended_treatment", "tranche"]],
        on="vendor",
        how="left"
    )

    for _, row in merged.iterrows():
        vendor = row["vendor"]
        treatment = row["recommended_treatment"]
        summary, logic_df = calculate_value_for_vendor(row, treatment)

        logic_map[vendor] = logic_df
        rows.append({
            "vendor": vendor,
            "recommended_treatment": treatment,
            "tranche": row["tranche"],
            "annual_spend_m": row["annual_spend_m"],
            "value_type": summary["value_type"],
            "gross_value_m": summary["gross_value_m"],
            "one_time_cost_m": summary["one_time_cost_m"],
            "net_value_m": summary["net_value_m"],
            "gross_pct": summary["gross_pct"],
            "cost_pct": summary["cost_pct"],
            "payback_months": summary["payback_months"],
        })

    return pd.DataFrame(rows), logic_map

# =========================================================
# 5. SYNTHETIC VENDOR CREATION (OPTION C)
# =========================================================

def next_vendor_number(existing_names):
    nums = []
    for v in existing_names:
        m = re.match(r"V(\d+)", str(v))
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1

def synthetic_vendor_from_prompt(prompt, vendor_name):
    text = prompt.lower()

    def level_from_words(default=3):
        if "very high" in text:
            return 5
        if "high" in text:
            return 4
        if "low" in text:
            return 2
        if "very low" in text:
            return 1
        return default

    replaceability = 3
    if "low replaceability" in text:
        replaceability = 2
    elif "high replaceability" in text:
        replaceability = 4

    lock_in = 3
    if "high lock-in" in text or "high lockin" in text:
        lock_in = 4
    elif "low lock-in" in text or "low lockin" in text:
        lock_in = 2

    execution_difficulty = 3
    if "high difficulty" in text or "complex" in text:
        execution_difficulty = 4
    elif "low difficulty" in text or "simple" in text:
        execution_difficulty = 2

    contract_flexibility = 3
    if "high flexibility" in text or "flexible contract" in text:
        contract_flexibility = 4
    elif "rigid contract" in text or "low flexibility" in text:
        contract_flexibility = 2

    value_potential = 3
    if "high value" in text or "high savings" in text:
        value_potential = 4
    elif "low value" in text:
        value_potential = 2

    governance_fit = 3
    if "strong governance" in text:
        governance_fit = 4

    business_criticality = 3
    if "critical" in text:
        business_criticality = 5
    elif "non critical" in text or "non-critical" in text:
        business_criticality = 2

    operational_readiness = 3
    vendor_health = 3
    annual_spend_m = round(random.choice([3.0, 4.5, 6.0, 7.5, 9.0, 11.0]), 1)

    metadata = {
        "vendor": vendor_name,
        "replaceability": replaceability,
        "execution_difficulty": execution_difficulty,
        "value_potential": value_potential,
        "operational_readiness": operational_readiness,
        "governance_fit": governance_fit,
        "vendor_health": vendor_health,
        "annual_spend_m": annual_spend_m,
        "business_criticality": business_criticality,
    }

    contract = generate_contract_text(vendor_name, contract_flexibility, lock_in)
    targets = {"contract_flexibility": contract_flexibility, "lock_in": lock_in}

    return metadata, contract, targets

# =========================================================
# 6. SESSION STATE INIT
# =========================================================

if "metadata_df" not in st.session_state:
    st.session_state.metadata_df = BASE_VENDOR_METADATA.copy()

if "contracts_dict" not in st.session_state:
    st.session_state.contracts_dict = {
        vendor: generate_contract_text(vendor, scores["contract_flexibility"], scores["lock_in"])
        for vendor, scores in BASE_CONTRACT_TARGETS.items()
    }

if "contract_targets" not in st.session_state:
    st.session_state.contract_targets = BASE_CONTRACT_TARGETS.copy()

if "copilot_message" not in st.session_state:
    st.session_state.copilot_message = ""

# =========================================================
# 7. EXPLANATIONS
# =========================================================

def explain_vendor(vendor, weighted_df, final_df):
    row = final_df[final_df["vendor"] == vendor].iloc[0]
    treatment = row["recommended_treatment"]
    details = weighted_df[(weighted_df["vendor"] == vendor) & (weighted_df["option"] == treatment)].sort_values("weighted_points", ascending=False)
    top3 = details.head(3)[["dimension", "actual_score", "preferred_range", "weighted_points"]]

    reasons = []
    for _, r in top3.iterrows():
        reasons.append(
            f"{r['dimension']} scored {int(r['actual_score'])}, fits the preferred range {r['preferred_range']} for {treatment}, "
            f"and contributed {r['weighted_points']:.1f} points."
        )
    return " ".join(reasons)

def explain_readiness(vendor, readiness_breakdown_df, readiness_summary_df):
    vendor_breakdown = readiness_breakdown_df[readiness_breakdown_df["vendor"] == vendor].sort_values("weighted_points", ascending=False)
    vendor_summary = readiness_summary_df[readiness_summary_df["vendor"] == vendor].iloc[0]
    top2 = vendor_breakdown.head(2)

    reasons = []
    for _, r in top2.iterrows():
        reasons.append(f"{r['dimension']} scored {int(r['actual_score'])} and contributed {r['weighted_points']:.1f} points.")

    return f"Readiness score is {vendor_summary['readiness_score']:.1f}, resulting in {vendor_summary['tranche']}. " + " ".join(reasons)

# =========================================================
# 8. SIDEBAR CONTROLS
# =========================================================

st.sidebar.title("Control Panel")

scenario = st.sidebar.selectbox("Scenario", list(SCENARIOS.keys()), index=0)
base_weights = SCENARIOS[scenario].copy()

st.sidebar.markdown("### Treatment Weights (%)")
w_replaceability = st.sidebar.slider("Replaceability", 0, 100, int(base_weights["replaceability"]), 5)
w_contract = st.sidebar.slider("Contract Flexibility", 0, 100, int(base_weights["contract_flexibility"]), 5)
w_difficulty = st.sidebar.slider("Execution Difficulty", 0, 100, int(base_weights["execution_difficulty"]), 5)
w_lockin = st.sidebar.slider("Lock-in", 0, 100, int(base_weights["lock_in"]), 5)
w_value = st.sidebar.slider("Value Potential", 0, 100, int(base_weights["value_potential"]), 5)

treatment_weights = normalize_weights({
    "replaceability": w_replaceability,
    "contract_flexibility": w_contract,
    "execution_difficulty": w_difficulty,
    "lock_in": w_lockin,
    "value_potential": w_value,
})

st.sidebar.markdown("---")
st.sidebar.markdown("### Live Simulator")

selected_vendor = st.sidebar.selectbox("Pick vendor to simulate", st.session_state.metadata_df["vendor"].tolist(), index=0)

selected_row = st.session_state.metadata_df[st.session_state.metadata_df["vendor"] == selected_vendor].iloc[0]
selected_contract_targets = st.session_state.contract_targets[selected_vendor]

sim_replaceability = st.sidebar.slider("Replaceability (sim)", 1, 5, int(selected_row["replaceability"]))
sim_execution_difficulty = st.sidebar.slider("Execution Difficulty (sim)", 1, 5, int(selected_row["execution_difficulty"]))
sim_value = st.sidebar.slider("Value Potential (sim)", 1, 5, int(selected_row["value_potential"]))
sim_operational = st.sidebar.slider("Operational Readiness (sim)", 1, 5, int(selected_row["operational_readiness"]))
sim_governance = st.sidebar.slider("Governance Fit (sim)", 1, 5, int(selected_row["governance_fit"]))
sim_health = st.sidebar.slider("Vendor Health (sim)", 1, 5, int(selected_row["vendor_health"]))
sim_spend = st.sidebar.slider("Annual Spend in $M (sim)", 1.0, 20.0, float(selected_row["annual_spend_m"]), 0.5)
sim_criticality = st.sidebar.slider("Business Criticality (sim)", 1, 5, int(selected_row["business_criticality"]))
sim_contract_flex = st.sidebar.slider("Contract Flexibility (via contract)", 1, 5, int(selected_contract_targets["contract_flexibility"]))
sim_lock_in = st.sidebar.slider("Lock-in (via contract)", 1, 5, int(selected_contract_targets["lock_in"]))

# =========================================================
# 9. APPLY SIMULATION TO WORKING COPY
# =========================================================

working_metadata = st.session_state.metadata_df.copy()
working_contracts = dict(st.session_state.contracts_dict)

working_metadata.loc[working_metadata["vendor"] == selected_vendor, "replaceability"] = sim_replaceability
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "execution_difficulty"] = sim_execution_difficulty
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "value_potential"] = sim_value
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "operational_readiness"] = sim_operational
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "governance_fit"] = sim_governance
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "vendor_health"] = sim_health
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "annual_spend_m"] = sim_spend
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "business_criticality"] = sim_criticality

working_contracts[selected_vendor] = generate_contract_text(selected_vendor, sim_contract_flex, sim_lock_in)

# =========================================================
# 10. CALCULATE OUTPUTS
# =========================================================

actual_df = build_actual_scores(working_metadata, working_contracts)
fit_df = build_fit_table(actual_df)
weighted_df = build_weighted_scores(fit_df, treatment_weights)
treatment_df = build_treatment_summary(weighted_df)
readiness_summary_df = build_readiness_summary(actual_df)
readiness_breakdown_df = build_readiness_breakdown(actual_df)

final_df = treatment_df.merge(
    readiness_summary_df[["vendor", "readiness_score", "tranche"]],
    on="vendor",
    how="left"
)

value_summary_df, value_logic_map = build_value_summary(actual_df, final_df)

final_df = final_df.merge(
    value_summary_df.drop(columns=["recommended_treatment", "tranche"]),
    on="vendor",
    how="left"
)

final_df["explanation"] = final_df["vendor"].apply(lambda v: explain_vendor(v, weighted_df, final_df))
final_df["readiness_explanation"] = final_df["vendor"].apply(lambda v: explain_readiness(v, readiness_breakdown_df, readiness_summary_df))

# =========================================================
# 11. COPILOT / PROMPT HANDLER
# =========================================================

def find_vendor_in_prompt(prompt, vendors):
    p = prompt.lower()
    for v in vendors:
        if str(v).lower() in p:
            return v
        alt = str(v).replace("V", "Vendor ")
        if alt.lower() in p:
            return v
    m = re.search(r"vendor\s*(\d+)", p)
    if m:
        guess = f"V{m.group(1)}"
        if guess in vendors:
            return guess
    return None

def handle_prompt(prompt, final_df, actual_df):
    p = prompt.strip().lower()
    vendors = final_df["vendor"].tolist()

    # Add vendor
    if "add vendor" in p or "upload vendor" in p:
        m = re.search(r"vendor\s*(\d+)", p)
        if m:
            vendor_name = f"V{m.group(1)}"
        else:
            vendor_name = f"V{next_vendor_number(vendors)}"

        if vendor_name in vendors:
            return f"{vendor_name} already exists in the portfolio."

        metadata, contract, targets = synthetic_vendor_from_prompt(prompt, vendor_name)
        st.session_state.metadata_df = pd.concat(
            [st.session_state.metadata_df, pd.DataFrame([metadata])],
            ignore_index=True
        )
        st.session_state.contracts_dict[vendor_name] = contract
        st.session_state.contract_targets[vendor_name] = targets

        return (
            f"{vendor_name} has been added using synthetic demo data. "
            f"Default assumptions were created for contract and metadata, and the dashboard will now refresh with the new vendor included."
        )

    # Vendor-specific questions
    vendor = find_vendor_in_prompt(prompt, vendors)

    if vendor and ("ideal candidate" in p or "candidate for what" in p or "best suited" in p):
        row = final_df[final_df["vendor"] == vendor].iloc[0]
        return (
            f"{vendor} is best suited for **{row['recommended_treatment']}**. "
            f"Reason: {row['explanation']} "
            f"Readiness score is {row['readiness_score']:.1f} in {row['tranche']}. "
            f"Estimated net value is {row['net_value_m']:.2f}M."
        )

    if vendor and ("why" in p or "explain" in p):
        row = final_df[final_df["vendor"] == vendor].iloc[0]
        return (
            f"For {vendor}, the recommended treatment is **{row['recommended_treatment']}**. "
            f"Why: {row['explanation']} "
            f"Readiness: {row['readiness_explanation']} "
            f"Estimated value: net {row['net_value_m']:.2f}M from gross {row['gross_value_m']:.2f}M and one-time cost {row['one_time_cost_m']:.2f}M."
        )

    if "top 3 vendors by net value" in p or "top vendors by net value" in p:
        top_df = final_df[["vendor", "recommended_treatment", "net_value_m"]].sort_values("net_value_m", ascending=False).head(3)
        lines = []
        for _, r in top_df.iterrows():
            lines.append(f"{r['vendor']} ({r['recommended_treatment']}) - {r['net_value_m']:.2f}M")
        return "Top vendors by net value: " + "; ".join(lines)

    if "tranche 1" in p and "which vendors" in p:
        df = final_df[final_df["tranche"] == "Tranche 1"][["vendor", "recommended_treatment", "net_value_m"]]
        if df.empty:
            return "There are no vendors currently in Tranche 1."
        lines = []
        for _, r in df.iterrows():
            lines.append(f"{r['vendor']} ({r['recommended_treatment']}, net value {r['net_value_m']:.2f}M)")
        return "Current Tranche 1 vendors: " + "; ".join(lines)

    if "total net value" in p or "portfolio net value" in p:
        total_net = final_df["net_value_m"].sum()
        total_gross = final_df["gross_value_m"].sum()
        total_cost = final_df["one_time_cost_m"].sum()
        return (
            f"The current portfolio value estimate is: gross {total_gross:.2f}M, "
            f"one-time cost {total_cost:.2f}M, and net value {total_net:.2f}M."
        )

    if vendor and ("show" in p or "details" in p):
        row = final_df[final_df["vendor"] == vendor].iloc[0]
        return (
            f"{vendor}: treatment {row['recommended_treatment']}, readiness {row['readiness_score']:.1f}, "
            f"{row['tranche']}, gross value {row['gross_value_m']:.2f}M, one-time cost {row['one_time_cost_m']:.2f}M, "
            f"net value {row['net_value_m']:.2f}M."
        )

    return (
        "I can help with questions like: "
        "'Vendor 5 is ideal candidate for what?', "
        "'Why is Vendor 4 managed?', "
        "'Show top 3 vendors by net value', "
        "'Which vendors are in Tranche 1?', "
        "'What is total net value?', "
        "or 'Add Vendor 11'."
    )

# =========================================================
# 12. UI
# =========================================================

st.title("Vendor Consolidation Dashboard")
st.caption("Demo for vendor consolidation: contract parsing + metadata scoring + treatment recommendation + readiness + value simulation + co-pilot")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Vendor Intelligence Hub",
    "2. Fit Logic",
    "3. Weighted Scores",
    "4. Readiness Logic",
    "5. Value Simulation",
    "6. Decision Cockpit",
    "7. Simulator View",
])

with tab1:
    st.subheader("Vendor Intelligence Hub")

    st.markdown("### Ask the Vendor Co-Pilot")
    sample_prompts = (
        "Try: 'Vendor 5 is ideal candidate for what?' | "
        "'Why is Vendor 4 managed?' | "
        "'Show top 3 vendors by net value' | "
        "'What is total net value?' | "
        "'Add Vendor 11' | "
        "'Add Vendor 12 with high lock-in and low replaceability'"
    )
    st.caption(sample_prompts)

    with st.form("copilot_form"):
        prompt_text = st.text_input("Ask anything related to the dashboard")
        submitted = st.form_submit_button("Run Prompt")

    if submitted and prompt_text.strip():
        msg = handle_prompt(prompt_text, final_df, actual_df)
        st.session_state.copilot_message = msg
        st.rerun()

    if st.session_state.copilot_message:
        st.success(st.session_state.copilot_message)

    st.markdown("---")

    vendor_pick = st.selectbox("Select vendor", actual_df["vendor"].tolist(), key="vih_vendor")
    contract_text = working_contracts[vendor_pick]
    contract_signals = extract_contract_signals(contract_text)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Parsed Contract Signals")
        signal_df = pd.DataFrame([{"signal": k, "value": v} for k, v in contract_signals.items()])
        st.dataframe(signal_df, use_container_width=True, hide_index=True)

        st.markdown("#### Actual Scores Used by the Model")
        vendor_actual = actual_df[actual_df["vendor"] == vendor_pick].T.reset_index()
        vendor_actual.columns = ["dimension", "score"]
        st.dataframe(vendor_actual, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Mock Contract Text")
        st.text_area("Contract", value=contract_text, height=380, key="contract_text_view")

with tab2:
    st.subheader("Step 2: Actual Score vs Preferred Range -> Fit Score")
    vendor_pick_fit = st.selectbox("Select vendor for fit view", actual_df["vendor"].tolist(), key="fit_vendor")
    vendor_fit = fit_df[fit_df["vendor"] == vendor_pick_fit].copy()
    st.dataframe(vendor_fit, use_container_width=True, hide_index=True)
    st.info("For each dimension, the model checks how well the vendor's actual score matches what each option prefers. Match = Fit 5, close = Fit 3, far = Fit 1.")

with tab3:
    st.subheader("Step 3: Fit Score x Weight -> Weighted Points")
    vendor_pick_weight = st.selectbox("Select vendor for weighted view", actual_df["vendor"].tolist(), key="weight_vendor")
    vendor_weight = weighted_df[weighted_df["vendor"] == vendor_pick_weight].copy()
    st.dataframe(vendor_weight, use_container_width=True, hide_index=True)

    option_summary = (
        vendor_weight.groupby("option", as_index=False)["weighted_points"]
        .sum()
        .sort_values("weighted_points", ascending=False)
    )
    st.markdown("#### Treatment Score Summary")
    st.dataframe(option_summary, use_container_width=True, hide_index=True)
    st.bar_chart(option_summary.set_index("option"))
    st.info("Weighted points = weight x fit / 5. The fit tells us suitability; the weight tells us importance.")

with tab4:
    st.subheader("Step 4: Readiness Logic")
    vendor_pick_readiness = st.selectbox("Select vendor for readiness view", actual_df["vendor"].tolist(), key="readiness_vendor")
    vendor_actual = actual_df[actual_df["vendor"] == vendor_pick_readiness].iloc[0]
    vendor_breakdown = readiness_breakdown_df[readiness_breakdown_df["vendor"] == vendor_pick_readiness].copy()
    vendor_summary = readiness_summary_df[readiness_summary_df["vendor"] == vendor_pick_readiness].iloc[0]

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.markdown("#### Readiness Inputs")
        readiness_inputs = pd.DataFrame([
            {"dimension": "Operational Readiness", "score": int(vendor_actual["operational_readiness"])},
            {"dimension": "Governance Fit", "score": int(vendor_actual["governance_fit"])},
            {"dimension": "Vendor Health", "score": int(vendor_actual["vendor_health"])},
            {"dimension": "Execution Difficulty", "score": int(vendor_actual["execution_difficulty"])},
            {"dimension": "Execution Readiness = 6 - Difficulty", "score": int(vendor_actual["execution_readiness"])},
        ])
        st.dataframe(readiness_inputs, use_container_width=True, hide_index=True)

        st.markdown("#### Readiness Breakdown")
        st.dataframe(vendor_breakdown, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Readiness Summary")
        summary_df = pd.DataFrame([
            {"metric": "Operational Contribution", "value": vendor_summary["operational_contribution"]},
            {"metric": "Governance Contribution", "value": vendor_summary["governance_contribution"]},
            {"metric": "Health Contribution", "value": vendor_summary["health_contribution"]},
            {"metric": "Execution Contribution", "value": vendor_summary["execution_contribution"]},
            {"metric": "Readiness Score", "value": vendor_summary["readiness_score"]},
            {"metric": "Tranche", "value": vendor_summary["tranche"]},
        ])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown("#### Contribution Chart")
        st.bar_chart(vendor_breakdown[["dimension", "weighted_points"]].set_index("dimension"))

    st.info("Readiness is computed separately from treatment. Each readiness dimension contributes points out of 100. Execution Readiness is calculated as 6 - Execution Difficulty.")

with tab5:
    st.subheader("Step 5: Value Simulation")
    vendor_pick_value = st.selectbox("Select vendor for value view", actual_df["vendor"].tolist(), key="value_vendor")

    vendor_actual = actual_df[actual_df["vendor"] == vendor_pick_value].iloc[0]
    vendor_final = final_df[final_df["vendor"] == vendor_pick_value].iloc[0]
    vendor_logic = value_logic_map[vendor_pick_value].copy()

    col1, col2 = st.columns([1.15, 1])

    with col1:
        st.markdown("#### Vendor-Level Inputs and Assumptions")
        value_inputs = pd.DataFrame([
            {"dimension": "Recommended Treatment", "value": vendor_final["recommended_treatment"], "inference": "This treatment determines which value logic is applied."},
            {"dimension": "Annual Spend ($M)", "value": vendor_actual["annual_spend_m"], "inference": "Higher spend creates a larger value base."},
            {"dimension": "Replaceability", "value": vendor_actual["replaceability"], "inference": "Higher replaceability typically improves Transition economics."},
            {"dimension": "Contract Flexibility", "value": vendor_actual["contract_flexibility"], "inference": "Higher flexibility improves Novate and Transition value."},
            {"dimension": "Execution Difficulty", "value": vendor_actual["execution_difficulty"], "inference": "Higher difficulty increases one-time cost and reduces savings."},
            {"dimension": "Lock-in", "value": vendor_actual["lock_in"], "inference": "Higher lock-in reduces savings and increases avoided-loss value under Retain."},
            {"dimension": "Value Potential", "value": vendor_actual["value_potential"], "inference": "Higher value potential lifts expected upside."},
            {"dimension": "Governance Fit", "value": vendor_actual["governance_fit"], "inference": "Higher governance fit improves Novate and Managed value."},
            {"dimension": "Business Criticality", "value": vendor_actual["business_criticality"], "inference": "Higher criticality increases avoided-loss logic for Retain."},
        ])
        st.dataframe(value_inputs, use_container_width=True, hide_index=True)

        st.markdown("#### Vendor-Level Logic Breakdown (%)")
        st.dataframe(vendor_logic, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Vendor-Level Value Summary")
        value_summary = pd.DataFrame([
            {"metric": "Value Type", "value": vendor_final["value_type"]},
            {"metric": "Gross Value ($M)", "value": vendor_final["gross_value_m"]},
            {"metric": "One-Time Cost ($M)", "value": vendor_final["one_time_cost_m"]},
            {"metric": "Net Value ($M)", "value": vendor_final["net_value_m"]},
            {"metric": "Gross Value %", "value": vendor_final["gross_pct"]},
            {"metric": "One-Time Cost %", "value": vendor_final["cost_pct"]},
            {"metric": "Payback (months)", "value": vendor_final["payback_months"] if pd.notnull(vendor_final["payback_months"]) else "N/A"},
        ])
        st.dataframe(value_summary, use_container_width=True, hide_index=True)

        chart_df = pd.DataFrame([
            {"metric": "Gross Value", "amount_m": vendor_final["gross_value_m"]},
            {"metric": "One-Time Cost", "amount_m": vendor_final["one_time_cost_m"]},
            {"metric": "Net Value", "amount_m": vendor_final["net_value_m"]},
        ]).set_index("metric")
        st.markdown("#### Vendor-Level Value Chart ($M)")
        st.bar_chart(chart_df)

    st.markdown("---")
    st.markdown("### Portfolio-Level Potential Value")

    portfolio_total_gross = round(final_df["gross_value_m"].sum(), 2)
    portfolio_total_cost = round(final_df["one_time_cost_m"].sum(), 2)
    portfolio_total_net = round(final_df["net_value_m"].sum(), 2)

    tranche_12_df = final_df[final_df["tranche"].isin(["Tranche 1", "Tranche 2"])].copy()
    tranche_12_gross = round(tranche_12_df["gross_value_m"].sum(), 2)
    tranche_12_cost = round(tranche_12_df["one_time_cost_m"].sum(), 2)
    tranche_12_net = round(tranche_12_df["net_value_m"].sum(), 2)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Portfolio Gross Value ($M)", portfolio_total_gross)
    with c2:
        st.metric("Portfolio One-Time Cost ($M)", portfolio_total_cost)
    with c3:
        st.metric("Portfolio Net Value ($M)", portfolio_total_net)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Tranche 1 + 2 Gross Value ($M)", tranche_12_gross)
    with c5:
        st.metric("Tranche 1 + 2 One-Time Cost ($M)", tranche_12_cost)
    with c6:
        st.metric("Tranche 1 + 2 Net Value ($M)", tranche_12_net)

with tab6:
    st.subheader("Decision Cockpit")

    col1, col2 = st.columns([2, 1])

    with col1:
        display_df = final_df[[
            "vendor", "Transition", "Novate", "Managed", "Retain",
            "recommended_treatment", "top_score", "score_gap_vs_next_best",
            "readiness_score", "tranche", "gross_value_m", "one_time_cost_m", "net_value_m"
        ]].copy()

        for col in ["Transition", "Novate", "Managed", "Retain", "top_score", "score_gap_vs_next_best", "readiness_score", "gross_value_m", "one_time_cost_m", "net_value_m"]:
            display_df[col] = display_df[col].round(2)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Portfolio Summary")
        treatment_counts = final_df["recommended_treatment"].value_counts().rename_axis("treatment").reset_index(name="count")
        tranche_counts = final_df["tranche"].value_counts().rename_axis("tranche").reset_index(name="count")

        total_gross = round(final_df["gross_value_m"].sum(), 2)
        total_cost = round(final_df["one_time_cost_m"].sum(), 2)
        total_net = round(final_df["net_value_m"].sum(), 2)

        st.markdown("**Treatment Count**")
        st.dataframe(treatment_counts, use_container_width=True, hide_index=True)
        st.markdown("**Tranche Count**")
        st.dataframe(tranche_counts, use_container_width=True, hide_index=True)
        st.markdown("**Portfolio Value ($M)**")
        st.dataframe(pd.DataFrame([
            {"metric": "Total Gross Value", "value": total_gross},
            {"metric": "Total One-Time Cost", "value": total_cost},
            {"metric": "Total Net Value", "value": total_net},
        ]), use_container_width=True, hide_index=True)

with tab7:
    st.subheader("Live Simulator")

    sim_row = final_df[final_df["vendor"] == selected_vendor].iloc[0]
    sim_actual = actual_df[actual_df["vendor"] == selected_vendor].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Current Simulated Inputs")
        sim_inputs = pd.DataFrame([
            {"dimension": "replaceability", "score": sim_actual["replaceability"]},
            {"dimension": "contract_flexibility", "score": sim_actual["contract_flexibility"]},
            {"dimension": "execution_difficulty", "score": sim_actual["execution_difficulty"]},
            {"dimension": "lock_in", "score": sim_actual["lock_in"]},
            {"dimension": "value_potential", "score": sim_actual["value_potential"]},
            {"dimension": "operational_readiness", "score": sim_actual["operational_readiness"]},
            {"dimension": "governance_fit", "score": sim_actual["governance_fit"]},
            {"dimension": "vendor_health", "score": sim_actual["vendor_health"]},
            {"dimension": "execution_readiness", "score": sim_actual["execution_readiness"]},
            {"dimension": "annual_spend_m", "score": sim_actual["annual_spend_m"]},
            {"dimension": "business_criticality", "score": sim_actual["business_criticality"]},
        ])
        st.dataframe(sim_inputs, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Current Simulated Result")
        sim_result = pd.DataFrame([
            {"metric": "Recommended Treatment", "value": sim_row["recommended_treatment"]},
            {"metric": "Transition Score", "value": round(sim_row["Transition"], 2)},
            {"metric": "Novate Score", "value": round(sim_row["Novate"], 2)},
            {"metric": "Managed Score", "value": round(sim_row["Managed"], 2)},
            {"metric": "Retain Score", "value": round(sim_row["Retain"], 2)},
            {"metric": "Readiness Score", "value": round(sim_row["readiness_score"], 2)},
            {"metric": "Tranche", "value": sim_row["tranche"]},
            {"metric": "Gross Value ($M)", "value": round(sim_row["gross_value_m"], 2)},
            {"metric": "One-Time Cost ($M)", "value": round(sim_row["one_time_cost_m"], 2)},
            {"metric": "Net Value ($M)", "value": round(sim_row["net_value_m"], 2)},
            {"metric": "Value Type", "value": sim_row["value_type"]},
        ])
        st.dataframe(sim_result, use_container_width=True, hide_index=True)

    st.markdown("#### Portfolio Summary for All Simulated Vendors")
    sim_portfolio_df = final_df[[
        "vendor", "recommended_treatment", "readiness_score", "tranche",
        "gross_value_m", "one_time_cost_m", "net_value_m"
    ]].copy().sort_values(["tranche", "net_value_m"], ascending=[True, False])

    st.dataframe(sim_portfolio_df, use_container_width=True, hide_index=True)

with st.expander("Model Notes"):
    st.markdown("""
**Co-Pilot capabilities**
- Ask vendor-specific questions
- Ask portfolio questions
- Add synthetic vendors using natural language prompts

**Examples**
- Vendor 5 is ideal candidate for what?
- Why is Vendor 4 managed?
- Show top 3 vendors by net value
- What is total net value?
- Add Vendor 11
- Add Vendor 12 with high lock-in and low replaceability

**Important**
- Prompt behavior is LLM-style UX implemented with local intent parsing for demo purposes.
- Added vendors are synthetic demo entities and are clearly treated as synthetic assumptions.
""")
