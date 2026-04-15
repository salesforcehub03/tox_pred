"""
Ground Truth Database for Toxicity Prediction Engine Validation
================================================================
Curated pharmacovigilance data from FDA labels, NIH LiverTox,
DailyMed, and published clinical literature.

Organ risk levels: "High", "Moderate", "Low", "None"
  - "High"     = Black-box warning, dose-limiting, or class-defining toxicity
  - "Moderate"  = Listed AE, clinically monitored, or significant signal
  - "Low"       = Rare/minor signal, or no clinical concern
  - "None"      = No established association

Sources:
  FDA = FDA-approved labeling / prescribing information
  LT  = NIH LiverTox (https://www.ncbi.nlm.nih.gov/books/NBK547852/)
  PM  = Published peer-reviewed pharmacovigilance
"""

GROUND_TRUTH = {
    # =========================================================================
    # 1. CITALOPRAM HYDROBROMIDE (SSRI)
    # =========================================================================
    "citalopram": {
        "name": "Citalopram Hydrobromide",
        "smiles": "C(#N)c1ccc2c(c1)C(CCN(C)C)c1cc(F)ccc1O2",
        "lookup_name": "citalopram",
        "known_organ_risks": {
            "liver":  "Low",       # Rare hepatotoxicity, idiosyncratic
            "lung":   "None",
            "kidney": "Low",       # Hyponatremia / SIADH
            "heart":  "High",      # FDA WARNING: Dose-dependent QT prolongation (>40mg)
            "brain":  "Moderate",  # Serotonin syndrome, seizures (rare), suicidal ideation (BBW)
        },
        "known_adverse_events": [
            "QT prolongation", "Torsade de pointes", "Serotonin syndrome",
            "Hyponatremia", "SIADH", "Suicidal ideation", "Nausea",
            "Somnolence", "Sexual dysfunction", "Withdrawal syndrome",
        ],
        "expected_structural_alerts": [],  # SSRI: clean structure, no classical toxicophores
        "source": "FDA Label (2017 revision); DailyMed; PMID:22053185 (QT data)"
    },

    # =========================================================================
    # 2. ESKETAMINE (NMDA Antagonist)
    # =========================================================================
    "esketamine": {
        "name": "Esketamine",
        "smiles": "CNC1(CCCCC1=O)C1=CC=CC=C1Cl",
        "lookup_name": "esketamine",
        "known_organ_risks": {
            "liver":  "Low",       # Transient transaminase elevations
            "lung":   "None",
            "kidney": "Low",       # Rare cystitis (chronic use)
            "heart":  "Moderate",  # Transient hypertension, tachycardia
            "brain":  "High",      # Dissociation, sedation, perceptual disturbances, suicidality (BBW)
        },
        "known_adverse_events": [
            "Dissociation", "Dizziness", "Nausea", "Sedation",
            "Vertigo", "Hypoesthesia", "Anxiety", "Increased blood pressure",
            "Suicidal ideation", "Dysgeusia",
        ],
        "expected_structural_alerts": [],  # Cyclohexanone — generally clean
        "source": "FDA Label (Spravato®, 2019); PMID:30950986"
    },

    # =========================================================================
    # 3. FENTANYL (Opioid Agonist)
    # =========================================================================
    "fentanyl": {
        "name": "Fentanyl",
        "smiles": "CCC(=O)N(C1CCN(CC1)CCC1=CC=CC=C1)C1=CC=CC=C1",
        "lookup_name": "fentanyl",
        "known_organ_risks": {
            "liver":  "Low",       # Hepatic metabolism via CYP3A4, rare DILI
            "lung":   "High",      # BBW: Respiratory depression — primary cause of death
            "kidney": "Low",
            "heart":  "Moderate",  # Bradycardia, QT prolongation at high doses
            "brain":  "High",      # CNS depression, dependence, seizures, muscle rigidity
        },
        "known_adverse_events": [
            "Respiratory depression", "Apnea", "Bradycardia", "Hypotension",
            "Muscle rigidity", "Nausea", "Constipation", "Somnolence",
            "Seizures", "Dependence",
        ],
        "expected_structural_alerts": ["aniline"],  # Aromatic amine (N-phenyl)
        "source": "FDA Label; PMID:27890469; WHO Model List"
    },

    # =========================================================================
    # 4. FLUNARIZINE (Calcium Channel Blocker)
    # =========================================================================
    "flunarizine": {
        "name": "Flunarizine",
        "smiles": "C(C1=CC=CC=C1)N1CCN(CC1)/C=C/C1=CC=C(F)C=C1F",
        "lookup_name": "flunarizine",
        "known_organ_risks": {
            "liver":  "Low",       # Rare hepatic AEs
            "lung":   "None",
            "kidney": "None",
            "heart":  "Low",       # Mild orthostatic effects
            "brain":  "High",      # Parkinsonism, depression, drowsiness, weight gain
        },
        "known_adverse_events": [
            "Parkinsonism", "Depression", "Drowsiness", "Weight gain",
            "Asthenia", "Extrapyramidal symptoms", "Galactorrhea",
        ],
        "expected_structural_alerts": [],  # Clean piperazine structure
        "source": "EMA Assessment; PMID:3542335; PMID:2648949"
    },

    # =========================================================================
    # 5. GALANTAMINE HBr (AChE Inhibitor)
    # =========================================================================
    "galantamine": {
        "name": "Galantamine Hydrobromide",
        "smiles": "CN1CCC2=CC(=C3C=C2C1CC4=CC(=C(C=C34)OC)O)O",
        "lookup_name": "galantamine",
        "known_organ_risks": {
            "liver":  "Low",       # Rare hepatotoxicity
            "lung":   "None",
            "kidney": "Low",
            "heart":  "Moderate",  # Bradycardia, syncope, AV block (vagotonic)
            "brain":  "Moderate",  # Dizziness, headache, insomnia, tremor
        },
        "known_adverse_events": [
            "Nausea", "Vomiting", "Diarrhea", "Dizziness", "Headache",
            "Bradycardia", "Syncope", "Weight loss", "Anorexia",
            "Insomnia", "Tremor",
        ],
        "expected_structural_alerts": ["phenol"],  # Catechol/phenol moiety in galantamine
        "source": "FDA Label (Razadyne®); NIH LiverTox; PMID:12804452"
    },

    # =========================================================================
    # 6. HALOPERIDOL (Typical Antipsychotic)
    # =========================================================================
    "haloperidol": {
        "name": "Haloperidol",
        "smiles": "OC1(CCN(CCCC(=O)C2=CC=C(F)C=C2)CC1)C1=CC=C(Cl)C=C1",
        "lookup_name": "haloperidol",
        "known_organ_risks": {
            "liver":  "Moderate",  # Cholestatic/hepatocellular injury (rare but documented)
            "lung":   "Low",       # NMS-associated respiratory failure (rare)
            "kidney": "Low",
            "heart":  "High",      # BBW: QT prolongation, TdP, sudden cardiac death
            "brain":  "High",      # EPS, tardive dyskinesia, NMS, sedation
        },
        "known_adverse_events": [
            "QT prolongation", "Torsade de pointes", "Sudden cardiac death",
            "Extrapyramidal symptoms", "Tardive dyskinesia",
            "Neuroleptic malignant syndrome", "Akathisia",
            "Sedation", "Hypotension", "Prolactin elevation",
        ],
        "expected_structural_alerts": [],  # Butyrophenone — generally clean RDKit alerts
        "source": "FDA Label; NIH LiverTox; PMID:15719150"
    },

    # =========================================================================
    # 7. HALOPERIDOL DECANOATE (Long-acting Haloperidol)
    # =========================================================================
    "haloperidol_decanoate": {
        "name": "Haloperidol Decanoate",
        "smiles": "CCCCCCCCCC(=O)OC1(CCN(CCCC(=O)C2=CC=C(F)C=C2)CC1)C1=CC=C(Cl)C=C1",
        "lookup_name": "haloperidol decanoate",
        "known_organ_risks": {
            "liver":  "Moderate",  # Same as haloperidol + ester hydrolysis
            "lung":   "Low",
            "kidney": "Low",
            "heart":  "High",      # Same QT risk as haloperidol
            "brain":  "High",      # Same EPS/NMS risk
        },
        "known_adverse_events": [
            "QT prolongation", "Extrapyramidal symptoms", "Tardive dyskinesia",
            "Neuroleptic malignant syndrome", "Injection site reactions",
            "Sedation", "Akathisia", "Prolactin elevation",
        ],
        "expected_structural_alerts": [],
        "source": "FDA Label; NIH LiverTox"
    },

    # =========================================================================
    # 8. METHYLPHENIDATE HCl (CNS Stimulant)
    # =========================================================================
    "methylphenidate": {
        "name": "Methylphenidate Hydrochloride",
        "smiles": "COC(=O)C(C1CCCCN1)C1=CC=CC=C1",
        "lookup_name": "methylphenidate",
        "known_organ_risks": {
            "liver":  "Low",       # Very rare hepatotoxicity
            "lung":   "None",
            "kidney": "None",
            "heart":  "Moderate",  # BBW: Cardiovascular risk (tachycardia, elevated BP, sudden death in predisposed)
            "brain":  "Moderate",  # Insomnia, nervousness, seizure threshold lowering, psychosis (rare)
        },
        "known_adverse_events": [
            "Tachycardia", "Increased blood pressure", "Palpitations",
            "Insomnia", "Nervousness", "Headache", "Decreased appetite",
            "Abdominal pain", "Weight loss", "Tics", "Seizures",
        ],
        "expected_structural_alerts": [],  # Clean piperidine
        "source": "FDA Label (Ritalin®/Concerta®); PMID:16864816"
    },

    # =========================================================================
    # 9. NALTREXONE HCl (Opioid Antagonist)
    # =========================================================================
    "naltrexone": {
        "name": "Naltrexone Hydrochloride",
        "smiles": "OC1=CC2=C(CC1=O)C1(CC3CC(C21)C1=CC=C(O)C3=C1O)C1CC1",
        "lookup_name": "naltrexone",
        "known_organ_risks": {
            "liver":  "High",      # BBW: Hepatotoxicity at supratherapeutic doses, dose-dependent transaminase elevation
            "lung":   "None",
            "kidney": "Low",
            "heart":  "Low",
            "brain":  "Moderate",  # Headache, anxiety, insomnia, dizziness, precipitated withdrawal
        },
        "known_adverse_events": [
            "Hepatotoxicity", "Transaminase elevation", "Nausea", "Headache",
            "Dizziness", "Anxiety", "Insomnia", "Abdominal pain",
            "Precipitated withdrawal", "Injection site reaction",
        ],
        "expected_structural_alerts": ["phenol"],  # Phenolic OH
        "source": "FDA Label (BBW); NIH LiverTox; PMID:15895072"
    },

    # =========================================================================
    # 10. PALIPERIDONE (Atypical Antipsychotic)
    # =========================================================================
    "paliperidone": {
        "name": "Paliperidone",
        "smiles": "CC1=C(C=CO1)CN1CCC(CC1)C1=NOC2=C1C=CC(=C2)F",
        "lookup_name": "paliperidone",
        "known_organ_risks": {
            "liver":  "Low",       # Minimal hepatic metabolism (renal clearance)
            "lung":   "None",
            "kidney": "moderate",  # Renally cleared — requires dose adjustment in RI
            "heart":  "Moderate",  # QT prolongation (less than haloperidol)
            "brain":  "Moderate",  # EPS, akathisia, somnolence, NMS (rare)
        },
        "known_adverse_events": [
            "QT prolongation", "Extrapyramidal symptoms", "Somnolence",
            "Akathisia", "Tachycardia", "Weight gain", "Metabolic syndrome",
            "Prolactin elevation", "Orthostatic hypotension",
        ],
        "expected_structural_alerts": [],
        "source": "FDA Label (Invega®); DailyMed; PMID:17679577"
    },

    # =========================================================================
    # 11. PALIPERIDONE PALMITATE (Long-acting)
    # =========================================================================
    "paliperidone_palmitate": {
        "name": "Paliperidone Palmitate",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OC1=CC2=C(C=C1)C(=NO2)C1CCN(CC3=CC(C)=CO3)CC1",
        "lookup_name": "paliperidone palmitate",
        "known_organ_risks": {
            "liver":  "Low",
            "lung":   "None",
            "kidney": "Moderate",  # Same renal dependence
            "heart":  "Moderate",  # QT prolongation
            "brain":  "Moderate",  # EPS, NMS risk
        },
        "known_adverse_events": [
            "Injection site reactions", "QT prolongation",
            "Extrapyramidal symptoms", "Weight gain", "Akathisia",
            "Somnolence", "Prolactin elevation", "Metabolic syndrome",
        ],
        "expected_structural_alerts": [],
        "source": "FDA Label (Invega Sustenna®); PMID:21169620"
    },

    # =========================================================================
    # 12. PRUCALOPRIDE (5-HT4 Agonist)
    # =========================================================================
    "prucalopride": {
        "name": "Prucalopride",
        "smiles": "COC1=CC(=C2C=C1)N=C(N2)N1CCC(CC1)NC(=O)C1=CC=C(F)C=C1",
        "lookup_name": "prucalopride",
        "known_organ_risks": {
            "liver":  "Low",       # Well-tolerated
            "lung":   "None",
            "kidney": "Low",
            "heart":  "Low",       # CHMP review confirmed no clinically relevant QT effect
            "brain":  "Low",       # Headache (common but benign)
        },
        "known_adverse_events": [
            "Headache", "Nausea", "Abdominal pain", "Diarrhea",
            "Flatulence", "Dizziness",
        ],
        "expected_structural_alerts": [],  # Clean benzimidazole
        "source": "EMA Assessment (Resolor®); FDA Label (Motegrity®); PMID:19558636"
    },

    # =========================================================================
    # 13. RISPERIDONE (Atypical Antipsychotic)
    # =========================================================================
    "risperidone": {
        "name": "Risperidone",
        "smiles": "CC1=C(C=CO1)CN1CCC(CC1)C1=NOC2=C1C=CC(=C2)F",
        "lookup_name": "risperidone",
        "known_organ_risks": {
            "liver":  "Low",       # Rare cholestatic hepatotoxicity
            "lung":   "None",
            "kidney": "Low",
            "heart":  "Moderate",  # QT prolongation, orthostatic hypotension
            "brain":  "High",      # EPS, tardive dyskinesia, NMS, sedation, seizures
        },
        "known_adverse_events": [
            "Extrapyramidal symptoms", "Tardive dyskinesia", "Somnolence",
            "Weight gain", "Prolactin elevation", "QT prolongation",
            "Orthostatic hypotension", "Metabolic syndrome",
            "Neuroleptic malignant syndrome", "Seizures",
        ],
        "expected_structural_alerts": [],
        "source": "FDA Label (Risperdal®); NIH LiverTox; PMID:8800985"
    },

    # =========================================================================
    # 14. TOPIRAMATE (Anticonvulsant)
    # =========================================================================
    "topiramate": {
        "name": "Topiramate",
        "smiles": "CC1(C)OC2COC3(COS(=O)(=O)N3C)OC2C2OC(C)(C)OC12",
        "lookup_name": "topiramate",
        "known_organ_risks": {
            "liver":  "Low",       # Rare hepatic failure
            "lung":   "None",
            "kidney": "Moderate",  # Kidney stones (~1.5%), metabolic acidosis
            "heart":  "Low",
            "brain":  "High",      # Cognitive impairment ("dopamax"), word-finding difficulty, paresthesia, psychomotor slowing
        },
        "known_adverse_events": [
            "Cognitive dysfunction", "Paresthesia", "Weight loss",
            "Metabolic acidosis", "Kidney stones", "Somnolence",
            "Dizziness", "Fatigue", "Psychomotor slowing",
            "Acute myopia / secondary angle-closure glaucoma",
        ],
        "expected_structural_alerts": ["sulfonamide"],  # Sulfamate group
        "source": "FDA Label (Topamax®); NIH LiverTox; PMID:12749485"
    },

    # =========================================================================
    # 15. TRAMADOL HYDROCHLORIDE (Opioid + SNRI)
    # =========================================================================
    "tramadol": {
        "name": "Tramadol Hydrochloride",
        "smiles": "COC1=CC=CC(=C1)C1(O)CCCC(C1)CN(C)C",
        "lookup_name": "tramadol",
        "known_organ_risks": {
            "liver":  "Moderate",  # Hepatotoxicity reported; CYP2D6-dependent toxicity
            "lung":   "Moderate",  # Respiratory depression (especially with polypharmacy)
            "kidney": "Low",
            "heart":  "Low",       # Rare QT effects
            "brain":  "High",      # SEIZURES (BBW-like), serotonin syndrome, CNS depression, dependence
        },
        "known_adverse_events": [
            "Seizures", "Serotonin syndrome", "Respiratory depression",
            "Nausea", "Dizziness", "Constipation", "Headache",
            "Somnolence", "Dependence", "Withdrawal", "Hypoglycemia",
        ],
        "expected_structural_alerts": ["phenol"],  # Methoxyphenyl (anisole)
        "source": "FDA Label; PMID:23588534; PMID:28072895"
    },

    # =========================================================================
    # 16. BELINOSTAT (HDAC Inhibitor — Oncology)
    # =========================================================================
    "belinostat": {
        "name": "Belinostat",
        "smiles": "ONC(=O)/C=C/C1=CC=CC(=C1)S(=O)(=O)NC1=CC=CC=C1",
        "lookup_name": "belinostat",
        "known_organ_risks": {
            "liver":  "High",      # Hepatotoxicity is dose-limiting; transaminase elevations common
            "lung":   "Low",       # Pneumonia (immunosuppression-related)
            "kidney": "Low",
            "heart":  "Moderate",  # QT prolongation
            "brain":  "Low",       # Fatigue, dizziness
        },
        "known_adverse_events": [
            "Thrombocytopenia", "Neutropenia", "Anemia", "Hepatotoxicity",
            "Nausea", "Vomiting", "Diarrhea", "Fatigue",
            "QT prolongation", "Tumor lysis syndrome",
        ],
        "expected_structural_alerts": [
            "hydroxamic_acid",      # The pharmacophore itself
            "Michael_acceptor",     # α,β-unsaturated hydroxamic acid (conjugated C=C-C=O)
            "sulfonamide",          # -SO2NH-
        ],
        "source": "FDA Label (Beleodaq®); PMID:25384179; NIH LiverTox"
    },

    # =========================================================================
    # 17. VORINOSTAT (HDAC Inhibitor — Oncology)
    # =========================================================================
    "vorinostat": {
        "name": "Vorinostat",
        "smiles": "ONC(=O)CCCCCCC(=O)NC1=CC=CC=C1",
        "lookup_name": "vorinostat",
        "known_organ_risks": {
            "liver":  "Moderate",  # Dose-dependent transaminase elevations
            "lung":   "Low",       # Pulmonary embolism (rare)
            "kidney": "Moderate",  # Elevated creatinine; dehydration-related AKI
            "heart":  "Moderate",  # QT prolongation; T-wave changes
            "brain":  "Low",       # Fatigue, dizziness
        },
        "known_adverse_events": [
            "Thrombocytopenia", "Anemia", "Diarrhea", "Fatigue", "Nausea",
            "Dysgeusia", "Elevated creatinine", "QT prolongation",
            "Pulmonary embolism", "Deep vein thrombosis", "Dehydration",
        ],
        "expected_structural_alerts": [
            "hydroxamic_acid",  # HDAC pharmacophore
            "aniline",          # Anilide bond
        ],
        "source": "FDA Label (Zolinza®); PMID:17060946; NIH LiverTox"
    },
}


def get_all_drugs():
    """Return list of all drug keys."""
    return list(GROUND_TRUTH.keys())


def get_drug(key):
    """Return ground truth for a single drug."""
    return GROUND_TRUTH.get(key)


def get_validation_summary():
    """Print a summary table of all drugs and their expected risk profiles."""
    print(f"\n{'Drug':<28} {'Liver':<10} {'Lung':<10} {'Kidney':<10} {'Heart':<10} {'Brain':<10}")
    print("=" * 88)
    for key, drug in GROUND_TRUTH.items():
        risks = drug['known_organ_risks']
        print(f"{drug['name']:<28} {risks['liver']:<10} {risks['lung']:<10} "
              f"{risks['kidney']:<10} {risks['heart']:<10} {risks['brain']:<10}")


if __name__ == "__main__":
    get_validation_summary()
