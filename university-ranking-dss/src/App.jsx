import { useMemo, useRef, useState } from 'react'
import { Navigate, Route, Routes, Link, useLocation } from 'react-router-dom'
import {
  AlertTriangle,
  Award,
  BarChart3,
  BookOpenCheck,
  Brain,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  CloudUpload,
  Database,
  FileSearch,
  History,
  KeyRound,
  LayoutDashboard,
  Lightbulb,
  Lock,
  LogOut,
  Menu,
  Microscope,
  SlidersHorizontal,
  TableProperties,
  Target,
  User,
  X,
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const FRAMEWORKS = [
  {
    name: 'WURI',
    color: '#d97706',
    focus: 'Innovation, entrepreneurship, social responsibility, crisis management, and student mobility.',
    officialWeight: 0.25,
    indicators: [
      ['Innovation', 0.32],
      ['Industrial Application', 0.22],
      ['Student Mobility', 0.16],
      ['Social Responsibility', 0.18],
      ['Crisis Management', 0.12],
    ],
  },
  {
    name: 'THE',
    color: '#2563eb',
    focus: 'Teaching, research environment, research quality, industry engagement, and international outlook.',
    officialWeight: 0.25,
    indicators: [
      ['Teaching', 0.29],
      ['Research Environment', 0.29],
      ['Research Quality', 0.30],
      ['Industry', 0.04],
      ['International Outlook', 0.08],
    ],
  },
  {
    name: 'QS',
    color: '#7c3aed',
    focus: 'Academic reputation, employer reputation, faculty-student ratio, citations, and internationalization.',
    officialWeight: 0.25,
    indicators: [
      ['Academic Reputation', 0.30],
      ['Employer Reputation', 0.15],
      ['Faculty Student Ratio', 0.10],
      ['Citations', 0.20],
      ['International Network', 0.10],
      ['Sustainability', 0.15],
    ],
  },
  {
    name: 'UI GreenMetric',
    color: '#059669',
    focus: 'Setting, energy, waste, water, transportation, education, and sustainable campus operations.',
    officialWeight: 0.25,
    indicators: [
      ['Setting Infrastructure', 0.15],
      ['Energy Climate', 0.21],
      ['Waste', 0.18],
      ['Water', 0.10],
      ['Transportation', 0.18],
      ['Education Research', 0.18],
    ],
  },
]

const EQAM_DIMENSIONS = [
  ['Semantic Relevance', 0.30],
  ['Model Confidence', 0.20],
  ['Evidence Completeness', 0.20],
  ['Source Reliability', 0.15],
  ['Evidence Strength', 0.15],
]

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
  ['Institutional Document Management', 'Collection, screening, verification, text extraction, segmentation, and metadata tracking'],
  ['Evidence Extraction & Knowledge Base', 'Enhanced SBERT embeddings, top-K retrieval, framework indicator mapping, and RBAC-protected evidence records'],
  ['Readiness Assessment Engine', 'EQAM, AES thresholding, framework-constrained AHP, fixed-reference TOPSIS, RRS, ARRS, and best-fit logic'],
  ['XAI & Recommendation Module', 'Evidence traceability, criterion contributions, gap identification, recommendations, and close-alternative explanations'],
  ['Dashboard & Reporting Module', 'Readiness dashboards, school ranking history, validation outputs, report-ready tables, and QA artifacts'],
]

const GOVERNANCE_ROWS = [
  ['Administrator', 'Manage users, institutional knowledge base, framework criteria, document records, and validation artifacts'],
  ['Evaluator', 'Review extracted evidence, EQAM dimensions, indicator mappings, and expert-validation cases'],
  ['Viewer', 'Read dashboards, reports, XAI explanations, and approved assessment history'],
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
      ['Five EQAM dimensions', 'Semantic relevance, model confidence, completeness, source reliability, and evidence strength are scored.'],
      ['Adjusted Evidence Score', 'AES uses weighted dimensions and an acceptance threshold tau = 0.70.'],
    ],
  },
  {
    title: 'MCDA',
    icon: SlidersHorizontal,
    items: [
      ['Framework-constrained AHP', 'Published framework weights are fixed while operational subcriteria use AHP consistency checks with CR <= 0.10.'],
      ['Fixed-reference TOPSIS', 'Readiness is evaluated against fixed ideal = 1 and anti-ideal = 0 anchors.'],
    ],
  },
  {
    title: 'Scoring & Aggregation',
    icon: Target,
    items: [
      ['RRS', 'Framework-specific Ranking Readiness Scores are computed on a 0-100 scale.'],
      ['ARRS', 'Aggregated Ranking Readiness Score uses equal framework weighting.'],
      ['Best-fit rule', 'The maximum RRS is selected unless close alternatives fall within the 5 percentage-point margin rule.'],
    ],
  },
  {
    title: 'XAI & Decision Support',
    icon: Lightbulb,
    items: [
      ['Traceability', 'Scores link back to source passages, page or section metadata, and accepted evidence status.'],
      ['Gap analysis', 'Criterion readiness and weak evidence dimensions are shown for administrators.'],
      ['Dashboards and reports', 'Dashboard, ranking, XAI, framework, and validation views support planning decisions.'],
    ],
  },
  {
    title: 'Validation, Testing & QA',
    icon: ClipboardCheck,
    items: [
      ['Baselines and ablation', 'Validation plan includes baseline and component-removal comparisons.'],
      ['Agreement statistics', "Fleiss' kappa and ICC are included for expert validation."],
      ['Robustness and ISO quality', 'Sensitivity checks and ISO/IEC 25010 functionality, usability, and security scope are documented.'],
    ],
  },
]


function isUsableBackendEvaluation(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return false

  const requiredFrameworks = FRAMEWORKS.map(({ name }) => name)
  const scores = data.scores
  const metadata = data.metadata

  if (typeof data.school_name !== 'string' || !data.school_name.trim()) return false
  if (typeof data.filename !== 'string' || !data.filename.trim()) return false
  if (typeof data.best_fit !== 'string' || !data.best_fit.trim()) return false
  if (!Number.isFinite(data.arrs) || data.arrs < 0 || data.arrs > 100) return false
  if (!scores || typeof scores !== 'object' || Array.isArray(scores)) return false
  if (!requiredFrameworks.every((name) => Number.isFinite(scores[name]) && scores[name] >= 0 && scores[name] <= 100)) return false
  if (!Array.isArray(data.evidence) || data.evidence.length === 0) return false
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) return false

  const requiredMetadata = ['source', 'sourceType', 'date', 'extractionStatus', 'verificationStatus', 'provenance']
  if (!requiredMetadata.every((key) => typeof metadata[key] === 'string' && metadata[key].trim())) return false
  if (!metadata.provenance.trim()) return false
  if (!Array.isArray(data.strengths) || !data.strengths.every((item) => typeof item === 'string' && item.trim())) return false
  if (!Array.isArray(data.weaknesses) || !data.weaknesses.every((item) => typeof item === 'string' && item.trim())) return false

  return data.evidence.every((item) =>
    item &&
    typeof item === 'object' &&
    typeof item.id === 'string' &&
    item.id.trim().length > 0 &&
    typeof item.passage === 'string' &&
    item.passage.trim().length > 0 &&
    typeof item.framework === 'string' &&
    requiredFrameworks.includes(item.framework) &&
    typeof item.indicator === 'string' &&
    item.indicator.trim().length > 0 &&
    typeof item.source === 'string' &&
    item.source.trim().length > 0 &&
    typeof item.date === 'string' &&
    item.date.trim().length > 0 &&
    Number.isInteger(item.page) &&
    item.page > 0 &&
    typeof item.section === 'string' &&
    item.section.trim().length > 0 &&
    typeof item.split === 'string' &&
    ['training', 'validation', 'test'].includes(item.split) &&
    Number.isFinite(item.aes) &&
    item.aes >= 0 &&
    item.aes <= 1 &&
    typeof item.accepted === 'boolean' &&
    item.dimensions &&
    typeof item.dimensions === 'object' &&
    EQAM_DIMENSIONS.every(([dimension]) =>
      Number.isFinite(item.dimensions[dimension]) &&
      item.dimensions[dimension] >= 0 &&
      item.dimensions[dimension] <= 1
    )
  )
}

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

const StatCard = ({ label, value, icon: Icon }) => (
  <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <div className="mb-4 inline-flex rounded-lg bg-slate-50 p-2 text-slate-700">
      <Icon size={20} />
    </div>
    <div className="text-2xl font-black text-slate-950">{value}</div>
    <div className="mt-1 text-sm font-medium text-slate-500">{label}</div>
  </div>
)

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLoginSubmit = async (event) => {
    event.preventDefault()
    setError('Authentication is not configured. Sign-in is disabled until an approved backend authentication service is connected.')
    onLogin(false)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-xl">
        <div className="mb-8">
          <div className="mb-4 inline-flex rounded-lg bg-slate-900 p-3 text-white">
            <Award size={28} />
          </div>
          <h1 className="text-3xl font-black tracking-normal text-slate-950">Ranking Readiness DSS</h1>
          <p className="mt-2 text-sm text-slate-500">Sign-in is disabled until server-side authentication is configured and security-reviewed.</p>
        </div>
        <div role="alert" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          {error || 'Authentication unavailable. The workspace remains locked.'}
        </div>
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

const Dashboard = ({ evaluation, history }) => {
  if (!evaluation) {
    return (
      <section className="flex min-h-full items-center justify-center p-6">
        <div className="max-w-xl text-center">
          <div className="mx-auto mb-5 inline-flex rounded-lg bg-slate-900 p-4 text-white">
            <CloudUpload size={36} />
          </div>
          <h2 className="text-3xl font-black tracking-normal text-slate-950">No assessment generated yet</h2>
          <p className="mt-3 text-slate-500">Upload an institutional document to run document screening, top-K evidence retrieval, EQAM scoring, and readiness aggregation.</p>
          <Link to="/upload" className="mt-6 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-3 text-sm font-bold text-white hover:bg-slate-800">
            Start Assessment <ChevronRight size={18} />
          </Link>
        </div>
      </section>
    )
  }

  const hasValidatedResult = isUsableBackendEvaluation(evaluation)
  if (!hasValidatedResult) {
    return (
      <section className="space-y-6 p-6 lg:p-8">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <div className="flex items-center gap-2 font-black text-amber-900">
            <AlertTriangle size={20} />
            Assessment result unavailable
          </div>
          <p className="mt-2 text-sm text-amber-900">
            No validated backend assessment is available. Local demonstration values are not used as institutional scores.
            Connect an authorized assessment service and complete the approved validation process before reporting RRS or ARRS.
          </p>
          <Link to="/upload" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white hover:bg-slate-800">
            Return to document upload <ChevronRight size={16} />
          </Link>
        </div>
      </section>
    )
  }

  const chartData = FRAMEWORKS.map((framework) => ({
    framework: framework.name,
    score: Number(evaluation.scores[framework.name]),
    color: framework.color,
  }))

  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-black uppercase text-slate-400">Verified institution</p>
          <h2 className="mt-1 text-3xl font-black tracking-normal text-slate-950">{evaluation.school_name}</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-500">Best-fit framework: <span className="font-bold text-slate-900">{evaluation.best_fit}</span></p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-bold text-amber-800">
          ARRS {evaluation.arrs}/100
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Accepted Evidence Records" value={`${evaluation.evidence.filter((item) => item.accepted).length}/${evaluation.evidence.length}`} icon={FileSearch} />
        <StatCard label="Frameworks Included" value={FRAMEWORKS.length} icon={BarChart3} />
        <StatCard label="Session Assessment Records" value={history.length} icon={History} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-black text-slate-950">Ranking Readiness Scores</h3>
            <span className="text-xs font-bold text-slate-500">Backend-provided framework results</span>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="framework" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => <Cell key={entry.framework} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 text-lg font-black text-slate-950">Document Metadata</h3>
          <dl className="grid grid-cols-1 gap-3 text-sm">
            {[
              ['Source', evaluation.metadata.source],
              ['Document class', evaluation.metadata.sourceType],
              ['Date', evaluation.metadata.date],
              ['Extraction', evaluation.metadata.extractionStatus],
              ['Verification', evaluation.metadata.verificationStatus],
              ['Provenance', evaluation.metadata.provenance],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg bg-slate-50 p-3">
                <dt className="text-xs font-black uppercase text-slate-400">{label}</dt>
                <dd className="mt-1 font-semibold text-slate-800">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}

const DocumentUpload = ({ onEvaluation }) => {
  const [status, setStatus] = useState('')
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0])
  const fileInputRef = useRef(null)

  const handleFileChange = async (event) => {
    const input = event.currentTarget
    const file = input.files?.[0]
    if (!file) return

    setStatus('Uploading document to the configured assessment API...')
    onEvaluation(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)

    try {
      const response = await fetch('/api/upload', { method: 'POST', body: formData })
      if (!response.ok) {
        throw new Error(`Assessment API returned HTTP ${response.status}`)
      }

      const data = await response.json()
      if (!isUsableBackendEvaluation(data)) {
        throw new Error('The API response does not contain the required validated assessment fields.')
      }

      onEvaluation(data)
      setStatus(`Backend assessment received for ${data.school_name}.`)
    } catch (error) {
      onEvaluation(null)
      setStatus(`No assessment was generated: ${error instanceof Error ? error.message : 'Assessment API unavailable'}. No demonstration scores were substituted.`)
    } finally {
      // Allow the same file to be selected again to retry a failed upload.
      input.value = ''
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

const EvidenceView = ({ evaluation }) => {
  const hasValidatedResult = isUsableBackendEvaluation(evaluation)
  return (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Semantic Evidence & EQAM</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Top-K evidence candidates are mapped to ranking indicators and scored across the five EQAM dimensions. Acceptance threshold tau = 0.70.</p>
    </div>
    {!hasValidatedResult ? (
      <EmptyState text="Validated backend evidence is unavailable. No sample or metadata-derived evidence is displayed." />
    ) : (
      <div className="grid grid-cols-1 gap-4">
        {evaluation.evidence.map((item) => (
          <article key={item.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded bg-slate-900 px-2 py-1 text-xs font-black text-white">{item.id}</span>
                  <span className="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">{item.framework}</span>
                  <span className="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">{item.indicator}</span>
                  <span className={`rounded px-2 py-1 text-xs font-bold ${item.accepted ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{item.accepted ? 'Accepted' : 'Review'}</span>
                </div>
                <p className="mt-3 text-sm font-medium leading-6 text-slate-700">{item.passage}</p>
                <p className="mt-3 text-xs font-semibold text-slate-500">{item.source} | {item.date} | page {item.page} | {item.section} | split: {item.split}</p>
              </div>
              <div className="min-w-32 rounded-lg bg-slate-50 p-3 text-center">
                <div className="text-xs font-black uppercase text-slate-400">AES</div>
                <div className="text-2xl font-black text-slate-950">{item.aes}</div>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-5">
              {EQAM_DIMENSIONS.map(([dimension, weight]) => (
                <div key={dimension} className="rounded-lg bg-slate-50 p-3">
                  <div className="text-xs font-black text-slate-500">{dimension}</div>
                  <div className="mt-1 text-lg font-black text-slate-950">{item.dimensions[dimension]}</div>
                  <div className="text-xs font-semibold text-slate-400">weight {weight}</div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    )}
  </section>
  )
}

const FrameworkAnalysis = ({ evaluation }) => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Framework-Constrained AHP & TOPSIS</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Official framework weights remain fixed. Operational indicators are checked by AHP consistency and readiness is computed against fixed ideal and anti-ideal references.</p>
    </div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      {FRAMEWORKS.map((framework) => (
        <div key={framework.name} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-black text-slate-950">{framework.name}</h3>
              <p className="mt-1 text-sm text-slate-500">{framework.focus}</p>
            </div>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-black text-slate-700">fixed {Math.round(framework.officialWeight * 100)}%</span>
          </div>
          <div className="space-y-3">
            {framework.indicators.map(([indicator, weight]) => (
              <div key={indicator}>
                <div className="mb-1 flex justify-between text-sm font-bold text-slate-700">
                  <span>{indicator}</span>
                  <span>{Math.round(weight * 100)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-slate-100">
                  <div className="h-full rounded" style={{ width: `${weight * 100}%`, backgroundColor: framework.color }} />
                </div>
              </div>
            ))}
          </div>
          {evaluation?.sub_scores?.[framework.name] && (
            <div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs font-semibold text-slate-600">
              Current sub-indicator points: {Object.entries(evaluation.sub_scores[framework.name]).map(([name, points]) => `${name} ${points}`).join(', ')}
            </div>
          )}
        </div>
      ))}
    </div>
  </section>
)

const ExplainableAI = ({ evaluation }) => {
  const hasValidatedResult = isUsableBackendEvaluation(evaluation)
  return (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Explainable AI & Decision Support</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Administrators can inspect score drivers, trace evidence, and identify readiness gaps by framework and criterion.</p>
    </div>
    {!hasValidatedResult ? (
      <EmptyState text="Validated backend explanations are unavailable. No generated sample findings are displayed." />
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
}

const ChecklistView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Checklist Compliance</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Each required feature is represented in the prototype as a visible workflow, algorithm panel, metadata field, or validation control.</p>
    </div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      {checklistGroups.map(({ title, icon: Icon, items }) => (
        <div key={title} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><Icon size={20} /> {title}</h3>
          <div className="space-y-3">
            {items.map(([name, description]) => (
              <div key={name} className="flex gap-3 rounded-lg bg-slate-50 p-3">
                <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={18} />
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
      <h2 className="text-3xl font-black tracking-normal text-slate-950">System Architecture & Traceability</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Structure follows the dissertation modules from document intake through dashboard reporting, with each module tied to a verifiable output.</p>
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
          <div className="rounded-lg bg-slate-50 p-3">Requirements traceability matrix and module verification log</div>
          <div className="rounded-lg bg-slate-50 p-3">Evidence table with source, date, page, section, framework, indicator, AES, and acceptance status</div>
          <div className="rounded-lg bg-slate-50 p-3">RRS, ARRS, Best-Fit recommendation, close-alternative notes, and criterion-level gaps</div>
          <div className="rounded-lg bg-slate-50 p-3">Validation summary for baseline, ablation, sensitivity, expert agreement, and ISO/IEC 25010</div>
        </div>
      </div>
    </div>
  </section>
)

const ValidationView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Validation, Testing & QA</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">Validation coverage follows baseline comparison, ablation, expert agreement, robustness, and ISO/IEC 25010 quality characteristics.</p>
    </div>
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-black uppercase text-slate-500">
            <tr>
              <th className="p-4">Validation Item</th>
              <th className="p-4">Checklist Implementation</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {VALIDATION_ROWS.map(([item, implementation]) => (
              <tr key={item}>
                <td className="p-4 font-black text-slate-900">{item}</td>
                <td className="p-4 text-slate-600">{implementation}</td>
                <td className="p-4"><span className="rounded bg-emerald-50 px-2 py-1 text-xs font-black text-emerald-700">Defined</span></td>
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

const HistoryView = ({ history }) => {
  const sorted = useMemo(() => [...history].sort((a, b) => b.arrs - a.arrs), [history])
  return (
    <section className="space-y-6 p-6 lg:p-8">
      <div>
        <h2 className="text-3xl font-black tracking-normal text-slate-950">Assessment Session History</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">This session-only list contains validated backend responses received during the current browser session. It is not an official university ranking.</p>
      </div>
      {sorted.length === 0 ? <EmptyState text="No assessment history yet." /> : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] text-left">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-black uppercase text-slate-500">
                <tr>
                  <th className="p-4">Rank</th>
                  <th className="p-4">Institution</th>
                  <th className="p-4">Document Source</th>
                  <th className="p-4">Best-Fit Framework</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4 text-right">ARRS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {sorted.map((item, index) => (
                  <tr key={`${item.filename}-${item.timestamp}`}>
                    <td className="p-4 font-black text-slate-950">#{index + 1}</td>
                    <td className="p-4 font-bold text-slate-800">{item.schoolName}</td>
                    <td className="p-4 text-slate-500">{item.filename}</td>
                    <td className="p-4 text-slate-600">{item.bestFit}</td>
                    <td className="p-4 text-slate-500">{item.timestamp}</td>
                    <td className="p-4 text-right font-black text-slate-950">{item.arrs}</td>
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
  const [evaluation, setEvaluation] = useState(null)
  const [history, setHistory] = useState([])

  const handleEvaluation = (nextEvaluation) => {
    setEvaluation(nextEvaluation)
    if (!isUsableBackendEvaluation(nextEvaluation)) return

    setHistory((previous) => [
      {
        filename: nextEvaluation.filename,
        schoolName: nextEvaluation.school_name,
        timestamp: new Date().toLocaleString(),
        bestFit: nextEvaluation.best_fit,
        arrs: Number(nextEvaluation.arrs),
      },
      ...previous,
    ])
  }

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={setIsAuthenticated} />} />
      <Route path="/*" element={isAuthenticated ? (
        <Shell onLogout={() => setIsAuthenticated(false)}>
          <Routes>
            <Route path="/" element={<Dashboard evaluation={evaluation} history={history} />} />
            <Route path="/upload" element={<DocumentUpload onEvaluation={handleEvaluation} />} />
            <Route path="/evidence" element={<EvidenceView evaluation={evaluation} />} />
            <Route path="/analysis" element={<FrameworkAnalysis evaluation={evaluation} />} />
            <Route path="/xai" element={<ExplainableAI evaluation={evaluation} />} />
            <Route path="/history" element={<HistoryView history={history} />} />
            <Route path="/architecture" element={<ArchitectureView />} />
            <Route path="/checklist" element={<ChecklistView />} />
            <Route path="/validation" element={<ValidationView />} />
          </Routes>
        </Shell>
      ) : <Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
