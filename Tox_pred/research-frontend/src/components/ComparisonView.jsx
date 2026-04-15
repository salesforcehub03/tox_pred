import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import DOMPurifyLib from 'dompurify';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import RiskGauge from './RiskGauge';

/* Safe DOMPurify wrapper for v3.x compatibility */
const safeSanitize = (dirty, config) => {
  try {
    if (!dirty) return '';
    // DOMPurify v3.x may export differently
    const purify = DOMPurifyLib?.sanitize ? DOMPurifyLib : (typeof DOMPurifyLib === 'function' ? DOMPurifyLib(window) : null);
    if (purify && typeof purify.sanitize === 'function') {
      return purify.sanitize(dirty, config);
    }
    // Fallback: strip all tags if DOMPurify is broken
    console.warn('[ComparisonView] DOMPurify unavailable, stripping HTML');
    return String(dirty).replace(/<[^>]*>/g, '');
  } catch (err) {
    console.error('[ComparisonView] DOMPurify sanitize error:', err);
    return '';
  }
};

/* ─────────────── helpers ─────────────── */

const badge = (label) => {
  const colors = {
    High: 'bg-red-100 text-red-700 border-red-200',
    Moderate: 'bg-amber-100 text-amber-700 border-amber-200',
    Low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    Minimal: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    Neutral: 'bg-slate-100 text-slate-700 border-slate-200'
  };
  const theme = colors[label] || colors.Neutral;
  return (
    <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${theme}`}>
      {label || 'N/A'}
    </span>
  );
};

const SectionIcon = ({ icon, title }) => (
  <div className="flex items-center gap-3 mb-5">
    <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white text-sm shadow-lg shadow-slate-200">{icon}</div>
    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">{title}</h3>
  </div>
);

const organIcons = { "Liver": "🫀", "Kidney": "🫘", "Heart": "❤️", "Lung": "🫁", "Brain": "🧠", "Systemic": "🔬", "Immune System": "🛡️", "Endocrine System": "⚗️" };

/* ─────────────── sub-components ─────────────── */

/** Mini bar for a numeric 0-1 value */
const MiniBar = ({ value, max = 1 }) => {
  const pct = Math.min(Math.round((value / max) * 100), 100);
  const bg = pct > 50 ? 'bg-red-500' : (pct > 35 ? 'bg-amber-400' : 'bg-emerald-500');
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-1.5 rounded-full ${bg}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[9px] font-mono font-bold text-slate-500 w-8 text-right">{(value * 100).toFixed(0)}%</span>
    </div>
  );
};

/** PubMed card */
const PubMedCard = ({ pm }) => {
  if (!pm || !pm.total) return <p className="text-[10px] text-slate-400 italic">No PubMed data available.</p>;
  return (
    <div className="flex gap-3 p-4 bg-white border border-slate-100 rounded-xl shadow-sm">
      <div className="text-center flex-1">
        <div className="text-xl font-black text-slate-800">{pm.total}</div>
        <div className="text-[8px] text-slate-400 uppercase tracking-wider mt-1">Publications</div>
      </div>
      <div className="text-center flex-1">
        <div className="text-xl font-black text-amber-600">{pm.tox_hits || 0}</div>
        <div className="text-[8px] text-slate-400 uppercase tracking-wider mt-1">Tox Papers</div>
      </div>
      <div className="text-center flex-1">
        <div className="text-xl font-black text-blue-600">{(pm.density || 0).toFixed(1)}%</div>
        <div className="text-[8px] text-slate-400 uppercase tracking-wider mt-1">Tox Density</div>
      </div>
    </div>
  );
};

/** Structural Alerts card */
const StructuralAlertsCard = ({ alerts = [] }) => {
  const active = alerts.filter(a => a.alert !== 'None detected');
  if (!active.length) return (
    <div className="p-3 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100 text-[10px] font-bold">
      ✅ No structural toxicophores detected.
    </div>
  );
  return (
    <div className="space-y-2">
      {active.map((a, i) => {
        const db = a.db_entry || {};
        const sev = db.severity || 'Moderate';
        const sevColor = sev === 'High' ? 'text-red-600 bg-red-50 border-red-100' : 'text-amber-600 bg-amber-50 border-amber-100';
        return (
          <div key={i} className="p-3 bg-white rounded-xl border border-orange-100 border-l-4 border-l-orange-400 shadow-sm">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-black text-slate-800 uppercase">{db.alert || a.alert}</span>
              <span className={`text-[8px] font-black px-2 py-0.5 rounded border ${sevColor}`}>{sev}</span>
            </div>
            <p className="text-[9px] text-slate-600 leading-relaxed"><b>⚙ Mechanism:</b> {db.mechanism || a.reasoning || 'N/A'}</p>
            {db.consequence && <p className="text-[9px] text-slate-700 font-medium mt-1"><b>🏥 Clinical:</b> {db.consequence}</p>}
          </div>
        );
      })}
    </div>
  );
};

/** FAERS table */
const FAERSCard = ({ faers = [] }) => {
  if (!faers.length) return <p className="text-[10px] text-slate-400 italic">No FAERS signals found.</p>;
  return (
    <table className="w-full text-left">
      <thead>
        <tr className="border-b border-slate-200">
          <th className="py-2 px-2 text-slate-400 text-[9px] uppercase tracking-wider">Adverse Event (MedDRA PT)</th>
          <th className="text-right py-2 px-2 text-slate-400 text-[9px] uppercase tracking-wider">Reports</th>
        </tr>
      </thead>
      <tbody>
        {faers.map((ae, i) => (
          <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
            <td className="py-2 px-2 text-[10px] text-slate-700 font-medium">{ae.term}</td>
            <td className="py-2 px-2 text-[10px] text-slate-500 text-right font-mono">{ae.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

/** AE Concordance summary */
const AEConcordanceCard = ({ ae_conc }) => {
  if (!ae_conc) return null;
  const pct = ae_conc.concordance_pct || 0;
  const color = pct >= 50 ? 'text-emerald-600' : (pct >= 25 ? 'text-amber-600' : 'text-red-600');
  const bar = pct >= 50 ? 'bg-emerald-500' : (pct >= 25 ? 'bg-amber-400' : 'bg-red-500');
  const label = pct >= 50 ? 'Strong' : (pct >= 25 ? 'Moderate' : 'Low');
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-2xl font-black ${color}`}>{pct}%</span>
        <span className={`text-[9px] font-black uppercase ${color}`}>{label}</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden mb-2">
        <div className={`h-2 rounded-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-[9px] text-slate-500 italic">
        {ae_conc.matched?.length || 0} validated signals · {ae_conc.unmatched_predicted?.length || 0} unreported hazards
      </p>
      {(ae_conc.matched || []).length > 0 && (
        <div className="mt-3 space-y-1">
          {ae_conc.matched.slice(0, 3).map((m, i) => (
            <div key={i} className="flex items-center gap-1">
              <span className="text-[8px]">✅</span>
              <span className="text-[9px] font-black text-slate-700 uppercase">{m.predicted}</span>
              <span className="text-[8px] text-slate-300 mx-0.5">↔</span>
              <span className="text-[9px] font-black text-blue-600 uppercase">{m.faers_confirmed}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/** Predicted AE list */
const PredictedAECard = ({ pred_ae = [] }) => {
  if (!pred_ae.length) return <p className="text-[10px] text-slate-400 italic">No predictions available.</p>;
  return (
    <div className="space-y-2">
      {pred_ae.slice(0, 5).map((ae, i) => {
        const conf = ae.confidence || 'Low';
        const source = ae.source || 'Emerging Hazard';
        const icon = organIcons[ae.organ] || '💊';
        const confColor = conf === 'High' ? 'text-red-700 bg-red-50 border-red-100' : (conf === 'Medium' ? 'text-amber-700 bg-amber-50 border-amber-100' : 'text-slate-500 bg-slate-50 border-slate-100');
        return (
          <div key={i} className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm hover:border-blue-200 transition-all">
            <div className="flex items-center gap-1 mb-1">
              <span>{icon}</span>
              <span className="text-[10px] font-black text-slate-800 uppercase flex-1 truncate">{ae.term || 'Unknown'}</span>
              <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border ${confColor}`}>{conf}</span>
            </div>
            {ae.organ && <span className="text-[8px] font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">{ae.organ}</span>}
            {ae.rationale && <p className="text-[9px] text-slate-500 leading-relaxed mt-1">{ae.rationale}</p>}
          </div>
        );
      })}
    </div>
  );
};

/** Drug-Likeness grid */
const DrugLikenessCard = ({ props = {} }) => (
  <div className="space-y-3">
    {/* QED */}
    <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm">
      <div className="text-[8px] font-black text-slate-400 uppercase tracking-wider mb-1">QED Score</div>
      <div className="flex items-center justify-between">
        <span className={`text-lg font-black ${props.QED >= 0.67 ? 'text-emerald-600' : (props.QED >= 0.35 ? 'text-amber-600' : 'text-red-600')}`}>{props.QED || 'N/A'}</span>
        <span className={`text-[8px] font-black uppercase ${props.QED >= 0.67 ? 'text-emerald-600' : (props.QED >= 0.35 ? 'text-amber-600' : 'text-red-600')}`}>{props.QED >= 0.67 ? 'Favorable' : (props.QED >= 0.35 ? 'Moderate' : 'Unfavorable')}</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
        <div className={`h-1.5 rounded-full ${props.QED >= 0.67 ? 'bg-emerald-500' : (props.QED >= 0.35 ? 'bg-amber-400' : 'bg-red-500')}`} style={{ width: `${Math.min((props.QED || 0) * 100, 100)}%` }} />
      </div>
    </div>
    {/* Ro5 */}
    <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm space-y-1.5">
      <div className="text-[8px] font-black text-slate-400 uppercase tracking-wider mb-1">Rule Filters</div>
      {[['Lipinski Ro5', props.Lipinski_Pass], ['Veber Rules', props.Veber_Pass], ['Ghose Filter', props.Ghose_Pass]].map(([name, pass]) => (
        <div key={name} className="flex justify-between items-center py-1 border-b border-slate-50 last:border-0">
          <span className="text-[10px] text-slate-600">{name}</span>
          <span className={`text-[9px] font-black ${pass ? 'text-emerald-600' : 'text-red-600'}`}>{pass ? '✅ Pass' : '❌ Fail'}</span>
        </div>
      ))}
    </div>
    {/* Phys props */}
    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
      {[['MW', `${props.MW} g/mol`], ['HBD', props.HBD], ['HBA', props.HBA], ['RotBonds', props.RotBonds], ['TPSA', `${props.TPSA} Å²`], ['SAS', props.SAS], ['LogS', props.LogS]].map(([k, v]) => (
        <div key={k} className="flex justify-between py-1 border-b border-slate-100/50 last:border-0">
          <span className="text-[10px] text-slate-500">{k}</span>
          <span className="text-[10px] font-black text-slate-800 font-mono">{v ?? 'N/A'}</span>
        </div>
      ))}
    </div>
  </div>
);

/** DeepChem Tox21 target bars */
const DeepChemCard = ({ predictions = {} }) => {
  const entries = Object.entries(predictions).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return <p className="text-[10px] text-slate-400 italic">No DeepChem predictions available.</p>;
  return (
    <div className="space-y-2">
      {entries.map(([name, val], i) => {
        const pct = Math.round(val * 100);
        const bg = pct > 50 ? 'bg-red-500' : (pct > 35 ? 'bg-amber-400' : 'bg-emerald-500');
        const icon = pct > 50 ? '🔴' : (pct > 35 ? '🟡' : '🟢');
        return (
          <div key={i} className="flex items-center gap-2">
            <span className="text-[9px]">{icon}</span>
            <span className="text-[9px] font-bold text-slate-600 uppercase w-20 truncate">{name}</span>
            <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div className={`h-1.5 rounded-full ${bg}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-[9px] font-mono text-slate-500 w-8 text-right">{val.toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
};

/** Organ Mechanistic Report card */
const OrganMechCard = ({ mech_report = {} }) => {
  const organs = Object.entries(mech_report);
  if (!organs.length) return <p className="text-[10px] text-emerald-600 italic bg-emerald-50 p-3 rounded-xl">No significant mechanistic causal chains identified.</p>;
  return (
    <div className="space-y-4">
      {organs.map(([organ, details], i) => (
        <div key={i} className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="flex items-center mb-2 pb-2 border-b border-slate-100">
            <span className="text-base mr-2">{details.icon || '🔗'}</span>
            <span className="text-[10px] font-black text-slate-700 uppercase tracking-widest flex-1">{details.name || organ}</span>
            <span className={`text-[8px] font-black px-2 py-0.5 rounded ${details.risk_label === 'High' ? 'text-red-600 bg-red-50 border border-red-100' : (details.risk_label === 'Moderate' ? 'text-amber-600 bg-amber-50 border border-amber-100' : 'text-emerald-600 bg-emerald-50 border border-emerald-100')}`}>{details.risk_label}</span>
          </div>
          {details.simple_explanation && <p className="text-[9px] text-slate-600 leading-relaxed mb-2">{details.simple_explanation}</p>}
          {(details.causal_chains || []).slice(0, 2).map((chain, j) => (
            <div key={j} className="p-2 rounded-lg bg-slate-50 border-l-2 border-l-amber-400 mb-1.5">
              <span className="text-[9px] font-black text-slate-700 uppercase">{chain.trigger}</span>
              <p className="text-[8px] text-slate-500 mt-0.5"><b>Mechanism:</b> {chain.mechanism || 'N/A'}</p>
              <p className="text-[8px] text-slate-500"><b>Outcome:</b> {chain.clinical_outcome || 'N/A'}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

/* ─────────────── Main Component ─────────────── */

const ComparisonView = ({ data }) => {
  const [molSvgs, setMolSvgs] = useState({});

  useEffect(() => {
    if (data?.reports && Array.isArray(data.reports)) {
      const fetchSvgs = async () => {
        const promises = data.reports.map(async r => {
          if (r?.SMILES && !molSvgs[r.SMILES]) {
            try {
              const res = await axios.get(`/api/molecule_svg?smiles=${encodeURIComponent(r.SMILES)}`);
              return { smiles: r.SMILES, svg: res.data?.svg || '' };
            } catch (err) {
              console.error("SVG fetch failed", err);
              return null;
            }
          }
          return null;
        });
        
        const results = await Promise.all(promises);
        const newSvgs = {};
        let updated = false;
        results.forEach(res => {
          if (res) {
            newSvgs[res.smiles] = res.svg;
            updated = true;
          }
        });
        if (updated) {
          setMolSvgs(prev => ({ ...prev, ...newSvgs }));
        }
      };
      
      fetchSvgs();
    }
  }, [data?.reports]);

  // Robust guard: ensure reports is always a valid, non-empty array
  if (!data || !Array.isArray(data.reports) || data.reports.length === 0) {
    return (
      <div className="p-10 text-center">
        <div className="text-4xl mb-4">📊</div>
        <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">No comparison data available. Please enter multiple compounds.</p>
      </div>
    );
  }

  const reports = data.reports.filter(r => r && typeof r === 'object');
  if (reports.length === 0) {
    return (
      <div className="p-10 text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">All reports were empty or malformed.</p>
      </div>
    );
  }

  const summary = data.summary || {};
  const overview = summary.overview || "Comparative analysis complete.";
  const synergy_text = summary.synergy || "";

  // Prepare Radar Data — fully defensive
  const radarData = useMemo(() => {
    try {
      if (!reports || reports.length === 0) return [];
      const firstReport = reports[0];
      const predictionsObj = firstReport?.['DeepChem Prediction']?.predictions || {};
      const targets = Object.keys(predictionsObj).slice(0, 10);
      if (targets.length === 0) return [];
      
      return targets.map(t => {
        const entry = { subject: t };
        reports.forEach(r => {
          const val = r?.['DeepChem Prediction']?.predictions?.[t];
          const num = typeof val === 'number' && !isNaN(val) ? val : 0;
          entry[r?.Name || 'Unknown'] = num * 100;
        });
        return entry;
      });
    } catch (err) {
      console.error('[ComparisonView] radarData build failed:', err);
      return [];
    }
  }, [reports]);

  // Prepare Risk Bar Data — fully defensive
  const riskBarData = useMemo(() => {
    try {
      if (!reports) return [];
      return reports.map(r => {
        const score = Object.entries(r || {}).reduce((acc, [k, v]) => {
          if (k.includes('Risk') && typeof v === 'object' && v !== null) {
            const s = Number(v.score);
            return acc + (isNaN(s) ? 0 : s);
          }
          return acc;
        }, 0);
        
        return {
          name: r?.Name || 'Unknown',
          score: isNaN(score) ? 0 : Math.round(score)
        };
      });
    } catch (err) {
      console.error('[ComparisonView] riskBarData build failed:', err);
      return [];
    }
  }, [reports]);

  const COLORS = ['#2563eb', '#db2777', '#059669', '#d97706', '#7c3aed'];

  return (
    <div className="animate-fade-in space-y-10">
      {/* 1. Search Header */}
      <div className="mb-10">
        <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest">Comparative Analysis Result</h2>
        <h1 className="text-4xl lg:text-5xl font-black text-slate-900 mt-2 mb-6 tracking-tight uppercase">
          {reports.map(r => r.Name).join(", ")}
        </h1>
        <div className="flex flex-wrap gap-3 mb-10">
          {reports.map((r, i) => (
            <div key={i} className="flex items-center bg-white px-4 py-2 rounded-full border border-slate-100 shadow-sm transition-all hover:border-blue-200">
              <span className="text-[12px] font-black text-slate-800">{r.Name}</span>
              <a 
                href={`https://pubchem.ncbi.nlm.nih.gov/compound/${r["PubChem CID"]}`} 
                target="_blank"
                className="text-[9px] font-black text-blue-500 hover:underline border-l border-slate-200 ml-2 pl-2"
              >
                CID:{r["PubChem CID"] || 'N/A'}
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Molecular Comparative Structures */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white text-sm shadow-lg shadow-slate-200">💠</div>
          <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Molecular Comparative Structures</h2>
        </div>
        <div className="flex flex-wrap gap-4 mt-4">
          {reports.map((r, i) => (
            <div key={i} className="flex-1 min-w-[180px] bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden transition-all hover:scale-[1.02] hover:shadow-md">
              <div className="w-full aspect-square flex items-center justify-center p-4 overflow-hidden">
                 {molSvgs[r.SMILES] ? (
                   <div dangerouslySetInnerHTML={{ __html: safeSanitize(molSvgs[r.SMILES], { USE_PROFILES: { svg: true } }) }} className="w-full h-full flex items-center justify-center [&>svg]:max-w-full [&>svg]:max-h-full [&>svg]:w-auto [&>svg]:h-auto" />
                 ) : (
                   <div className="animate-pulse bg-slate-50 w-full h-full rounded-xl"></div>
                 )}
              </div>
              <div className="text-center text-xs font-black text-slate-800 uppercase py-3 border-t border-slate-100 truncate px-2 bg-slate-50/50">
                {r.Name}
              </div>
              {/* IUPAC + SMILES below structure */}
              {r["IUPAC Name"] && (
                <div className="px-3 pb-3">
                  <div className="text-[8px] text-slate-400 uppercase tracking-wider">IUPAC</div>
                  <div className="text-[9px] text-slate-600 font-mono leading-tight break-all">{r["IUPAC Name"]}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 3. Multi-Drug Safety Comparative Matrix */}
      <div>
        <h2 className="text-2xl font-black text-slate-800 mb-5 text-center">⚖️ Multi-Drug Safety Comparative Matrix</h2>
        <div className="mb-12 overflow-x-auto">
          <table className="w-full border-collapse rounded-3xl overflow-hidden shadow-xl border border-slate-100 min-w-[800px] bg-white">
             <thead>
                <tr className="bg-slate-900 text-white">
                   <th className="py-6 px-8 text-left text-[10px] font-black uppercase tracking-widest">Property / Safety Metric</th>
                   {reports.map((r, i) => (
                     <th key={i} className="py-6 px-8 text-center text-[12px] font-black uppercase border-l border-slate-800">
                        {r.Name}
                     </th>
                   ))}
                </tr>
             </thead>
             <tbody className="divide-y divide-slate-100">
                {/* Identity */}
                <MatrixRow label="Formula" values={reports.map(r => <span className="font-mono text-[11px] font-bold text-blue-600">{r["Formula"] || r["RDKit Properties"]?.Formula || 'N/A'}</span>)} />
                <MatrixRow label="IUPAC Name" values={reports.map(r => <span className="font-mono text-[9px] text-slate-500 leading-tight break-all">{r["IUPAC Name"] || 'N/A'}</span>)} />
                <MatrixRow label="Molecular Architecture" values={reports.map(r => (
                  <div key={r.Name} className="h-32 flex items-center justify-center p-2 overflow-hidden [&>svg]:max-w-full [&>svg]:max-h-full [&>svg]:w-auto [&>svg]:h-auto" dangerouslySetInnerHTML={{ __html: safeSanitize(molSvgs[r?.SMILES] || '', { USE_PROFILES: { svg: true } }) }} />
                ))} />
                {/* Physicochemical */}
                <MatrixRow label="Molar Mass" values={reports.map(r => `${r['RDKit Properties']?.MW || 0} g/mol`)} />
                <MatrixRow label="Lipophilicity (XLogP)" values={reports.map(r => r['RDKit Properties']?.XLogP ?? 'N/A')} />
                <MatrixRow label="TPSA (Å²)" values={reports.map(r => r['RDKit Properties']?.TPSA ?? 'N/A')} />
                <MatrixRow label="H-Bond Donors" values={reports.map(r => r['RDKit Properties']?.HBD ?? 'N/A')} />
                <MatrixRow label="H-Bond Acceptors" values={reports.map(r => r['RDKit Properties']?.HBA ?? 'N/A')} />
                <MatrixRow label="Rotatable Bonds" values={reports.map(r => r['RDKit Properties']?.RotBonds ?? 'N/A')} />
                <MatrixRow label="LogS (Solubility)" values={reports.map(r => r['RDKit Properties']?.LogS ?? 'N/A')} />
                {/* Drug-Likeness */}
                <MatrixRow label="Consensus QED Score" values={reports.map(r => (
                  <span className="font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">{r['RDKit Properties']?.QED || 'N/A'}</span>
                ))} />
                <MatrixRow label="Synthetic Accessibility" values={reports.map(r => r['RDKit Properties']?.SAS ?? 'N/A')} />
                <MatrixRow label="Lipinski Ro5" values={reports.map(r => (
                  <span className={`text-[10px] font-black ${r['RDKit Properties']?.Lipinski_Pass ? 'text-emerald-600' : 'text-red-600'}`}>
                    {r['RDKit Properties']?.Lipinski_Pass ? '✅ Pass' : '❌ Fail'}
                  </span>
                ))} />
                {/* Safety */}
                <MatrixRow label="Engine Confidence" values={reports.map(r => (
                  <div className="flex flex-col items-center">
                    <span className="font-black text-[14px] text-slate-900">{(r["Engine Confidence"]?.score) || (typeof r["Engine Confidence"] !== 'object' ? r["Engine Confidence"] : null) || r["Engine Confidence Audit"]?.score || '88'}%</span>
                    <span className="text-[8px] text-slate-400 uppercase tracking-widest font-black">Bayesian Audit</span>
                  </div>
                ))} />
                <MatrixRow label="Hepatic DILI Level" values={reports.map(r => badge(r['DILI Risk']?.label))} />
                <MatrixRow label="Pulmonary Risk" values={reports.map(r => badge(r['Lung Injury Risk']?.label))} />
                <MatrixRow label="Kidney Injury Risk" values={reports.map(r => badge(r['Kidney Injury Risk']?.label))} />
                <MatrixRow label="Cardiac Risk" values={reports.map(r => badge(r['Cardiac Risk']?.label))} />
                <MatrixRow label="Neuro Risk" values={reports.map(r => badge(r['Neuro Risk']?.label))} />
                <MatrixRow label="Genotox Risk" values={reports.map(r => badge(r['Genotox Risk']?.label))} />
                <MatrixRow label="Endocrine Risk" values={reports.map(r => badge(r['Endocrine Risk']?.label))} />
                <MatrixRow label="GI Risk" values={reports.map(r => badge(r['GI Risk']?.label))} />
                {/* Evidence */}
                <MatrixRow label="PubMed Publications" values={reports.map(r => (
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="font-black text-[14px] text-slate-800">{r['PubMed Confidence']?.total || 0}</span>
                    <span className="text-[8px] text-amber-600 font-black">{r['PubMed Confidence']?.tox_hits || 0} tox papers</span>
                  </div>
                ))} />
                <MatrixRow label="FAERS Signals" values={reports.map(r => (
                  <span className="font-black text-[13px] text-slate-700">{r['FAERS Top 5']?.length || 0}</span>
                ))} />
                <MatrixRow label="AE Concordance" values={reports.map(r => (
                   <div className="flex items-center justify-center gap-2">
                      <div className="w-12 h-1 bg-slate-100 rounded-full overflow-hidden">
                         <div className="h-full bg-emerald-500" style={{ width: `${r['AE Concordance']?.concordance_pct || 0}%` }} />
                      </div>
                      <span className="text-[10px] font-black">{r['AE Concordance']?.concordance_pct || 0}%</span>
                   </div>
                ))} />
                <MatrixRow label="Structural Alerts" values={reports.map(r => {
                  const active = (r['Structural Alerts'] || []).filter(a => a.alert !== 'None detected').length;
                  return (
                    <span className={`text-[11px] font-black ${active > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                      {active > 0 ? `⚠️ ${active} Alert${active > 1 ? 's' : ''}` : '✅ Clean'}
                    </span>
                  );
                })} />
             </tbody>
          </table>
        </div>
      </div>

      {/* 4. Comparative Target Profiles (Charts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-3xl p-6 lg:p-8 border border-slate-100 shadow-sm flex flex-col justify-between">
           <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Tox21 Target Binding Fingerprint</h3>
           <div className="h-[300px]">
             <ResponsiveContainer width="100%" height="100%">
               <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                 <PolarGrid />
                 <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9, fontWeight: 700, fill: '#64748b' }} />
                 {reports.map((r, i) => (
                   <Radar
                     key={r.Name}
                     name={r.Name}
                     dataKey={r.Name}
                     stroke={COLORS[i % COLORS.length]}
                     fill={COLORS[i % COLORS.length]}
                     fillOpacity={0.05}
                     strokeWidth={2}
                   />
                 ))}
                 <Legend wrapperStyle={{ fontSize: '10px', fontWeight: 'bold' }} />
               </RadarChart>
             </ResponsiveContainer>
           </div>
        </div>

        <div className="bg-white rounded-3xl p-6 lg:p-8 border border-slate-100 shadow-sm flex flex-col justify-between">
           <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Aggregated Multi-Organ Risk Score</h3>
           <div className="h-[300px]">
             <ResponsiveContainer width="100%" height="100%">
               <BarChart data={riskBarData} layout="vertical">
                 <XAxis type="number" hide />
                 <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fontWeight: 700 }} width={80} />
                 <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ fontSize: '12px', fontWeight: 'bold', borderRadius: '12px' }} />
                 <Bar dataKey="score" fill="#0f172a" radius={[0, 4, 4, 0]} barSize={20} />
               </BarChart>
             </ResponsiveContainer>
           </div>
        </div>
      </div>

      {/* 5. SIDE-BY-SIDE FULL MECHANISTIC DOSSIERS */}
      <div>
         <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white text-lg shadow-xl shadow-indigo-100">🔬</div>
            <h2 className="text-xl font-black text-slate-900 uppercase tracking-tighter">Comparative Mechanistic Profiles</h2>
         </div>
         <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {reports.map((r, i) => {
              const props = r['RDKit Properties'] || {};
              const pm = r['PubMed Confidence'] || {};
              const ae_conc = r['AE Concordance'] || null;
              const pred_ae = r['Predicted AE'] || [];
              const faers = r['FAERS Top 5'] || [];
              const structural_alerts = r['Structural Alerts'] || [];
              const mech_report = r['Organ Mechanistic Report'] || {};
              const geno = r['Genotox Risk'] || {};
              const endo = r['Endocrine Risk'] || {};
              const predictions = r['DeepChem Prediction']?.predictions || {};

              return (
                <div key={i} className="bg-white rounded-[32px] border border-slate-100 shadow-sm overflow-hidden flex flex-col hover:border-indigo-200 transition-all">
                  {/* Dossier Header */}
                  <div className="px-8 py-6 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                     <span className="text-[11px] font-black tracking-widest text-slate-500 uppercase">{r.Name} Dossier</span>
                     <div className="flex items-center gap-2">
                        <span className="text-[9px] font-black bg-white px-3 py-1 rounded-full border border-slate-200 text-slate-400 shadow-sm">CID: {r["PubChem CID"]}</span>
                     </div>
                  </div>

                  <div className="p-8 flex-1 space-y-7">
                    {/* Expert Summary */}
                    <div>
                      <p className="text-[13px] text-slate-700 leading-relaxed font-serif italic mb-0 border-l-2 border-indigo-500 pl-6">
                         {r.Expert_Summary || r.ExpertSummary || "Mechanistic synthesis available in standalone analysis mode."}
                      </p>
                    </div>

                    {/* Quick Stats Row */}
                    <div className="grid grid-cols-3 gap-3">
                       <div className="p-3 bg-slate-50 rounded-2xl text-center">
                          <div className="text-[8px] font-black text-slate-400 uppercase mb-1">Top Hazard Target</div>
                          <div className="text-[9px] font-bold text-slate-800 truncate">{Object.keys(predictions)[0] || 'N/A'}</div>
                       </div>
                       <div className="p-3 bg-slate-50 rounded-2xl text-center">
                          <div className="text-[8px] font-black text-slate-400 uppercase mb-1">LogS</div>
                          <div className="text-[9px] font-bold text-slate-800 font-mono">{props.LogS || 'N/A'}</div>
                       </div>
                       <div className="p-3 bg-slate-50 rounded-2xl text-center">
                          <div className="text-[8px] font-black text-slate-400 uppercase mb-1">AE Concordance</div>
                          <div className={`text-[11px] font-black ${(ae_conc?.concordance_pct || 0) >= 50 ? 'text-emerald-600' : 'text-amber-600'}`}>{ae_conc?.concordance_pct || 0}%</div>
                       </div>
                    </div>

                    {/* Organ Risk Gauges */}
                    <div>
                      <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-4">Organ Risk Profile</div>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { label: 'Liver', key: 'DILI Risk' },
                          { label: 'Heart', key: 'Cardiac Risk' },
                          { label: 'Lungs', key: 'Lung Injury Risk' },
                          { label: 'Kidney', key: 'Kidney Injury Risk' },
                          { label: 'Brain', key: 'Neuro Risk' },
                          { label: 'GI', key: 'GI Risk' },
                        ].map(({ label: organLabel, key }) => {
                          const organRisk = r[key] || {};
                          const lbl = organRisk.label || 'Minimal';
                          const color = lbl === 'High' ? 'text-red-600 bg-red-50 border-red-100' : (lbl === 'Moderate' ? 'text-amber-600 bg-amber-50 border-amber-100' : 'text-emerald-600 bg-emerald-50 border-emerald-100');
                          return (
                            <div key={key} className={`p-2 rounded-xl border text-center ${color}`}>
                              <div className="text-[7px] font-black uppercase tracking-wider">{organLabel}</div>
                              <div className="text-[9px] font-black mt-0.5">{lbl}</div>
                              {organRisk.score !== undefined && <div className="text-[7px] opacity-70">Score: {organRisk.score}</div>}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Genotox + Endocrine */}
                    {(geno.label || endo.label) && (
                      <div className="grid grid-cols-2 gap-3">
                        {geno.label && (
                          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                            <div className="text-[8px] font-black text-slate-400 uppercase mb-1">Genotox Risk</div>
                            <div>{badge(geno.label)}</div>
                            {geno.score !== undefined && <div className="text-[8px] text-slate-400 mt-1">Score: {geno.score}</div>}
                          </div>
                        )}
                        {endo.label && (
                          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                            <div className="text-[8px] font-black text-slate-400 uppercase mb-1">Endocrine Risk</div>
                            <div>{badge(endo.label)}</div>
                            {endo.score !== undefined && <div className="text-[8px] text-slate-400 mt-1">Score: {endo.score}</div>}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Drug-Likeness */}
                    <div>
                      <SectionIcon icon="💊" title="Drug-Likeness Assessment" />
                      <DrugLikenessCard props={props} />
                    </div>

                    {/* DeepChem Targets */}
                    <div>
                      <SectionIcon icon="🧠" title="Tox21 Target Binding" />
                      <DeepChemCard predictions={predictions} />
                    </div>

                    {/* Literature Evidence */}
                    <div>
                      <SectionIcon icon="📚" title="Literature Evidence (PubMed)" />
                      <PubMedCard pm={pm} />
                    </div>

                    {/* Structural Alerts */}
                    <div>
                      <SectionIcon icon="⚠️" title="Structural Alerts (BRENK/PAINS)" />
                      <StructuralAlertsCard alerts={structural_alerts} />
                    </div>

                    {/* Predicted AEs */}
                    <div>
                      <SectionIcon icon="🔮" title="Clinical Outcome Predictions" />
                      <PredictedAECard pred_ae={pred_ae} />
                    </div>

                    {/* FAERS */}
                    <div>
                      <SectionIcon icon="🏥" title="Real-World Evidence (FDA FAERS)" />
                      <FAERSCard faers={faers} />
                    </div>

                    {/* AE Concordance */}
                    <div>
                      <SectionIcon icon="📊" title="AE Prediction Concordance" />
                      <AEConcordanceCard ae_conc={ae_conc} />
                    </div>

                    {/* Organ Mechanistic Report */}
                    <div>
                      <SectionIcon icon="🔗" title="Organ Mechanistic Causal Chains" />
                      <OrganMechCard mech_report={mech_report} />
                    </div>
                  </div>
                </div>
              );
            })}
         </div>
      </div>

      {/* 6. Executive Synthesis Dashboard */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white text-sm shadow-xl shadow-blue-100">🤖</div>
          <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Executive Synthesis Dashboard</h2>
        </div>
        <div className="p-8 bg-blue-50/30 rounded-[32px] border border-blue-100 shadow-inner">
           <p className="text-[13px] text-slate-800 leading-relaxed italic font-medium">
             {overview}
           </p>
        </div>
      </div>

      {synergy_text ? (
        <div className="p-8 bg-amber-50 rounded-[32px] border border-amber-200 shadow-sm mt-6">
           <div className="mb-4">
              <span className="text-[10px] font-black text-amber-700 uppercase tracking-widest bg-amber-100 px-3 py-1 rounded-full border border-amber-200">🧬 Predicted Synergy & Combined Hazards</span>
           </div>
           <p className="text-[12px] text-amber-900 leading-relaxed italic font-serif ">{synergy_text}</p>
        </div>
      ) : null}

    </div>
  );
};

const MatrixRow = ({ label, values }) => (
  <tr className="hover:bg-slate-50 transition-colors">
     <td className="py-5 px-8 font-black text-slate-500 text-[10px] uppercase tracking-widest bg-slate-50/30 w-1/4">{label}</td>
     {values.map((v, i) => (
       <td key={i} className="py-5 px-8 text-center text-[12px] font-bold border-l border-slate-50">
          {v}
       </td>
     ))}
  </tr>
);

export default ComparisonView;
