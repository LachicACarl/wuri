import { useState, useRef } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import { LayoutDashboard, FileUp, BarChart3, Lightbulb, CloudUpload, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

// 1. Dashboard Component
const Dashboard = () => {
  const readinessData = [
    { framework: 'WURI', score: 85, color: '#f59e0b' },
    { framework: 'THE', score: 72, color: '#3b82f6' },
    { framework: 'QS', score: 78, color: '#8b5cf6' },
    { framework: 'UI GreenMetric', score: 92, color: '#10b981' },
  ];

  return (
    <div className="p-8 w-full max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800">Comprehensive Dashboard</h2>
        <p className="text-slate-500 mt-2">Institutional Readiness Overview</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8 flex items-center justify-between border-l-4 border-l-blue-600">
        <div>
          <h3 className="text-lg font-semibold text-slate-700">Aggregated Ranking Readiness Score (ARRS)</h3>
          <p className="text-sm text-slate-500 mt-1">Overall composite measure across all selected frameworks</p>
        </div>
        <div className="text-4xl font-bold text-blue-600">
          81.75
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {readinessData.map((data) => (
          <div key={data.framework} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-center items-center">
            <h4 className="text-slate-600 font-medium mb-2 text-center">{data.framework} RRS</h4>
            <span className="text-3xl font-bold" style={{ color: data.color }}>
              {data.score}
            </span>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-96">
        <h3 className="text-lg font-semibold text-slate-700 mb-6">Framework Comparison</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={readinessData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="framework" axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} axisLine={false} tickLine={false} />
            <Tooltip cursor={{fill: '#f8fafc'}} />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {readinessData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// 2. Document Upload Component
const DocumentUpload = () => {
  const [status, setStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setStatus('Uploading and processing...');
    
    // Package the file into a FormData object
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Send the file to your FastAPI backend
      const response = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        // Update the status to show the backend's extraction results
        setStatus(`✅ ${data.message}: ${data.filename} (${data.character_count} chars). Preview: "${data.preview}"`);
      } else {
        setStatus('❌ Upload failed. Please try again.');
      }
    } catch (error) {
      console.error("Error uploading:", error);
      setStatus('❌ Network error. Make sure the Python server is running.');
    }
  };

  return (
    <div className="p-8 w-full max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800">Document Integration</h2>
        <p className="text-slate-500 mt-2">Upload institutional documents for semantic evidence extraction and readiness assessment.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div 
          onClick={() => fileInputRef.current.click()}
          className="border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 flex flex-col items-center justify-center p-12 hover:bg-slate-100 hover:border-blue-400 transition-colors cursor-pointer"
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileChange} 
            accept=".pdf,.docx,.txt" 
          />
          <CloudUpload size={48} className="text-blue-500 mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-2">Click or drag documents to upload</h3>
          <p className="text-sm text-slate-500 text-center max-w-md mb-6">
            Supported formats: PDF, DOCX, TXT. Ensure documents contain relevant institutional data for WURI, THE, QS, or UI GreenMetric assessment.
          </p>
          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
            Browse Files
          </button>
        </div>

        {status && (
          <div className="mt-6 p-4 rounded-lg bg-slate-50 border border-slate-200 text-center text-sm font-medium text-slate-700">
            {status}
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <h4 className="font-semibold text-blue-800 mb-2">Required Evidence Types</h4>
            <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
              <li>Strategic Plans & Annual Reports</li>
              <li>Accreditation Documents</li>
              <li>Research & Extension Manuals</li>
              <li>Sustainability Protocols</li>
            </ul>
          </div>
          <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
            <h4 className="font-semibold text-amber-800 mb-2">Processing Note</h4>
            <p className="text-sm text-amber-700">
              Documents are processed using the Modified Sentence-BERT model to extract semantic evidence. Processing time depends on document length.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// 3. Explainable AI Component
const ExplainableAI = () => {
  return (
    <div className="p-8 w-full max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800">Explainable AI Recommendations</h2>
        <p className="text-slate-500 mt-2">Transparent decision support, evidence traceability, and strategic gap analysis.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-xl font-bold text-slate-700 border-b pb-2">Evidence Traceability</h3>
          
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="text-green-500" size={20} />
              <h4 className="font-semibold text-slate-800">WURI: Industrial Application</h4>
              <span className="ml-auto bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded">Score: High</span>
            </div>
            <p className="text-sm text-slate-600 mb-4 font-medium">Indicator: The institution demonstrates real impact on industry through innovative entrepreneurial programs.</p>
            <div className="bg-slate-50 p-4 rounded border border-slate-200">
              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2 block">Extracted Evidence (Annual Report, pg. 14)</span>
              <p className="text-sm text-slate-700 italic">"The university launched a new startup incubator program that supported 15 student-led businesses, resulting in a 20% increase in local industry partnerships and $50,000 in seed funding."</p>
            </div>
            <p className="text-xs text-blue-600 mt-3 font-medium">Semantic Match Confidence: 94%</p>
          </div>
        </div>

        <div className="space-y-6">
          <h3 className="text-xl font-bold text-slate-700 border-b pb-2">Strategic Gap Analysis</h3>
          
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 border-t-4 border-t-amber-500">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="text-amber-500" size={20} />
              <h4 className="font-semibold text-slate-800">THE: International Outlook</h4>
            </div>
            <p className="text-sm text-slate-600 mb-4">Insufficient evidence regarding international co-authorship and global faculty ratios.</p>
            
            <div className="mt-4 pt-4 border-t border-slate-100">
              <h5 className="text-sm font-bold text-slate-700 mb-2">Priority Action:</h5>
              <div className="flex items-start gap-2 text-sm text-slate-600">
                <ArrowRight className="text-blue-500 shrink-0 mt-0.5" size={16} />
                <p>Upload documentation detailing international research collaborations and student exchange programs to improve this metric.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// 4. Placeholder for Framework Analysis
const FrameworkAnalysis = () => <div className="p-6"><h2 className="text-2xl font-bold">Framework Analysis</h2></div>

// 5. The Main App Component
function App() {
  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      <nav className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 bg-slate-950">
          <h1 className="text-xl font-bold text-blue-400">Ranking DSS</h1>
        </div>
        <div className="flex flex-col flex-1 py-4 space-y-2 px-2">
          <Link to="/" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition-colors">
            <LayoutDashboard size={20} /> Dashboard
          </Link>
          <Link to="/upload" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition-colors">
            <FileUp size={20} /> Document Upload
          </Link>
          <Link to="/analysis" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition-colors">
            <BarChart3 size={20} /> Framework Analysis
          </Link>
          <Link to="/xai" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition-colors">
            <Lightbulb size={20} /> Explainable AI
          </Link>
        </div>
      </nav>

      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<DocumentUpload />} />
          <Route path="/analysis" element={<FrameworkAnalysis />} />
          <Route path="/xai" element={<ExplainableAI />} />
        </Routes>
      </main>
    </div>
  )
}

export default App