import React, { useState } from 'react';
import MethodologyTooltip from './MethodologyTooltip';

const RiskGauge = ({ title, data, maxScore = 20, tooltipPosition = 'right' }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  if (!data) return null;
  
  const score = data.score || 0;
  const label = data.label || 'Unknown';
  const pct = Math.min(Math.round((score / maxScore) * 100), 100);

  const colors = {
    High: {
      text: 'text-red-600',
      bg: 'bg-red-500/5',
      border: 'border-red-200/50',
      bar: 'bg-red-500',
    },
    Moderate: {
      text: 'text-amber-600',
      bg: 'bg-amber-500/5',
      border: 'border-amber-200/50',
      bar: 'bg-amber-400',
    },
    Low: {
      text: 'text-emerald-600',
      bg: 'bg-emerald-500/5',
      border: 'border-emerald-200/50',
      bar: 'bg-emerald-500',
    },
    Neutral: {
      text: 'text-emerald-600',
      bg: 'bg-emerald-500/5',
      border: 'border-emerald-200/50',
      bar: 'bg-emerald-500',
    }
  };

  const theme = colors[label] || colors.Low;

  const tooltipPosClasses = tooltipPosition === 'right' 
    ? 'left-full ml-5 top-[-100px]' 
    : 'right-full mr-5 top-[-100px]';

  return (
    <div 
      className={`flex flex-col items-center group relative w-full max-w-[130px] transition-all duration-300
        ${showTooltip ? 'z-[1000] scale-[1.05]' : 'z-10'}
      `}
    >
      <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2 transition-colors group-hover:text-blue-500">
        {title}
      </div>
      
      <div 
        className={`relative w-full h-20 flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-300 cursor-help
          ${theme.bg} ${theme.border} hover:border-blue-400 hover:shadow-lg hover:shadow-blue-500/5 group-hover:translate-y-[-2px]`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className={`text-lg font-black tracking-tighter ${theme.text}`}>{label}</div>
        <div className="text-[9px] text-slate-400 font-mono font-bold">{score}/{maxScore}</div>

        {/* DIRECTIONAL POPOVER (QualPredict Aesthetic) */}
        {showTooltip && data.methodology && (
          <div className={`absolute z-[500] pointer-events-none animate-in fade-in zoom-in duration-200 ${tooltipPosClasses}`}>
            <MethodologyTooltip 
              methodology={data.methodology} 
              organName={title} 
            />
          </div>
        )}
      </div>

      <div className="w-[80%] bg-slate-100 rounded-full h-1 overflow-hidden mt-3 transition-all group-hover:w-full">
        <div 
          className={`h-1 rounded-full ${theme.bar} transition-all duration-1000 ease-out`} 
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

export default RiskGauge;
