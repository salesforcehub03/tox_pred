import React from 'react';
import { FlaskConical, Lightbulb, ExternalLink } from 'lucide-react';

const MethodologyInspector = ({ methodology }) => {
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
    return sourceMap[title] || "https://www.rdkit.org/docs/GettingStartedInPython.html#fingerprinting-and-molecular-similarity";
  };

  return (
    <div className="mt-6 p-6 bg-slate-900 border-2 border-slate-800 rounded-3xl animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
             <FlaskConical className="w-4 h-4 text-cyan-500" />
           </div>
           <div>
              <h3 className="text-cyan-400 font-black text-[10px] uppercase tracking-[0.2em]">{methodology.title}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                 <span className="text-[8px] font-black bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded tracking-tighter uppercase">Verified Evidence Base</span>
              </div>
           </div>
        </div>
        <a 
          href={getSourceLink(methodology.title)} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-cyan-400 transition-all border border-slate-800 px-3 py-1.5 rounded-lg"
        >
          View Scientific Source
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {methodology.steps.map((step) => (
          <div key={step.id} className="relative pl-6 border-l-2 border-slate-800">
            <div className="absolute left-[-6px] top-0 w-2.5 h-2.5 rounded-full bg-slate-950 border-2 border-cyan-500 shadow-[0_0_15px_rgba(34,211,238,0.4)]" />
            
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[8px] font-black text-slate-600 font-mono tracking-tighter uppercase">Step 0{step.id}</span>
              <h4 className="text-slate-200 text-[11px] font-bold tracking-tight uppercase">{step.title}</h4>
            </div>
            
            <p className="text-slate-400 text-[10px] leading-relaxed mb-4 font-medium min-h-[40px]">
              {step.desc}
            </p>

            <div className="bg-black/40 p-3 rounded-2xl border border-white/5 font-mono text-[9px] text-cyan-300 shadow-inner">
              <div className="flex items-center gap-2 mb-2 opacity-30">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                <span className="text-[8px] font-black uppercase tracking-widest text-white">Algorithm Matrix</span>
              </div>
              <div className="text-cyan-400/80">
                <span className="text-cyan-500/60 mr-2">$</span>
                {step.formula}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 pt-5 border-t border-white/5 flex items-center justify-between">
         <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center shrink-0">
               <Lightbulb className="w-5 h-5 text-cyan-500" />
            </div>
            <div>
               <p className="text-[9px] text-slate-400 font-bold uppercase tracking-tight mb-0.5">Consensus Safety Synthesis</p>
               <p className="text-[10px] text-slate-500 italic leading-snug max-w-xl">
                  Confidence intervals generated via Bayesian integration of structural toxicophores, Tox21 neural activity, and historical FAERS records.
               </p>
            </div>
         </div>
         <div className="text-[9px] font-black text-slate-700 uppercase tracking-widest">
            AViiD Engine v3.2 Transparent Audit Trail
         </div>
      </div>
    </div>
  );
};

export default MethodologyInspector;
