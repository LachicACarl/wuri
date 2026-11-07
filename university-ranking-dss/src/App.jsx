import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, Route, Routes, Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  AlertTriangle,
  Award,
  BarChart3,
  Building2,
  BookOpenCheck,
  Brain,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  CloudUpload,
  Database,
  FileSearch,
  FileText,
  KeyRound,
  LayoutDashboard,
  Lightbulb,
  Lock,
  LogOut,
  Menu,
  Microscope,
  Network,
  ShieldCheck,
  SlidersHorizontal,
  TableProperties,
  Target,
  Trophy,
  User,
  X,
} from 'lucide-react'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

const apiFetch = (path, options = {}) => fetch(`${API_BASE_URL}${path}`, {
  ...options,
  credentials: 'include',
})

const DOCUMENT_TYPES = [
  'Strategic plan',
  'Annual/accomplishment report',
  'Accreditation report',
  'Research publication',
  'Faculty profile',
  'Sustainability report',
  'Extension report',
  'Institutional policy',
]

const VALIDATION_ROWS = [
  ['Enhanced SBERT performance', 'Accuracy, macro-Precision, macro-Recall, macro-F1, semantic similarity, confusion matrix, Precision@K, and Recall@K'],
  ['Baseline comparison', 'Enhanced SBERT + constrained AHP-TOPSIS vs conventional Sentence-BERT + standard AHP-TOPSIS under equivalent conditions'],
  ['Ablation analysis', 'Introduce or remove Enhanced SBERT, EQAM, and enhanced MCDA components to isolate contribution'],
  ['Expert validation', "Fleiss' kappa for categorical relevance/mapping and ICC for EQAM/readiness ratings"],
  ['RRS, ARRS, Best-Fit validation', 'MAE, RMSE, Spearman rank association, exact agreement, and separate reporting for margins below 5 points'],
  ['Sensitivity and robustness', 'Criterion-weight perturbation, evidence removal, confidence changes, and institutional profile variation'],
  ['XAI evaluation', 'Explanation clarity, interpretability, evidence traceability, usefulness, score consistency, and user confidence'],
  ['ISO/IEC 25010 scope', 'Functionality, usability, and security characteristics using standardized evaluator tasks'],
]

const SOP_ALIGNMENT_ROWS = [
  ['SOP 1', 'Design and implementation', 'Requirements traceability matrix, functional tests, module verification log'],
  ['SOP 2', 'Enhanced SBERT performance', 'Accuracy, Precision, Recall, F1-Score, semantic similarity, confusion matrix'],
  ['SOP 3', 'Baseline comparison', 'Same documents, preprocessing, partitions, ranking criteria, and evaluation cases'],
  ['SOP 4', 'Score validation', 'RRS, ARRS, Best-Fit exact agreement, MAE, RMSE, Spearman correlation'],
  ['SOP 5', 'EQAM evaluation', 'Dimension statistics, expert agreement, evidence-acceptance Precision/Recall/F1'],
  ['SOP 6', 'EQAM influence on RRS', 'Correlation, regression or association analysis per EQAM dimension'],
  ['SOP 7', 'Sensitivity and robustness', 'Weight, evidence, confidence, and profile perturbation scenarios'],
  ['SOP 8', 'XAI evaluation', 'Explanation clarity, interpretability, traceability, usefulness, consistency, confidence'],
  ['SOP 9', 'ISO/IEC 25010 quality', 'Functionality, usability, security weighted mean and standard deviation'],
]

const ARCHITECTURE_MODULES = [
  ['Institutional Document Management', 'Authenticated upload, malware scan gates, text extraction, segmentation, and metadata storage; institutional authorization still requires review.'],
  ['Evidence Extraction & Retrieval', 'Extracted passages are persisted; optional local-model matches are retrieval candidates, not verified evidence.'],
  ['Readiness Assessment', 'EQAM, AHP, and TOPSIS helpers exist, but no end-to-end readiness calculation is connected to upload.'],
  ['XAI & Recommendations', 'Score explanations and recommendations are unavailable because no readiness score is generated.'],
  ['Dashboard & Reporting', 'Institution and research status views are available; assessment history lists workflow records without scores or rankings.'],
]

const GOVERNANCE_ROWS = [
  ['Administrator', 'Manage authorized institution records, document metadata, and research-validation workflows'],
  ['Evaluator', 'Review evidence metadata, indicator mappings, and expert-validation cases'],
  ['Viewer', 'Read permitted institution and workflow status records; ranking reports are unavailable'],
]

const checklistGroups = [
  {
    title: 'Document Integration & Management',
    icon: Database,
    items: [
      ['Institutional collection', 'Strategic plans, reports, publications, faculty profiles, sustainability, extension, and policies are represented as document classes.'],
      ['Screening and metadata', 'Upload workflow tracks source, date, type, file size, page/section, extraction status, and verification status.'],
      ['Secure knowledge base', 'Role-based access control is represented through administrator, evaluator, and viewer permissions.'],
    ],
  },
  {
    title: 'Semantic Evidence Extraction & Matching',
    icon: Brain,
    items: [
      ['Enhanced Sentence-BERT', 'Domain-adapted SBERT is modeled as the embedding engine for sentence-level semantic similarity.'],
      ['Framework mapping', 'Evidence is mapped to WURI, THE, QS, and UI GreenMetric indicators.'],
      ['Top-K retrieval', 'The app ranks evidence passages and exposes the top evidence candidates with dataset split metadata.'],
    ],
  },
  {
    title: 'Evidence Quality Assessment Mechanism',
    icon: ShieldCheck,
    items: [
      ['Five EQAM dimensions', 'Chapter 3 specifies these dimensions; the upload workflow does not calculate them.'],
      ['Adjusted Evidence Score', 'EQAM/AES helper code is provisional and is not connected to upload or a verified acceptance threshold.'],
    ],
  },
  {
    title: 'MCDA',
    icon: SlidersHorizontal,
    items: [
      ['Framework-constrained AHP', 'AHP utilities exist; framework criteria and weights remain unverified and no institutional assessment invokes them.'],
      ['Fixed-reference TOPSIS', 'A TOPSIS helper exists, but the approved evidence-to-criterion aggregation rule is missing.'],
    ],
  },
  {
    title: 'Scoring & Aggregation',
    icon: Target,
    items: [
      ['RRS', 'A calculation helper exists; no institution RRS is produced or persisted.'],
      ['ARRS', 'An aggregation helper exists; no institution ARRS is produced or persisted.'],
      ['Best-fit rule', 'A selection helper exists; no Best-Fit recommendation is generated for uploaded evidence.'],
    ],
  },
  {
    title: 'XAI & Decision Support',
    icon: Lightbulb,
    items: [
      ['Traceability', 'Passages retain extraction metadata; source authorization and research permission remain unverified after upload.'],
      ['Gap analysis', 'Criterion readiness and EQAM gaps are unavailable without an implemented assessment.'],
      ['Dashboards and reports', 'The dashboard reports institutions and gate status; it does not provide rankings or score reports.'],
    ],
  },
  {
    title: 'Validation, Testing & QA',
    icon: ClipboardCheck,
    items: [
      ['Baselines and ablation', 'A0 retrieval evaluation is separate from the incomplete AHP-TOPSIS baseline; A1-A4 are not implemented.'],
      ['Agreement statistics', "Some agreement helpers exist; ICC model approval and all empirical expert judgments remain outstanding."],
      ['Robustness and ISO quality', 'These are planned evaluations; no evaluator responses or empirical results are available.'],
    ],
  },
]

const NavLink = ({ to, icon: Icon, children, onClick }) => {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
        active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
      }`}
    >
      <Icon size={18} />
      {children}
    </Link>
  )
}

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLoginSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Invalid credentials')
      }
      onLogin(true)
      navigate('/')
    } catch {
      setError('Authentication failed. Start the backend and use an authorized account.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-xl">
        <div className="mb-8">
          <div className="mb-4 inline-flex rounded-lg bg-slate-900 p-3 text-white">
            <Award size={28} />
          </div>
          <h1 className="text-3xl font-black tracking-normal text-slate-950">Ranking Readiness DSS</h1>
          <p className="mt-2 text-sm text-slate-500">Enhanced SBERT, EQAM, constrained AHP, and fixed-reference TOPSIS.</p>
        </div>
        {error && <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">{error}</div>}
        <form onSubmit={handleLoginSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-xs font-bold uppercase text-slate-500">Username</span>
            <span className="relative block">
              <User className="absolute left-3 top-3 text-slate-400" size={18} />
              <input className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm font-semibold text-slate-900 outline-none focus:border-slate-900" value={username} onChange={(event) => setUsername(event.target.value)} />
            </span>
          </label>
          <label className="block">
            <span className="mb-1.5 block text-xs font-bold uppercase text-slate-500">Password</span>
            <span className="relative block">
              <Lock className="absolute left-3 top-3 text-slate-400" size={18} />
              <input type="password" className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm font-semibold text-slate-900 outline-none focus:border-slate-900" value={password} onChange={(event) => setPassword(event.target.value)} />
            </span>
          </label>
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-bold text-white hover:bg-slate-800">
            Sign In <ChevronRight size={18} />
          </button>
        </form>
      </div>
    </div>
  )
}

const PersistedDashboard = () => {
  const navigate = useNavigate()
  const [institutions, setInstitutions] = useState([])
  const [status, setStatus] = useState('Loading institutions...')

  useEffect(() => {
    let active = true
    apiFetch('/api/institutions')
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load permitted institutions.')
        return response.json()
      })
      .then((data) => {
        if (active) {
          setInstitutions(data.institutions || [])
          setStatus('')
        }
      })
      .catch((error) => {
        if (active) setStatus(error.message || 'Unable to load permitted institutions.')
      })
    return () => { active = false }
  }, [])

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">Institution workspace</p>
          <h1 className="mt-1 text-3xl font-black text-slate-950">Readiness Dashboard</h1>
          <p className="mt-2 text-sm text-slate-500">Review persisted institutions and authorized evidence readiness.</p>
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/institutions')} className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-black text-slate-700 hover:bg-slate-50">
            Manage institutions
          </button>
          <button type="button" onClick={() => navigate('/upload')} className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800">
            Upload evidence
          </button>
        </div>
      </div>

      {status ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm font-semibold text-slate-600">{status}</div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wider text-slate-400">Permitted institutions</p>
              <p className="mt-2 text-3xl font-black text-slate-950">{institutions.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wider text-slate-400">Persisted workspace</p>
              <p className="mt-2 text-sm font-bold text-emerald-700">Connected to backend</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wider text-slate-400">Scoring state</p>
              <p className="mt-2 text-sm font-bold text-amber-700">Research-gated; no ranking score</p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-6 py-5">
              <h2 className="text-xl font-black text-slate-950">Permitted institutions</h2>
              <p className="mt-1 text-sm text-slate-500">Only institutions returned by the authenticated backend session appear here.</p>
            </div>
            {institutions.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <p className="font-bold text-slate-700">No institutions are available.</p>
                <p className="mt-1 text-sm text-slate-500">Create an authorized institution registry record to begin.</p>
              </div>
            ) : (
              <div className="grid gap-4 p-6 md:grid-cols-2">
                {institutions.map((institution) => (
                  <button
                    type="button"
                    key={institution.id}
                    onClick={() => navigate('/institutions')}
                    className="rounded-xl border border-slate-200 p-5 text-left transition hover:border-slate-400 hover:bg-slate-50"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-black text-slate-950">{institution.display_name || institution.name}</h3>
                        <p className="mt-1 text-sm text-slate-500">{institution.region || institution.country || 'Location not recorded'}</p>
                      </div>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{institution.role}</span>
                    </div>
                    <p className="mt-4 text-xs font-bold uppercase tracking-wider text-slate-400">Open institution registry</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  )
}

const DocumentUpload = ({ onEvaluation }) => {
  const [status, setStatus] = useState('')
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0])
  const [institutions, setInstitutions] = useState([])
  const [frameworks, setFrameworks] = useState([])
  const [institutionId, setInstitutionId] = useState('')
  const [frameworkId, setFrameworkId] = useState('')
  const [criterionId, setCriterionId] = useState('')
  const fileInputRef = useRef(null)

  useEffect(() => {
    Promise.all([
      apiFetch('/api/institutions').then((response) => response.json()),
      apiFetch('/api/frameworks').then((response) => response.json()),
    ]).then(([institutionData, frameworkData]) => {
      setInstitutions(institutionData.institutions || [])
      setFrameworks(frameworkData.frameworks || [])
      if (institutionData.institutions?.[0]) setInstitutionId(institutionData.institutions[0].id)
      if (frameworkData.frameworks?.[0]) setFrameworkId(frameworkData.frameworks[0].framework_id)
    }).catch((error) => setStatus(error.message))
  }, [])

  const selectedFramework = frameworks.find((item) => item.framework_id === frameworkId)
  const criteria = Object.keys(selectedFramework?.criteria || {})

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setStatus('Uploading document for server-side processing...')

    const formData = new FormData()
    formData.append('file', file)
    const params = new URLSearchParams({
      institution_id: institutionId,
      framework_id: frameworkId,
      framework_edition: selectedFramework?.methodology_version || '',
      criterion_id: criterionId,
      title: file.name,
    })

    try {
      const response = await apiFetch(`/api/upload?${params.toString()}`, { method: 'POST', body: formData })
      if (response.ok) {
        const data = await response.json()
        onEvaluation(data)
        setStatus(`Document processing complete for ${file.name}. Readiness scoring is not implemented.`)
        return
      }
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || data.message || 'Backend returned an error')
    } catch (error) {
      setStatus(`Assessment unavailable: ${error.message}. No readiness score was generated.`)
    }
  }

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="text-3xl font-black tracking-normal text-slate-950">Document Integration & Screening</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">Upload PDF, DOCX, or TXT evidence. The workflow tracks document type, source metadata, extraction status, role access, and evidence segmentation.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 text-lg font-black text-slate-950">Document Collection Coverage</h3>
          <div className="mb-4 space-y-3">
            <select value={institutionId} onChange={(event) => setInstitutionId(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="">Select institution</option>
              {institutions.map((institution) => <option key={institution.id} value={institution.id}>{institution.display_name || institution.name}</option>)}
            </select>
            <select value={frameworkId} onChange={(event) => { setFrameworkId(event.target.value); setCriterionId('') }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {frameworks.map((framework) => <option key={framework.framework_id} value={framework.framework_id}>{framework.framework_id} {framework.methodology_version}</option>)}
            </select>
            <select value={criterionId} onChange={(event) => setCriterionId(event.target.value)} required className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="">Select criterion mapping</option>
              {criteria.map((criterion) => <option key={criterion} value={criterion}>{criterion}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {DOCUMENT_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setDocumentType(type)}
                className={`rounded-lg border px-3 py-2 text-left text-sm font-semibold transition ${documentType === type ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'}`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center transition hover:border-slate-900 hover:bg-white"
          >
            <input ref={fileInputRef} type="file" className="hidden" accept=".pdf,.docx,.txt" onChange={handleFileChange} />
            <CloudUpload className="mb-4 text-slate-900" size={42} />
            <h3 className="text-xl font-black text-slate-950">Upload Institutional Evidence</h3>
            <p className="mt-2 max-w-lg text-sm text-slate-500">Supported formats: PDF, DOCX, TXT. Selected type: <span className="font-bold text-slate-900">{documentType}</span></p>
            <span className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white">Browse Files</span>
          </div>
          {status && <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm font-semibold text-slate-700">{status}</div>}
        </div>
      </div>
    </section>
  )
}

const EvidenceView = ({ evaluation }) => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Extracted Evidence & Retrieval Candidates</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Extracted passages and indicator matches are review candidates only. EQAM scoring and readiness assessment are unavailable.</p>
    </div>
    {!evaluation ? (
      <EmptyState text="Upload a document to view retrieved evidence." />
    ) : (
      <div className="space-y-5">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-black text-slate-950">{evaluation.document?.filename}</h3>
              <p className="mt-1 text-sm text-slate-500">
                {evaluation.passages?.length || 0} extracted passage(s) · processing: {evaluation.processing_status}
              </p>
            </div>
            <span className="rounded bg-amber-50 px-3 py-1 text-xs font-black text-amber-700">
              Assessment state: {evaluation.assessment_status?.state || evaluation.readiness_assessment_status || 'unavailable'}
            </span>
          </div>
          <p className="mt-3 text-sm font-semibold text-amber-800">
            Institutional authorization and source provenance remain unverified. Retrieved matches are candidates only; no readiness score was generated.
          </p>
          {evaluation.assessment_status?.reason && (
            <p className="mt-2 text-sm text-slate-600">Scoring prerequisite: {evaluation.assessment_status.reason}</p>
          )}
          {evaluation.warnings?.map((warning) => (
            <div key={warning} className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-800">{warning}</div>
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4">
        {(evaluation.passages || []).map((item) => (
          <article key={item.passage_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded bg-slate-900 px-2 py-1 text-xs font-black text-white">{item.passage_id}</span>
                  {item.page_number && <span className="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">Page {item.page_number}</span>}
                  {item.section_title && <span className="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">{item.section_title}</span>}
                </div>
                <p className="mt-3 text-sm font-medium leading-6 text-slate-700">{item.text}</p>
                <p className="mt-3 text-xs font-semibold text-slate-500">{item.extraction_method} · offset {item.start_offset ?? 'n/a'}–{item.end_offset ?? 'n/a'}</p>
              </div>
            </div>
          </article>
        ))}
        </div>
        {evaluation.matches?.length > 0 && (
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-black text-slate-950">Candidate indicator matches</h3>
            <div className="mt-4 space-y-2">
              {evaluation.matches.map((match) => (
                <div key={`${match.passage_id}-${match.framework}-${match.indicator}`} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 p-3 text-sm">
                  <span className="font-bold text-slate-800">{match.framework} · {match.indicator}</span>
                  <span className="font-black text-slate-700">cosine similarity {match.similarity}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )}
  </section>
)

const InstitutionRegistry = () => {
  const [institutions, setInstitutions] = useState([])
  const [frameworks, setFrameworks] = useState([])
  const [selectedInstitution, setSelectedInstitution] = useState('')
  const [selectedFramework, setSelectedFramework] = useState('')
  const [selectedCriterion, setSelectedCriterion] = useState('')
  const [evidenceStatus, setEvidenceStatus] = useState(null)
  const [readiness, setReadiness] = useState([])
  const [documents, setDocuments] = useState([])
  const [name, setName] = useState('')
  const [status, setStatus] = useState('')

  const loadInstitutions = useCallback(async () => {
    const response = await apiFetch('/api/institutions')
    if (!response.ok) throw new Error('Institution registry is unavailable.')
    const data = await response.json()
    setInstitutions(data.institutions || [])
    if (!selectedInstitution && data.institutions?.[0]) setSelectedInstitution(data.institutions[0].id)
  }, [selectedInstitution])

  useEffect(() => {
    apiFetch('/api/institutions')
      .then((response) => {
        if (!response.ok) throw new Error('Institution registry is unavailable.')
        return response.json()
      })
      .then((data) => {
        setInstitutions(data.institutions || [])
        if (data.institutions?.[0]) setSelectedInstitution(data.institutions[0].id)
        return apiFetch('/api/frameworks')
      })
      .then((response) => response.json())
      .then((frameworkData) => {
        setFrameworks(frameworkData.frameworks || [])
        if (frameworkData.frameworks?.[0]) setSelectedFramework(frameworkData.frameworks[0].framework_id)
      })
      .catch((error) => setStatus(error.message))
  }, [])

  useEffect(() => {
    const framework = frameworks.find((item) => item.framework_id === selectedFramework)
    if (!selectedInstitution || !framework) return
    Promise.all([
      apiFetch(`/api/institutions/${selectedInstitution}/readiness?framework_id=${encodeURIComponent(selectedFramework)}&framework_edition=${encodeURIComponent(framework.methodology_version)}`).then((response) => response.json()),
      apiFetch(`/api/institutions/${selectedInstitution}/documents`).then((response) => response.json()),
    ]).then(([readinessData, documentData]) => {
      setReadiness(readinessData.records || [])
      setDocuments(documentData.documents || [])
    })
      .catch((error) => setStatus(error.message))
  }, [frameworks, selectedFramework, selectedInstitution])

  const createInstitution = async (event) => {
    event.preventDefault()
    setStatus('')
    const response = await apiFetch('/api/institutions', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      setStatus(data.detail || 'Institution could not be created.')
      return
    }
    setName('')
    setStatus('Institution created. No ranking score was generated.')
    await loadInstitutions()
  }

  const framework = frameworks.find((item) => item.framework_id === selectedFramework)
  const readinessByCriterion = new Map(readiness.map((item) => [item.criterion_id, item]))
  const criteria = Object.keys(framework?.criteria || {})
  const activeCriterion = criteria.includes(selectedCriterion) ? selectedCriterion : criteria[0]
  const currentEvidenceStatus = evidenceStatus || readinessByCriterion.get(activeCriterion)?.evidence_status || 'unknown'

  const saveReadiness = async (event) => {
    event.preventDefault()
    const item = readinessByCriterion.get(activeCriterion)
    const response = await apiFetch(`/api/institutions/${selectedInstitution}/readiness`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        framework_id: selectedFramework,
        framework_edition: framework.methodology_version,
        criterion_id: activeCriterion,
        ...(item || {}),
        evidence_status: currentEvidenceStatus,
      }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      setStatus(data.detail || 'Readiness metadata could not be saved.')
      return
    }
    setStatus('Readiness metadata saved. No ranking score was generated.')
    const refreshed = await apiFetch(`/api/institutions/${selectedInstitution}/readiness?framework_id=${encodeURIComponent(selectedFramework)}&framework_edition=${encodeURIComponent(framework.methodology_version)}`)
    setReadiness((await refreshed.json()).records || [])
  }

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="text-3xl font-black text-slate-950">Institution Registry & Evidence Readiness</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">Manage authorized institution records and evidence metadata. This checklist does not calculate RRS, ARRS, or official rankings.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-lg font-black text-slate-950">Institutions</h3>
          <select value={selectedInstitution} onChange={(event) => setSelectedInstitution(event.target.value)} className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="">Select an institution</option>
            {institutions.map((institution) => <option key={institution.id} value={institution.id}>{institution.display_name || institution.name}</option>)}
          </select>
          <form onSubmit={createInstitution} className="mt-6 space-y-3 border-t border-slate-100 pt-5">
            <label className="text-xs font-black uppercase tracking-wider text-slate-400">Add institution</label>
            <input value={name} onChange={(event) => setName(event.target.value)} required placeholder="Official institution name" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <button type="submit" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white">Create registry record</button>
          </form>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-lg font-black text-slate-950">Framework checklist</h3>
            <select value={selectedFramework} onChange={(event) => { setSelectedFramework(event.target.value); setSelectedCriterion(''); setEvidenceStatus(null) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {frameworks.map((item) => <option key={item.framework_id} value={item.framework_id}>{item.framework_id} {item.methodology_version}</option>)}
            </select>
          </div>
          {!selectedInstitution || !framework ? (
            <p className="mt-6 text-sm font-semibold text-slate-500">Select an institution and framework edition.</p>
          ) : (
            <div className="mt-5 space-y-2">
              <div className="mb-4 rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-black uppercase tracking-wider text-slate-400">Mapped documents</p>
                {documents.length === 0 ? <p className="mt-2 text-sm font-semibold text-slate-500">No institution documents uploaded.</p> : documents.filter((document) => document.framework_id === selectedFramework).map((document) => <div key={`${document.id}-${document.criterion_id}`} className="mt-2 flex items-center justify-between gap-3 text-sm"><span className="font-semibold text-slate-700">{document.title || document.filename}</span><span className="text-xs font-bold text-slate-500">{document.review_status} · {document.research_permission_status}</span></div>)}
              </div>
              {criteria.map((criterion) => {
                const item = readinessByCriterion.get(criterion)
                return <div key={criterion} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm"><span className="font-semibold text-slate-700">{criterion}</span><span className="rounded bg-amber-100 px-2 py-1 text-xs font-black text-amber-700">{item?.evidence_status || 'unknown'}</span></div>
              })}
              <form onSubmit={saveReadiness} className="mt-5 grid gap-3 border-t border-slate-100 pt-5 sm:grid-cols-[1fr_auto_auto]">
                <select value={activeCriterion || ''} onChange={(event) => { setSelectedCriterion(event.target.value); setEvidenceStatus(null) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  {criteria.map((criterion) => <option key={criterion} value={criterion}>{criterion}</option>)}
                </select>
                <select value={currentEvidenceStatus} onChange={(event) => setEvidenceStatus(event.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  <option value="unknown">Unknown</option>
                  <option value="available">Available</option>
                  <option value="incomplete">Incomplete</option>
                  <option value="missing">Missing</option>
                </select>
                <button type="submit" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white">Save status</button>
              </form>
            </div>
          )}
          {status && <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm font-semibold text-slate-600">{status}</p>}
        </div>
      </div>
    </section>
  )
}

const FrameworkAnalysis = () => {
  const [frameworks, setFrameworks] = useState([])
  const [status, setStatus] = useState('Loading the backend framework catalog...')

  useEffect(() => {
    let active = true
    apiFetch('/api/frameworks')
      .then(async (response) => {
        if (!response.ok) throw new Error('Framework catalog is unavailable.')
        return response.json()
      })
      .then((data) => {
        if (!active) return
        setFrameworks(data.frameworks || [])
        setStatus(data.scoring_enabled ? 'Scoring is enabled by the backend.' : 'Scoring is disabled; criteria and weights are not approved for assessment.')
      })
      .catch((error) => {
        if (active) setStatus(`Framework catalog unavailable: ${error.message}`)
      })
    return () => { active = false }
  }, [])

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="text-3xl font-black tracking-normal text-slate-950">Framework Criteria Catalog</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">The backend catalog is provisional and supports retrieval only. Official weights and readiness scoring are unavailable until criteria are verified and locked.</p>
      </div>
      <div role="status" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-900">{status}</div>
      {frameworks.length === 0 ? <EmptyState text="No framework catalog is available." /> : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {frameworks.map((framework) => (
            <div key={framework.framework_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-xl font-black text-slate-950">{framework.official_name}</h3>
                  <p className="mt-1 text-sm text-slate-500">Edition {framework.methodology_version || 'not recorded'}</p>
                </div>
                <span className="rounded-lg bg-amber-50 px-3 py-1 text-xs font-black text-amber-800">{framework.criteria_status || 'status unavailable'}</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">Weight status: {framework.weight_status || 'unverified'}</p>
              <ul className="space-y-2">
                {Object.entries(framework.criteria || {}).map(([criterionId, description]) => (
                  <li key={criterionId} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                    <span className="font-bold">{criterionId}</span>{description ? ` · ${description}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

const ExplainableAI = ({ evaluation }) => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Explainable AI & Decision Support</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Score explanations and criterion gaps are unavailable because the validated readiness scoring workflow is not implemented.</p>
    </div>
    {!evaluation || !evaluation.strengths ? (
      <EmptyState text="No traceable scoring output is available to explain." />
    ) : (
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="rounded-lg border border-emerald-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-emerald-700"><CheckCircle2 size={20} /> Strengths</h3>
          <ul className="space-y-3">
            {evaluation.strengths.map((item) => <li key={item} className="rounded-lg bg-emerald-50 p-3 text-sm font-semibold text-slate-700">{item}</li>)}
          </ul>
        </div>
        <div className="rounded-lg border border-amber-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-amber-700"><AlertTriangle size={20} /> Gaps</h3>
          <ul className="space-y-3">
            {evaluation.weaknesses.map((item) => <li key={item} className="rounded-lg bg-amber-50 p-3 text-sm font-semibold text-slate-700">{item}</li>)}
          </ul>
        </div>
      </div>
    )}
  </section>
)

const ChecklistView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Research Requirements & Prototype Scope</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">These items summarize planned requirements. A visible screen or utility function does not mean the workflow is implemented or validated.</p>
    </div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      {checklistGroups.map(({ title, icon: Icon, items }) => (
        <div key={title} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><Icon size={20} /> {title}</h3>
          <div className="space-y-3">
            {items.map(([name, description]) => (
              <div key={name} className="flex gap-3 rounded-lg bg-slate-50 p-3">
                <AlertTriangle className="mt-0.5 shrink-0 text-amber-600" size={18} />
                <div>
                  <div className="text-sm font-black text-slate-800">{name}</div>
                  <div className="mt-1 text-sm text-slate-500">{description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </section>
)

const ArchitectureView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Proposed Architecture & Traceability</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">This view summarizes intended modules. Readiness scoring, score explanations, ranking history, and report artifacts are not connected to the document upload workflow.</p>
    </div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
      {ARCHITECTURE_MODULES.map(([module, output], index) => (
        <div key={module} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-sm font-black text-white">{index + 1}</div>
          <h3 className="text-base font-black text-slate-950">{module}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-500">{output}</p>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><KeyRound size={20} /> Role-Based Access Control</h3>
        <div className="space-y-3">
          {GOVERNANCE_ROWS.map(([role, permission]) => (
            <div key={role} className="rounded-lg bg-slate-50 p-3">
              <div className="text-sm font-black text-slate-900">{role}</div>
              <div className="mt-1 text-sm text-slate-500">{permission}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><TableProperties size={20} /> Report Artifacts</h3>
        <div className="space-y-3 text-sm font-semibold text-slate-600">
          <div className="rounded-lg bg-slate-50 p-3">Traceability and module verification artifacts are planned; screen presence does not establish implementation.</div>
          <div className="rounded-lg bg-slate-50 p-3">Evidence metadata is persisted; source authorization, AES, and evidence acceptance are not verified by upload.</div>
          <div className="rounded-lg bg-slate-50 p-3">RRS, ARRS, Best-Fit, and criterion-level gap reports are unavailable.</div>
          <div className="rounded-lg bg-slate-50 p-3">Validation summaries require approved data and completed evaluation; no empirical results are available.</div>
        </div>
      </div>
    </div>
  </section>
)

const ValidationView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Validation Plan</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Planned validation requirements and metrics are listed below. They are not completed empirical results.</p>
    </div>
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-black uppercase text-slate-500">
            <tr>
              <th className="p-4">Validation Item</th>
              <th className="p-4">Planned measure</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {VALIDATION_ROWS.map(([item, implementation]) => (
              <tr key={item}>
                <td className="p-4 font-black text-slate-900">{item}</td>
                <td className="p-4 text-slate-600">{implementation}</td>
                <td className="p-4"><span className="rounded bg-amber-50 px-2 py-1 text-xs font-black text-amber-800">Not evaluated</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-black text-slate-950">SOP-Objective-Method-Metric Alignment</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-left">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-black uppercase text-slate-500">
            <tr>
              <th className="p-4">SOP</th>
              <th className="p-4">Evaluation Focus</th>
              <th className="p-4">Metric or Output</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {SOP_ALIGNMENT_ROWS.map(([sop, focus, metric]) => (
              <tr key={sop}>
                <td className="p-4 font-black text-slate-900">{sop}</td>
                <td className="p-4 text-slate-600">{focus}</td>
                <td className="p-4 text-slate-600">{metric}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </section>
)

const fetchResearchValidation = async () => {
  const response = await apiFetch('/api/research/validation/status', {
    credentials: 'include',
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Unable to load research-validation status.')
  return data
}

const ResearchValidationView = () => {
  const [status, setStatus] = useState(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState('')
  const [preflightReports, setPreflightReports] = useState({})
  const [runningConfig, setRunningConfig] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [datasetVersion, setDatasetVersion] = useState('')
  const [annotationVersion, setAnnotationVersion] = useState('')
  const [datasetProvenance, setDatasetProvenance] = useState('')
  const [randomSeed, setRandomSeed] = useState('0')
  const [annotationQueue, setAnnotationQueue] = useState([])
  const [annotationQueueError, setAnnotationQueueError] = useState('')
  const [reviewingExample, setReviewingExample] = useState('')
  const [reviewDrafts, setReviewDrafts] = useState({})
  const [datasetReviewNote, setDatasetReviewNote] = useState('')
  const [approvingDataset, setApprovingDataset] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const data = await fetchResearchValidation()
      setStatus(data)
      setSelectedDatasetId((current) => (
        current && data.datasets.some((dataset) => dataset.id === current)
          ? current
          : data.datasets[0]?.id || ''
      ))
    } catch (loadError) {
      setError(loadError.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!selectedDatasetId) return
    let active = true
    Promise.all(['A0', 'A1', 'A2', 'A3', 'A4'].map(async (configurationId) => {
      const params = new URLSearchParams({
        dataset_id: selectedDatasetId,
        configuration_id: configurationId,
        evaluation_scope: configurationId === 'A0' ? 'retrieval' : 'readiness',
      })
      const response = await apiFetch(`/api/research/experiments/preflight?${params}`)
      const report = await response.json()
      if (!response.ok) throw new Error(report.detail || 'Unable to check experiment prerequisites.')
      return [configurationId, report]
    }))
      .then((reports) => {
        if (active) setPreflightReports({
          datasetId: selectedDatasetId,
          reports: Object.fromEntries(reports),
        })
      })
      .catch((loadError) => {
        if (active) setError(loadError.message)
      })
    return () => { active = false }
  }, [selectedDatasetId])

  useEffect(() => {
    if (!selectedDatasetId) return undefined
    let active = true
    apiFetch(`/api/research/datasets/${selectedDatasetId}/annotations`, {
      credentials: 'include',
    })
      .then(async (response) => {
        const result = await response.json()
        if (!response.ok) throw new Error(result.detail || 'Annotation review is unavailable.')
        return result.annotations
      })
      .then((annotations) => {
        if (active) {
          setAnnotationQueue(annotations)
          setAnnotationQueueError('')
          setReviewDrafts({})
        }
      })
      .catch((loadError) => {
        if (active) {
          setAnnotationQueue([])
          setAnnotationQueueError(typeof loadError.message === 'string'
            ? loadError.message
            : JSON.stringify(loadError.message))
        }
      })
    return () => { active = false }
  }, [selectedDatasetId])

  useEffect(() => {
    let active = true
    fetchResearchValidation()
      .then((data) => {
        if (active) setStatus(data)
      })
      .catch((loadError) => {
        if (active) setError(loadError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const handleDatasetFile = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setImporting(true)
    setMessage('')
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('dataset_version', datasetVersion)
      form.append('annotation_version', annotationVersion)
      form.append('provenance', datasetProvenance)
      form.append('random_seed', randomSeed)
      const response = await apiFetch('/api/research/datasets/import', {
        method: 'POST',
        credentials: 'include',
        body: form,
      })
      const result = await response.json()
      if (!response.ok) {
        throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail))
      }
      setMessage(`Dataset ${result.report.dataset_version} imported. Split counts: ${Object.entries(result.report.split_counts).map(([name, count]) => `${name} ${count}`).join(', ')}.`)
      await refresh()
    } catch (importError) {
      setError(importError.message)
    } finally {
      setImporting(false)
      event.target.value = ''
    }
  }

  const runExperiment = async (configurationId) => {
    setRunningConfig(configurationId)
    setError('')
    setMessage('')
    try {
      const response = await apiFetch('/api/research/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          configuration_id: configurationId,
          random_seed: status.datasets.find((dataset) => dataset.id === selectedDatasetId)?.split_seed ?? 0,
          evaluation_scope: configurationId === 'A0' ? 'retrieval' : 'readiness',
        }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Experiment request failed.')
      const scope = configurationId === 'A0' ? 'retrieval-only' : 'readiness'
      setMessage(`${configurationId} ${scope}: ${result.execution_state}. Results are available only for completed runs.`)
      await refresh()
    } catch (runError) {
      setError(runError.message)
    } finally {
      setRunningConfig('')
    }
  }

  const submitAnnotationReview = async (annotation) => {
    const draft = reviewDrafts[annotation.example_id] || {}
    const original = /^(true|1|yes|positive|relevant)$/i.test(String(annotation.imported_label))
    const label = draft.label === undefined ? original : draft.label === 'true'
    const adjudication = annotation.independent_review_count >= 2
    const decision = adjudication ? 'adjudicate' : (label === original ? 'confirm' : 'correct')
    setReviewingExample(annotation.example_id)
    setError('')
    try {
      const response = await apiFetch(`/api/research/datasets/${selectedDatasetId}/annotation-reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          reviews: [{
            example_id: annotation.example_id,
            label,
            decision,
            note: draft.note || '',
          }],
        }),
      })
      const result = await response.json()
      if (!response.ok) {
        const detail = typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail)
        throw new Error(detail || 'Annotation review failed.')
      }
      const queueResponse = await apiFetch(`/api/research/datasets/${selectedDatasetId}/annotations`, {
        credentials: 'include',
      })
      const queueResult = await queueResponse.json()
      if (!queueResponse.ok) throw new Error(queueResult.detail || 'Unable to refresh annotation review queue.')
      setAnnotationQueue(queueResult.annotations)
      setReviewDrafts((current) => {
        const next = { ...current }
        delete next[annotation.example_id]
        return next
      })
      setMessage(`Saved ${decision} for ${annotation.example_id}.`)
    } catch (reviewError) {
      setError(reviewError.message)
    } finally {
      setReviewingExample('')
    }
  }

  const approveReviewedDataset = async () => {
    setApprovingDataset(true)
    setError('')
    try {
      const response = await apiFetch(`/api/research/datasets/${selectedDatasetId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ decision: 'approved', note: datasetReviewNote }),
      })
      const result = await response.json()
      if (!response.ok) {
        const detail = typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail)
        throw new Error(detail || 'Dataset approval failed.')
      }
      setMessage(`Dataset approval recorded: ${result.verification_status}.`)
      setDatasetReviewNote('')
      await refresh()
    } catch (reviewError) {
      setError(reviewError.message)
    } finally {
      setApprovingDataset(false)
    }
  }

  const stateStyle = (value) => {
    if (value === 'completed' || value === 'completed_with_limitations') return 'bg-emerald-50 text-emerald-700'
    if (value === 'ready_to_run') return 'bg-blue-50 text-blue-700'
    if (value === 'running') return 'bg-amber-50 text-amber-700'
    if (value === 'failed') return 'bg-red-50 text-red-700'
    return 'bg-slate-100 text-slate-700'
  }

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="flex items-center gap-3 text-3xl font-black tracking-normal text-slate-950"><Microscope /> Research Validation</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">Reproducible research runs are separated from application tests. No empirical result is shown unless it is generated from an authorized expert-labeled dataset and traceable model configuration.</p>
      </div>
      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">{error}</div>}
      {message && <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-800">{message}</div>}
      {loading && <EmptyState text="Loading research prerequisites…" />}
      {!loading && status && (
        <>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-lg font-black text-amber-950">
                {status.empirical_results_available
                  ? 'Readiness research runs are available with limitations'
                  : status.retrieval_results_available
                    ? 'Retrieval results are available; readiness scoring remains blocked'
                    : 'Empirical validation is not yet available'}
              </h3>
              <span className={`rounded px-2 py-1 text-xs font-black ${stateStyle(status.state)}`}>{status.state}</span>
            </div>
            <p className="mt-2 text-sm text-amber-900">{status.empirical_result_note}</p>
            <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-amber-900">
              {status.missing_prerequisites.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {Object.entries(status.dataset_counts).map(([label, count]) => (
              <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <div className="text-xs font-bold uppercase text-slate-500">{label.replaceAll('_', ' ')}</div>
                <div className="mt-2 text-2xl font-black text-slate-950">{count}</div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-black text-slate-950">Import a research dataset</h3>
            <p className="mt-1 text-sm text-slate-500">Upload CSV or JSONL with example_id, framework, indicator, binary label, source_document_id, institution_group_id, and either text or source_passage_id. The original file is retained privately with its SHA-256 and line-level validation report. Imports stay unapproved until independent per-example review and dataset approval are complete.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-bold text-slate-600">Dataset version
                <input value={datasetVersion} onChange={(event) => setDatasetVersion(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" maxLength={100} />
              </label>
              <label className="text-xs font-bold text-slate-600">Annotation version
                <input value={annotationVersion} onChange={(event) => setAnnotationVersion(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" maxLength={100} />
              </label>
              <label className="text-xs font-bold text-slate-600">Provenance
                <input value={datasetProvenance} onChange={(event) => setDatasetProvenance(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" maxLength={2000} />
              </label>
              <label className="text-xs font-bold text-slate-600">Split seed
                <input type="number" value={randomSeed} onChange={(event) => setRandomSeed(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" />
              </label>
            </div>
            <label className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800">
              <input type="file" accept=".csv,.jsonl,text/csv,application/x-ndjson" className="sr-only" disabled={importing || !datasetVersion.trim() || !annotationVersion.trim() || !datasetProvenance.trim()} onChange={handleDatasetFile} />
              {importing ? 'Importing…' : 'Select CSV or JSONL'}
            </label>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-black text-slate-950">Independent annotation review</h3>
            <p className="mt-1 text-sm text-slate-500">Each example needs two distinct reviewers. Disagreements remain unresolved until a third reviewer adjudicates; the imported label and original model prediction are preserved separately.</p>
            {annotationQueueError
              ? <p role="status" className="mt-3 text-sm text-amber-800">{annotationQueueError}</p>
              : annotationQueue.length === 0
                ? <p className="mt-3 text-sm text-slate-500">No annotations are currently available for this reviewer, or the selected dataset has no outstanding reviews.</p>
                : (
                  <div className="mt-4 space-y-3">
                    {annotationQueue.map((annotation) => {
                      const draft = reviewDrafts[annotation.example_id] || {}
                      const importedPositive = /^(true|1|yes|positive|relevant)$/i.test(String(annotation.imported_label))
                      const selectedLabel = draft.label ?? (importedPositive ? 'true' : 'false')
                      const needsAdjudication = annotation.independent_review_count >= 2
                        && annotation.distinct_review_labels > 1
                      return (
                        <article key={annotation.example_id} className="rounded-lg border border-slate-200 p-4">
                          <div className="flex flex-wrap justify-between gap-2 text-sm">
                            <strong>{annotation.example_id} · {annotation.framework} / {annotation.indicator}</strong>
                            <span className="text-xs text-slate-500">
                              {needsAdjudication ? 'Adjudication required' : `${annotation.independent_review_count} of 2 independent reviews`}
                            </span>
                          </div>
                          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{annotation.text || 'No evidence text was resolved.'}</p>
                          <p className="mt-2 text-xs text-slate-500">Imported label: {String(annotation.imported_label)} · Group: {annotation.institution_group_id}</p>
                          {annotation.original_prediction_json && <pre className="mt-1 overflow-auto whitespace-pre-wrap text-xs text-slate-500">Original model prediction: {annotation.original_prediction_json}</pre>}
                          <div className="mt-3 grid gap-3 sm:grid-cols-2">
                            <label className="text-xs font-bold text-slate-600">Reviewed relevance
                              <select value={selectedLabel} onChange={(event) => setReviewDrafts((current) => ({
                                ...current,
                                [annotation.example_id]: { ...current[annotation.example_id], label: event.target.value },
                              }))} className="mt-1 block w-full rounded border border-slate-300 bg-white p-2 text-sm">
                                <option value="true">Relevant</option>
                                <option value="false">Not relevant</option>
                              </select>
                            </label>
                            <label className="text-xs font-bold text-slate-600">Review rationale
                              <input value={draft.note || ''} onChange={(event) => setReviewDrafts((current) => ({
                                ...current,
                                [annotation.example_id]: { ...current[annotation.example_id], note: event.target.value },
                              }))} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" minLength={10} maxLength={2000} />
                            </label>
                          </div>
                          <button type="button" disabled={reviewingExample === annotation.example_id || (draft.note || '').trim().length < 10} onClick={() => submitAnnotationReview(annotation)} className="mt-3 rounded bg-slate-900 px-3 py-2 text-xs font-bold text-white disabled:bg-slate-300">
                            {reviewingExample === annotation.example_id ? 'Saving…' : needsAdjudication ? 'Submit adjudication' : 'Submit independent review'}
                          </button>
                        </article>
                      )
                    })}
                  </div>
                )}
            {status.datasets.find((dataset) => dataset.id === selectedDatasetId)?.verification_status === 'submitted' && (
              <div className="mt-5 border-t pt-4">
                <label className="block text-xs font-bold text-slate-600">Dataset approval rationale
                  <input value={datasetReviewNote} onChange={(event) => setDatasetReviewNote(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm" minLength={10} maxLength={2000} />
                </label>
                <button type="button" disabled={approvingDataset || datasetReviewNote.trim().length < 10} onClick={approveReviewedDataset} className="mt-3 rounded bg-emerald-700 px-3 py-2 text-xs font-bold text-white disabled:bg-slate-300">
                  {approvingDataset ? 'Approving…' : 'Approve after annotation review'}
                </button>
              </div>
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {status.ablations.map((ablation) => (
              <article key={ablation.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                {(() => {
                  const reports = preflightReports.datasetId === selectedDatasetId
                    ? preflightReports.reports
                    : {}
                  const report = reports[ablation.id]
                  const isChecking = Boolean(selectedDatasetId) && !report && !error
                  const runDisabled = !selectedDatasetId || !report?.execution_allowed || isChecking || Boolean(runningConfig)
                  const blockers = report?.checks.filter((check) => check.status !== 'passed') || []
                  return (
                    <>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs font-black uppercase tracking-wide text-slate-400">{ablation.id}</div>
                    <h3 className="mt-1 text-base font-black text-slate-950">{ablation.name}</h3>
                    {ablation.id === 'A0' && <p className="mt-1 text-xs font-semibold text-amber-800">Available run scope: held-out Sentence-BERT retrieval only. Readiness/AHP–TOPSIS output remains blocked.</p>}
                  </div>
                  <span className={`shrink-0 rounded px-2 py-1 text-xs font-black ${stateStyle(report?.state || ablation.status)}`}>{report?.state || ablation.status}</span>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-600">
                  {Object.entries(ablation.components).map(([component, value]) => (
                    <div key={component} className="rounded bg-slate-50 p-2">
                      <dt className="font-bold">{component.replaceAll('_', ' ')}</dt>
                      <dd className="mt-1">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
                <label className="mt-4 block text-xs font-bold text-slate-600">
                  Dataset version
                  <select
                    className="mt-1 block w-full rounded border border-slate-300 bg-white p-2 text-sm"
                    value={selectedDatasetId}
                    onChange={(event) => setSelectedDatasetId(event.target.value)}
                  >
                    <option value="">Select a dataset</option>
                    {status.datasets.map((dataset) => (
                      <option key={dataset.id} value={dataset.id}>
                        {dataset.dataset_version} · {dataset.verification_status}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="mt-3 text-xs text-slate-600">
                  {report?.dataset
                    ? `Train ${report.dataset.partition_counts.train} · Validation ${report.dataset.partition_counts.validation} · Test ${report.dataset.partition_counts.test}`
                    : 'Partition counts are unavailable until a dataset is selected.'}
                </div>
                {report && (
                  <>
                    <p className="mt-2 text-xs text-slate-600">
                      Model: {report.model.role} · {report.model.version || 'artifact unavailable'}
                      {` · Artifact digest ${report.model.artifact_hash_verified ? `verified (${report.model.artifact_sha256})` : 'not verified'}`}
                      {report.protocol_version ? ` · Protocol ${report.protocol_version}` : ''}
                    </p>
                    {report.retrieval_query_counts && (
                      <p className="mt-1 text-xs text-slate-600">
                        Test queries: {report.retrieval_query_counts.eligible_test_queries} eligible of {report.retrieval_query_counts.test_queries}
                      </p>
                    )}
                  </>
                )}
                <ul className="mt-3 space-y-1 text-xs text-slate-600">
                  {blockers.map((check) => <li key={check.name}><strong>{check.name}:</strong> {check.reason}</li>)}
                </ul>
                <button
                  type="button"
                  className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                  disabled={runDisabled}
                  title={runDisabled ? (blockers[0]?.reason || 'Check prerequisites before running.') : 'Run this experiment'}
                  onClick={() => runExperiment(ablation.id)}
                >
                  {runningConfig === ablation.id ? 'Running…' : isChecking ? 'Checking prerequisites…' : ablation.id === 'A0' ? 'Run A0 retrieval' : `Run ${ablation.id}`}
                </button>
                {runDisabled && <p className="mt-2 text-xs text-slate-500">Run is disabled: {blockers[0]?.reason || 'Select a dataset and complete preflight.'}</p>}
                    </>
                  )
                })()}
              </article>
            ))}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-black text-slate-950">Versioned datasets</h3>
            {status.datasets.length === 0 ? <p className="mt-2 text-sm text-slate-500">No research datasets are stored for this institution.</p> : (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[620px] text-left text-sm">
                  <thead className="border-b bg-slate-50 text-xs font-black uppercase text-slate-500">
                    <tr><th className="p-3">Dataset</th><th className="p-3">Review status</th><th className="p-3">Annotation</th><th className="p-3">Train / Validation / Test</th><th className="p-3">Seed</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {status.datasets.map((dataset) => (
                      <tr key={dataset.id}>
                        <td className="p-3 font-bold">{dataset.dataset_version}</td>
                        <td className="p-3">{dataset.verification_status}</td>
                        <td className="p-3">{dataset.annotation_version}</td>
                        <td className="p-3">{dataset.train_count} / {dataset.validation_count} / {dataset.test_count}</td>
                        <td className="p-3">{dataset.split_seed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-black text-slate-950">Implemented metric infrastructure</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {status.implemented_metrics.map((metric) => <span key={metric} className="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">{metric}</span>)}
            </div>
            <p className="mt-3 text-sm text-slate-500">Metrics are not displayed as results until an eligible experiment has completed.</p>
          </div>
          {status.research_runs.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-black text-slate-950">Stored experiment runs</h3>
              <div className="mt-3 space-y-3">
                {status.research_runs.map((run) => (
                  <div key={run.id} className="rounded-lg bg-slate-50 p-3">
                    <div className="flex flex-wrap justify-between gap-2 text-sm">
                      <span className="font-bold">{run.configuration_id} · {run.experiment_type} · {run.dataset_id || 'no approved dataset link'}</span>
                      <span className={`rounded px-2 py-1 text-xs font-black ${stateStyle(run.execution_state || run.status)}`}>{run.execution_state || run.status}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">Scope: {run.configuration?.evaluation_scope || 'readiness'} · Model: {run.model_version || 'not recorded'} · Method: {run.method_version} · Seed: {run.random_seed}</div>
                    {(run.execution_state === 'completed' || run.execution_state === 'completed_with_limitations') && run.result && (
                      <>
                        <div className="mt-2 text-xs text-slate-600">Samples: {JSON.stringify(run.sample_counts || {})} · Evaluation: {JSON.stringify(run.evaluation_config || {})}</div>
                        {run.result.limitations?.length > 0 && <p className="mt-2 text-xs text-amber-800">Limitations: {run.result.limitations.join('; ')}</p>}
                        <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-slate-700">{JSON.stringify(run.result, null, 2)}</pre>
                      </>
                    )}
                    {run.execution_state === 'failed' && <p className="mt-2 text-xs text-red-700">{run.error_summary || 'Execution failed; no results were stored.'}</p>}
                    {run.preflight?.checks && run.execution_state !== 'completed' && (
                      <ul className="mt-2 space-y-1 text-xs text-amber-900">
                        {run.preflight.checks.filter((check) => check.status !== 'passed').map((check) => <li key={check.name}>{check.name}: {check.reason}</li>)}
                      </ul>
                    )}
                    {run.warnings?.length > 0 && <p className="mt-2 text-xs text-amber-800">Warnings: {run.warnings.join('; ')}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}

const HistoryView = () => {
  const [assessments, setAssessments] = useState([])
  const [status, setStatus] = useState('Loading persisted assessment records...')

  useEffect(() => {
    let active = true
    apiFetch('/api/assessments')
      .then(async (response) => {
        if (!response.ok) throw new Error('Assessment records are unavailable.')
        return response.json()
      })
      .then((data) => {
        if (!active) return
        const records = data.assessments || []
        setAssessments(records)
        setStatus(records.length ? '' : 'No persisted assessment records are available.')
      })
      .catch((error) => {
        if (active) setStatus(`Assessment history unavailable: ${error.message}`)
      })
    return () => { active = false }
  }, [])

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="text-3xl font-black tracking-normal text-slate-950">Persisted Assessment Records</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">This view lists backend workflow records and their processing state. Ranking scores and Best-Fit recommendations are not implemented.</p>
      </div>
      {status && <div role="status" className="rounded-lg border border-slate-200 bg-white p-4 text-sm font-semibold text-slate-700">{status}</div>}
      {assessments.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-black uppercase text-slate-500">
                <tr>
                  <th className="p-4">Institution</th>
                  <th className="p-4">Assessment ID</th>
                  <th className="p-4">Workflow status</th>
                  <th className="p-4">Created</th>
                  <th className="p-4">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {assessments.map((item) => (
                  <tr key={item.id}>
                    <td className="p-4 font-bold text-slate-800">{item.institution_name || 'Institution unavailable'}</td>
                    <td className="p-4 font-mono text-xs text-slate-600">{item.id}</td>
                    <td className="p-4 text-slate-700">{item.status || 'status unavailable'}</td>
                    <td className="p-4 text-slate-500">{item.created_at || 'not recorded'}</td>
                    <td className="p-4 text-slate-500">{item.updated_at || 'not recorded'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}

// Retained as a legacy prototype component; the authenticated dashboard uses persisted institutions.
// eslint-disable-next-line no-unused-vars
const NewSubmission = ({ submissions, setSubmissions, universities }) => {
  const navigate = useNavigate()
  const [universityId, setUniversityId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [files, setFiles] = useState([])
  const [error, setError] = useState('')
  const selectedUniversity = universities.find((university) => university.id === universityId)



  const handleFiles = (event) => {
    const selectedFiles = Array.from(event.target.files || [])

    if (selectedFiles.length === 0) {
      return
    }

    setFiles((previous) => {
      const existingNames = new Set(previous.map((file) => file.name))

      const newFiles = selectedFiles.filter(
        (file) => !existingNames.has(file.name)
      )

      return [...previous, ...newFiles]
    })

    event.target.value = ''
  }

  const removeFile = (index) => {
    setFiles((previous) => previous.filter((_, fileIndex) => fileIndex !== index))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    setError('')

    if (!selectedUniversity) {
      setError('Please select a university.')
      return
    }

    if (!title.trim()) {
      setError('Please enter a submission title.')
      return
    }

    if (files.length === 0) {
      setError('Please upload at least one document.')
      return
    }

    const submissionId = `SUB-${String(submissions.length + 1).padStart(4, '0')}-${Date.now()}`

    const newSubmission = {
      id: submissionId,
      universityName: selectedUniversity.name,
      title: title.trim(),
      description: description.trim(),
      status: 'Pending',
      createdAt: new Date().toLocaleString(),
      documents: files.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type,
      })),
    }

    setSubmissions((previous) => [newSubmission, ...previous])
    navigate(`/submissions/${submissionId}`)
  }

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div className="border-b border-slate-200 pb-6">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mb-4 text-sm font-bold text-slate-500 hover:text-slate-900"
        >
          ← Back to Dashboard
        </button>

        <p className="text-xs font-black uppercase text-slate-400">
          Client 1
        </p>

        <h2 className="mt-1 text-3xl font-black text-slate-950">
          New Submission
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          Create a new university submission and attach multiple supporting documents.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-black text-slate-950">
            University Information
          </h3>

          <div className="mt-5">
            <label className="mb-2 block text-sm font-bold text-slate-700">
              University
            </label>

            <select
              value={universityId}
              onChange={(event) => setUniversityId(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-slate-900"
            >
              <option value="">Select a university</option>

              {universities.map((university) => (
                <option key={university.id} value={university.id}>
                  {university.name} ({university.shortName})
                </option>
              ))}
            </select>

            {selectedUniversity && (
              <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                <span className="font-bold">Location:</span>{' '}
                {selectedUniversity.location}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-black text-slate-950">
            Submission Details
          </h3>

          <div className="mt-5 space-y-4">
            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                Submission Title
              </label>

              <input
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Example: WURI 2026 Institutional Submission"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-900"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                Description
              </label>

              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
                placeholder="Add notes or additional information about this submission..."
                className="w-full resize-none rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-900"
              />
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-black text-slate-950">
                Supporting Documents
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Upload multiple PDF, DOCX, or TXT files for this submission.
              </p>
            </div>

            <label className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-slate-900 px-4 py-3 text-sm font-bold text-white hover:bg-slate-800">
              + Add Documents

              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFiles}
                className="hidden"
              />
            </label>
          </div>

          {files.length === 0 ? (
            <div className="mt-5 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <CloudUpload className="mx-auto mb-3 text-slate-400" size={36} />

              <p className="font-bold text-slate-700">
                No documents selected
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Click "Add Documents" to select multiple files.
              </p>
            </div>
          ) : (
            <div className="mt-5 space-y-2">
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between rounded-lg border border-slate-200 p-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <FileText size={20} className="shrink-0 text-slate-500" />

                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-slate-800">
                        {file.name}
                      </p>

                      <p className="text-xs text-slate-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="ml-3 rounded px-3 py-1 text-xs font-bold text-red-600 hover:bg-red-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-bold text-red-700">
            {error}
          </div>
        )}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>

          <button
            type="submit"
            className="rounded-lg bg-slate-900 px-6 py-3 text-sm font-black text-white hover:bg-slate-800"
          >
            Submit Documents
          </button>
        </div>
      </form>
    </section>
  )
}
// Retained as a legacy prototype component; the authenticated dashboard uses persisted institutions.
// eslint-disable-next-line no-unused-vars
const ClientDashboard = ({ submissions }) => {
  const navigate = useNavigate()
  const [schoolFilter, setSchoolFilter] = useState('')

  const normalizedFilter = schoolFilter.trim().toLowerCase()

  const filteredSubmissions = normalizedFilter
    ? submissions.filter((submission) =>
        (submission.universityName || '')
          .toLowerCase()
          .includes(normalizedFilter)
      )
    : submissions

  const totalSubmissions = filteredSubmissions.length

  const pendingCount = filteredSubmissions.filter(
    (submission) => submission.status === 'Pending'
  ).length

  const underReviewCount = filteredSubmissions.filter(
    (submission) => submission.status === 'Under Review'
  ).length

  const completedCount = filteredSubmissions.filter(
    (submission) => submission.status === 'Completed'
  ).length

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
            Client 1
          </p>

          <h1 className="mt-1 text-3xl font-black text-slate-950">
            Submission Dashboard
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage and monitor your university submissions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/submission/new')}
          className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800"
        >
          + New Submission
        </button>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="mb-2 block text-sm font-black text-slate-700">
          School / University
        </label>

        <input
          type="text"
          value={schoolFilter}
          onChange={(event) => setSchoolFilter(event.target.value)}
          placeholder="Enter school / university name"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-medium text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-900 md:max-w-xl"
        />

        <p className="mt-2 text-xs text-slate-500">
          {schoolFilter.trim()
            ? 'Showing submissions matching the school name.'
            : 'Enter a school name to filter submissions.'}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Total Submissions
          </p>

          <p className="mt-2 text-3xl font-black text-slate-950">
            {totalSubmissions}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Pending
          </p>

          <p className="mt-2 text-3xl font-black text-amber-600">
            {pendingCount}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Under Review
          </p>

          <p className="mt-2 text-3xl font-black text-blue-600">
            {underReviewCount}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Completed
          </p>

          <p className="mt-2 text-3xl font-black text-emerald-600">
            {completedCount}
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 className="text-xl font-black text-slate-950">
              Recent Submissions
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {schoolFilter.trim()
                ? 'Submissions matching the entered school.'
                : 'Your latest submissions across all schools.'}
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate('/submissions')}
            className="text-sm font-black text-slate-700 hover:text-slate-950"
          >
            View All
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredSubmissions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="font-bold text-slate-700">
                No submissions found.
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Create a new submission to get started.
              </p>

              <button
                type="button"
                onClick={() => navigate('/submission/new')}
                className="mt-5 rounded-xl bg-slate-950 px-5 py-3 text-sm font-black text-white"
              >
                + New Submission
              </button>
            </div>
          ) : (
            filteredSubmissions.slice(0, 5).map((submission) => (
              <button
                type="button"
                key={submission.id}
                onClick={() => navigate('/submissions/' + submission.id)}
                className="flex w-full flex-col gap-3 px-6 py-5 text-left transition hover:bg-slate-50 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-black text-slate-950">
                      {submission.id}
                    </span>

                    <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">
                      {submission.universityName}
                    </span>
                  </div>

                  <p className="mt-2 text-sm font-bold text-slate-800">
                    {submission.title}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {submission.documents?.length || 0} supporting document(s)
                    {' · '}
                    {submission.createdAt}
                  </p>
                </div>

                <span
                  className={
                    'rounded-lg px-3 py-1.5 text-xs font-black ' +
                    (submission.status === 'Completed'
                      ? 'bg-emerald-100 text-emerald-700'
                      : submission.status === 'Under Review'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-amber-100 text-amber-700')
                  }
                >
                  {submission.status}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </section>
  )
}
// Retained as a legacy prototype component; the authenticated dashboard uses persisted institutions.
// eslint-disable-next-line no-unused-vars
const SubmissionDetails = ({ submissions }) => {
  const navigate = useNavigate()
  const { submissionId } = useParams()

  const submission = submissions.find(
    (item) => item.id === submissionId
  )

  if (!submission) {
    return (
      <section className="space-y-6 p-6 lg:p-8">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="text-sm font-bold text-slate-500 hover:text-slate-900"
        >
          ← Back to Dashboard
        </button>

        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center">
          <h2 className="text-2xl font-black text-slate-950">
            Submission Not Found
          </h2>
          <p className="mt-2 text-sm font-semibold text-slate-500">
            The requested submission could not be found.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mb-4 text-sm font-bold text-slate-500 hover:text-slate-900"
        >
          ← Back to Dashboard
        </button>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-wider text-slate-400">
              Submission Details
            </p>

            <h2 className="mt-1 text-3xl font-black text-slate-950">
              {submission.id}
            </h2>

            <p className="mt-2 text-sm font-semibold text-slate-500">
              {submission.createdAt}
            </p>
          </div>

          <span
            className={
              submission.status === 'Completed'
                ? 'rounded-lg bg-emerald-100 px-4 py-2 text-xs font-black text-emerald-700'
                : submission.status === 'Under Review'
                  ? 'rounded-lg bg-blue-100 px-4 py-2 text-xs font-black text-blue-700'
                  : 'rounded-lg bg-amber-100 px-4 py-2 text-xs font-black text-amber-700'
            }
          >
            {submission.status}
          </span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Submission Information
          </p>

          <h3 className="mt-2 text-2xl font-black text-slate-950">
            {submission.title}
          </h3>

          <div className="mt-6 space-y-4">
            <div>
              <p className="text-xs font-black uppercase text-slate-400">
                University
              </p>
              <p className="mt-1 font-bold text-slate-900">
                {submission.universityName}
              </p>
            </div>

            <div>
              <p className="text-xs font-black uppercase text-slate-400">
                Description
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-600">
                {submission.description || 'No description provided.'}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            Submission Summary
          </p>

          <div className="mt-5">
            <p className="text-4xl font-black text-slate-950">
              {submission.documents.length}
            </p>

            <p className="text-sm font-semibold text-slate-500">
              Documents Uploaded
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-wider text-slate-400">
              Uploaded Documents
            </p>

            <h3 className="mt-1 text-xl font-black text-slate-950">
              {submission.documents.length} Documents
            </h3>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {submission.documents.map((document, index) => (
            <div
              key={document.name + '-' + index}
              className="flex flex-col gap-3 rounded-lg border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-sm font-black text-slate-700">
                  {index + 1}
                </div>

                <div>
                  <p className="font-bold text-slate-900">
                    {document.name}
                  </p>

                  <p className="text-xs font-semibold text-slate-400">
                    {document.type || 'Document'}
                  </p>
                </div>
              </div>

              <span className="text-xs font-bold text-slate-400">
                {document.size
                  ? Math.max(1, Math.round(document.size / 1024))
                  : 0}{' '}
                KB
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
const EmptyState = ({ text }) => (
  <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-sm font-semibold text-slate-500 shadow-sm">{text}</div>
)

const Shell = ({ children, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const closeMenu = () => setMobileMenuOpen(false)
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      <div className="absolute left-0 top-0 z-40 flex w-full items-center justify-between border-b border-slate-200 bg-white p-4 md:hidden">
        <div className="flex items-center gap-2 font-black text-slate-950"><Award size={20} /> Ranking DSS</div>
        <button className="rounded-lg p-2 text-slate-700 hover:bg-slate-100" onClick={() => setMobileMenuOpen((open) => !open)}>{mobileMenuOpen ? <X /> : <Menu />}</button>
      </div>
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-72 shrink-0 flex-col border-r border-slate-200 bg-white transition md:static ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="hidden border-b border-slate-100 p-5 md:block">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-slate-900 p-2 text-white"><Award size={22} /></div>
            <div>
              <div className="font-black text-slate-950">Ranking DSS</div>
              <div className="text-xs font-semibold text-slate-400">WURI, THE, QS, GreenMetric</div>
            </div>
          </div>
        </div>
        <nav className="mt-16 flex-1 space-y-1 overflow-y-auto p-3 md:mt-0">
          <div className="px-3 pb-2 text-xs font-black uppercase text-slate-400">Workspace</div>
          <NavLink to="/" icon={LayoutDashboard} onClick={closeMenu}>Dashboard</NavLink>
          <NavLink to="/upload" icon={CloudUpload} onClick={closeMenu}>Document Upload</NavLink>
          <NavLink to="/evidence" icon={FileSearch} onClick={closeMenu}>Evidence & EQAM</NavLink>
          <NavLink to="/analysis" icon={BarChart3} onClick={closeMenu}>Framework Analysis</NavLink>
          <NavLink to="/xai" icon={Lightbulb} onClick={closeMenu}>XAI Support</NavLink>
          <NavLink to="/history" icon={Trophy} onClick={closeMenu}>Rank & History</NavLink>
          <div className="px-3 pb-2 pt-5 text-xs font-black uppercase text-slate-400">Governance</div>
          <NavLink to="/architecture" icon={Network} onClick={closeMenu}>Architecture</NavLink>
          <NavLink to="/checklist" icon={BookOpenCheck} onClick={closeMenu}>Checklist</NavLink>
          <NavLink to="/validation" icon={Microscope} onClick={closeMenu}>Validation QA</NavLink>
          <NavLink to="/research-validation" icon={FileSearch} onClick={closeMenu}>Research Validation</NavLink>
          <NavLink to="/institutions" icon={Building2} onClick={closeMenu}>Institutions</NavLink>
        </nav>
        <div className="border-t border-slate-100 p-3">
          <button onClick={onLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-bold text-slate-600 hover:bg-red-50 hover:text-red-700">
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto pt-16 md:pt-0">{children}</main>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authChecking, setAuthChecking] = useState(true)
  const [evaluation, setEvaluation] = useState(null)
  useEffect(() => {
    apiFetch('/api/auth/session')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Authentication required')
        }
        return response.json()
      })
      .then(() => setIsAuthenticated(true))
      .catch(() => setIsAuthenticated(false))
      .finally(() => setAuthChecking(false))
  }, [])

  const handleLogout = async () => {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' })
    } finally {
      setIsAuthenticated(false)
      setEvaluation(null)
    }
  }

  const handleEvaluation = (nextEvaluation) => {
    setEvaluation(nextEvaluation)
  }

  return (
    authChecking ? (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-sm font-bold text-slate-600">
        Checking authentication...
      </div>
    ) : (
    <Routes>
      <Route path="/login" element={<Login onLogin={setIsAuthenticated} />} />
      <Route path="/*" element={isAuthenticated ? (
        <Shell onLogout={handleLogout}>
          <Routes>
            <Route path="/" element={<PersistedDashboard />} />
            <Route path="/upload" element={<DocumentUpload onEvaluation={handleEvaluation} />} />
            <Route path="/evidence" element={<EvidenceView evaluation={evaluation} />} />
            <Route path="/analysis" element={<FrameworkAnalysis />} />
            <Route path="/xai" element={<ExplainableAI evaluation={evaluation} />} />
        <Route path="/history" element={<HistoryView />} />
            <Route path="/architecture" element={<ArchitectureView />} />
            <Route path="/checklist" element={<ChecklistView />} />
            <Route path="/validation" element={<ValidationView />} />
            <Route path="/research-validation" element={<ResearchValidationView />} />
            <Route path="/institutions" element={<InstitutionRegistry />} />
          </Routes>
        </Shell>
      ) : <Navigate to="/login" replace />} />
    </Routes>
    )
  )
}

export default App
