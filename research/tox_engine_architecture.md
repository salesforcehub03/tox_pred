# ToxLab Prediction Engine Architecture

Here is a complete, deep-dive breakdown of how the **ToxLab Fast Prediction Engine** works locally. The system operates as a sophisticated offline ensemble model that relies on deterministic, rigorous computational chemistry to generate predictions.

## 1. Cheminformatics & Topological Profiling (`rdkit`)
At the foundation, the application uses **RDKit**, the industry-standard cheminformatics framework.
* **Property Calculation:** It deterministically computes metrics like molecular weight, polar surface area (TPSA), and lipophilicity (XLogP). These metrics flag potential phospholipidosis or poor pharmacokinetics (e.g., violations of Lipinski's Rule of 5).
* **Structural Alert Filtering:** RDKit’s `FilterCatalog` is configured with **BRENK** and **PAINS** filters. The engine scans the compound for known *toxicophores* (e.g., anilines, nitro groups, quinones) which act as structural liabilities for covalent binding, haptenation, and oxidative stress.

## 2. Deep-Learning Virtual Screening (`deepchem` + `tensorflow-cpu`)
We utilize the open-source **DeepChem** framework to run virtual bio-target screening trained directly on the NIH **Tox21** library.
* **Featurization:** The compound’s SMILES string is mathematically decomposed into an **ECFP-1024** (Extended Connectivity Fingerprint). 
* **Target Binding Proximity:** DeepChem predicts the molecule's likelihood of binding to or disrupting 12 specific biological "alarm" systems. This tracks interactions with Nuclear Receptors (NR: like AhR or Estrogen) and Stress-Response pathways (SR: like p53 activation for DNA damage, or MMP for mitochondrial uncoupling).

## 3. Algorithmic Synthesis Engine (The "PhD" Rules Engine)
This is the offline logic built to replace generative artificial intelligence models (Azure OpenAI). It operates as a strict **Expert Rules Engine**.
* **Embedded Pharmacology Dictionaries:** The codebase incorporates heavily curated dictionaries (`TARGET_BIOLOGY` & `TOXICOPHORE_DB`). They contain deep mechanistic reasoning (e.g., exactly *how* a specific hydrazine depletes GSH).
* **Deterministic Narrative Generation:** The algorithm reads the raw scores from RDKit and DeepChem. If it evaluates high lipophilicity + a quinone alert + high mitochondrial disruption, the Python code seamlessly concatenates pre-written scientific clauses mapping those vectors, outputting a precise, PhD-level 4-paragraph clinical thesis and Drug-Induced Liver Injury (DILI) score.

## 4. Real-World API Data Integration (`requests` + `biopython`)
While the primary predictions are offline, the system cross-validates via real-world API aggregation:
* **openFDA FAERS via `requests`:** It maps the predicted compound directly to the FDA's live adverse event database to append genuine historical clinical signals (e.g., post-market reports of hepatotoxicity).
* **NCBI PubMed via `biopython`:** It accesses `Entrez` to calculate the "Toxicity Literature Density" (measuring the proportion of research papers focused on this compound's toxicity paradigms).

## 5. Web Application Layer (`fasthtml` + Tailwind CSS)
Unlike standard React or Streamlit UIs, the app is rendered via **FastHTML**—a modern Python-to-HTML abstraction. 
* It uses pure Python functions (`Div()`, `Span()`) to stream HTML containing **Tailwind CSS** stylings directly to the browser.
* This allows the application to run instantaneously via an ASGI server overlay (Uvicorn), avoiding the massive payload of a Javascript-heavy frontend framework.
