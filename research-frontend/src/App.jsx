import React, { useState, useEffect } from 'react';
import axios from 'axios';
// Components
import SingleView from './components/SingleView';
import ComparisonView from './components/ComparisonView';

/* ─── Error Boundary ─── */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] Rendering crash caught:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-10 bg-red-50 border border-red-200 rounded-3xl text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-black text-red-800 mb-2">Rendering Error</h2>
          <p className="text-sm text-red-600 font-medium mb-4">
            {this.state.error?.message || 'An unexpected error occurred while rendering the results.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="bg-red-600 text-white font-bold px-6 py-2 rounded-xl hover:bg-red-700 transition-all"
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const App = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const validateInput = (input) => {
    if (!input || input.trim().length < 2) return "Please enter a valid drug name or SMILES string.";
    // Basic SMILES heuristic: contains chemical symbols and characteristic SMILES chars
    const isSmiles = /^[A-Za-z0-9#\(\)\+=\-\[\]\.\/\\@]+$/.test(input) && (input.includes('=') || input.includes('(') || input.includes('#') || input.split('').some(c => 'cnops'.includes(c.toLowerCase())));
    if (!isSmiles && input.length < 3 && !/^[A-Za-z]+$/.test(input)) return "Input is too short to be a valid drug name.";
    return null;
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery) return;

    setLoading(true);
    setError(null);
    const validationError = validateInput(searchQuery);
    if (validationError) {
      setError(validationError);
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post('/api/analyze', {
        input: searchQuery,
        mode: activeTab === 'single' ? 'single' : 'multi'
      });
      const data = response.data;
      
      if (data.type === 'comparison' && activeTab === 'single') {
        setActiveTab('multi');
      } else if (data.Name && activeTab === 'multi') {
        setActiveTab('single');
      }
      
      setResults(data);
    } catch (error) {
      console.error("Analysis failed:", error);
      setError("Molecular analysis failed. Please verify that the backend engine is running on port 8125.");
    } finally {
      setLoading(false);
    }
  };

  const cn = (...inputs) => inputs.filter(Boolean).join(' ');

  return (
    <div className="min-h-screen bg-white text-slate-800 font-sans selection:bg-blue-100 selection:text-blue-900 antialiased">
      {/* Header */}
      <header className="px-8 py-8 border-b border-slate-100 bg-white/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-xl shadow-blue-200"></div>
            <div className="flex flex-col">
              <h1 className="text-2xl font-black text-slate-900 tracking-tighter uppercase whitespace-nowrap">Toxicity Prediction</h1>
              <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest whitespace-nowrap">
                Advanced Molecular Safety Intelligence • DeepChem Engine v3.2
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="bg-white min-h-screen">
        {/* Navigation Tabs */}
        <div className="flex max-w-6xl mx-auto border-b border-slate-100 mb-8 pt-4">
          <button 
            onClick={() => setActiveTab('single')}
            aria-label="Switch to Single Compound Tab"
            className={cn(
              "flex-1 py-4 text-center font-black text-[12px] uppercase tracking-widest transition-all border-b-2 outline-none",
              activeTab === 'single' 
                ? "text-blue-600 border-blue-600 bg-blue-50/30" 
                : "text-slate-400 hover:text-slate-600 border-transparent"
            )}
          >
            Single Compound Intelligence
          </button>
          <button 
            onClick={() => setActiveTab('multi')}
            aria-label="Switch to Multi Compound Tab"
            className={cn(
              "flex-1 py-4 text-center font-black text-[12px] uppercase tracking-widest transition-all border-b-2 outline-none",
              activeTab === 'multi' 
                ? "text-pink-600 border-pink-600 bg-pink-50/30" 
                : "text-slate-400 hover:text-slate-600 border-transparent"
            )}
          >
            Comparative Safety Dossier
          </button>
        </div>

        {/* Workspace */}
        <main className="max-w-6xl mx-auto px-8 pb-20 mt-10">
          {/* Input Panel */}
          <div className="mb-10 px-6 py-8 bg-slate-50/50 rounded-3xl border border-dashed border-slate-200">
             <div className="border-b border-slate-200/60 pb-2 mb-4">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.12em]">
                  {activeTab === 'single' ? "🧪 Clinical Compound Intelligence" : "⚖️ Comparative Clinical Safety Dossier"}
                </span>
             </div>
             
             <form onSubmit={handleAnalyze} className="mt-6">
                {activeTab === 'single' ? (
                  <div className="flex items-center gap-4 bg-white p-3 rounded-2xl border border-slate-100 shadow-sm focus-within:border-blue-300 focus-within:ring-4 focus-within:ring-blue-50 transition-all">
                     <input 
                       type="text" 
                       placeholder="Enter Clinical Drug Name (e.g. Aspirin, Tylenol, Belinostat) or SMILES" 
                       className="flex-1 bg-transparent border-none text-slate-800 placeholder-slate-300 font-mono text-[13px] focus:ring-0 outline-none"
                       value={searchQuery}
                       onChange={(e) => setSearchQuery(e.target.value)}
                       aria-label="Compound search input"
                     />
                     <button aria-label="Analyze" className="bg-blue-600 hover:bg-blue-700 text-white font-black px-8 py-3 rounded-xl transition-all shadow-lg shadow-blue-200 flex items-center shrink-0">
                        <span className="mr-2">Analyze Compound</span>
                        <span aria-hidden="true">🧬</span>
                     </button>
                  </div>
                ) : (
                  <>
                    <textarea 
                      placeholder="Enter Multiple Clinical Drug Names (e.g. Aspirin, Caffeine, Belinostat, Ibuprofen)..." 
                      className="w-full h-32 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-slate-800 placeholder-slate-300 font-mono text-[13px] focus:ring-4 focus:ring-pink-50 focus:border-pink-300 transition-all outline-none resize-none mb-4"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button className="w-full bg-pink-600 hover:bg-pink-700 text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-pink-200 flex items-center justify-center">
                       <span className="mr-2">Generate Comparative Safety Dossier</span>
                       <span>📊</span>
                    </button>
                  </>
                )}
             </form>

             {/* Error Banner */}
             {error && (
               <div className="mt-6 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-center gap-4 animate-in fade-in slide-in-from-top-4">
                 <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center text-red-600 shrink-0">
                   ⚠️
                 </div>
                 <div className="flex-1">
                   <h3 className="text-sm font-black text-red-900 uppercase tracking-tight">System Message</h3>
                   <p className="text-xs text-red-600 font-medium">{error}</p>
                 </div>
                 <button 
                   onClick={() => setError(null)}
                   className="text-red-400 hover:text-red-600 transition-colors p-2"
                 >
                   ✕
                 </button>
               </div>
             )}
          </div>

          {/* Results Area */}
          <div id="results-area" className="animate-fade-in relative min-h-[400px]">
            {loading ? (
              <div className="absolute inset-0 z-50 bg-white/80 backdrop-blur-lg flex flex-col items-center justify-center rounded-3xl" aria-busy="true">
                <div className="w-20 h-20 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-8"></div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight mb-2">Synthesizing Safety Evidence...</h2>
                <p className="text-blue-600 text-sm font-bold uppercase tracking-widest animate-pulse italic">
                  Estimating posterior probabilities across biological targets
                </p>
              </div>
            ) : results ? (
              <ErrorBoundary key={JSON.stringify(results?.Name || results?.type || 'r')}>
                {activeTab === 'multi' || results.type === 'comparison' ? (
                  <ComparisonView data={(() => {
                    // Normalize data to always have valid reports array
                    const reports = Array.isArray(results.reports) ? results.reports : (results.Name ? [results] : []);
                    const summary = results.summary || { overview: 'Comparative analysis complete.' };
                    return { ...results, reports, summary };
                  })()} />
                ) : (
                  <SingleView report={results.reports ? results.reports[0] : results} />
                )}
              </ErrorBoundary>
            ) : (
              <div className="flex items-center justify-center py-40 opacity-20 filter grayscale">
                <div className="text-center">
                  <div className="text-6xl mb-4">🔬</div>
                  <p className="font-black uppercase tracking-widest text-[11px]">Ready for clinical inference</p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>


    </div>
  );
};

export default App;
