import sys
import os
import json
import math
from fasthtml.common import *

# Setup paths for reorganized structure
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(ROOT_DIR, "src"))
sys.path.append(os.path.join(ROOT_DIR, "data"))

from toxicity_predictor import ToxicityPredictor, TOXICOPHORE_DB, TARGET_BIOLOGY

# Initialize the Toxicity Predictor (loads models and sets up OpenAI locally)
predictor = ToxicityPredictor()

# Setup FastHTML app with Tailwind CSS via CDN for premium styling
app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap"),
        Script(src="https://cdn.tailwindcss.com"),
        Style("""
            body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #334155; }
            .scientific-shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
            .causal-line { width: 2px; background: linear-gradient(to bottom, #cbd5e1 0%, #cbd5e1 100%); background-size: 2px 8px; background-repeat: repeat-y; }
            .causal-node { width: 12px; height: 12px; border-radius: 9999px; border: 2px solid #94a3b8; background: white; margin-left: -5px; }
            .causal-node.active { border-color: #3b82f6; background: #3b82f6; }
            .mono { font-family: 'JetBrains Mono', monospace; }
            .animate-fade-in { animation: fadeIn 0.4s ease-out; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
            .htmx-indicator { display: none; }
            .htmx-request .htmx-indicator { display: flex; }
            .htmx-request #results { opacity: 0.2; filter: blur(2px); pointer-events: none; transition: all 0.3s ease; }
            .tab-btn.active { border-bottom: 3px solid #0f172a; color: #0f172a; font-weight: 900; }
            .loading-overlay { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(4px); }
        """),
    )
)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER RENDERERS — All data-rich, production-grade components
# ═══════════════════════════════════════════════════════════════════════════════

def _badge(label):
    """Colored risk badge."""
    if label == "High":
        return Span(label, cls="px-3 py-1 bg-red-100 text-red-700 font-black text-[10px] rounded-md border border-red-200 uppercase tracking-wider")
    elif label == "Moderate":
        return Span(label, cls="px-3 py-1 bg-amber-100 text-amber-700 font-black text-[10px] rounded-md border border-amber-200 uppercase tracking-wider")
    return Span(label, cls="px-3 py-1 bg-green-100 text-green-700 font-black text-[10px] rounded-md border border-green-200 uppercase tracking-wider")

def _section_label(icon, text):
    """Standard section header."""
    return Div(
        Span(f"{icon} {text}", cls="text-[10px] font-black text-slate-400 uppercase tracking-[0.12em]"),
        cls="border-b border-slate-200/60 pb-2 mb-4 mt-6"
    )

def _kv(label, val, mono=False):
    """Key-value row."""
    val_cls = "font-bold text-slate-800" + (" mono text-[10px]" if mono else "")
    return Div(
        Span(label, cls="text-slate-400 text-[11px]"),
        Span(str(val), cls=f"text-[11px] {val_cls}"),
        cls="flex justify-between py-2 border-b border-slate-50 last:border-0"
    )

def _card(title_icon, title, *children, border_color="border-slate-200"):
    """Standard content card."""
    return Div(
        # Header
        Div(
            Span(title_icon, cls="mr-2"),
            Span(title, cls="text-[10px] font-black text-slate-500 uppercase tracking-widest"),
            cls="mb-5 pb-3 border-b border-slate-100 flex items-center"
        ),
        *children,
        cls=f"p-6 bg-white rounded-xl scientific-shadow border {border_color} mb-6 transition-all hover:border-slate-300"
    )

def render_causal_chain(report):
    """Visualizes the 'Structure -> Target -> Outcome' mechanistic flow."""
    dili = report.get("DILI Risk", {})
    lung = report.get("Lung Injury Risk", {})
    dc = report.get("DeepChem Prediction", {}).get("predictions", {})
    alerts = [a for a in report.get("Structural Alerts", []) if a['alert'] != 'None detected']
    
    steps = [
        ("Molecular Chassis", f"logP {report.get('RDKit Properties', {}).get('XLogP')} | TPSA {report.get('RDKit Properties', {}).get('TPSA')}", True),
        ("Structural Alert", alerts[0]['alert'] if alerts else "No Toxicophores", bool(alerts)),
        ("Target Binding", f"Top: {sorted(dc.items(), key=lambda x:x[1], reverse=True)[0][0]}" if dc else "None", bool(dc)),
        ("Risk Outcome", f"DILI: {dili.get('label')} | Lung: {lung.get('label')}", dili.get('score', 0) > 5 or lung.get('score', 0) > 5)
    ]
    
    chain_items = []
    for i, (label, val, active) in enumerate(steps):
        chain_items.append(Div(
            Div(cls=f"causal-node {'active' if active else ''}"),
            Div(
                Div(label, cls="text-[9px] font-black text-slate-400 uppercase tracking-tighter"),
                Div(val, cls="text-[11px] font-bold text-slate-700 truncate max-w-[180px]"),
                cls="ml-4"
            ),
            cls="flex items-center mb-6 relative z-10"
        ))
        if i < len(steps)-1:
            chain_items.append(Div(cls="causal-line absolute left-[5px] top-[12px] h-12 w-[2px] z-0"))

    return Div(
        _section_label("⛓️", "Mechanistic Causal Chain"),
        Div(*chain_items, cls="relative pl-2 mt-4"),
        cls="mb-4"
    )

def render_risk_gauge(title, res, max_score):
    if not res: return Div()
    score = res.get('score', 0)
    risk_level = res.get('label', 'Unknown')
    pct = min(int((score / max_score) * 100), 100) if max_score else 0

    color = "text-red-600" if risk_level == "High" else ("text-amber-500" if risk_level == "Moderate" else "text-emerald-600")
    bg = "bg-red-50" if risk_level == "High" else ("bg-amber-50" if risk_level == "Moderate" else "bg-emerald-50")
    border = "border-red-200" if risk_level == "High" else ("border-amber-200" if risk_level == "Moderate" else "border-emerald-200")
    bar_color = "bg-red-500" if risk_level == "High" else ("bg-amber-400" if risk_level == "Moderate" else "bg-emerald-500")

    return Div(
        Div(title, cls="text-[9px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2 text-center"),
        Div(
            Div(risk_level, cls=f"text-xl font-black {color}"),
            Div(f"{score}/{max_score}", cls="text-[10px] text-slate-400 mono"),
            cls=f"flex flex-col items-center justify-center w-36 h-20 rounded-2xl border-2 {border} {bg} mx-auto shadow-sm"
        ),
        # Progress bar
        Div(
            Div(cls=f"h-1 rounded-full {bar_color}", style=f"width: {pct}%"),
            cls="w-full bg-slate-100 rounded-full h-1 mt-2 overflow-hidden"
        ),
        cls="flex flex-col items-center"
    )

def render_identity_header(report):
    props = report.get("RDKit Properties", {})
    dili = report.get("DILI Risk", {})
    lung = report.get("Lung Injury Risk", {})

    badges = []
    for label, val, unit in [
        ("CID", report.get("CID", "N/A"), ""),
        ("MW", props.get("MW", "N/A"), "g/mol"),
        ("XLogP", props.get("XLogP", "N/A"), ""),
        ("TPSA", props.get("TPSA", "N/A"), "Å²"),
    ]:
        badges.append(
            Span(
                Span(label, cls="text-slate-400 mr-1"),
                Span(f"{val}", cls="text-blue-700 font-black"),
                Span(f" {unit}" if unit else "", cls="text-slate-400"),
                cls="bg-slate-50 px-3 py-1.5 rounded-lg text-[11px] border border-slate-100"
            )
        )

    mol_svg = predictor.generate_mol_svg(report.get("SMILES", ""))
    
    return Div(
        Div(
            H2(report.get("Name", "Compound Profile"), cls="text-3xl font-black text-slate-800 mb-1 tracking-tight"),
            Div(
                Span("PubChem Verified Identity", cls="text-[9px] font-black bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-widest mr-2"),
                Span(report.get("IUPAC Name", "N/A"), cls="text-[11px] text-slate-400 mono leading-relaxed"),
                cls="flex items-center mb-3"
            ),
            Div(
                Span("SMILES Structure Source", cls="text-[9px] font-black text-slate-300 uppercase tracking-wider mr-2"),
                Span(report.get("SMILES", "N/A"), cls="text-[10px] text-slate-500 mono break-all"),
                cls="mb-3 bg-slate-50/50 px-3 py-2 rounded-lg border border-slate-100"
            ),
            Div(*badges, cls="flex flex-wrap gap-2 mt-2"),
            cls="flex-1"
        ),
        # Molecular Visual
        Div(
            NotStr(mol_svg),
            cls="w-48 h-48 bg-slate-50/30 rounded-2xl flex items-center justify-center p-4 border border-slate-100"
        ) if mol_svg else Div(),
        Div(
            render_risk_gauge("Hepatic DILI Risk", dili, 20),
            render_risk_gauge("Pulmonary Risk", lung, 15),
            cls="flex gap-8 flex-shrink-0"
        ),
        cls="p-8 bg-white rounded-2xl shadow-sm border border-slate-100 mb-5 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 animate-fade-in"
    )

def render_descriptors(props):
    rows = [
        ("Molecular Weight",   f"{props.get('MW','N/A')} g/mol"),
        ("Exact Mass",         f"{props.get('Exact_Mass','N/A')}"),
        ("XLogP (Crippen)",    str(props.get('XLogP','N/A'))),
        ("Wildman-Crippen MR", str(props.get('Wildman_Crippen_MR','N/A'))),
        ("TPSA",               f"{props.get('TPSA','N/A')} Å²"),
        ("H-Bond Donors",      str(props.get('HBD','N/A'))),
        ("H-Bond Acceptors",   str(props.get('HBA','N/A'))),
        ("Rotatable Bonds",    str(props.get('RotBonds','N/A'))),
        ("Aromatic Rings",     str(props.get('AromaticRings','N/A'))),
        ("Total Ring Systems", str(props.get('TotalRings','N/A'))),
        ("Heavy Atoms",        str(props.get('HeavyAtomCount','N/A'))),
        ("Fsp3 (Saturation)",  str(props.get('Fsp3','N/A'))),
        ("Formal Charge",      str(props.get('FormalCharge','N/A'))),
        ("Stereocenters",      str(props.get('Stereocenters','N/A'))),
    ]
    
    violations = [v for v in props.get('Lipinski_Violations', []) if v]
    lipinski_status = "✅ Pass" if props.get('Lipinski_Pass') else f"❌ Fail ({len(violations)} Violations)"
    veber_status = "✅ Pass" if props.get('Veber_Pass') else "❌ Fail"
    ghose_status = "✅ Pass" if props.get('Ghose_Pass') else "❌ Fail"
    
    return Div(
        *[_kv(label, val) for label, val in rows],
        # Rule checks
        Div(
            Span("Lipinski Ro5", cls="text-slate-400 text-[11px] font-bold"),
            Span(lipinski_status, cls="text-[11px] font-black " + ("text-emerald-600" if props.get('Lipinski_Pass') else "text-red-600")),
            cls="flex justify-between py-2 mt-2 border-t border-slate-200"
        ),
        Div(
            *[P(v, cls="text-[10px] text-red-400 italic mono ml-4") for v in violations],
            cls="mt-1"
        ) if violations else Div(),
        Div(
            Span("Veber Rules", cls="text-slate-400 text-[11px] font-bold"),
            Span(veber_status, cls="text-[11px] font-black " + ("text-emerald-600" if props.get('Veber_Pass') else "text-red-600")),
            cls="flex justify-between py-2 border-t border-slate-100"
        ),
        Div(
            Span("Ghose Filter", cls="text-slate-400 text-[11px] font-bold"),
            Span(ghose_status, cls="text-[11px] font-black " + ("text-emerald-600" if props.get('Ghose_Pass') else "text-red-600")),
            cls="flex justify-between py-2 border-t border-slate-100"
        ),
        cls="bg-slate-50 border border-slate-100 p-5 rounded-xl mt-2"
    )

def render_alert_cards(alerts):
    real_alerts = [a for a in alerts if a['alert'] != 'None detected']
    if not real_alerts:
        return Div("✅ No structural toxicophores detected.", cls="p-4 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100 text-xs font-bold")

    cards = []
    for a in real_alerts:
        db = a.get('db_entry', {})
        sev = db.get('severity', 'Moderate')
        sev_color = "text-red-600 bg-red-50 border-red-100" if sev == "High" else "text-amber-600 bg-amber-50 border-amber-100"
        cards.append(Div(
            Div(
                Span(db.get('alert', a['alert']), cls="text-[11px] font-black text-slate-800 uppercase"),
                Span(sev, cls=f"text-[9px] font-black {sev_color} px-2 py-0.5 rounded border"),
                cls="flex justify-between items-center mb-3"
            ),
            Div(
                P(B("⚙ Mechanism: "), db.get('mechanism', a.get('reasoning', 'N/A')), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                P(B("🔬 Pathway: "), db.get('pathway', 'N/A'), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                P(B("💊 Metabolism: "), db.get('metabolism', 'N/A'), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                P(B("🏥 Clinical: "), db.get('consequence', 'N/A'), cls="text-[10px] text-slate-700 font-medium"),
            ),
            cls="p-4 bg-white rounded-xl border border-orange-100 border-l-4 border-l-orange-400 mb-3 shadow-sm"
        ))
    return Div(*cards)

def render_scoring_breakdown(factors, title, icon="•"):
    if not factors:
        return P(f"✅ No significant {title.lower()} risk factors.", cls="text-xs text-emerald-600 italic bg-emerald-50 p-3 rounded-lg")
    return Div(
        H4(title, cls="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-3"),
        *[Div(
            Span(icon, cls="text-slate-300 mr-2 flex-shrink-0"),
            Span(f, cls="text-[11px] text-slate-600 leading-relaxed"),
            cls="flex items-start py-2 border-b border-slate-50 last:border-0"
        ) for f in factors],
        cls="mb-5"
    )

def render_ae_table(faers_list):
    if not faers_list:
        return P("No FAERS signals found for this compound.", cls="text-xs text-slate-400 italic")

    header = Tr(
        Th("Adverse Event (MedDRA PT)", cls="text-left py-2.5 px-4 text-slate-400 text-[10px] uppercase tracking-wider"),
        Th("Reports", cls="text-right py-2.5 px-4 text-slate-400 text-[10px] uppercase tracking-wider"),
        cls="border-b border-slate-200"
    )
    rows = [header]
    for ae in faers_list:
        rows.append(Tr(
            Td(ae['term'], cls="py-2.5 px-4 text-[11px] text-slate-700 font-medium"),
            Td(str(ae['count']), cls="py-2.5 px-4 text-[11px] text-slate-500 text-right mono"),
            cls="border-b border-slate-50 hover:bg-slate-50/50"
        ))
    return Table(*rows, cls="w-full")

def render_target_bars(deepchem_data):
    if not deepchem_data or deepchem_data == "Prediction failed":
        return P("DeepChem prediction unavailable.", cls="text-slate-500 italic text-xs")

    preds = deepchem_data.get('predictions', {})
    if not preds:
        return P("No Tox21 predictions.", cls="text-slate-500 italic text-xs")

    featurizer = deepchem_data.get('featurizer', 'ECFP-1024')
    note = deepchem_data.get('note', '')

    sorted_targets = sorted(preds.items(), key=lambda x: x[1], reverse=True)

    bars = []
    for target, prob in sorted_targets:
        pct = int(prob * 100)
        bar_color = "bg-red-500" if pct > 50 else ("bg-amber-400" if pct > 35 else "bg-emerald-500")
        flag = "🔴" if pct > 50 else ("🟡" if pct > 35 else "🟢")
        bars.append(
            Div(
                Div(
                    Span(flag, cls="mr-1"),
                    Span(target, cls="text-[10px] font-bold text-slate-600 uppercase"),
                    cls="w-28 flex items-center truncate"
                ),
                Div(
                    Div(cls=f"h-2 rounded-full {bar_color} transition-all", style=f"width: {pct}%"),
                    cls="flex-1 bg-slate-100 rounded-full h-2 mx-3 overflow-hidden"
                ),
                Div(f"{prob:.2f}", cls="w-10 text-[10px] text-right text-slate-500 mono font-bold"),
                cls="flex items-center mb-2"
            )
        )

    return Div(
        *bars,
        Div(
            Span(f"Featurizer: {featurizer}", cls="mono text-[9px] text-slate-400"),
            Span(" • 🔴 >50% High  🟡 35–50% Mod  🟢 <35% Low", cls="text-[9px] text-slate-400 ml-2"),
            cls="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-1"
        ),
        P(note, cls="text-[9px] text-slate-400 italic mt-1") if note else Div(),
        cls="mt-1"
    )

def render_target_biology(enriched_targets):
    if not enriched_targets: return Div()
    cards = []
    for t in enriched_targets:
        cards.append(Div(
            Div(
                Span(f"{t['flag']} {t['full_name']}", cls="text-[11px] font-black text-slate-800 uppercase"),
                Span(f"{int(t['value']*100)}%", cls="text-xs font-black text-blue-600"),
                cls="flex justify-between items-center mb-2"
            ),
            Div(
                P(B("Function: "), t['function'], cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                P(B("If Hit: "), t['mechanism'], cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                P(B("Risk: "), t['consequence'], cls="text-[10px] text-slate-700 font-medium italic"),
                cls="bg-blue-50/30 p-3 rounded-xl border border-blue-100/50"
            ),
            cls="mb-4 last:mb-0"
        ))
    return Div(
        _section_label("🔬", "Top Target Biological Deep-Dive"),
        *cards
    )

def render_pubmed(pm):
    if not pm: return Div()
    total = pm.get('total', 0)
    tox_hits = pm.get('tox_hits', 0)
    density = pm.get('density', 0)
    return Div(
        _section_label("📚", "Literature & Methodology"),
        Div(
            Div(
                Div(str(total), cls="text-2xl font-black text-slate-800"),
                Div("Total Publications", cls="text-[9px] text-slate-400 uppercase tracking-wider mt-1"),
                cls="text-center flex-1"
            ),
            Div(
                Div(str(tox_hits), cls="text-2xl font-black text-amber-600"),
                Div("Toxicity Papers", cls="text-[9px] text-slate-400 uppercase tracking-wider mt-1"),
                cls="text-center flex-1"
            ),
            Div(
                Div(f"{density:.1f}%", cls="text-2xl font-black text-blue-600"),
                Div("Tox Literature Density", cls="text-[9px] text-slate-400 uppercase tracking-wider mt-1"),
                cls="text-center flex-1"
            ),
            cls="flex gap-4 p-4 bg-white border border-slate-100 rounded-xl shadow-sm mb-4"
        ),
        Div(
            P("🔬 Featurizer Methodology", cls="text-[10px] font-black text-slate-400 mb-2 uppercase"),
            Div("DeepChem Tox21 Pipeline executing ECFP-1024 fingerprints with 12 specific stress-response and nuclear-receptor centroids.", 
                cls="text-[10px] text-slate-500 font-medium leading-relaxed"),
            cls="p-4 bg-slate-50 rounded-xl border-t-2 border-slate-900"
        )
    )

def render_predicted_ae(ae_list):
    if not ae_list:
        return P("Insufficient structural/bioactivity data for predictive modeling.", cls="text-xs text-slate-400 italic")
    cards = []
    for ae in ae_list:
        conf = ae.get('confidence', 'Low')
        conf_color = "text-red-700" if conf == "High" else ("text-amber-700" if conf == "Medium" else "text-slate-500")
        conf_bg = "bg-red-50 border-red-100" if conf == "High" else ("bg-amber-50 border-amber-100" if conf == "Medium" else "bg-slate-50 border-slate-100")
        
        # New: Source Badges for Synthesis
        source = ae.get('source', 'Emerging Hazard')
        source_cls = "bg-blue-600 text-white" if source == "Confirmed Signal" else ("bg-amber-500 text-white" if source == "Emerging Hazard" else "bg-slate-500 text-white")
        
        organ = ae.get('organ', '')
        organ_icons = {"Liver": "🫀", "Kidney": "🫘", "Heart": "❤️", "Lung": "🫁", "Brain": "🧠", "Systemic": "🔬", "Immune System": "🛡️", "Endocrine System": "⚗️"}
        organ_icon = organ_icons.get(organ, "💊")

        evidence = ae.get('evidence_sources', [])
        mech_chain = ae.get('mechanism_chain', '')

        # Construct specific evidence badges based on the new backend keys
        evidence_badges = []
        for e in evidence:
            if "Structural" in e:
                badge_cls = "bg-orange-50 text-orange-600 border-orange-100"
            elif "Tox21" in e or "DeepChem" in e:
                badge_cls = "bg-purple-50 text-purple-600 border-purple-100"
            elif "FAERS" in e:
                badge_cls = "bg-emerald-50 text-emerald-600 border-emerald-100"
            else:
                badge_cls = "bg-slate-50 text-slate-500 border-slate-100"
            evidence_badges.append(Span(e, cls=f"text-[8px] px-1.5 py-0.5 rounded mr-1 font-bold border {badge_cls}"))

        cards.append(Div(
            Div(
                Span(f"{organ_icon} ", cls="mr-1"),
                Span(ae.get('term', 'Unknown Event'), cls="text-[11px] font-black text-slate-800 uppercase"),
                Span(source, cls=f"text-[7px] font-black {source_cls} px-1.5 py-0.5 rounded-sm ml-2 tracking-tighter uppercase"),
                Span(conf, cls=f"text-[9px] font-black {conf_color} {conf_bg} px-2 py-0.5 rounded border ml-auto"),
                cls="flex items-center mb-1.5"
            ),
            Div(
                Span(organ, cls="text-[9px] font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100 mr-2 shadow-sm"),
                *evidence_badges,
                cls="flex flex-wrap items-center gap-1 mb-2.5"
            ) if organ else Div(),
            P(ae.get('rationale', ''), cls="text-[10px] text-slate-600 leading-relaxed mb-3"),
            Div(
                Span("🔬 Mech-Logic Path: ", cls="text-[8px] font-black text-slate-400 uppercase mr-1"),
                Span(mech_chain, cls="text-[9px] text-slate-500 mono leading-relaxed italic"),
                cls="bg-slate-50/50 p-2.5 rounded-lg border border-slate-100/50"
            ) if mech_chain else Div(),
            cls="p-4 bg-white rounded-2xl border border-slate-100 mb-4 shadow-sm hover:border-blue-200 transition-all hover:shadow-md"
        ))
    return Div(*cards)

def render_ae_concordance(concordance_data):
    """Renders concordance gauge between predicted and real-world AEs with BioBERT semantics."""
    if not concordance_data:
        return Div()
    pct = concordance_data.get('concordance_pct', 0)
    matched = concordance_data.get('matched', [])
    unmatched_pred = concordance_data.get('unmatched_predicted', [])
    unmatched_faers = concordance_data.get('unmatched_faers', [])

    gauge_color = "bg-emerald-500" if pct >= 50 else ("bg-amber-400" if pct >= 25 else "bg-red-500")
    gauge_text = "text-emerald-600" if pct >= 50 else ("text-amber-600" if pct >= 25 else "text-red-600")
    gauge_label = "Strong" if pct >= 50 else ("Moderate" if pct >= 25 else "Low")

    match_items = []
    for m in matched:
        match_type = m.get('match_type', 'Keyword')
        match_badge = "bg-blue-600 text-white" if match_type == "Semantic" else "bg-slate-200 text-slate-600"
        
        match_items.append(Div(
            Span("✅", cls="mr-2 flex-shrink-0 mt-0.5"),
            Div(
                Div(
                    Span(m['predicted'], cls="text-[10px] font-black text-slate-800 uppercase"),
                    Span(" ↔ ", cls="text-[10px] text-slate-300 mx-1"),
                    Span(m['faers_confirmed'], cls="text-[10px] font-black text-blue-700 uppercase"),
                    cls="flex items-center"
                ),
                Div(
                    Span(m.get('organ', 'Systemic'), cls="text-[8px] font-black text-slate-400 uppercase mr-2 tracking-widest"),
                    Span(f"Match: {match_type}", cls=f"text-[7px] font-black px-1.5 py-0.5 rounded-full {match_badge} uppercase tracking-tighter mr-2"),
                    Span(f"({m.get('faers_count', 0)} clinical reports)", cls="text-[9px] text-slate-500 italic"),
                    cls="flex items-center mt-1"
                ),
            ),
            cls="flex items-start py-3 border-b border-slate-100 last:border-0 hover:bg-slate-50/50 rounded-lg transition-colors px-2"
        ))

    novel_items = []
    for u in unmatched_pred:
        novel_items.append(Div(
            Span("🔮", cls="mr-2 flex-shrink-0"),
            Div(
                Span(u.get('term', ''), cls="text-[10px] font-bold text-amber-700 uppercase"),
                Span(f"({u.get('organ', '')})", cls="text-[8px] font-black text-slate-400 uppercase ml-2 tracking-tighter"),
                cls="flex items-center"
            ),
            cls="flex items-center py-2 border-b border-slate-50 last:border-0 px-2"
        ))

    return Div(
        # Concordance Gauge
        Div(
            Div("Precision Safety Cross-Match (Tox21 vs FAERS)", cls="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-3"),
            Div(
                Div(
                    Div(f"{pct:.0f}%", cls=f"text-4xl font-black {gauge_text} tracking-tighter"),
                    Div(gauge_label, cls=f"text-[10px] font-black {gauge_text} uppercase tracking-widest"),
                    cls="text-center"
                ),
                cls="flex flex-col items-center mb-4"
            ),
            Div(
                Div(cls=f"h-2.5 rounded-full {gauge_color} shadow-sm transition-all duration-700", style=f"width: {pct}%"),
                cls="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden mb-2"
            ),
            P(f"BioBERT engine identified {len(matched)} semantic overlaps between predicted pathways and real-world outcomes.", cls="text-[9px] text-slate-500 italic text-center leading-relaxed"),
            cls="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm mb-5"
        ),
        # Matched AEs
        Div(
            Div("Validated Safety Signals (Semantic Concordance)", cls="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-3 flex items-center"),
            Div(*match_items, cls="space-y-1"),
            cls="p-5 bg-emerald-50/40 rounded-2xl border border-emerald-100 mb-4 shadow-sm"
        ) if match_items else Div(),
        # Novel Predictions
        Div(
            Div("Unreported Hazards (Prediction Only)", cls="text-[9px] font-black text-amber-600 uppercase tracking-widest mb-3"),
            Div(*novel_items, cls="space-y-1"),
            P("⚠️ These molecular hazards exhibit strong theoretical binding but haven't reached clinical reporting volume yet.", cls="text-[8px] text-amber-600/70 italic mt-3 bg-white/50 p-2 rounded border border-amber-100"),
            cls="p-5 bg-amber-50/40 rounded-2xl border border-amber-100 mb-4 shadow-sm"
        ) if novel_items else Div(),
    )

def render_organ_toxicity_dashboard(report):
    """5-organ risk gauge dashboard."""
    organs = [
        ("🫀", "Liver", report.get("DILI Risk", {}), 20),
        ("🫁", "Lung", report.get("Lung Injury Risk", {}), 20),
        ("🫘", "Kidney", report.get("Kidney Injury Risk", {}), 20),
        ("❤️", "Heart", report.get("Cardiac Risk", {}), 20),
        ("🧠", "Brain", report.get("Neuro Risk", {}), 20),
    ]
    gauges = []
    for icon, name, risk, max_score in organs:
        if not risk: continue
        score = risk.get('score', 0)
        label = risk.get('label', 'Low')
        pct = min(int((score / max_score) * 100), 100) if max_score else 0
        color = "text-red-600" if label == "High" else ("text-amber-500" if label == "Moderate" else "text-emerald-600")
        bg = "bg-red-50" if label == "High" else ("bg-amber-50" if label == "Moderate" else "bg-emerald-50")
        border = "border-red-200" if label == "High" else ("border-amber-200" if label == "Moderate" else "border-emerald-200")
        bar_color = "bg-red-500" if label == "High" else ("bg-amber-400" if label == "Moderate" else "bg-emerald-500")

        gauges.append(Div(
            Div(f"{icon}", cls="text-2xl mb-1 text-center"),
            Div(name, cls="text-[9px] font-black text-slate-400 uppercase tracking-[0.12em] mb-2 text-center"),
            Div(
                Div(label, cls=f"text-lg font-black {color}"),
                Div(f"{score}/{max_score}", cls="text-[10px] text-slate-400 mono"),
                cls=f"flex flex-col items-center justify-center w-full py-3 rounded-2xl border-2 {border} {bg} shadow-sm"
            ),
            Div(
                Div(cls=f"h-1.5 rounded-full {bar_color}", style=f"width: {pct}%"),
                cls="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden"
            ),
            cls="flex-1 min-w-[100px] flex flex-col items-center p-3"
        ))

    return Div(
        _section_label("🏥", "Multi-Organ Toxicity Dashboard"),
        Div(
            Div(*gauges, cls="flex flex-wrap justify-center gap-4 p-6"),
            # New Scoring Logic Section
            Div(
                Details(
                    Summary("View Scoring Methodology per Organ", cls="text-[10px] font-black text-slate-400 uppercase tracking-widest cursor-pointer hover:text-blue-500 transition-colors py-4 px-6 border-t border-slate-50 flex items-center justify-center"),
                    Div(
                        Div(
                            Div(
                                Div(B("🫀 Liver: "), "Alerts (40%) + SR-MMP/p53 (30%) + FAERS (20%) + High Lipophilicity (10%)", cls="mb-2"),
                                Div(B("🫁 Lung: "), "Alerts (50%) + DNA Damage/p53 (30%) + FAERS Respiratory (20%)", cls="mb-2"),
                                Div(B("🫘 Kidney: "), "Halogens/Aminoglycosides (40%) + OAT1/OCT2 (30%) + FAERS (20%) + MW Factor (10%)", cls="mb-2"),
                                Div(B("❤️ Heart: "), "hERG Binding (40%) + Ion Channels (30%) + FAERS (20%) + Polarity Balance (10%)", cls="mb-2"),
                                Div(B("🧠 Brain: "), "BBB Penetration (40%) + AChE/Aromatase (30%) + FAERS Neuro (30%)", cls="mb-0"),
                                cls="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 text-[9px] text-slate-500 leading-relaxed"
                            ),
                            cls="p-6 bg-slate-50/50 rounded-b-2xl border-t border-slate-100"
                        )
                    )
                ),
                cls="w-full"
            ),
            cls="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden"
        ),
        cls="mb-6"
    )

def render_mechanistic_causality(mech_report):
    """Renders per-organ causal chain diagrams with compound relationships."""
    if not mech_report:
        return Div()

    organ_sections = []
    for organ_key, data in mech_report.items():
        chains = data.get('causal_chains', [])
        if not chains: continue

        chain_cards = []
        for i, chain in enumerate(chains):
            sev = chain.get('severity', 'Moderate')
            sev_color = "border-l-red-500 bg-red-50/20" if sev == "High" else "border-l-amber-400 bg-amber-50/20"

            evidence_tags = []
            for t in chain.get('supporting_targets', [])[:3]:
                evidence_tags.append(Span(t, cls="text-[8px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded mr-1 mb-1"))
            for f in chain.get('faers_evidence', [])[:2]:
                evidence_tags.append(Span(f"FAERS: {f}", cls="text-[8px] text-emerald-500 bg-emerald-50 px-1.5 py-0.5 rounded mr-1 mb-1"))

            chain_cards.append(Div(
                Div(
                    Span(f"Chain {i+1}: ", cls="text-[9px] font-black text-slate-400"),
                    Span(chain['trigger'], cls="text-[11px] font-black text-slate-800 uppercase"),
                    Span(sev, cls=f"text-[8px] font-black ml-auto px-2 py-0.5 rounded {'text-red-600 bg-red-50 border border-red-100' if sev == 'High' else 'text-amber-600 bg-amber-50 border border-amber-100'}"),
                    cls="flex items-center mb-3"
                ),
                Div(
                    P(B("⚙ Metabolic Path: "), chain.get('metabolic_path', 'N/A'), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                    P(B("🔬 Mechanism: "), chain.get('mechanism', 'N/A'), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                    P(B("🧬 Pathway: "), chain.get('pathway_disrupted', 'N/A'), cls="text-[10px] text-slate-600 mb-1.5 leading-relaxed"),
                    P(B("🏥 Outcome: "), chain.get('clinical_outcome', 'N/A'), cls="text-[10px] text-slate-700 font-medium"),
                ),
                Div(*evidence_tags, cls="flex flex-wrap mt-3 pt-2 border-t border-slate-100") if evidence_tags else Div(),
                cls=f"p-4 rounded-xl border border-l-4 {sev_color} mb-3 shadow-sm"
            ))

        # Compound Relationships Summary
        rels = data.get('compound_relationships', [])
        rel_div = Div()
        if rels:
            rel_div = Div(
                Div("Compound → Mechanism → Pathway Relationships", cls="text-[9px] font-black text-slate-400 uppercase mb-2"),
                *[Div(Span("→ ", cls="text-blue-400 mr-1"), Span(r, cls="text-[10px] text-slate-600 mono"), cls="py-1.5 border-b border-slate-50 last:border-0 flex") for r in rels],
                cls="p-3 bg-slate-50/50 rounded-xl border border-slate-100 mt-3"
            )

        organ_sections.append(Div(
            Div(
                Span(data['icon'], cls="text-xl mr-2"),
                Span(data['name'], cls="text-[11px] font-black text-slate-700 uppercase tracking-widest"),
                Span(data['risk_label'], cls=f"ml-auto text-[9px] font-black px-2 py-0.5 rounded {'text-red-600 bg-red-50 border border-red-100' if data['risk_label'] == 'High' else ('text-amber-600 bg-amber-50 border border-amber-100' if data['risk_label'] == 'Moderate' else 'text-emerald-600 bg-emerald-50 border border-emerald-100')}"),
                cls="flex items-center mb-4 pb-3 border-b border-slate-200"
            ),
            # Simple Terms Clinical Synopsis
            Div(
                Div(
                    Span("📝 Clinical Synopsis (Simple Terms)", cls="text-[10px] font-black text-blue-600 uppercase tracking-wider mb-2 flex items-center"),
                    P(data.get('simple_explanation', 'No synopsis available.'), cls="text-[11px] text-slate-600 leading-relaxed"),
                    cls="p-4 bg-blue-50/40 rounded-xl border border-blue-100/50 mb-5"
                )
            ) if data.get('simple_explanation') else Div(),
            *chain_cards,
            rel_div,
            cls="p-5 bg-white rounded-2xl border border-slate-100 shadow-sm mb-5"
        ))

    if not organ_sections:
        return Div(P("No significant mechanistic causal chains identified.", cls="text-xs text-emerald-600 italic bg-emerald-50 p-4 rounded-xl"))

    return Div(
        _section_label("🔗", "Mechanistic Organ Causality Report"),
        P("Detailed compound → metabolite → organ damage chains with multi-source evidence.", cls="text-[10px] text-slate-400 italic mb-4"),
        *organ_sections,
    )

def render_dili_deep_dive(dili, lung):
    """Comprehensive DILI + Lung injury analysis with factor contribution bars."""
    if not dili and not lung:
        return Div()

    def _risk_section(title, icon, risk, max_score, color_hi, color_lo):
        if not risk:
            return Div()
        score = risk.get('score', 0)
        label = risk.get('label', 'Unknown')
        pct = min(int((score / max_score) * 100), 100) if max_score else 0
        bar_color = color_hi if label == "High" else ("bg-amber-400" if label == "Moderate" else color_lo)
        factors = risk.get('factors', [])

        factor_items = []
        for i, f in enumerate(factors):
            factor_items.append(Div(
                Span(f"F{i+1}", cls="text-[8px] font-black text-white bg-slate-400 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"),
                Span(f, cls="text-[10px] text-slate-600 leading-relaxed"),
                cls="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0"
            ))

        return Div(
            Div(
                Span(icon, cls="mr-2 text-lg"),
                Span(title, cls="text-[10px] font-black text-slate-500 uppercase tracking-widest"),
                cls="flex items-center mb-4"
            ),
            # Score display
            Div(
                Div(label, cls=f"text-2xl font-black {'text-red-600' if label == 'High' else ('text-amber-500' if label == 'Moderate' else 'text-emerald-600')}"),
                Div(f"Score: {score}/{max_score}", cls="text-[10px] text-slate-400 mono"),
                cls="text-center mb-3"
            ),
            Div(
                Div(cls=f"h-2.5 rounded-full {bar_color} transition-all", style=f"width: {pct}%"),
                cls="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden mb-5"
            ),
            # Factors
            Div(*factor_items, cls="mt-2") if factor_items else Div("No contributing factors detected.", cls="text-[10px] text-emerald-600 italic"),
            cls="p-5 bg-white rounded-xl border border-slate-100 shadow-sm mb-4"
        )

    return Div(
        _risk_section("Hepatic DILI Risk Analysis", "🫀", dili, 20, "bg-red-500", "bg-emerald-500"),
        _risk_section("Pulmonary Injury Risk Analysis", "🫁", lung, 15, "bg-red-500", "bg-emerald-500"),
    )

def render_drug_likeness(props):
    """Drug-likeness assessment panel with QED, SAS and multi-rule summary."""
    qed = props.get('QED')
    sas = props.get('SAS')

    # QED interpretation
    if qed is not None:
        qed_pct = int(qed * 100)
        qed_color = "bg-emerald-500" if qed >= 0.67 else ("bg-amber-400" if qed >= 0.35 else "bg-red-500")
        qed_label = "Favorable" if qed >= 0.67 else ("Moderate" if qed >= 0.35 else "Unfavorable")
        qed_text_color = "text-emerald-600" if qed >= 0.67 else ("text-amber-600" if qed >= 0.35 else "text-red-600")
    else:
        qed_pct, qed_color, qed_label, qed_text_color = 0, "bg-slate-300", "N/A", "text-slate-400"

    # SAS interpretation
    if sas is not None:
        sas_label = "Easy" if sas <= 4 else ("Moderate" if sas <= 6 else "Difficult")
        sas_color = "text-emerald-600" if sas <= 4 else ("text-amber-600" if sas <= 6 else "text-red-600")
    else:
        sas_label, sas_color = "N/A", "text-slate-400"

    rules = [
        ("Lipinski Ro5", props.get('Lipinski_Pass', False), "MW≤500, LogP≤5, HBD≤5, HBA≤10"),
        ("Veber Rules", props.get('Veber_Pass', False), "RotBonds≤10, TPSA≤140"),
        ("Ghose Filter", props.get('Ghose_Pass', False), "160≤MW≤480, -0.4≤LogP≤5.6"),
    ]

    return Div(
        # QED Score
        Div(
            Div("QED Score", cls="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-2"),
            Div(
                Div(f"{qed if qed is not None else 'N/A'}", cls=f"text-3xl font-black {qed_text_color}"),
                Div(qed_label, cls=f"text-[10px] font-black {qed_text_color} uppercase"),
                cls="text-center mb-3"
            ),
            Div(
                Div(cls=f"h-2 rounded-full {qed_color}", style=f"width: {qed_pct}%"),
                cls="w-full bg-slate-100 rounded-full h-2 overflow-hidden"
            ),
            P("Quantitative Estimate of Drug-likeness (0–1). Higher = more drug-like.", cls="text-[9px] text-slate-400 italic mt-2"),
            cls="p-4 bg-white rounded-xl border border-slate-100 shadow-sm mb-4"
        ),
        # SAS Score
        Div(
            Div("Synthetic Accessibility", cls="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-2"),
            Div(
                Div(f"{sas if sas is not None else 'N/A'}", cls=f"text-2xl font-black {sas_color}"),
                Div(f"({sas_label})", cls=f"text-[10px] font-black {sas_color}"),
                cls="text-center"
            ),
            P("SA Score (1–10). Lower = easier to synthesize.", cls="text-[9px] text-slate-400 italic mt-2"),
            cls="p-4 bg-white rounded-xl border border-slate-100 shadow-sm mb-4"
        ),
        # Rule Summary Table
        Div(
            Div("Drug-Likeness Rule Assessment", cls="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-3"),
            *[Div(
                Span(name, cls="text-[11px] font-bold text-slate-600"),
                Span("✅ Pass" if passed else "❌ Fail", cls="text-[10px] font-black " + ("text-emerald-600" if passed else "text-red-600")),
                P(desc, cls="text-[9px] text-slate-400 italic mt-0.5") if not passed else Div(),
                cls="flex flex-wrap justify-between items-center py-2 border-b border-slate-50 last:border-0"
            ) for name, passed, desc in rules],
            cls="p-4 bg-white rounded-xl border border-slate-100 shadow-sm"
        ),
    )

def render_methodology():
    return Div(
        _section_label("📖", "Pharma-Grade Methodology & Science Documentation"),
        Details(
            Summary("Core AI Model Architecture (DeepChem Tox21)", cls="text-[11px] font-bold text-slate-600 hover:text-blue-600 py-2"),
            Div(
                P("The platform utilizes a DeepChem-based Multitask Neural Network for high-throughput toxicity screening:", cls="mb-3"),
                Ul(
                    Li(B("Base Model: "), "MultitaskClassifier (DNN) trained on the NIH Tox21 dataset."),
                    Li(B("Featurization: "), "1024-bit Extended Connectivity Fingerprints (ECFP4) representing localized atomic environments with a radius of 2."),
                    Li(B("Architecture: "), "Deep MLP with dropout (0.25) and ReLU activation, optimized for 12 distinct bio-target outcomes (SR-MMP, SR-p53, etc.)."),
                    Li(B("Validation: "), "Model performance is benchmarked at ROC-AUC ~0.84 for most targets."),
                    cls="list-disc pl-4 space-y-2"
                ),
                cls="text-[10px] text-slate-500 p-5 bg-slate-50 rounded-xl border border-slate-100 mt-2"
            ),
            cls="border-b border-slate-100"
        ),
        Details(
            Summary("Multi-Factor Organ Toxicity Math (Weighting Logic)", cls="text-[11px] font-bold text-slate-600 hover:text-blue-600 py-2"),
            Div(
                P("Total Risk scores (e.g., 0-20 for Liver) are calculated via a deterministic weighted sum of evidence sources:", cls="mb-4"),
                Div(
                    Div(
                        Span("🫀 Hepatic (DILI):", cls="font-black text-blue-700 mr-2"),
                        Span("Structural High (3pt/ea) + Tox21 Mitochondrial/p53 (4pt/ea) + FAERS Clinical (3pt) + Physicochemical (1pt).", cls="text-slate-500"),
                        cls="mb-3 py-2 border-b border-slate-200/50"
                    ),
                    Div(
                        Span("🫁 Pulmonary:", cls="font-black text-blue-700 mr-2"),
                        Span("Respiratory Alerts (5pt/ea) + Tox21 ARE/HSE (3pt/ea) + FAERS Respiratory Signals (3pt).", cls="text-slate-500"),
                        cls="mb-3 py-2 border-b border-slate-200/50"
                    ),
                    Div(
                        Span("🫘 Renal:", cls="font-black text-blue-700 mr-2"),
                        Span("OAT/OCT Transporter Alerts (4pt/ea) + Tox21 ARE/MMP (3pt/ea) + FAERS Renal Signals (2pt) + MW Factor (1pt).", cls="text-slate-500"),
                        cls="mb-3 py-2 border-b border-slate-200/50"
                    ),
                    Div(
                        Span("❤️ Cardiac:", cls="font-black text-blue-700 mr-2"),
                        Span("hERG Binding DNN (4pt) + Ion Channel Alerts (3pt/ea) + FAERS Cardiac Events (3pt) + Polarity (1pt).", cls="text-slate-500"),
                        cls="mb-3 py-2 border-b border-slate-200/50"
                    ),
                    Div(
                        Span("🧠 Neuro:", cls="font-black text-blue-700 mr-2"),
                        Span("BBB Penetration Probability (3pt) + Tox21 AhR/HSE (4pt/ea) + FAERS Neuro Records (3pt).", cls="text-slate-500"),
                        cls="py-2"
                    ),
                    cls="text-[9px] leading-relaxed"
                ),
                cls="p-5 bg-blue-50/30 rounded-xl"
            ),
            cls="border-b border-slate-100"
        ),
        Details(
            Summary("Adv. Adverse Event Synthesis (AE Sync Engine)", cls="text-[11px] font-bold text-slate-600 hover:text-blue-600 py-2"),
            Div(
                P("The platform bridges the gap between AI hazards and FAERS observations using a Semantic Synthesis Loop:", cls="mb-2 font-black"),
                Ul(
                    Li(B("Confirmed Signal: "), "Mechanistic AI hazard matched against a real-world clinical MedDRA term found in FAERS."),
                    Li(B("Emerging Hazard: "), "A structural/binding risk identified by the AI but not yet showing high signal in post-market data."),
                    Li(B("Clinical Observation: "), "A high-frequency FAERS signal that has no known structural toxicophore, necessitating closer mechanistic review."),
                    cls="list-decimal pl-4 space-y-1"
                ),
                cls="text-[10px] text-slate-500 p-4 bg-slate-50 rounded-xl mt-2"
            ),
            cls="border-b border-slate-100"
        ),
        cls="mt-2"
    )

def render_data_sources():
    sources = [
        ("PubChem", "Live API", "bg-emerald-100 text-emerald-700 border-emerald-200"),
        ("openFDA FAERS", "Live API", "bg-emerald-100 text-emerald-700 border-emerald-200"),
        ("NCBI PubMed", "Live API", "bg-emerald-100 text-emerald-700 border-emerald-200"),
        ("RDKit BRENK/PAINS", "Local", "bg-amber-100 text-amber-700 border-amber-200"),
        ("DeepChem Tox21", "Local", "bg-amber-100 text-amber-700 border-amber-200"),
        ("Azure OpenAI", "Summary Only", "bg-indigo-100 text-indigo-700 border-indigo-200"),
    ]
    items = []
    for name, label, cls_str in sources:
        items.append(Div(
            Span(name, cls="text-[11px] text-slate-600"),
            Span(label, cls=f"text-[9px] font-black px-2 py-0.5 rounded-full border {cls_str}"),
            cls="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0"
        ))
    return Div(
        *items,
        Div("All risk scoring is deterministic. GPT provides narrative summary only.", cls="text-[9px] text-slate-400 italic mt-3 pt-2 border-t border-slate-100"),
        cls="bg-slate-50/50 p-4 rounded-xl border border-slate-100"
    )

def render_multi_risk_chart(reports):
    """Comparative bar chart for DILI and Pulmonary risk scores."""
    bars = []
    for r in reports:
        dili = r.get("DILI Risk", {}).get("score", 0)
        lung = r.get("Lung Injury Risk", {}).get("score", 0)
        
        # Max scores for percentage calculation
        d_pct = min(int((dili / 20) * 100), 100)
        l_pct = min(int((lung / 15) * 100), 100)
        
        bars.append(Div(
            Div(r.get('Name'), cls="text-[10px] font-black text-slate-500 uppercase mb-3 text-center truncate w-full"),
            # DILI Bar
            Div(
                Div(f"DILI: {dili}", cls="text-[8px] font-black text-red-700 uppercase mb-1"),
                Div(Div(cls="h-2 bg-red-500 rounded-full", style=f"width: {d_pct}%"), cls="w-full bg-red-50 rounded-full h-2 overflow-hidden"),
                cls="mb-3"
            ),
            # Lung Bar
            Div(
                Div(f"Lung: {lung}", cls="text-[8px] font-black text-emerald-700 uppercase mb-1"),
                Div(Div(cls="h-2 bg-emerald-500 rounded-full", style=f"width: {l_pct}%"), cls="w-full bg-emerald-50 rounded-full h-2 overflow-hidden"),
            ),
            cls="flex-1 min-w-[120px] p-4 bg-white rounded-2xl border border-slate-100 shadow-sm"
        ))
        
    return Div(
        _section_label("📊", "Comparative Risk Analytics"),
        Div(*bars, cls="flex flex-wrap gap-4 mt-4"),
        cls="mb-10"
    )

def render_multi_radar_chart(reports):
    """SVG-based Radar Chart overlaying binding profiles for multiple drugs."""
    targets = ["NR-AR", "NR-AhR", "NR-ER", "SR-ARE", "SR-MMP", "SR-p53"]
    colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
    
    # SVG Constants
    size = 300
    center = size / 2
    radius = 100
    
    # Helper to get polygon points
    # Helper to get polygon points
    def get_points(report, r_val):
        pts = []
        deepchem_data = report.get("DeepChem Prediction", {})
        # Robustly handle cases where DeepChem might have returned an 'error' or empty structure
        if not isinstance(deepchem_data, dict):
            preds = {}
        else:
            preds = deepchem_data.get("predictions", {})
            
        for i, t in enumerate(targets):
            # If target missing, use a tiny baseline 0.05 to avoid collapsing the polygon to a single point
            val = float(preds.get(t, 0.05))
            angle = (i / len(targets)) * 2 * 3.14159 - 1.5708
            x = center + radius * val * math.cos(angle)
            y = center + radius * val * math.sin(angle)
            pts.append(f"{x},{y}")
        return " ".join(pts)

    # 1. Background Circles & Axes
    bg_elements = []
    for r in [0.25, 0.5, 0.75, 1.0]:
        bg_elements.append(f'<circle cx="{center}" cy="{center}" r="{radius*r}" fill="none" stroke="#e2e8f0" stroke-width="0.5" />')
    
    # 2. Drug Polygons
    polygons = []
    legends = []
    import math # Ensure math is available
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
    for i, r in enumerate(reports):
        color = colors[i % len(colors)]
        pts = get_points(r, radius)
        # Added a glow-like effect for multiple drugs
        polygons.append(f"""
            <polygon points="{pts}" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="2.5" />
            <polygon points="{pts}" fill="none" stroke="{color}" stroke-width="1" stroke-dasharray="2,2" opacity="0.4" />
        """)
        legends.append(Div(Span(cls=f"w-3 h-3 rounded-full mr-2", style=f"background-color: {color}"), Span(r.get('Name'), cls="text-[10px] font-bold text-slate-600"), cls="flex items-center mr-4 mb-2"))

    # 3. Label text
    labels = []
    for i, t in enumerate(targets):
        angle = (i / len(targets)) * 2 * 3.14159 - 1.5708
        x = center + (radius + 28) * math.cos(angle)
        y = center + (radius + 28) * math.sin(angle)
        # Smart text alignment
        anchor = "middle"
        if math.cos(angle) > 0.2: anchor = "start"
        elif math.cos(angle) < -0.2: anchor = "end"
        labels.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="monospace" font-weight="900" font-size="9" fill="#94a3b8">{t}</text>')

    svg_content = f"""
    <svg viewBox="0 0 {size} {size}" class="w-full max-w-[400px] mx-auto overflow-visible">
        <defs>
            <radialGradient id="radar-glow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.05"/>
                <stop offset="100%" stop-color="transparent" stop-opacity="0"/>
            </radialGradient>
        </defs>
        <circle cx="{center}" cy="{center}" r="{radius}" fill="url(#radar-glow)" />
        {''.join(bg_elements)}
        {''.join(polygons)}
        {''.join(labels)}
    </svg>
    """
    
    return Div(
        _section_label("🕸️", "Target Binding Fingerprint (Tox21 Radar)"),
        Div(
            Div(NotStr(svg_content), cls="flex-1"),
            Div(*legends, cls="flex flex-wrap lg:flex-col lg:justify-center mt-6 lg:mt-0 lg:ml-10 min-w-[150px]"),
            cls="flex flex-col lg:flex-row items-center justify-center p-8 bg-white rounded-3xl border border-slate-100 shadow-sm"
        ),
        cls="mb-10"
    )

def render_structure_grid(reports):
    """Side-by-side 2D structure visualizations for the comparison batch."""
    cards = []
    for r in reports:
        svg = predictor.generate_mol_svg(r.get('SMILES', ''))
        cards.append(Div(
            Div(NotStr(svg), cls="w-full aspect-square flex items-center justify-center p-4"),
            Div(r.get('Name'), cls="text-center text-xs font-black text-slate-800 uppercase py-3 border-t border-slate-100 truncate px-2 bg-slate-50/50"),
            cls="flex-1 min-w-[180px] bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden transition-all hover:scale-[1.02] hover:shadow-md"
        ))
    return Div(
        _section_label("💠", "Molecular Comparative Structures"),
        Div(*cards, cls="flex flex-wrap gap-4 mt-4"),
        cls="mb-10"
    )

def render_single_view(report):
    props = report.get("RDKit Properties", {})
    dili = report.get("DILI Risk", {})
    lung = report.get("Lung Injury Risk", {})
    pred_ae = report.get("Predicted AE", [])
    target_bio = report.get("Top Targets Biology", [])
    pm = report.get("PubMed Confidence", {})
    ae_conc = report.get("AE Concordance", {})
    mech_report = report.get("Organ Mechanistic Report", {})

    report_link = A("📄 Full Research Dossier", href=f"/report/0", target="_blank", 
                   cls="mb-4 inline-block px-4 py-2 bg-slate-50 text-blue-600 font-black text-[10px] rounded-lg border border-blue-100 hover:bg-blue-50 transition-colors uppercase tracking-widest")

    return Div(
        render_identity_header(report),
        report_link,
        # FULL-WIDTH: Multi-Organ Toxicity Dashboard
        render_organ_toxicity_dashboard(report),
        Div(
            # COLUMN 1: MECHANISTIC NARRATIVE & IDENTITY
            Div(
                _card("🔬", "Mechanistic Safety Case (PhD Analysis)",
                    Div(report.get("Expert Summary", "Analysis pending..."), cls="text-[12px] text-slate-700 leading-relaxed font-serif whitespace-pre-wrap select-text mb-6"),
                    render_causal_chain(report),
                    border_color="border-blue-200/50 shadow-blue-50/50"
                ),
                _card("🔬", "PubChem Identity Metadata", 
                    Div(
                        Div(Span("Verified Common Name", cls="text-[9px] text-slate-400 uppercase"), P(report.get('Name'), cls="text-xs font-black text-blue-700"), cls="mb-3"),
                        Div(Span("PubChem CID", cls="text-[9px] text-slate-400 uppercase"), P(str(report.get('PubChem CID', 'N/A')), cls="text-xs font-black text-slate-800 mono"), cls="mb-3"),
                        Div(Span("IUPAC Name", cls="text-[9px] text-slate-400 uppercase"), P(report.get('IUPAC Name', 'N/A'), cls="text-[10px] text-slate-600 mono leading-tight"), cls="mb-3"),
                        A("View in PubChem ↗", href=f"https://pubchem.ncbi.nlm.nih.gov/compound/{report.get('PubChem CID')}", target="_blank", cls="text-[9px] font-black text-blue-600 hover:underline")
                    )
                ),
                _card("📊", "Literature Evidence (PubMed)", render_pubmed(pm)),
                cls="flex flex-col"
            ),
            # COLUMN 2: TOXICOLOGICAL HAZARDS
            Div(
                _card("⚠️", "Toxicophore Fingerprinting (BRENK/PAINS)", render_alert_cards(report.get("Structural Alerts", [])), border_color="border-orange-200/50"),
                _card("🧬", "DILI & Pulmonary Multi-Factor Analysis", render_dili_deep_dive(dili, lung), border_color="border-red-200/50"),
                _card("🏥", "Real-World Evidence (FDA FAERS)", render_ae_table(report.get("FAERS Top 5", []))),
                _card("📊", "AE Prediction Concordance (Predicted vs FAERS)", render_ae_concordance(ae_conc)),
                cls="flex flex-col"
            ),
            # COLUMN 3: PROPERTIES & PREDICTIONS
            Div(
                _card("🔮", "Clinical Outcome Predictions (Organ-Aware AI)", render_predicted_ae(pred_ae)),
                _card("💊", "Drug-Likeness Assessment (Cheminformatics)", render_drug_likeness(props), render_descriptors(props)),
                _card("🧠", "Bio-Target Profiling (Tox21/DeepChem)", render_target_bars(report.get("DeepChem Prediction")), render_target_biology(target_bio)),
                _card("🔌", "Data Lineage & Methodology", render_data_sources(), render_methodology()),
                cls="flex flex-col"
            ),
            cls="grid grid-cols-1 lg:grid-cols-3 gap-6"
        ),
        # FULL-WIDTH: Mechanistic Organ Causality Report
        _card("🔗", "Mechanistic Organ Causality Report",
            render_mechanistic_causality(mech_report),
            border_color="border-indigo-200/50"
        ),
        cls="animate-fade-in"
    )

def render_comparison_view(batch_result):
    reports = batch_result.get("reports", [])
    dossier = batch_result.get("summary", {})
    overview = dossier.get("overview", "Comparative analysis complete.")
    synergy_text = dossier.get("synergy", "")
    drug_dossiers = {d['name']: d['rationale'] for d in dossier.get('dossiers', [])}

    if not reports: return Div("No results.", cls="p-10 text-slate-400")

    # Top Identity Row (PubChem Source)
    identity_chips = []
    for r in reports:
        cid = r.get("PubChem CID", "N/A")
        name = r.get("Name", "Unknown")
        identity_chips.append(Div(
            Span(name, cls="text-[12px] font-black text-slate-800"),
            A(f" CID:{cid}", href=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid != "N/A" else "#", target="_blank", 
              cls="text-[9px] font-black text-blue-500 hover:underline border-l border-slate-200 ml-2 pl-2"),
            cls="flex items-center bg-white px-4 py-2 rounded-full border border-slate-100 shadow-sm transition-all hover:border-blue-200"
        ))

    search_header = Div(
        H2("Comparative Analysis Result", cls="text-sm font-black text-slate-400 uppercase tracking-widest"),
        H1(", ".join([r.get('Name') for r in reports]), cls="text-4xl font-black text-slate-900 mt-2 mb-6 tracking-tight"),
        Div(*identity_chips, cls="flex flex-wrap gap-3 mb-10"),
        cls="mb-10"
    )

    report_links = [A(f"📄 Full Research Dossier: {r.get('Name')}", href=f"/report/{i}", target="_blank", cls="text-[10px] text-blue-600 font-black uppercase hover:underline mr-4") for i, r in enumerate(reports)]

    synergy_cards = []
    if synergy_text and synergy_text != "N/A":
        synergy_cards.append(Div(
            Div(Span("🧬 Predicted Synergy & Combined Hazards", cls="text-[10px] font-black text-amber-700 uppercase tracking-widest"), cls="mb-3"),
            P(synergy_text, cls="text-[11px] text-amber-800 leading-relaxed italic"),
            cls="p-5 bg-amber-50 rounded-xl border border-amber-200 mb-6 shadow-sm"
        ))

    # Evidence Cards for each drug (High Density matching Single View)
    detailed_dossiers = []
    for r in reports:
        dili = r.get("DILI Risk", {})
        lung = r.get("Lung Injury Risk", {})
        props = r.get("RDKit Properties", {})
        pred_ae = r.get("Predicted AE", [])
        target_bio = r.get("Top Targets Biology", [])
        ae_conc = r.get("AE Concordance", {})
        
        detailed_dossiers.append(Div(
            H3(f"Detailed Safety Dossier: {r.get('Name')}", cls="text-xl font-black text-slate-800 mb-6 pb-2 border-b-2 border-slate-900 inline-block uppercase tracking-tighter"),
            # Multi-Organ Dashboard (Full Width)
            render_organ_toxicity_dashboard(r),
            Div(
                # Row 1: AI Case + Structural
                Div(
                    _card("🔬", "Mechanistic Case", 
                        P(drug_dossiers.get(r.get('Name'), ""), cls="text-[12px] text-slate-700 leading-relaxed font-serif"),
                        render_causal_chain(r)
                    ),
                    _card("⚠️", "Structural Risks", render_alert_cards(r.get("Structural Alerts", []))),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-6"
                ),
                # Row 2: Deep DILI + Target Bio
                Div(
                    _card("🧬", "DILI & Pulmonary Deep-Dive", render_dili_deep_dive(dili, lung)),
                    _card("🧠", "Target Biological Reasoning", render_target_biology(target_bio)),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-6"
                ),
                # Row 3: Targets + AEs + Concordance
                Div(
                    _card("🧠", "Target Binding Profile", render_target_bars(r.get("DeepChem Prediction"))),
                    _card("🔮", "Predicted Clinical AEs (Organ-Aware)", render_predicted_ae(pred_ae)),
                    _card("📊", "AE Concordance", render_ae_concordance(ae_conc)),
                    cls="grid grid-cols-1 lg:grid-cols-3 gap-6"
                ),
            ),
            cls="mb-16 p-10 bg-slate-50/50 rounded-[2.5rem] border border-slate-100 shadow-sm"
        ))

    matrix_rows = []
    # Structural Row at top of matrix
    matrix_rows.append(Tr(
        Th("Structure", cls="text-left py-4 px-6 bg-slate-50 text-slate-400 text-[9px] font-black uppercase tracking-widest"),
        *[Td(NotStr(predictor.generate_mol_svg(r.get('SMILES', ''))), cls="text-center py-4 px-6 bg-white border-b border-slate-100 flex items-center justify-center h-48") for r in reports],
    ))
    matrix_rows.append(Tr(
        Th("Molecular Property", cls="text-left py-4 px-6 bg-slate-50 text-slate-400 text-[9px] font-black uppercase tracking-widest"),
        *[Th(r.get('Name'), cls="text-center py-4 px-6 bg-slate-900 text-white font-black text-[11px]") for r in reports],
    ))

    def add_row(label, values):
        matrix_rows.append(Tr(
            Td(label, cls="py-3 px-5 font-bold text-slate-600 text-[11px] border-b border-slate-100 bg-slate-50/30"),
            *[Td(v, cls="py-3 px-5 text-center text-[11px] border-b border-slate-100") for v in values],
        ))

    def get_val(r, *keys, default="N/A"):
        curr = r
        for k in keys:
            if isinstance(curr, dict): curr = curr.get(k, {})
            else: return default
        return curr if curr and curr != {} else default

    # Extended Comparison Matrix (Pharma-Grade)
    add_row("Identity (CID)", [str(get_val(r, 'PubChem CID', default="N/A")) for r in reports])
    add_row("Molecular Weight", [f"{get_val(r, 'RDKit Properties', 'MW', default=0)} g/mol" for r in reports])
    add_row("XLogP (Aqueous)", [str(get_val(r, 'RDKit Properties', 'XLogP')) for r in reports])
    add_row("TPSA (Polarity)", [f"{get_val(r, 'RDKit Properties', 'TPSA')} Å²" for r in reports])
    add_row("QED (Drug-Likeness)", [Div(Span(f"{get_val(r, 'RDKit Properties', 'QED')}", cls="font-black text-blue-600"), cls="bg-blue-50 py-1 rounded") for r in reports])
    add_row("SAS (Accessibility)", [str(get_val(r, 'RDKit Properties', 'SAS')) for r in reports])
    add_row("Lipinski Ro5", ["✅ Pass" if get_val(r, 'RDKit Properties', 'Lipinski_Pass') else "❌ Fail" for r in reports])
    add_row("Veber Rule Pass", ["✅ Pass" if get_val(r, 'RDKit Properties', 'Veber_Pass') else "❌ Fail" for r in reports])
    add_row("Ghose Filter Pass", ["✅ Pass" if get_val(r, 'RDKit Properties', 'Ghose_Pass') else "❌ Fail" for r in reports])
    add_row("Formal Charge", [str(get_val(r, 'RDKit Properties', 'FormalCharge')) for r in reports])
    add_row("Hepatic DILI Level", [_badge(get_val(r, 'DILI Risk', 'label')) for r in reports])
    add_row("Hepatic DILI Score", [f"{get_val(r, 'DILI Risk', 'score', default=0)}/20" for r in reports])
    add_row("Pulmonary Risk", [_badge(get_val(r, 'Lung Injury Risk', 'label')) for r in reports])
    add_row("Kidney Risk", [_badge(get_val(r, 'Kidney Injury Risk', 'label')) for r in reports])
    add_row("Cardiac Risk", [_badge(get_val(r, 'Cardiac Risk', 'label')) for r in reports])
    add_row("Neuro Risk", [_badge(get_val(r, 'Neuro Risk', 'label')) for r in reports])
    add_row("AE Concordance", [Div(Span(f"{get_val(r, 'AE Concordance', 'concordance_pct', default=0)}%", cls="font-black text-blue-600"), cls="bg-blue-50 py-1 rounded") for r in reports])
    add_row("Toxicophores Count", [str(len([a for a in get_val(r, 'Structural Alerts', default=[]) if a.get('alert') != 'None detected'])) for r in reports])
    
    # Tox21 Target
    target_names = []
    for r in reports:
        preds = get_val(r, 'DeepChem Prediction', 'predictions', default={})
        if isinstance(preds, dict) and preds:
            top_t = sorted(preds.items(), key=lambda x:x[1], reverse=True)[0]
            target_names.append(f"{top_t[0]} ({int(top_t[1]*100)}%)")
        else:
            target_names.append("N/A")
    add_row("Primary Bio-Target", target_names)
    
    # FAERS AE
    faers_aes = []
    for r in reports:
        faers = get_val(r, 'FAERS Top 5', default=[])
        if faers and isinstance(faers, list):
            faers_aes.append(faers[0]['term'])
        else:
            faers_aes.append("None")
    add_row("Top Clinical AE", faers_aes)
    
    add_row("PubMed Tox Density", [f"{get_val(r, 'PubMed Confidence', 'density', default=0)}%" for r in reports])

    return Div(
        search_header,
        render_structure_grid(reports),
        render_multi_radar_chart(reports),
        render_multi_risk_chart(reports),
        H2("⚖️ Multi-Drug Safety Comparative Matrix", cls="text-2xl font-black text-slate-800 mb-5"),
        Div(Table(*matrix_rows, cls="w-full border-collapse rounded-xl overflow-hidden shadow-sm border border-slate-100"), cls="mb-12 overflow-x-auto"),
        _section_label("🤖", "Executive Synthesis Dashboard"),
        Div(Div(*report_links, cls="mb-4"), P(overview, cls="text-[12px] text-slate-700 leading-relaxed italic border-l-4 border-blue-500 pl-6 bg-blue-50/20 p-5 rounded-r-xl"), cls="mb-6 p-6 bg-white rounded-2xl shadow-sm border border-blue-100"),
        Div(*synergy_cards, cls="mb-8"),
        
        # Enhanced Detailed Dossiers in Comparison
        *detailed_dossiers,
        
        cls="animate-fade-in"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@rt("/report/{idx}")
def get_report(idx: int, session):
    res = session.get('last_multi_results') if session.get('current_tab') == 'multi' else session.get('last_result')
    if not res: return Div("Expired.", cls="p-10")
    data = res[idx] if isinstance(res, list) else res
    return Div(H3(f"Dossier: {data.get('Name')}", cls="font-black mb-4"), Pre(predictor.generate_plain_text_report(data), cls="bg-white p-6 rounded border mono text-[10px]"), cls="p-10 bg-slate-50")

def render_single_tab(active=True, **kwargs):
    cls = "flex-1 py-4 text-center font-black text-[12px] uppercase tracking-widest transition-all "
    cls += "text-blue-600 border-b-2 border-blue-600 bg-blue-50/30" if active else "text-slate-400 hover:text-slate-600 border-b-2 border-transparent"
    return A("Single Compound Intelligence", hx_get="/switch_tab?tab=single", hx_target="#main-workspace", hx_indicator="#loading-overlay", cls=cls, id="tab-single", **kwargs)

def render_multi_tab(active=False, **kwargs):
    cls = "flex-1 py-4 text-center font-black text-[12px] uppercase tracking-widest transition-all "
    cls += "text-pink-600 border-b-2 border-pink-600 bg-pink-50/30" if active else "text-slate-400 hover:text-slate-600 border-b-2 border-transparent"
    return A("Comparative Safety Dossier", hx_get="/switch_tab?tab=multi", hx_target="#main-workspace", hx_indicator="#loading-overlay", cls=cls, id="tab-multi", **kwargs)

def render_single_input():
    return Div(
        _section_label("🧪", "Clinical Compound Intelligence"),
        Form(
            Div(
                Input(name="smiles", placeholder="Enter Clinical Drug Name (e.g. Aspirin, Tylenol, Belinostat) or SMILES", 
                      cls="flex-1 bg-transparent border-none text-slate-800 placeholder-slate-300 font-mono text-[13px] focus:ring-0"),
                Button(
                    Span("Analyze Compound", cls="mr-2"), 
                    "🧬", 
                    cls="bg-blue-600 hover:bg-blue-700 text-white font-black px-8 py-3 rounded-xl transition-all shadow-lg shadow-blue-200 flex items-center"
                ),
                cls="flex items-center gap-4 bg-white p-3 rounded-2xl border border-slate-100 shadow-sm focus-within:border-blue-300 focus-within:ring-4 focus-within:ring-blue-50"
            ),
            hx_post="/analyze?mode=single", hx_target="#results-area", hx_indicator="#loading-overlay",
            cls="mt-6"
        ),
        cls="mb-10 px-6 py-8 bg-slate-50/50 rounded-3xl border border-dashed border-slate-200"
    )

def render_multi_input():
    return Div(
        _section_label("⚖️", "Comparative Clinical Safety Dossier"),
        Form(
            Textarea(name="smiles_list", placeholder="Enter Multiple Clinical Drug Names (e.g. Aspirin, Caffeine, Belinostat, Ibuprofen)...", 
                     cls="w-full h-32 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-slate-800 placeholder-slate-300 font-mono text-[13px] focus:ring-4 focus:ring-pink-50 focus:border-pink-300 transition-all resize-none mb-4"),
            Button(
                Span("Generate Comparative Safety Dossier", cls="mr-2"), 
                "📊", 
                cls="w-full bg-pink-600 hover:bg-pink-700 text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-pink-200 flex items-center justify-center"
            ),
            hx_post="/analyze?mode=multi", hx_target="#results-area", hx_indicator="#loading-overlay",
            cls="mt-6"
        ),
        cls="mb-10 px-6 py-8 bg-slate-50/50 rounded-3xl border border-dashed border-slate-200"
    )

@rt("/")
def get(session):
    if 'current_tab' not in session: session['current_tab'] = 'single'
    tab = session['current_tab']
    
    # Results retrieval
    results_html = Div(id="results-area")
    if tab == 'single' and 'last_result' in session:
        results_html = Div(render_single_view(session['last_result']), id="results-area")
    elif tab == 'multi' and 'last_multi_results' in session:
        results_html = Div(render_comparison_view(session['last_multi_results']), id="results-area")

    return Title("Toxicity Prediction Safety • Pharma-Grade Cheminformatics"), Main(
        Header(
            Div(
                Div(
                    Div(cls="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-xl shadow-blue-200 animate-pulse"),
                    Div(
                        H1("Toxicity Prediction", cls="text-2xl font-black text-slate-900 tracking-tighter"),
                        P("Advanced Molecular Safety Intelligence • DeepChem Engine v3.2", cls="text-[10px] text-slate-400 font-black uppercase tracking-widest"),
                        cls="flex flex-col"
                    ),
                    cls="flex items-center gap-5"
                ),
                cls="max-w-6xl mx-auto flex justify-between items-center"
            ),
            cls="px-8 py-8 border-b border-slate-100 bg-white/80 backdrop-blur-xl sticky top-0 z-50"
        ),
        Div(
            # Secondary Navigation (Workspaces)
            Div(
                render_single_tab(tab == 'single'),
                render_multi_tab(tab == 'multi'),
                cls="flex max-w-6xl mx-auto border-b border-slate-100 mb-8"
            ),
            # Active Workspace
            Div(
                render_single_input() if tab == 'single' else render_multi_input(),
                results_html,
                id="main-workspace",
                cls="max-w-6xl mx-auto px-8 pb-20 mt-10"
            ),
            cls="bg-white min-h-screen"
        ),
        # Professional Processing Feedback
        Div(
            Div(
                Div(cls="w-20 h-20 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-8"),
                H2("Synthesizing Safety Evidence...", cls="text-2xl font-black text-white tracking-tight mb-2"),
                P(id="loading-status-text", cls="text-blue-200 text-sm font-bold uppercase tracking-widest animate-pulse"),
                cls="flex flex-col items-center"
            ),
            id="loading-overlay",
            cls="htmx-indicator fixed inset-0 z-[100] bg-slate-900/90 backdrop-blur-lg flex items-center justify-center"
        ),
        Script("""
            const messages = [
                "Resolving Clinical Drug Identity from PubChem...",
                "Retrieving 2D Molecular Structure Data...",
                "Calculating Reactive Metabolite Trajectories...",
                "Scanning BRENK/PAINS Toxicophore Database...",
                "Querying FDA FAERS Clinical Evidence...",
                "Profiling Tox21 Bio-Target Engagement...",
                "Synthesizing PhD-Grade Mechanistic Safety Case..."
            ];
            document.body.addEventListener('htmx:beforeRequest', function() {
                let text = document.getElementById('loading-status-text');
                if(text) text.innerText = messages[Math.floor(Math.random() * messages.length)];
            });
        """),
        cls="antialiased selection:bg-blue-100 selection:text-blue-900"
    )

@rt("/switch_tab")
def get(tab: str, session):
    session['current_tab'] = tab
    results_html = Div(id="results-area")
    if tab == 'single' and 'last_result' in session:
        results_html = Div(render_single_view(session['last_result']), id="results-area")
    elif tab == 'multi' and 'last_multi_results' in session:
        results_html = Div(render_comparison_view(session['last_multi_results']), id="results-area")
        
    return (
        Div(
            render_single_input() if tab == 'single' else render_multi_input(),
            results_html,
            id="main-workspace"
        ),
        render_single_tab(tab == 'single', hx_swap_oob="true"),
        render_multi_tab(tab == 'multi', hx_swap_oob="true")
    )

@rt("/analyze")
def post(smiles: str = None, smiles_list: str = None, mode: str = "single", session = None):
    input_str = smiles if mode == "single" else smiles_list
    if not input_str: return Div(P("Error: No input provided", cls="text-red-500 font-bold p-4 bg-red-50 rounded-xl"))

    try:
        # ToxicityPredictor.run_workflow handles both single strings and lists/comma-sep
        # We will pass the cleaned input directly
        result = predictor.run_workflow(input_str)
        
        if isinstance(result, dict) and result.get('type') == "comparison":
            session['last_multi_results'] = result
            session['current_tab'] = 'multi'
            return render_comparison_view(result)
        else:
            session['last_result'] = result
            session['current_tab'] = 'single'
            return render_single_view(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Div(
            H3("Synthesis Failure", cls="text-xl font-black text-red-600 mb-2"),
            Pre(str(e), cls="bg-red-50 p-4 rounded-xl text-red-500 text-xs overflow-auto"),
            cls="p-8 border-2 border-red-100 rounded-3xl"
        )

serve()

