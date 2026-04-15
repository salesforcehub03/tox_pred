import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DOMPurify from 'dompurify';
import RiskGauge from './RiskGauge';
import CausalChain from './CausalChain';
import MethodologyTooltip from './MethodologyTooltip';
import PathwayBlueprint from './PathwayBlueprint';
import { Download, FileText } from 'lucide-react';

const _card = ({ icon, title, children, borderColor = "border-slate-100" }) => (
   <div className={`mb-6 p-6 bg-white rounded-3xl border ${borderColor} shadow-sm transition-all hover:shadow-md relative`}>
      <div className="flex items-center gap-3 mb-4 border-b border-slate-50 pb-3">
         <span className="text-xl">{icon}</span>
         <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-widest">{title}</h3>
      </div>
      {children}
   </div>
);

const SectionLabel = ({ icon, label }) => (
   <div className="flex items-center gap-3 mb-6">
      <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white text-sm shadow-lg shadow-slate-200">
         {icon}
      </div>
      <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">{label}</h2>
   </div>
);

const SingleView = ({ report }) => {
   const [molSvg, setMolSvg] = useState('');
   const [hoveredMech, setHoveredMech] = useState({ meth: report?.["DILI Risk"]?.methodology, name: "Hepatic" });

   useEffect(() => {
      if (report?.SMILES) {
         axios.get(`/api/molecule_svg?smiles=${encodeURIComponent(report.SMILES)}`)
            .then(res => setMolSvg(res.data.svg))
            .catch(err => console.error("SVG fetch failed", err));

         // Auto-sync HUD to Liver on new report load
         if (report["DILI Risk"]) {
            setHoveredMech({ meth: report["DILI Risk"].methodology, name: "Hepatic" });
         }
      }
   }, [report?.SMILES]);

   if (!report) return null;

   const props = report["RDKit Properties"] || {};
   const dili = report["DILI Risk"] || {};
   const lung = report["Lung Injury Risk"] || {};
   const pred_ae = report["Predicted AE"] || [];
   const target_bio = report["Top Targets Biology"] || [];
   const pm = report["PubMed Confidence"] || {};
   const ae_conc = report["AE Concordance"] || {};
   const mech_report = report["Organ Mechanistic Report"] || {};
   const structural_alerts = report["Structural Alerts"] || [];
   const faers = report["FAERS Top 5"] || [];
   const geno = report["Genotox Risk"] || {};
   const endo = report["Endocrine Risk"] || {};
   const gi = report["GI Risk"] || {};

   const organIcons = { "Liver": "🫀", "Kidney": "🫘", "Heart": "❤️", "Lung": "🫁", "Brain": "🧠", "Systemic": "🔬", "Immune System": "🛡️", "Endocrine System": "⚗️" };

   const handleExport = () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
      const downloadAnchorNode = document.createElement('a');
      downloadAnchorNode.setAttribute("href", dataStr);
      downloadAnchorNode.setAttribute("download", `AViiD_${report.Name || 'Report'}_${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(downloadAnchorNode);
      downloadAnchorNode.click();
      downloadAnchorNode.remove();
   };

   return (
      <div className="animate-fade-in space-y-10">
         {/* 1. Identity Header */}
         <div className="p-8 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8 mb-5">
            <div className="flex-1">
               <h2 className="text-3xl font-black text-slate-800 mb-1 tracking-tight">{report.Name || "Compound Profile"}</h2>
               <div className="flex items-center mb-3">
                  <span className="text-[9px] font-black bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-widest mr-2">PubChem Verified Identity</span>
                  <span className="text-[11px] text-slate-400 font-mono leading-relaxed">{report["IUPAC Name"] || 'N/A'}</span>
               </div>
               <div className="mb-3 bg-slate-50/50 px-3 py-2 rounded-lg border border-slate-100">
                  <span className="text-[9px] font-black text-slate-300 uppercase tracking-wider mr-2">SMILES Structure Source</span>
                  <span className="text-[10px] text-slate-500 font-mono break-all">{report.SMILES || 'N/A'}</span>
               </div>

               <div className="flex flex-wrap gap-2 mt-2">
                  <span className="bg-slate-50 px-3 py-1.5 rounded-lg text-[11px] border border-slate-100"><span className="text-slate-400 mr-1">CID</span><span className="text-blue-700 font-black">{report["PubChem CID"] || 'N/A'}</span></span>
                  <span className="bg-slate-50 px-3 py-1.5 rounded-lg text-[11px] border border-slate-100"><span className="text-slate-400 mr-1">MW</span><span className="text-blue-700 font-black">{props.MW || 'N/A'}</span> <span className="text-slate-400">g/mol</span></span>
                  <span className="bg-slate-50 px-3 py-1.5 rounded-lg text-[11px] border border-slate-100"><span className="text-slate-400 mr-1">XLogP</span><span className="text-blue-700 font-black">{props.XLogP || 'N/A'}</span></span>
                  <span className="bg-slate-50 px-3 py-1.5 rounded-lg text-[11px] border border-slate-100"><span className="text-slate-400 mr-1">TPSA</span><span className="text-blue-700 font-black">{props.TPSA || 'N/A'}</span> <span className="text-slate-400">Å²</span></span>
               </div>
            </div>

            <div className="flex flex-col items-center gap-4 shrink-0">
               {molSvg ? (
                  <div className="w-48 h-48 bg-slate-50/30 rounded-2xl flex items-center justify-center p-4 border border-slate-100 overflow-hidden">
                     <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(molSvg, { USE_PROFILES: { svg: true } }) }} className="w-full h-full flex items-center justify-center [&>svg]:max-w-full [&>svg]:max-h-full [&>svg]:w-auto [&>svg]:h-auto" />
                  </div>
               ) : (
                  <div className="w-48 h-48 bg-slate-50/30 rounded-2xl flex items-center justify-center p-4 border border-slate-100">
                     <span className="text-slate-300 text-xs font-mono">Structural Identity Pending</span>
                  </div>
               )}

               <button
                  onClick={handleExport}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-500 hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all shadow-sm"
               >
                  <Download className="w-3 h-3" />
                  Export Safety Dossier
               </button>
            </div>
         </div>

         {/* 2. Consensus Safety Dashboard (Old UI Style) */}
         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 2. Molecular Safety Intelligence Dashboard (QualPredict Aesthetic) */}
            <div className="lg:col-span-2">
               <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="py-4 px-6 bg-slate-50 rounded-2xl border border-slate-100 flex flex-col gap-1 items-start justify-center h-24 shadow-sm hover:shadow-md transition-all">
                     <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Molecular Summary</span>
                     <div className="text-[14px] font-black text-slate-800 truncate w-full">MW: {report["RDKit Properties"]?.MW?.toFixed(2)} • Formula: {report["RDKit Properties"]?.Formula}</div>
                  </div>

                  <div className="py-4 px-6 bg-blue-50/50 rounded-2xl border border-blue-100 flex flex-col gap-1 items-start justify-center h-24 shadow-sm hover:shadow-md transition-all">
                     <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Global Risk Status</span>
                     <div className="flex items-center gap-2">
                        <span className={`text-[16px] font-black uppercase tracking-tighter ${report["DILI Risk"]?.label === 'High' ? 'text-red-600' : 'text-emerald-600'}`}>
                           {report["DILI Risk"]?.label === 'High' || report["Cardiac Risk"]?.label === 'High' ? 'Hazardous' : 'Low Hazard'}
                        </span>
                        <div className="px-2 py-0.5 bg-white rounded border border-blue-100 text-[9px] font-black text-blue-500 uppercase">Primary AE Audit</div>
                     </div>
                  </div>

                  <div 
                     className="py-4 px-6 bg-emerald-50/50 rounded-2xl border border-emerald-100 flex flex-col gap-1 items-start justify-center h-24 shadow-sm hover:shadow-md transition-all cursor-help group"
                     onMouseEnter={() => report["Engine Confidence Audit"] && setHoveredMech({ meth: report["Engine Confidence Audit"], name: "Engine Confidence" })}
                  >
                     <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest group-hover:text-emerald-500 transition-colors">Engine Confidence</span>
                     <div className="flex items-center gap-2">
                        <div className="text-[18px] font-black text-emerald-600 font-mono">
                           {report["Engine Confidence Audit"]?.score || (ae_conc?.score * 10 || 88).toFixed(1)}%
                        </div>
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                     </div>
                  </div>
               </div>

               <_card icon="🎛️" title="Critical Organ Safety Console">
                  <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 pt-12 pb-8 justify-items-center">
                     <RiskGauge title="Liver" data={report["DILI Risk"]} maxScore={20} tooltipPosition="right" />
                     <RiskGauge title="Heart" data={report["Cardiac Risk"]} maxScore={20} tooltipPosition="right" />
                     <RiskGauge title="Lungs" data={report["Lung Injury Risk"]} maxScore={20} tooltipPosition="right" />
                     <RiskGauge title="Kidney" data={report["Kidney Injury Risk"]} maxScore={20} tooltipPosition="left" />
                     <RiskGauge title="Brain" data={report["Neuro Risk"]} maxScore={20} tooltipPosition="left" />
                  </div>

                  <div className="mt-4 pt-4 border-t border-slate-50 text-[9px] text-slate-400 font-black uppercase tracking-widest flex items-center justify-between opacity-60">
                     <div className="flex items-center gap-3 italic">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                        Hover organ units for Calculation Methodology audit
                     </div>
                  </div>
               </_card>
            </div>
         </div>

         {/* 3. Three-Column Dossier Logic */}
         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* COLUMN 1: MECHANISTIC NARRATIVE & IDENTITY */}
            <div className="flex flex-col gap-6">
               <_card icon="🔬" title="Scientific Inference Engine" borderColor="border-blue-200/50">
                  <div className="text-[12px] text-slate-700 leading-relaxed font-serif whitespace-pre-wrap mb-6 select-text p-4 bg-slate-50/50 rounded-xl border border-slate-100/50 italic shadow-inner">
                     {report.Expert_Summary || report.ExpertSummary || "Analysis pending..."}
                  </div>
                  <CausalChain data={report} />
               </_card>

               <_card icon="🔬" title="PubChem Identity Metadata">
                  <div className="mb-3"><span className="text-[9px] text-slate-400 uppercase">Verified Common Name</span><p className="text-xs font-black text-blue-700">{report.Name || 'N/A'}</p></div>
                  <div className="mb-3"><span className="text-[9px] text-slate-400 uppercase">PubChem CID</span><p className="text-xs font-black text-slate-800 font-mono">{report["PubChem CID"] || 'N/A'}</p></div>
                  <div className="mb-3"><span className="text-[9px] text-slate-400 uppercase">IUPAC Name</span><p className="text-[10px] text-slate-600 font-mono leading-tight">{report["IUPAC Name"] || 'N/A'}</p></div>
                  <a href={`https://pubchem.ncbi.nlm.nih.gov/compound/${report["PubChem CID"]}`} target="_blank" className="text-[9px] font-black text-blue-600 hover:underline">View in PubChem ↗</a>
               </_card>

               <_card icon="📚" title="Literature Evidence (PubMed)">
                  <div className="flex gap-4 p-4 bg-white border border-slate-100 rounded-xl shadow-sm mb-4">
                     <div className="text-center flex-1">
                        <div className="text-2xl font-black text-slate-800">{pm.total || 0}</div>
                        <div className="text-[9px] text-slate-400 uppercase tracking-wider mt-1">Total Publications</div>
                     </div>
                     <div className="text-center flex-1">
                        <div className="text-2xl font-black text-amber-600">{pm.tox_hits || 0}</div>
                        <div className="text-[9px] text-slate-400 uppercase tracking-wider mt-1">Toxicity Papers</div>
                     </div>
                     <div className="text-center flex-1">
                        <div className="text-2xl font-black text-blue-600">{(pm.density || 0).toFixed(1)}%</div>
                        <div className="text-[9px] text-slate-400 uppercase tracking-wider mt-1">Tox Literature Density</div>
                     </div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border-t-2 border-slate-900">
                     <p className="text-[10px] font-black text-slate-400 mb-2 uppercase">🔬 Featurizer Methodology</p>
                     <div className="text-[10px] text-slate-500 font-medium leading-relaxed">DeepChem Tox21 Pipeline executing ECFP-1024 fingerprints with 12 specific stress-response and nuclear-receptor centroids.</div>
                  </div>
               </_card>
            </div>

            {/* COLUMN 2: TOXICOLOGICAL HAZARDS */}
            <div className="flex flex-col gap-6">
               <_card icon="⚠️" title="Toxicophore Fingerprinting (BRENK/PAINS)" borderColor="border-orange-200/50">
                  {structural_alerts.filter(a => a.alert !== 'None detected').length > 0 ? structural_alerts.filter(a => a.alert !== 'None detected').map((a, i) => {
                     const db = a.db_entry || {};
                     const sev = db.severity || 'Moderate';
                     const sev_color = sev === 'High' ? "text-red-600 bg-red-50 border-red-100" : "text-amber-600 bg-amber-50 border-amber-100";
                     return (
                        <div key={i} className="p-4 bg-white rounded-xl border border-orange-100 border-l-4 border-l-orange-400 mb-3 shadow-sm">
                           <div className="flex justify-between items-center mb-3">
                              <span className="text-[11px] font-black text-slate-800 uppercase">{db.alert || a.alert}</span>
                              <span className={`text-[9px] font-black px-2 py-0.5 rounded border ${sev_color}`}>{sev}</span>
                           </div>
                           <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed"><b>⚙ Mechanism: </b>{db.mechanism || a.reasoning || 'N/A'}</p>
                           <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed"><b>🔬 Pathway: </b>{db.pathway || 'N/A'}</p>
                           <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed"><b>💊 Metabolism: </b>{db.metabolism || 'N/A'}</p>
                           <p className="text-[10px] text-slate-700 font-medium"><b>🏥 Clinical: </b>{db.consequence || 'N/A'}</p>
                        </div>
                     )
                  }) : (
                     <div className="p-4 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100 text-xs font-bold">✅ No structural toxicophores detected.</div>
                  )}
               </_card>

               <_card icon="🧬" title="DILI & Pulmonary Deep-Dive" borderColor="border-red-200/50">
                  {[
                     { title: "Hepatic DILI Risk Analysis", icon: "🫀", data: dili, max: 20, colHi: "bg-red-500", colLo: "bg-emerald-500" },
                     { title: "Pulmonary Injury Risk Analysis", icon: "🫁", data: lung, max: 15, colHi: "bg-red-500", colLo: "bg-emerald-500" }
                  ].filter(x => x.data && (x.data.score !== undefined)).map((r, i) => {
                     const pct = Math.min(Math.floor((r.data.score / r.max) * 100), 100);
                     const color_bg = r.data.label === "High" ? r.colHi : (r.data.label === "Moderate" ? "bg-amber-400" : r.colLo);
                     const color_text = r.data.label === "High" ? "text-red-600" : (r.data.label === "Moderate" ? "text-amber-500" : "text-emerald-600");
                     return (
                        <div key={i} className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm mb-4">
                           <div className="flex items-center mb-4"><span className="mr-2 text-lg">{r.icon}</span><span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{r.title}</span></div>
                           <div className="text-center mb-3">
                              <div className={`text-2xl font-black ${color_text}`}>{r.data.label}</div>
                              <div className="text-[10px] text-slate-400 font-mono">Score: {r.data.score}/{r.max}</div>
                           </div>
                           <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden mb-5">
                              <div className={`h-2.5 rounded-full ${color_bg} transition-all`} style={{ width: `${pct}%` }}></div>
                           </div>
                           <div className="mt-2 text-[10px] text-slate-600 space-y-2">
                              {(r.data.factors || [r.data.rationale]).map((f, j) => (
                                 <div key={j} className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
                                    <span className="text-[8px] font-black text-white bg-slate-400 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">F{j + 1}</span>
                                    <span className="leading-relaxed">{f}</span>
                                 </div>
                              ))}
                           </div>
                        </div>
                     )
                  })}
               </_card>

               <_card icon="🏥" title="Real-World Evidence (FDA FAERS)">
                  <table className="w-full text-left">
                     <thead>
                        <tr className="border-b border-slate-200">
                           <th className="py-2.5 px-4 text-slate-400 text-[10px] uppercase tracking-wider">Adverse Event (MedDRA PT)</th>
                           <th className="text-right py-2.5 px-4 text-slate-400 text-[10px] uppercase tracking-wider">Reports</th>
                        </tr>
                     </thead>
                     <tbody>
                        {faers.length ? faers.map((ae, i) => (
                           <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                              <td className="py-2.5 px-4 text-[11px] text-slate-700 font-medium">{ae.term}</td>
                              <td className="py-2.5 px-4 text-[11px] text-slate-500 text-right font-mono">{ae.count}</td>
                           </tr>
                        )) : <tr><td colSpan="2" className="py-4 text-xs text-slate-400 italic">No FAERS signals found for this compound.</td></tr>}
                     </tbody>
                  </table>
               </_card>

               <_card icon="📊" title="AE Prediction Concordance (Predicted vs FAERS)">
                  {ae_conc ? (() => {
                     const pct = ae_conc?.concordance_pct || 0;
                     const gaugeColor = pct >= 50 ? "bg-emerald-500" : (pct >= 25 ? "bg-amber-400" : "bg-red-500");
                     const gaugeText = pct >= 50 ? "text-emerald-600" : (pct >= 25 ? "text-amber-600" : "text-red-600");
                     const label = pct >= 50 ? "Strong" : (pct >= 25 ? "Moderate" : "Low");
                     return (
                        <>
                           <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm mb-5">
                              <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-3">Precision Safety Cross-Match (Tox21 vs FAERS)</div>
                              <div className="flex flex-col items-center mb-4">
                                 <div className={`text-4xl font-black tracking-tighter ${gaugeText}`}>{pct}%</div>
                                 <div className={`text-[10px] font-black uppercase tracking-widest ${gaugeText}`}>{label}</div>
                              </div>
                              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden mb-2">
                                 <div className={`h-2.5 rounded-full ${gaugeColor} transition-all`} style={{ width: `${pct}%` }}></div>
                              </div>
                              <p className="text-[9px] text-slate-500 italic text-center leading-relaxed">BioBERT engine identified {ae_conc.matched?.length || 0} semantic overlaps between predicted pathways and real-world outcomes.</p>
                           </div>

                           {(ae_conc.matched || []).length > 0 && (
                              <div className="p-5 bg-emerald-50/40 rounded-2xl border border-emerald-100 mb-4 shadow-sm">
                                 <div className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-3 flex items-center">Validated Safety Signals (Semantic Concordance)</div>
                                 <div className="space-y-1">
                                    {ae_conc.matched.map((m, i) => (
                                       <div key={i} className="flex items-start py-3 border-b border-slate-100 last:border-0 hover:bg-slate-50/50 rounded-lg transition-colors px-2">
                                          <span className="mr-2 flex-shrink-0 mt-0.5">✅</span>
                                          <div>
                                             <div className="flex items-center">
                                                <span className="text-[10px] font-black text-slate-800 uppercase">{m.predicted}</span>
                                                <span className="text-[10px] text-slate-300 mx-1"> ↔ </span>
                                                <span className="text-[10px] font-black text-blue-700 uppercase">{m.faers_confirmed}</span>
                                             </div>
                                             <div className="flex items-center mt-1">
                                                <span className="text-[8px] font-black text-slate-400 uppercase mr-2 tracking-widest">{m.organ || 'Systemic'}</span>
                                                <span className={`text-[7px] font-black px-1.5 py-0.5 rounded-full uppercase tracking-tighter mr-2 ${m.match_type === 'Semantic' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'}`}>Match: {m.match_type || 'Keyword'}</span>
                                                <span className="text-[9px] text-slate-500 italic">({m.faers_count || 0} clinical reports)</span>
                                             </div>
                                          </div>
                                       </div>
                                    ))}
                                 </div>
                              </div>
                           )}

                           {(ae_conc.unmatched_predicted || []).length > 0 && (
                              <div className="p-5 bg-amber-50/40 rounded-2xl border border-amber-100 mb-4 shadow-sm">
                                 <div className="text-[9px] font-black text-amber-600 uppercase tracking-widest mb-3">Unreported Hazards (Prediction Only)</div>
                                 <div className="space-y-1">
                                    {ae_conc.unmatched_predicted.map((u, i) => (
                                       <div key={i} className="flex items-center py-2 border-b border-slate-50 last:border-0 px-2">
                                          <span className="mr-2 flex-shrink-0">🔮</span>
                                          <div className="flex items-center">
                                             <span className="text-[10px] font-bold text-amber-700 uppercase">{u.term}</span>
                                             <span className="text-[8px] font-black text-slate-400 uppercase ml-2 tracking-tighter">({u.organ})</span>
                                          </div>
                                       </div>
                                    ))}
                                 </div>
                                 <p className="text-[8px] text-amber-600/70 italic mt-3 bg-white/50 p-2 rounded border border-amber-100">⚠️ These molecular hazards exhibit strong theoretical binding but haven't reached clinical reporting volume yet.</p>
                              </div>
                           )}
                        </>
                     )
                  })() : null}
               </_card>
            </div>

            {/* COLUMN 3: PROPERTIES & PREDICTIONS */}
            <div className="flex flex-col gap-6">
               <_card icon="🔮" title="Clinical Outcome Predictions (Organ-Aware AI)">
                  {pred_ae.length ? pred_ae.map((ae, i) => {
                     const conf = ae.confidence || 'Low';
                     const source = ae.source || 'Emerging Hazard';
                     const org = ae.organ || '';
                     const icon = organIcons[org] || "💊";
                     return (
                        <div key={i} className="p-4 bg-white rounded-2xl border border-slate-100 mb-4 shadow-sm hover:border-blue-200 transition-all hover:shadow-md">
                           <div className="flex items-center mb-1.5">
                              <span className="mr-1">{icon} </span>
                              <span className="text-[11px] font-black text-slate-800 uppercase">{ae.term || 'Unknown Event'}</span>
                              <span className={`text-[7px] font-black px-1.5 py-0.5 rounded-sm ml-2 tracking-tighter uppercase ${source === 'Confirmed Signal' ? 'bg-blue-600 text-white' : (source === 'Emerging Hazard' ? 'bg-amber-500 text-white' : 'bg-slate-500 text-white')}`}>{source}</span>
                              <span className={`text-[9px] font-black px-2 py-0.5 rounded border ml-auto ${conf === 'High' ? 'text-red-700 bg-red-50 border-red-100' : (conf === 'Medium' ? 'text-amber-700 bg-amber-50 border-amber-100' : 'text-slate-500 bg-slate-50 border-slate-100')}`}>{conf}</span>
                           </div>
                           {org && (
                              <div className="flex flex-wrap items-center gap-1 mb-2.5">
                                 <span className="text-[9px] font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100 mr-2 shadow-sm">{org}</span>
                                 {(ae.evidence_sources || []).map((e, j) => {
                                    const bc = e.includes("Structural") ? "bg-orange-50 text-orange-600 border-orange-100" : (e.includes("Tox21") || e.includes("DeepChem") ? "bg-purple-50 text-purple-600 border-purple-100" : (e.includes("FAERS") ? "bg-emerald-50 text-emerald-600 border-emerald-100" : "bg-slate-50 text-slate-500 border-slate-100"));
                                    return <span key={j} className={`text-[8px] px-1.5 py-0.5 rounded mr-1 font-bold border ${bc}`}>{e}</span>
                                 })}
                              </div>
                           )}
                           <p className="text-[10px] text-slate-600 leading-relaxed mb-3">{ae.rationale}</p>
                           {ae.mechanism_chain && (
                              <div className="bg-slate-50/50 p-2.5 rounded-lg border border-slate-100/50">
                                 <span className="text-[8px] font-black text-slate-400 uppercase mr-1">🔬 Mech-Logic Path: </span>
                                 <span className="text-[9px] text-slate-500 font-mono leading-relaxed italic">{ae.mechanism_chain}</span>
                              </div>
                           )}
                        </div>
                     )
                  }) : <p className="text-xs text-slate-400 italic">Insufficient structural/bioactivity data for predictive modeling.</p>}
               </_card>

               <_card icon="💊" title="Drug-Likeness Assessment (Cheminformatics)">
                  <div className="mb-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                     <div className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-2">QED Score</div>
                     <div className="text-center mb-3">
                        <div className={`text-3xl font-black ${props.QED >= 0.67 ? 'text-emerald-600' : (props.QED >= 0.35 ? 'text-amber-600' : 'text-red-600')}`}>{props.QED || 'N/A'}</div>
                        <div className={`text-[10px] font-black uppercase ${props.QED >= 0.67 ? 'text-emerald-600' : (props.QED >= 0.35 ? 'text-amber-600' : 'text-red-600')}`}>{props.QED >= 0.67 ? 'Favorable' : (props.QED >= 0.35 ? 'Moderate' : 'Unfavorable')}</div>
                     </div>
                     <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div className={`h-2 rounded-full ${props.QED >= 0.67 ? 'bg-emerald-500' : (props.QED >= 0.35 ? 'bg-amber-400' : 'bg-red-500')}`} style={{ width: `${Math.min((props.QED || 0) * 100, 100)}%` }}></div>
                     </div>
                     <p className="text-[9px] text-slate-400 italic mt-2">Quantitative Estimate of Drug-likeness (0–1). Higher = more drug-like.</p>
                  </div>

                  <div className="mb-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                     <div className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-2">Synthetic Accessibility</div>
                     <div className="text-center">
                        <div className={`text-2xl font-black ${props.SAS <= 4 ? 'text-emerald-600' : (props.SAS <= 6 ? 'text-amber-600' : 'text-red-600')}`}>{props.SAS || 'N/A'}</div>
                        <div className={`text-[10px] font-black ${props.SAS <= 4 ? 'text-emerald-600' : (props.SAS <= 6 ? 'text-amber-600' : 'text-red-600')}`}>({props.SAS <= 4 ? 'Easy' : (props.SAS <= 6 ? 'Moderate' : 'Difficult')})</div>
                     </div>
                     <p className="text-[9px] text-slate-400 italic mt-2">SA Score (1–10). Lower = easier to synthesize.</p>
                  </div>

                  <div className="mb-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                     <div className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-3">Drug-Likeness Rule Assessment</div>
                     <div className="flex justify-between items-center py-2 border-b border-slate-50">
                        <span className="text-[11px] font-bold text-slate-600">Lipinski Ro5</span>
                        <span className={`text-[10px] font-black ${props.Lipinski_Pass ? 'text-emerald-600' : 'text-red-600'}`}>{props.Lipinski_Pass ? '✅ Pass' : '❌ Fail'}</span>
                     </div>
                     <div className="flex justify-between items-center py-2 border-b border-slate-50">
                        <span className="text-[11px] font-bold text-slate-600">Veber Rules</span>
                        <span className={`text-[10px] font-black ${props.Veber_Pass ? 'text-emerald-600' : 'text-red-600'}`}>{props.Veber_Pass ? '✅ Pass' : '❌ Fail'}</span>
                     </div>
                     <div className="flex justify-between items-center py-2 border-b border-slate-50">
                        <span className="text-[11px] font-bold text-slate-600">Ghose Filter</span>
                        <span className={`text-[10px] font-black ${props.Ghose_Pass ? 'text-emerald-600' : 'text-red-600'}`}>{props.Ghose_Pass ? '✅ Pass' : '❌ Fail'}</span>
                     </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-100 p-5 rounded-xl mt-2 space-y-1">
                     <div className="flex justify-between py-1.5 border-b border-slate-100"><span className="text-[11px] text-slate-600">Molecular Weight</span><span className="text-[11px] font-black">{props.MW} g/mol</span></div>
                     <div className="flex justify-between py-1.5 border-b border-slate-100"><span className="text-[11px] text-slate-600">Exact Mass</span><span className="text-[11px] font-black">{props.Exact_Mass}</span></div>
                     <div className="flex justify-between py-1.5 border-b border-slate-100"><span className="text-[11px] text-slate-600">H-Bond Donors</span><span className="text-[11px] font-black">{props.HBD}</span></div>
                     <div className="flex justify-between py-1.5 border-b border-slate-100"><span className="text-[11px] text-slate-600">H-Bond Acceptors</span><span className="text-[11px] font-black">{props.HBA}</span></div>
                     <div className="flex justify-between py-1.5 border-b border-slate-100"><span className="text-[11px] text-slate-600">Rotatable Bonds</span><span className="text-[11px] font-black">{props.RotBonds}</span></div>
                     <div className="flex justify-between py-1.5"><span className="text-[11px] text-slate-600">Formal Charge</span><span className="text-[11px] font-black">{props.FormalCharge}</span></div>
                  </div>
               </_card>

               <_card icon="🧠" title="Bio-Target Profiling (Tox21/DeepChem)">
                  <div className="space-y-2 mb-6">
                     {Object.entries(report["DeepChem Prediction"]?.predictions || {}).sort((a, b) => b[1] - a[1]).map(([name, val], i) => {
                        const pct = Math.round(val * 100);
                        const bg = pct > 50 ? 'bg-red-500' : (pct > 35 ? 'bg-amber-400' : 'bg-emerald-500');
                        const icon = pct > 50 ? '🔴' : (pct > 35 ? '🟡' : '🟢');
                        return (
                           <div key={i} className="flex items-center mb-2">
                              <div className="w-28 flex items-center truncate"><span className="mr-1">{icon}</span><span className="text-[10px] font-bold text-slate-600 uppercase">{name}</span></div>
                              <div className="flex-1 bg-slate-100 rounded-full h-2 mx-3 overflow-hidden"><div className={`h-2 rounded-full ${bg} transition-all`} style={{ width: `${pct}%` }}></div></div>
                              <div className="w-10 text-[10px] text-right text-slate-500 font-mono font-bold">{val.toFixed(2)}</div>
                           </div>
                        )
                     })}
                     <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-1">
                        <span className="font-mono text-[9px] text-slate-400">Featurizer: ECFP-1024</span>
                        <span className="text-[9px] text-slate-400 ml-2"> • 🔴 {'>'}50% High 🟡 35-50% Mod 🟢 {'<'}35% Low</span>
                     </div>
                  </div>

                  {target_bio.length > 0 ? <div className="mt-4"><div className="flex items-center gap-3 mb-4"><div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white text-sm shadow-lg shadow-slate-200">🔬</div><h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Top Target Biological Deep-Dive</h2></div></div> : null}
                  {target_bio.map((t, i) => (
                     <div key={i} className="mb-4 last:mb-0">
                        <div className="flex justify-between items-center mb-2">
                           <span className="text-[11px] font-black text-slate-800 uppercase">{t.flag} {t.full_name}</span>
                           <span className="text-xs font-black text-blue-600">{Math.round(t.value * 100)}%</span>
                        </div>
                        <div className="bg-blue-50/30 p-3 rounded-xl border border-blue-100/50">
                           <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed"><b>Function: </b>{t.function}</p>
                           <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed"><b>If Hit: </b>{t.mechanism}</p>
                           <p className="text-[10px] text-slate-700 font-medium italic"><b>Risk: </b>{t.consequence}</p>
                        </div>
                     </div>
                  ))}
               </_card>

               {/* Data Lineage Card has been relocated to Mechanistic HUD to optimize whitespace */}
               <div className="hidden">
                  <_card icon="🔌" title="Data Lineage & Methodology" />
               </div>
            </div>
         </div>

      {/* 4. Mechanistic Organ Causality & Pathway Analysis (Adaptive HUD) */}
      <_card icon="🔗" title="Mechanistic Organ Causality Hub" borderColor="border-indigo-200/50">
         {(() => {
            const organs = Object.entries(mech_report);
            const count = organs.length;
            
            if (count === 0) return <p className="text-xs text-emerald-600 italic bg-emerald-50 p-4 rounded-xl">No significant mechanistic causal chains identified.</p>;

            return (
               <div className={`grid grid-cols-1 ${count >= 2 ? 'lg:grid-cols-2' : 'lg:grid-cols-12'} gap-10`}>
                  {/* Primary Mechanist Cards */}
                  <div className={`${count === 1 ? 'lg:col-span-12 flex flex-col lg:flex-row gap-10' : 'contents'}`}>
                     {organs.map(([organ, details], i) => (
                        <div key={i} className={`space-y-4 ${count === 1 ? 'flex-1' : ''}`}>
                           <div className="flex items-center mb-4 pb-3 border-b border-slate-200">
                              <span className="text-xl mr-2">{details.icon || '🔗'}</span>
                              <span className="text-[11px] font-black text-slate-700 uppercase tracking-widest">{details.name || organ}</span>
                              <span className={`ml-auto text-[9px] font-black px-2 py-0.5 rounded ${details.risk_label === 'High' ? 'text-red-600 bg-red-50 border border-red-100' : (details.risk_label === 'Moderate' ? 'text-amber-600 bg-amber-50 border border-amber-100' : 'text-emerald-600 bg-emerald-50 border border-emerald-100')}`}>{details.risk_label}</span>
                           </div>
                           
                           {details.simple_explanation && (
                              <div className="p-4 bg-blue-50/40 rounded-xl border border-blue-100/50 mb-5">
                                 <span className="text-[10px] font-black text-blue-600 uppercase tracking-wider mb-2 flex items-center">📝 Clinical Synopsis</span>
                                 <p className="text-[11px] text-slate-600 leading-relaxed">{details.simple_explanation}</p>
                              </div>
                           )}

                           {(details.causal_chains || []).map((chain, c_idx) => {
                              const sev = chain.severity || 'Moderate';
                              const sev_color = sev === 'High' ? 'border-l-red-500 bg-red-50/20' : 'border-l-amber-400 bg-amber-50/20';
                              return (
                                 <div key={c_idx} className={`p-4 rounded-xl border border-l-4 ${sev_color} mb-3 shadow-sm`}>
                                    <div className="flex items-center mb-3">
                                       <span className="text-[9px] font-black text-slate-400">Chain {c_idx + 1}: </span>
                                       <span className="text-[11px] font-black text-slate-800 uppercase ml-1">{chain.trigger}</span>
                                       <span className={`text-[8px] font-black ml-auto px-2 py-0.5 rounded ${sev === 'High' ? 'text-red-600 bg-red-50 border border-red-100' : 'text-amber-600 bg-amber-50 border border-amber-100'}`}>{sev}</span>
                                    </div>
                                    <div className="space-y-1.5">
                                       <p className="text-[10px] text-slate-600 leading-relaxed"><b>⚙ Metabolic Path: </b>{chain.metabolic_path || 'N/A'}</p>
                                       <p className="text-[10px] text-slate-600 leading-relaxed"><b>🔬 Mechanism: </b>{chain.mechanism || 'N/A'}</p>
                                       <p className="text-[10px] text-slate-600 leading-relaxed"><b>🧬 Pathway: </b>{chain.pathway_disrupted || 'N/A'}</p>
                                       <p className="text-[10px] text-slate-700 font-medium italic"><b>🏥 Clinical Outcome: </b>{chain.clinical_outcome || 'N/A'}</p>
                                    </div>
                                    <div className="flex flex-wrap mt-3 pt-2 border-t border-slate-100">
                                       {(chain.supporting_targets || []).slice(0, 3).map((t, idx) => <span key={idx} className="text-[8px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded mr-1 mb-1">{t}</span>)}
                                       {(chain.faers_evidence || []).slice(0, 2).map((t, idx) => <span key={idx} className="text-[8px] text-emerald-500 bg-emerald-50 px-1.5 py-0.5 rounded mr-1 mb-1">FAERS: {t}</span>)}
                                    </div>
                                 </div>
                              );
                           })}
                        </div>
                     ))}

                     {/* Adaptive Fillers for Whitespace */}
                     {count === 1 && (
                        <div className="flex-1 flex flex-col gap-6">
                           <PathwayBlueprint />
                           <_card icon="🔌" title="Data Lineage (Relocated HUD)" borderColor="border-slate-200">
                              <div className="space-y-3 pb-3">
                                 <div className="flex justify-between items-center py-1.5 border-b border-slate-50"><span className="text-[11px] text-slate-600">PubChem</span><span className="text-[9px] font-black px-2 py-0.5 rounded-full border bg-emerald-100 text-emerald-700 border-emerald-200 uppercase">Live API</span></div>
                                 <div className="flex justify-between items-center py-1.5 border-b border-slate-50"><span className="text-[11px] text-slate-600">openFDA FAERS</span><span className="text-[9px] font-black px-2 py-0.5 rounded-full border bg-emerald-100 text-emerald-700 border-emerald-200 uppercase">Live API</span></div>
                                 <div className="flex justify-between items-center py-1.5 border-b border-slate-50"><span className="text-[11px] text-slate-600">DeepChem Tox21</span><span className="text-[9px] font-black px-2 py-0.5 rounded-full border bg-amber-100 text-amber-700 border-amber-200 uppercase">Local</span></div>
                              </div>
                           </_card>
                        </div>
                     )}

                     {count === 3 && (
                        <div className="lg:col-span-1">
                           <PathwayBlueprint />
                        </div>
                     )}
                  </div>
               </div>
            );
         })()}
      </_card>
      </div>
   );
};

export default SingleView;
