import React from 'react';

const CausalChain = ({ data }) => {
  const chain = data['Causal Chain'] || [];
  
  if (!chain || chain.length === 0) {
    return (
      <div className="text-[10px] text-slate-400 italic py-4">
        No causal pathway identified for this molecular scaffold.
      </div>
    );
  }

  return (
    <div className="mt-4 border-l-2 border-slate-100 pl-4 space-y-2">
      {chain.map((step, i) => {
        const isLast = i === chain.length - 1;
        const isFirst = i === 0;

        return (
          <div key={i} className="flex group/chain">
            {/* Timeline element */}
            <div className="flex flex-col items-center mr-5 pt-1.5 relative">
              <div className={`w-3 h-3 rounded-full border-2 ${isFirst ? 'bg-indigo-600 border-indigo-200 shadow-[0_0_12px_rgba(79,70,229,0.4)]' : 'bg-white border-slate-300'} z-10 transition-all group-hover/chain:scale-125`} />
              {!isLast ? <div className="w-[2px] flex-1 bg-gradient-to-b from-slate-200 to-slate-50 my-1.5" /> : null}
              {isFirst && <div className="absolute top-1.5 w-3 h-3 rounded-full bg-indigo-500 animate-ping opacity-20" />}
            </div>

            {/* Content element */}
            <div className={`flex-1 ${!isLast ? 'pb-8' : 'pb-2'}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] font-mono">
                  {step.layer || 'Unknown'}
                </span>
                {isFirst && <span className="text-[8px] font-black bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded border border-indigo-100 uppercase tracking-tighter">Primary Trigger</span>}
              </div>
              <p className="text-[12px] font-black text-slate-900 leading-tight mb-1.5 tracking-tight group-hover/chain:text-indigo-700 transition-colors">
                {step.node || 'N/A'}
              </p>
              <div className="bg-slate-50/80 p-2.5 rounded-lg border border-slate-100 group-hover/chain:border-indigo-100 transition-all">
                <p className="text-[10px] text-slate-500 italic leading-relaxed select-text">
                  {step.evidence || 'Baseline molecular evidence recorded.'}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CausalChain;
