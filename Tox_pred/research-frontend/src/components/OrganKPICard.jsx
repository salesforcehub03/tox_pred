import React, { useState, useMemo } from 'react';
import { 
  Info, 
  ExternalLink, 
  ChevronRight, 
  Zap, 
  Database, 
  Activity,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const OrganKPICard = ({ organ, data, gateName }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showAudit, setShowAudit] = useState(false);

  if (!data) return null;
  const { label = 'N/A', score = 0, factors = [], bayes_data = {} } = data;

  const rawSumNum = useMemo(() => {
    return (bayes_data?.prior_pts || 0) * 1.2 + 
           (bayes_data?.likelihood_pts || 0) * 1.0 + 
           (bayes_data?.observation_pts || 0) * 1.5;
  }, [bayes_data]);

  const getStatusColor = (lbl) => {
    switch (lbl) {
      case 'High': return 'bg-red-600 text-white';
      case 'Moderate': return 'bg-amber-500 text-white';
      default: return 'bg-emerald-500 text-white';
    }
  };

  const getBorderColor = (lbl) => {
    switch (lbl) {
      case 'High': return 'border-red-200';
      case 'Moderate': return 'border-amber-200';
      default: return 'border-emerald-200';
    }
  };

  const getBgLight = (lbl) => {
    switch (lbl) {
      case 'High': return 'bg-red-50';
      case 'Moderate': return 'bg-amber-50';
      default: return 'bg-emerald-50';
    }
  };

  return (
    <div 
      className={`relative group bg-white rounded-2xl border-2 ${getBorderColor(label)} shadow-premium hover:shadow-premium-hover transition-all duration-300 overflow-hidden flex flex-col`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="p-5 flex-1">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xs font-black uppercase tracking-widest text-scientific-400">{organ}</h3>
          <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${getStatusColor(label)}`}>
            {label}
          </div>
        </div>

        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-black tabular-nums">{score}</span>
          <span className="text-sm font-bold text-scientific-400">%</span>
        </div>
        
        <p className="text-[10px] mt-2 font-medium text-scientific-500">
          Composite Confidence Score
        </p>
      </div>

      <div className={`p-3 border-t bg-scientific-50 flex items-center justify-between`}>
        <button 
          onClick={() => setShowAudit(true)}
          className="text-[10px] font-bold text-blue-600 uppercase flex items-center gap-1 hover:underline"
        >
          <Info size={12} />
          View Audit Logic
        </button>
        <ChevronRight size={14} className="text-scientific-300" />
      </div>

      {/* Hover Analysis Popup */}
      <AnimatePresence>
        {isHovered && !showAudit ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute -top-4 -left-4 -right-4 bg-white rounded-3xl shadow-2xl border border-scientific-200 z-50 p-6 pointer-events-none"
          >
            <div className="flex items-center gap-2 mb-4 border-b pb-3">
              <Zap size={16} className="text-blue-500" />
              <h4 className="text-sm font-black uppercase tracking-wider">Metric Breakdown</h4>
            </div>
            
            <div className="space-y-4">
              <BreakdownItem 
                label="Structural Prior" 
                value={bayes_data?.prior_pts || 0} 
                max={5} 
                weight={1.2}
                color="blue"
              />
              <BreakdownItem 
                label="Tox21 Likelihood" 
                value={bayes_data?.likelihood_pts || 0} 
                max={5} 
                weight={1.0}
                color="indigo"
              />
              <BreakdownItem 
                label="Clinical Outcome" 
                value={bayes_data?.observation_pts || 0} 
                max={5} 
                weight={1.5}
                color="purple"
              />
            </div>

            <div className="mt-6 pt-4 border-t flex justify-between items-center">
              <div>
                <p className="text-[10px] uppercase font-bold text-scientific-400">Gate Multiplier</p>
                <p className="text-xs font-black text-blue-600">{gateName || 'Neutral'}</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] uppercase font-bold text-scientific-400">Total Raw</p>
                <p className="text-xl font-black text-scientific-900">
                  {rawSumNum.toFixed(1)}
                </p>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {/* Audit Modal */}
      <AnimatePresence>
        {showAudit ? (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-scientific-950/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden"
            >
              <div className="p-8 border-b border-scientific-100 flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-black text-scientific-900 tracking-tight">{organ} Safety Audit</h2>
                  <p className="text-scientific-500 font-medium">Full Bayesian Mathematical Derivation</p>
                </div>
                <button 
                  onClick={() => setShowAudit(false)}
                  className="w-10 h-10 rounded-full hover:bg-scientific-100 flex items-center justify-center transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              <div className="p-8 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                  <div className="space-y-6">
                    <AuditSection title="Evidence Stream Summary">
                       <ul className="space-y-3">
                          {factors.map((f, i) => (
                            <li key={i} className="flex gap-3 text-sm font-medium">
                               <AlertCircle size={16} className="text-blue-500 shrink-0" />
                               {f}
                            </li>
                          ))}
                          {factors.length === 0 ? (
                            <li className="text-sm font-medium text-scientific-400 italic">No evidence factors detected.</li>
                          ) : null}
                       </ul>
                    </AuditSection>
                  </div>

                  <div className="bg-scientific-50 rounded-2xl p-6 border border-scientific-100">
                    <h4 className="text-xs font-black uppercase tracking-widest text-scientific-500 mb-4">Calculation Formula</h4>
                    <div className="font-mono text-[11px] space-y-2 text-scientific-700 leading-relaxed">
                       <p className="text-blue-600 font-bold">prior_w = prior_pts ({bayes_data?.prior_pts || 0}) × 1.2</p>
                       <p className="text-indigo-600 font-bold">like_w = like_pts ({bayes_data?.likelihood_pts || 0}) × 1.0</p>
                       <p className="text-purple-600 font-bold">obs_w = obs_pts ({bayes_data?.observation_pts || 0}) × 1.5</p>
                       <div className="h-px bg-scientific-200 my-2" />
                       <p className="font-black text-scientific-900">raw_sum = {rawSumNum.toFixed(2)}</p>
                       <p className="font-black text-scientific-900 underline decoration-blue-500 decoration-2">final = min(99, (raw_sum / 20) × 100)</p>
                    </div>

                    <div className="mt-8 flex items-end justify-between">
                       <div>
                          <p className="text-[10px] font-black uppercase text-scientific-400">Final Risk</p>
                          <p className={`text-2xl font-black ${label === 'High' ? 'text-red-600' : label === 'Moderate' ? 'text-amber-500' : 'text-emerald-500'}`}>
                            {score}%
                          </p>
                       </div>
                       <div className={`px-4 py-2 rounded-xl text-xs font-black uppercase ${getStatusColor(label)}`}>
                          {label} Risk
                       </div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-2xl p-6 border border-blue-100">
                   <h4 className="flex items-center gap-2 text-sm font-black text-blue-900 uppercase mb-3">
                      <ShieldCheck size={18} />
                      Scientific Rationale
                   </h4>
                   <p className="text-blue-800 text-sm leading-relaxed">
                      The {organ} risk assessment utilizes a Bayesian consensus between structural toxicophores, human adverse event probability from deep learning, and corroborated clinical reports from FDA surveillance. A score of {score}% indicates {label === 'High' ? 'significant' : label === 'Moderate' ? 'noticeable' : 'minimal'} liability based on the aggregate weighted evidence.
                   </p>
                </div>
              </div>

              <div className="p-6 bg-scientific-50 border-t border-scientific-100 flex justify-end">
                 <button 
                  onClick={() => setShowAudit(false)}
                  className="px-8 py-3 bg-scientific-900 text-white font-bold rounded-xl hover:bg-scientific-950 transition-colors"
                 >
                   Dismiss Audit
                 </button>
              </div>
            </motion.div>
          </div>
        ) : null}
      </AnimatePresence>
    </div>
  );
};

const BreakdownItem = ({ label, value, max, weight, color }) => {
  const percentage = (value / max) * 100;
  const colorMap = {
    blue: 'bg-blue-500',
    indigo: 'bg-indigo-500',
    purple: 'bg-purple-500'
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[10px] font-black uppercase tracking-wider text-scientific-500">{label}</span>
        <span className="text-[10px] font-black text-scientific-900">{value} / {max} <span className="text-scientific-400">(w={weight})</span></span>
      </div>
      <div className="h-1.5 w-full bg-scientific-100 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          className={`h-full ${colorMap[color]}`}
        />
      </div>
    </div>
  );
};

const AuditSection = ({ title, children }) => (
  <div>
    <h4 className="text-xs font-black uppercase tracking-widest text-scientific-500 mb-4">{title}</h4>
    {children}
  </div>
);

const X = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const ShieldCheck = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    <path d="m9 12 2 2 4-4"></path>
  </svg>
);

export default OrganKPICard;
