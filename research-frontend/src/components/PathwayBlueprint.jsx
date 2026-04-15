import React from 'react';
import { Network, Database, BrainCircuit, Activity } from 'lucide-react';

/**
 * PathwayBlueprint - A visual schematic for filling whitespace in causality reports.
 * Displays a high-fidelity "Scientific Logic Map" of how the platform connects findings.
 */
const PathwayBlueprint = () => {
  return (
    <div className="w-full h-full min-h-[300px] bg-slate-900 rounded-2xl border-2 border-indigo-500/20 p-8 flex flex-col relative overflow-hidden group">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:20px_20px]" />
      
      <div className="relative z-10 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-8">
           <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Network className="w-6 h-6" />
           </div>
           <div>
              <h4 className="text-[12px] font-black text-white uppercase tracking-wider">Causality Pathway HUD</h4>
              <p className="text-[9px] text-slate-400 font-mono italic">Mechanistic Logic Visualization v3.2</p>
           </div>
        </div>

        {/* Visual Flow Schematic */}
        <div className="flex-1 flex flex-col gap-6 justify-center">
            {/* Step 1: Input */}
            <div className="flex items-center gap-4 group/step">
               <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 group-hover/step:border-indigo-500 transition-colors">
                  <Database className="w-4 h-4" />
               </div>
               <div className="flex-1 border-b border-dashed border-slate-800 pb-2">
                  <span className="text-[10px] font-black text-slate-500 uppercase">Input Layer</span>
                  <div className="text-[11px] text-indigo-400 font-mono">Molecular Fingerprint (ECFP4)</div>
               </div>
            </div>

            {/* Step 2: Inference */}
            <div className="flex items-center gap-4 group/step ml-4">
               <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 group-hover/step:border-blue-500 transition-colors">
                  <BrainCircuit className="w-4 h-4" />
               </div>
               <div className="flex-1 border-b border-dashed border-slate-800 pb-2">
                  <span className="text-[10px] font-black text-slate-500 uppercase">Inference Engine</span>
                  <div className="text-[11px] text-blue-400 font-mono">GNN-Assisted Target Mapping</div>
               </div>
            </div>

            {/* Step 3: Synthesis */}
            <div className="flex items-center gap-4 group/step ml-8">
               <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 group-hover/step:border-emerald-500 transition-colors">
                  <Activity className="w-4 h-4" />
               </div>
               <div className="flex-1 border-b border-dashed border-slate-800 pb-2">
                  <span className="text-[10px] font-black text-slate-500 uppercase">Synthesis Layer</span>
                  <div className="text-[11px] text-emerald-400 font-mono">Organ-Aware Risk Consolidation</div>
               </div>
            </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex justify-between items-center opacity-40grayscale group-hover:grayscale-0 transition-all">
           <div className="flex -space-x-2">
              <div className="w-6 h-6 rounded-full bg-slate-700 border-2 border-slate-900" />
              <div className="w-6 h-6 rounded-full bg-slate-600 border-2 border-slate-900" />
              <div className="w-6 h-6 rounded-full bg-indigo-900 border-2 border-slate-900" />
           </div>
           <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Active Audit Active</span>
        </div>
      </div>

      {/* Futuristic corner accent */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 blur-[60px] rounded-full" />
      <div className="absolute bottom-4 right-4 text-[7px] font-mono text-slate-700 uppercase vertical-text tracking-[0.3em]">PROVENANCE-SECURED</div>
    </div>
  );
};

export default PathwayBlueprint;
