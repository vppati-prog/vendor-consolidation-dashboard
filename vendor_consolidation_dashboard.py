import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vendor Consolidation Dashboard", layout="wide")

# =========================================================
# 1. BASE DATA - 10 VENDORS (LIKE-FOR-LIKE WITH EXCEL EXAMPLE)
# =========================================================

BASE_VENDOR_METADATA = pd.DataFrame([
    {"vendor": "V1",  "replaceability": 5, "execution_difficulty": 2, "value_potential": 5, "operational_readiness": 4, "governance_fit": 4, "vendor_health": 4},
    {"vendor": "V2",  "replaceability": 4, "execution_difficulty": 3, "value_potential": 4, "operational_readiness": 3, "governance_fit": 4, "vendor_health": 3},
    {"vendor": "V3",  "replaceability": 3, "execution_difficulty": 3, "value_potential": 3, "operational_readiness": 3, "governance_fit": 5, "vendor_health": 4},
    {"vendor": "V4",  "replaceability": 2, "execution_difficulty": 4, "value_potential": 3, "operational_readiness": 2, "governance_fit": 4, "vendor_health": 3},
    {"vendor": "V5",  "replaceability": 1, "execution_difficulty": 5, "value_potential": 2, "operational_readiness": 1, "governance_fit": 2, "vendor_health": 3},
    {"vendor": "V6",  "replaceability": 3, "execution_difficulty": 4, "value_potential": 4, "operational_readiness": 3, "governance_fit": 4, "vendor_health": 4},
    {"vendor": "V7",  "replaceability": 2, "execution_difficulty": 4, "value_potential": 2, "operational_readiness": 2, "governance_fit": 4, "vendor_health": 3},
    {"vendor": "V8",  "replaceability": 5, "execution_difficulty": 2, "value_potential": 4, "operational_readiness": 5, "governance_fit": 4, "vendor_health": 4},
    {"vendor": "V9",  "replaceability": 1, "execution_difficulty": 5, "value_potential": 1, "operational_readiness": 1, "governance_fit": 2, "vendor_health": 2},
    {"vendor": "V10", "replaceability": 3, "execution_difficulty": 3, "value_potential": 3, "operational_readiness": 3, "governance_fit": 3, "vendor_health": 3},
])

CONTRACT_SCORE_TARGETS = {
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

# Build base contract text
BASE_CONTRACTS = {
    vendor: generate_contract_text(vendor, scores["contract_flexibility"], scores["lock_in"])
    for vendor, scores in CONTRACT_SCORE_TARGETS.items()
}

# =========================================================
# 3. MODEL LOGIC
# =========================================================

TREATMENT_DIMENSIONS = [
    "replaceability",
    "contract_flexibility",
    "execution_difficulty",
    "lock_in",
    "value_potential",
]

READINESS_DIMENSIONS = [
    "operational_readiness",
    "governance_fit",
    "vendor_health",
    "execution_readiness",  # this is inverse of execution_difficulty
]

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

DEFAULT_TREATMENT_WEIGHTS = {
    "replaceability": 30,
    "contract_flexibility": 20,
    "execution_difficulty": 20,
    "lock_in": 10,
    "value_potential": 20,
}

READINESS_WEIGHTS = {
    "operational_readiness": 35,
    "governance_fit": 25,
    "vendor_health": 20,
    "execution_readiness": 20,
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
        contract_flexibility = derive_contract_flexibility(contract_text)
        lock_in = derive_lock_in(contract_text)

        records.append({
            "vendor": vendor,
            "replaceability": int(row["replaceability"]),
            "contract_flexibility": int(contract_flexibility),
            "execution_difficulty": int(row["execution_difficulty"]),
            "lock_in": int(lock_in),
            "value_potential": int(row["value_potential"]),
            "operational_readiness": int(row["operational_readiness"]),
            "governance_fit": int(row["governance_fit"]),
            "vendor_health": int(row["vendor_health"]),
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
        weighted_points = weight * row["fit_score"] / 5.0  # out of 100 once all weights sum to 100
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

    pivot = summary.pivot(index="vendor", columns="option", values="option_score").reset_index()
    pivot = pivot.fillna(0)

    option_cols = ["Transition", "Novate", "Managed", "Retain"]
    pivot["recommended_treatment"] = pivot[option_cols].idxmax(axis=1)
    pivot["top_score"] = pivot[option_cols].max(axis=1)

    # confidence gap between top 2 options
    def score_gap(row):
        vals = sorted([row[c] for c in option_cols], reverse=True)
        return round(vals[0] - vals[1], 2)

    pivot["score_gap_vs_next_best"] = pivot.apply(score_gap, axis=1)
    return pivot

def build_readiness_summary(actual_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in actual_df.iterrows():
        weighted_score = (
            READINESS_WEIGHTS["operational_readiness"] * row["operational_readiness"] +
            READINESS_WEIGHTS["governance_fit"] * row["governance_fit"] +
            READINESS_WEIGHTS["vendor_health"] * row["vendor_health"] +
            READINESS_WEIGHTS["execution_readiness"] * row["execution_readiness"]
        ) / 5.0  # converts 1-5 weighted scale into 0-100

        if weighted_score >= 75:
            tranche = "Tranche 1"
        elif weighted_score >= 50:
            tranche = "Tranche 2"
        else:
            tranche = "Tranche 3"

        rows.append({
            "vendor": row["vendor"],
            "readiness_score": round(weighted_score, 2),
            "tranche": tranche,
        })
    return pd.DataFrame(rows)

def explain_vendor(vendor: str, weighted_df: pd.DataFrame, final_df: pd.DataFrame) -> str:
    row = final_df[final_df["vendor"] == vendor].iloc[0]
    treatment = row["recommended_treatment"]

    details = weighted_df[
        (weighted_df["vendor"] == vendor) &
        (weighted_df["option"] == treatment)
    ].sort_values("weighted_points", ascending=False)

    top3 = details.head(3)[["dimension", "actual_score", "preferred_range", "weighted_points"]]
    reasons = []
    for _, r in top3.iterrows():
        reasons.append(
            f"{r['dimension']} scored {int(r['actual_score'])}, "
            f"which fits the preferred range {r['preferred_range']} for {treatment} "
            f"and contributed {r['weighted_points']:.1f} points."
        )

    return " ".join(reasons)

# =========================================================
# 4. SIDEBAR CONTROLS
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

selected_vendor = st.sidebar.selectbox("Pick vendor to simulate", BASE_VENDOR_METADATA["vendor"].tolist(), index=0)

selected_row = BASE_VENDOR_METADATA[BASE_VENDOR_METADATA["vendor"] == selected_vendor].iloc[0]
selected_contract_targets = CONTRACT_SCORE_TARGETS[selected_vendor]

sim_replaceability = st.sidebar.slider("Replaceability (sim)", 1, 5, int(selected_row["replaceability"]))
sim_execution_difficulty = st.sidebar.slider("Execution Difficulty (sim)", 1, 5, int(selected_row["execution_difficulty"]))
sim_value = st.sidebar.slider("Value Potential (sim)", 1, 5, int(selected_row["value_potential"]))
sim_operational = st.sidebar.slider("Operational Readiness (sim)", 1, 5, int(selected_row["operational_readiness"]))
sim_governance = st.sidebar.slider("Governance Fit (sim)", 1, 5, int(selected_row["governance_fit"]))
sim_health = st.sidebar.slider("Vendor Health (sim)", 1, 5, int(selected_row["vendor_health"]))

sim_contract_flex = st.sidebar.slider("Contract Flexibility (via contract)", 1, 5, int(selected_contract_targets["contract_flexibility"]))
sim_lock_in = st.sidebar.slider("Lock-in (via contract)", 1, 5, int(selected_contract_targets["lock_in"]))

# =========================================================
# 5. APPLY SIMULATION TO A WORKING COPY
# =========================================================

working_metadata = BASE_VENDOR_METADATA.copy()
working_contracts = BASE_CONTRACTS.copy()

working_metadata.loc[working_metadata["vendor"] == selected_vendor, "replaceability"] = sim_replaceability
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "execution_difficulty"] = sim_execution_difficulty
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "value_potential"] = sim_value
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "operational_readiness"] = sim_operational
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "governance_fit"] = sim_governance
working_metadata.loc[working_metadata["vendor"] == selected_vendor, "vendor_health"] = sim_health

working_contracts[selected_vendor] = generate_contract_text(selected_vendor, sim_contract_flex, sim_lock_in)

# =========================================================
# 6. CALCULATE MODEL OUTPUTS
# =========================================================

actual_df = build_actual_scores(working_metadata, working_contracts)
fit_df = build_fit_table(actual_df)
weighted_df = build_weighted_scores(fit_df, treatment_weights)
treatment_df = build_treatment_summary(weighted_df)
readiness_df = build_readiness_summary(actual_df)

final_df = treatment_df.merge(readiness_df, on="vendor", how="left")
final_df["explanation"] = final_df["vendor"].apply(lambda v: explain_vendor(v, weighted_df, final_df))

# =========================================================
# 7. UI
# =========================================================

st.title("Vendor Consolidation Dashboard")
st.caption("Demo for 10 vendors: contract parsing + metadata scoring + treatment recommendation + readiness tranche")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Vendor Intelligence Hub",
    "2. Fit Logic",
    "3. Weighted Scores",
    "4. Decision Cockpit",
    "5. Simulator View",
])

# -------------------------------
# TAB 1 - Vendor Intelligence Hub
# -------------------------------
with tab1:
    st.subheader("Vendor Intelligence Hub")

    vendor_pick = st.selectbox("Select vendor", actual_df["vendor"].tolist(), key="vih_vendor")
    contract_text = working_contracts[vendor_pick]
    contract_signals = extract_contract_signals(contract_text)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Parsed Contract Signals")
        signal_df = pd.DataFrame([
            {"signal": k, "value": v} for k, v in contract_signals.items()
        ])
        st.dataframe(signal_df, use_container_width=True, hide_index=True)

        st.markdown("#### Actual Scores Used by the Model")
        vendor_actual = actual_df[actual_df["vendor"] == vendor_pick].T.reset_index()
        vendor_actual.columns = ["dimension", "score"]
        st.dataframe(vendor_actual, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Mock Contract Text")
        st.text_area("Contract", value=contract_text, height=380, key="contract_text_view")

# -------------------------------
# TAB 2 - Fit Logic
# -------------------------------
with tab2:
    st.subheader("Step 2: Actual Score vs Preferred Range -> Fit Score")

    vendor_pick_fit = st.selectbox("Select vendor for fit view", actual_df["vendor"].tolist(), key="fit_vendor")
    vendor_fit = fit_df[fit_df["vendor"] == vendor_pick_fit].copy()
    st.dataframe(vendor_fit, use_container_width=True, hide_index=True)

    st.info(
        "Layman logic: for each dimension, the model checks how well the vendor's actual score matches "
        "what each option prefers. Match = Fit 5, close = Fit 3, far = Fit 1."
    )

# -------------------------------
# TAB 3 - Weighted Scores
# -------------------------------
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

    st.info(
        "Layman logic: the fit tells us how suitable a dimension is for an option. "
        "The weight tells us how important that dimension is overall. "
        "Weighted points = weight x fit / 5."
    )

# -------------------------------
# TAB 4 - Decision Cockpit
# -------------------------------
with tab4:
    st.subheader("Decision Cockpit")

    col1, col2 = st.columns([2, 1])

    with col1:
        display_df = final_df[[
            "vendor", "Transition", "Novate", "Managed", "Retain",
            "recommended_treatment", "top_score", "score_gap_vs_next_best",
            "readiness_score", "tranche"
        ]].copy()

        for col in ["Transition", "Novate", "Managed", "Retain", "top_score", "score_gap_vs_next_best", "readiness_score"]:
            display_df[col] = display_df[col].round(2)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Portfolio Summary")
        treatment_counts = final_df["recommended_treatment"].value_counts().rename_axis("treatment").reset_index(name="count")
        tranche_counts = final_df["tranche"].value_counts().rename_axis("tranche").reset_index(name="count")

        st.markdown("**Treatment Count**")
        st.dataframe(treatment_counts, use_container_width=True, hide_index=True)
        st.markdown("**Tranche Count**")
        st.dataframe(tranche_counts, use_container_width=True, hide_index=True)

    st.markdown("#### Explanation")
    vendor_pick_explain = st.selectbox("Select vendor for explanation", final_df["vendor"].tolist(), key="explain_vendor")
    explain_row = final_df[final_df["vendor"] == vendor_pick_explain].iloc[0]

    st.write(f"**Recommended treatment:** {explain_row['recommended_treatment']}")
    st.write(f"**Readiness score:** {explain_row['readiness_score']}")
    st.write(f"**Tranche:** {explain_row['tranche']}")
    st.write(f"**Why:** {explain_row['explanation']}")

# -------------------------------
# TAB 5 - Simulator
# -------------------------------
with tab5:
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
        ])
        st.dataframe(sim_result, use_container_width=True, hide_index=True)

    st.success(
        f"Live demo: you are currently simulating vendor {selected_vendor}. "
        "Every slider move in the sidebar recalculates the contract, actual scores, fit scores, "
        "weighted scores, treatment recommendation, readiness score, and tranche."
    )

# =========================================================
# 8. FOOTER / MODEL NOTES
# =========================================================

with st.expander("Model Notes"):
    st.markdown("""
**How this demo works**
1. Mock contracts are generated for each vendor.
2. The contract parser derives two contract-based dimensions:
   - contract_flexibility
   - lock_in
3. Remaining dimensions come from synthetic metadata.
4. For each treatment option, the model checks how well the actual score fits the preferred range.
5. Fit scores are converted into weighted points.
6. Highest treatment score wins.
7. Readiness uses:
   - operational_readiness
   - governance_fit
   - vendor_health
   - inverse of execution_difficulty

**Readiness formula**
- execution_readiness = 6 - execution_difficulty
- readiness_score = weighted score out of 100

**Tranche thresholds**
- 75+ = Tranche 1
- 50 to 74.99 = Tranche 2
- Below 50 = Tranche 3
""")
