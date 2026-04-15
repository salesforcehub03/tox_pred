import React from 'react';
import { FlaskConical, ExternalLink, ShieldCheck } from 'lucide-react';

const MethodologyTooltip = ({ methodology, organName }) => {
  if (!methodology) return null;

  const getSourceLink = (title) => {
    const sourceMap = {
      "Hepatotoxicity Audit (FDA Hy's Law)": "https://www.fda.gov/media/71742/download",
      "Cardiac Safety Audit (hERG / TdP Risk)": "https://www.nature.com/articles/nrd.2016.120",
      "Nephrotoxicity Audit (RTLI / Renal Risk)": "https://www.biorxiv.org/content/10.1101/2020.10.14.339614v1",
      "Neurotoxicity Audit (logBB / Brain Risk)": "https://www.nature.com/articles/srep17330",
      "Pulmonary Audit (Oxidative Stress / Lung)": "https://pubmed.ncbi.nlm.nih.gov/24564883/",
      "Genotoxicity Audit (DNA Damage / p53)": "https://www.fda.gov/media/79268/download",
      "Endocrine Disruptor Audit (OECD Guidance)": "https://www.oecd.org/env/test-no-455-performance-based-test-guideline-for-stably-transfected-transactivation-in-vitro-assays-to-detect-estrogen-receptor-agonists-and-antagonists-9789264263659-en.htm",
      "Gastrointestinal Audit (Mucosal Irritation)": "https://www.oecd-ilibrary.org/environment/test-no-437-bovine-corneal-opacity-and-permeability-test-method-for-identifying-i-ocular-corrosives-and-severe-irritants-and-ii-substances-not-requiring-classification-for-eye-irritation-or-serious-eye-damage_9789264203846-en"
    };
    return sourceMap[title] || "https://rdkit.org/";
  };

  return (
    <div className="w-[450px] bg-[#1a1b2e] border-2 border-slate-500 rounded-lg shadow-[0_45px_90px_-10px_rgba(0,0,0,0.9)] overflow-hidden animate-in fade-in zoom-in duration-200 ring-2 ring-black/50">
      {/* QualPredict Header Style */}
      <div className="px-6 py-4 border-b border-slate-700/30 flex items-center justify-between">
        <h3 className="text-blue-400 font-bold text-[11px] uppercase tracking-wider flex items-center gap-2">
          <FlaskConical className="w-4 h-4" />
          CALCULATION METHODOLOGY
        </h3>
        <div className="flex items-center gap-2">
           <a 
             href={getSourceLink(methodology.title)} 
             target="_blank" 
             rel="noopener noreferrer"
             className="text-slate-500 hover:text-white transition-colors"
           >
             <ExternalLink className="w-3.5 h-3.5" />
           </a>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {methodology.steps ? (
          methodology.steps.map((step, idx) => (
            <div key={idx} className="flex gap-4">
              <div className="shrink-0 w-6 h-6 rounded-full bg-indigo-500 flex items-center justify-center text-white text-[11px] font-black italic shadow-lg shadow-indigo-500/20">
                {idx + 1}
              </div>
              <div className="space-y-3">
                <h4 className="text-slate-100 text-[12px] font-bold tracking-tight">
                  {step.title || step.name}
                </h4>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  {step.desc || step.details}
                </p>
                <div className="bg-[#11121d] rounded-lg p-3 border border-slate-800/50 overflow-x-auto">
                   <code className="text-[11px] font-mono text-slate-300">
                      {step.formula}
                   </code>
                </div>
              </div>
            </div>
          ))
        ) : methodology.components ? (
          <div className="space-y-6">
            <div className="p-4 bg-indigo-500/10 rounded-xl border border-indigo-500/20 mb-6">
              <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-2">Calculated Aggregation Formula</span>
              <code className="text-[12px] font-mono text-indigo-300">{methodology.formula}</code>
            </div>
            {methodology.components.map((comp, idx) => (
              <div key={idx} className="flex gap-4">
                <div className="shrink-0 w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-[11px] font-black italic">
                  {idx + 1}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-slate-100 text-[12px] font-bold">{comp.name}</h4>
                    <span className="text-blue-400 font-mono text-[11px] font-bold">{comp.value}</span>
                  </div>
                  <p className="text-slate-500 text-[10px] italic">{comp.desc}</p>
                </div>
              </div>
            ))}
            {methodology.verification && (
              <div className="mt-6 p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Statistical Verification</span>
                </div>
                <p className="text-[11px] text-slate-400 font-mono">{methodology.verification}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-slate-500 text-[11px] italic">No detailed methodology breakdown available for this component.</p>
        )}

        <div className="pt-4 mt-4 border-t border-slate-700/30 flex items-center justify-between">
           <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Confidence Analysis Active</span>
           </div>
           <span className="text-[10px] font-mono text-slate-600">PRO-ENGINE v3.2</span>
        </div>
      </div>
    </div>
  );
};

export default MethodologyTooltip;
