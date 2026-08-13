import { useState, useRef } from 'react'
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom'
import { LayoutDashboard, FileUp, BarChart3, Lightbulb, CloudUpload, CheckCircle, AlertTriangle, Lock, User, LogOut, Menu, X, Cpu, Sliders, Award, Target, History, Clock, Search, ChevronDown, TrendingUp, Building2, Trophy } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

// 1. Login Component
const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (username === 'admin' && password === 'admin123') {
      onLogin(true);
      navigate('/');
    } else {
      setError('Invalid username or password (try admin / admin123)');
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-900 px-4">
      <div className="bg-white p-8 sm:p-12 rounded-3xl shadow-2xl w-full max-w-lg border border-slate-100">
        <div className="text-center mb-8">
          <div className="inline-flex p-3.5 bg-indigo-50 text-indigo-600 rounded-2xl mb-3 shadow-inner">
            <Award size={36} />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Ranking DSS Portal</h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">Modified SBERT & AHP-TOPSIS Framework</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleLoginSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Username</label>
            <div className="relative">
              <User className="absolute left-3.5 top-3.5 text-slate-400" size={18} />
              <input 
                type="text" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required
                placeholder="Enter username"
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-600 text-sm font-medium text-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 text-slate-400" size={18} />
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required
                placeholder="Enter password"
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-600 text-sm font-medium text-slate-800"
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="w-full bg-indigo-600 text-white py-3.5 rounded-xl font-semibold hover:bg-indigo-700 transition-colors text-sm shadow-lg shadow-indigo-100 mt-2"
          >
            Sign In to System
          </button>
        </form>
      </div>
    </div>
  )
}

// 2. Dashboard Component
const Dashboard = ({ readinessData, arrsScore, bestFit, subScores, schoolName, strengths, weaknesses, hasGenerated }) => {
  if (!hasGenerated) {
    return (
      <div className="p-8 sm:p-12 w-full min-h-full flex flex-col items-center justify-center text-center my-auto">
        <div className="p-6 bg-indigo-50 text-indigo-600 rounded-3xl mb-3 shadow-sm">
          <CloudUpload size={48} />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">No Assessment Generated Yet</h2>
        <p className="text-slate-500 max-w-md text-sm sm:text-base mt-2">
          Please go to <span className="font-semibold text-indigo-600">Document Upload</span> and upload an institutional document to execute semantic extraction and multi-criteria evaluation.
        </p>
        <Link to="/upload" className="mt-6 bg-indigo-600 text-white px-6 py-3 rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-100">
          Go to Document Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 sm:p-10 w-full space-y-8 bg-slate-50/50 min-h-full">
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-indigo-600">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <Building2 size={28} />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Verified Submitting Institution</span>
            <h2 className="text-xl font-extrabold text-slate-900 mt-0.5">{schoolName}</h2>
          </div>
        </div>
        <div className="bg-indigo-50 border border-indigo-100 px-4 py-2 rounded-xl text-indigo-700 text-xs sm:text-sm font-semibold flex items-center gap-2">
          <Target size={16} /> Best-Fit Framework: <span className="font-bold underline">{bestFit}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-base border-b border-slate-100 pb-3">
            <CheckCircle size={20} /> Identified Institutional Strengths
          </div>
          <ul className="space-y-2.5">
            {strengths.map((item, idx) => (
              <li key={idx} className="text-sm text-slate-700 bg-emerald-50/50 border border-emerald-100 p-3 rounded-xl flex items-start gap-2.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0"></span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-amber-600 font-bold text-base border-b border-slate-100 pb-3">
            <AlertTriangle size={20} /> Areas for Improvement & Weaknesses
          </div>
          <ul className="space-y-2.5">
            {weaknesses.map((item, idx) => (
              <li key={idx} className="text-sm text-slate-700 bg-amber-50/50 border border-amber-100 p-3 rounded-xl flex items-start gap-2.5">
                <span className="w-2 h-2 rounded-full bg-amber-500 mt-1.5 shrink-0"></span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900">Framework Readiness & Sub-Indicator Points</h3>
          <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-lg">ARRS Composite: {arrsScore}</span>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500">
              <th className="p-4 pl-6">Framework</th>
              <th className="p-4">Readiness Score (RRS)</th>
              <th className="p-4 pr-6">Sub-Indicator Point Breakdown</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {readinessData.map((data) => (
              <tr key={data.framework} className="hover:bg-slate-50/50 transition-colors">
                <td className="p-4 pl-6 font-bold text-slate-900">{data.framework}</td>
                <td className="p-4">
                  <span className="font-extrabold text-indigo-600 text-base">{data.score}</span>
                  <span className="text-xs text-slate-400 ml-1">/ 100</span>
                </td>
                <td className="p-4 pr-6">
                  <div className="flex flex-wrap gap-1.5">
                    {subScores[data.framework] && Object.entries(subScores[data.framework]).map(([subName, pts]) => (
                      <span key={subName} className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                        {subName}: <strong>{pts}</strong>
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// 3. Document Upload Component
const DocumentUpload = ({ updateEvaluation }) => {
  const [status, setStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setStatus('Executing school verification, SBERT extraction, and points evaluation...');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.scores && Object.keys(data.scores).length > 0) {
          updateEvaluation(data.filename, data.school_name, data.scores, data.sub_scores, data.arrs, data.best_fit, data.strengths, data.weaknesses);
          setStatus(`✅ Evaluated ${data.school_name} successfully! Best-Fit: ${data.best_fit}`);
        } else {
          setStatus(`✅ ${data.message}: ${data.filename}`);
        }
      } else {
        setStatus('❌ Evaluation failed. Please check backend connection.');
      }
    } catch (error) {
      console.error("Error uploading:", error);
      setStatus('❌ Network error. Make sure the FastAPI python server is active.');
    }
  };

  return (
    <div className="p-6 sm:p-10 w-full space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Document Integration & School Verification</h2>
        <p className="text-slate-500 text-sm sm:text-base mt-1">Upload institutional reports to verify the school and generate strengths/weaknesses tables.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-6 sm:p-8">
        <div 
          onClick={() => fileInputRef.current.click()}
          className="border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50 flex flex-col items-center justify-center p-12 sm:p-24 hover:bg-slate-50 hover:border-indigo-500 transition-all cursor-pointer text-center group w-full"
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileChange} 
            accept=".pdf,.docx,.txt" 
          />
          <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl mb-4 group-hover:scale-105 transition-transform">
            <CloudUpload size={36} />
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-1">Click or drag institutional files here</h3>
          <p className="text-xs sm:text-sm text-slate-500 max-w-lg mb-6">
            Supported formats: PDF, DOCX, TXT. System will detect the school name and analyze strengths/weaknesses.
          </p>
          <button className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-colors text-sm shadow-sm shadow-indigo-100">
            Browse Files
          </button>
        </div>

        {status && (
          <div className="mt-6 p-4 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs sm:text-sm font-medium text-slate-700 break-words">
            {status}
          </div>
        )}
      </div>
    </div>
  )
}

// 4. School Rank Component (New Tab)
const SchoolRankView = ({ history }) => {
  // Sort history items by ARRS score descending to establish institutional ranking
  const sortedRankings = [...history].sort((a, b) => b.arrs - a.arrs);

  return (
    <div className="p-6 sm:p-10 w-full space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Institutional School Rankings</h2>
        <p className="text-slate-500 text-sm sm:text-base mt-1">Comparative ranking table of evaluated universities based on ARRS and Best-Fit Frameworks.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 overflow-hidden w-full">
        {sortedRankings.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No institutional ranking data available. Upload documents in the Document Upload tab to populate rankings.
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase text-slate-600">
                  <th className="p-4 pl-6">Rank</th>
                  <th className="p-4">Institution / School Name</th>
                  <th className="p-4">Best-Fit Framework</th>
                  <th className="p-4">Document Source</th>
                  <th className="p-4 pr-6 text-right">ARRS Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {sortedRankings.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 pl-6 font-extrabold text-slate-900 flex items-center gap-2">
                      <span className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs ${index === 0 ? 'bg-amber-100 text-amber-700 font-black' : index === 1 ? 'bg-slate-200 text-slate-700' : index === 2 ? 'bg-amber-50 text-amber-800' : 'bg-slate-100 text-slate-600'}`}>
                        #{index + 1}
                      </span>
                    </td>
                    <td className="p-4 font-bold text-slate-900 flex items-center gap-2.5">
                      <Building2 size={16} className="text-indigo-600" /> {item.schoolName}
                    </td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-bold">
                        {item.bestFit}
                      </span>
                    </td>
                    <td className="p-4 text-slate-500 text-xs">{item.filename}</td>
                    <td className="p-4 pr-6 text-right font-black text-indigo-600 text-base">{item.arrs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// 5. Assessment History Component
const HistoryView = ({ history }) => {
  return (
    <div className="p-6 sm:p-10 w-full space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Assessment History & School Submissions</h2>
        <p className="text-slate-500 text-sm sm:text-base mt-1">Audit trail of previously evaluated schools and institutional documents.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 overflow-hidden w-full">
        {history.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No assessment records found. Upload a document to start building history.
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase text-slate-600">
                  <th className="p-4">Submitting School</th>
                  <th className="p-4">Filename</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Best-Fit Framework</th>
                  <th className="p-4">ARRS Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {history.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 font-bold text-slate-900 flex items-center gap-2">
                      <Building2 size={16} className="text-indigo-600" /> {item.schoolName}
                    </td>
                    <td className="p-4 text-slate-500">{item.filename}</td>
                    <td className="p-4 text-slate-500 flex items-center gap-1.5">
                      <Clock size={14} /> {item.timestamp}
                    </td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-bold">
                        {item.bestFit}
                      </span>
                    </td>
                    <td className="p-4 font-extrabold text-indigo-600">{item.arrs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// 6. Framework Analysis Component
const FrameworkAnalysis = () => {
  return (
    <div className="p-6 sm:p-10 w-full space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Framework Analysis & Points Criteria</h2>
        <p className="text-slate-500 text-sm sm:text-base mt-1">Sub-indicator point weight distributions across WURI, THE, QS, and UI GreenMetric.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200/80 space-y-6">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2.5">
            <Sliders className="text-indigo-600" size={20} /> Framework Pillar Weighting
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm font-semibold text-slate-700 mb-1.5">
                <span>Research & Academic Excellence (QS / THE)</span>
                <span className="text-indigo-600">35%</span>
              </div>
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5">
                <div className="bg-indigo-600 h-full rounded-full" style={{ width: '35%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm font-semibold text-slate-700 mb-1.5">
                <span>Innovation & Entrepreneurship (WURI)</span>
                <span className="text-amber-500">30%</span>
              </div>
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: '30%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm font-semibold text-slate-700 mb-1.5">
                <span>Environmental Sustainability (GreenMetric)</span>
                <span className="text-emerald-500">20%</span>
              </div>
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: '20%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm font-semibold text-slate-700 mb-1.5">
                <span>International Outlook & Ratios</span>
                <span className="text-purple-500">15%</span>
              </div>
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5">
                <div className="bg-purple-500 h-full rounded-full" style={{ width: '15%' }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200/80 space-y-6">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2.5">
            <Cpu className="text-indigo-600" size={20} /> Points Aggregation Engine
          </h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Sub-indicator scores are calculated via semantic embedding proximity (0–100 scale) and synthesized into framework Ranking Readiness Scores (RRS) and the composite ARRS index.
          </p>
        </div>
      </div>
    </div>
  )
}

// 7. Explainable AI Component
const ExplainableAI = ({ bestFit, hasGenerated, strengths, weaknesses }) => {
  return (
    <div className="p-6 sm:p-10 w-full space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Explainable AI Recommendations</h2>
        <p className="text-slate-500 text-sm sm:text-base mt-1">Transparent evidence traceability, strengths, and gap analysis.</p>
      </div>

      {!hasGenerated ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-12 text-center text-slate-500 text-sm w-full">
          Please upload and evaluate an institutional document first to view XAI recommendations and trace evidence.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-6 border-l-4 border-l-emerald-500 space-y-4">
            <h4 className="font-bold text-slate-900 text-base flex items-center gap-2 text-emerald-700">
              <CheckCircle size={20} /> Strengths Analysis ({bestFit})
            </h4>
            <ul className="space-y-2">
              {strengths.map((str, i) => (
                <li key={i} className="text-xs sm:text-sm text-slate-700 bg-emerald-50/40 p-2.5 rounded-lg">✓ {str}</li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-6 border-l-4 border-l-amber-500 space-y-4">
            <h4 className="font-bold text-slate-900 text-base flex items-center gap-2 text-amber-700">
              <AlertTriangle size={20} /> Weakness & Gap Analysis
            </h4>
            <ul className="space-y-2">
              {weaknesses.map((weak, i) => (
                <li key={i} className="text-xs sm:text-sm text-slate-700 bg-amber-50/40 p-2.5 rounded-lg">⚠ {weak}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

// 8. Main App Component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [schoolName, setSchoolName] = useState('');
  const [arrsScore, setArrsScore] = useState(0);
  const [bestFitFramework, setBestFitFramework] = useState('');
  const [readinessData, setReadinessData] = useState([
    { framework: 'WURI', score: 0, color: '#f59e0b' },
    { framework: 'THE', score: 0, color: '#3b82f6' },
    { framework: 'QS', score: 0, color: '#8b5cf6' },
    { framework: 'UI GreenMetric', score: 0, color: '#10b981' },
  ]);
  const [subScores, setSubScores] = useState({});
  const [strengths, setStrengths] = useState([]);
  const [weaknesses, setWeaknesses] = useState([]);
  const [history, setHistory] = useState([]);

  const updateEvaluation = (filename, detectedSchool, newScores, newSubScores, newArrs, bestFit, detectedStrengths, detectedWeaknesses) => {
    setHasGenerated(true);
    setSchoolName(detectedSchool);
    setArrsScore(newArrs);
    setBestFitFramework(bestFit);
    setSubScores(newSubScores);
    setStrengths(detectedStrengths);
    setWeaknesses(detectedWeaknesses);
    setReadinessData([
      { framework: 'WURI', score: newScores.WURI || 0, color: '#f59e0b' },
      { framework: 'THE', score: newScores.THE || 0, color: '#3b82f6' },
      { framework: 'QS', score: newScores.QS || 0, color: '#8b5cf6' },
      { framework: 'UI GreenMetric', score: newScores['UI GreenMetric'] || 0, color: '#10b981' },
    ]);

    const timestamp = new Date().toLocaleString();
    setHistory(prev => [{ filename, schoolName: detectedSchool, timestamp, bestFit, arrs: newArrs }, ...prev]);
  };

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={setIsAuthenticated} />} />
      
      <Route 
        path="/*" 
        element={
          isAuthenticated ? (
            <div className="flex h-screen w-screen overflow-hidden bg-white font-sans">
              
              {/* Mobile Header Bar */}
              <div className="md:hidden bg-white text-slate-900 p-4 flex items-center justify-between border-b border-slate-200 shrink-0 w-full absolute top-0 left-0 z-40">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-indigo-600 text-white rounded-xl">
                    <Award size={18} />
                  </div>
                  <span className="font-bold text-base text-slate-900">Ranking DSS</span>
                </div>
                <button 
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="p-2 text-slate-600 hover:text-slate-900 focus:outline-none"
                >
                  {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
              </div>

              {/* Sidebar Navigation */}
              <nav className={`
                fixed md:static z-30 inset-y-0 left-0 w-64 bg-white text-slate-700 flex flex-col transition-transform duration-300 ease-in-out shrink-0 h-full border-r border-slate-200/80
                ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
              `}>
                <div className="p-6 pb-4 hidden md:flex items-center justify-between border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-fuchsia-500 to-pink-500 flex items-center justify-center text-white shadow-md shadow-pink-500/20">
                      <Award size={18} />
                    </div>
                    <span className="font-black text-lg text-slate-900 tracking-tight">Ranking DSS</span>
                  </div>
                  <div className="text-slate-400 hover:text-slate-600 cursor-pointer">
                    <Search size={18} />
                  </div>
                </div>

                <div className="flex flex-col flex-1 py-4 space-y-1.5 px-3 overflow-y-auto mt-16 md:mt-2">
                  <div className="px-3 pb-2 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Discover</div>
                  <Link 
                    to="/" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <LayoutDashboard size={18} /> Dashboard & Points
                  </Link>
                  <Link 
                    to="/upload" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <FileUp size={18} /> Document Upload
                  </Link>
                  <Link 
                    to="/rank" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <Trophy size={18} /> School Rank
                  </Link>
                  <Link 
                    to="/history" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <History size={18} /> Assessment History
                  </Link>

                  <div className="px-3 pt-4 pb-2 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Analytics & AI</div>
                  <Link 
                    to="/analysis" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <BarChart3 size={18} /> Framework Analysis
                  </Link>
                  <Link 
                    to="/xai" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 hover:bg-indigo-50 hover:text-indigo-600 rounded-xl transition-all text-sm font-semibold text-slate-600"
                  >
                    <Lightbulb size={18} /> Explainable AI
                  </Link>
                </div>

                <div className="p-3 border-t border-slate-100 bg-white">
                  <button 
                    onClick={() => setIsAuthenticated(false)}
                    className="flex items-center gap-3 text-slate-500 hover:text-red-600 text-sm font-semibold transition-colors w-full px-3 py-2.5 rounded-xl hover:bg-red-50"
                  >
                    <LogOut size={18} /> Sign Out
                  </button>
                </div>
              </nav>

              {/* Main Content Viewport */}
              <main className="flex-1 flex flex-col h-full overflow-y-auto bg-slate-50/50 pt-16 md:pt-0">
                <Routes>
                  <Route path="/" element={<Dashboard readinessData={readinessData} arrsScore={arrsScore} bestFit={bestFitFramework} subScores={subScores} schoolName={schoolName} strengths={strengths} weaknesses={weaknesses} hasGenerated={hasGenerated} />} />
                  <Route path="/upload" element={<DocumentUpload updateEvaluation={updateEvaluation} />} />
                  <Route path="/rank" element={<SchoolRankView history={history} />} />
                  <Route path="/history" element={<HistoryView history={history} />} />
                  <Route path="/analysis" element={<FrameworkAnalysis />} />
                  <Route path="/xai" element={<ExplainableAI bestFit={bestFitFramework} hasGenerated={hasGenerated} strengths={strengths} weaknesses={weaknesses} />} />
                </Routes>
              </main>

            </div>
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
    </Routes>
  )
}

export default App