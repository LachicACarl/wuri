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
  LogOut,
  Menu,
  Network,
  Microscope,
  SlidersHorizontal,
  ShieldCheck,
  TableProperties,
  Target,
  Trophy,
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
  // These are proposed project requirements, not completed feature claims.
  {
    title: 'Document Integration & Management',
    icon: Database,
    items: [
      ['Institutional collection', 'Strategic plans, reports, publications, faculty profiles, sustainability, extension, and policies are represented as document classes.'],
      ['Screening and metadata', 'Planned workflow fields include source, date, type, file size, page/section, extraction status, and verification status. Upload tracking is not implemented.'],
      ['Secure knowledge base', 'Administrator, evaluator, and viewer roles are proposed. Server-side role enforcement and a secure knowledge base are not implemented.'],
    ],
  },
  {
    title: 'Semantic Evidence Extraction & Matching',
    icon: Brain,
    items: [
      ['Enhanced Sentence-BERT', 'Domain-adapted SBERT is a proposed model component. No embedding model or inference pipeline is included in this frontend.'],
      ['Framework mapping', 'Mapping evidence to WURI, THE, QS, and UI GreenMetric indicators is a planned capability; no mapping engine is implemented.'],
      ['Top-K retrieval', 'Top-K retrieval and dataset split tracking are planned capabilities; no retrieval pipeline is implemented.'],
    ],
  },
  {
    title: 'Evidence Quality Assessment Mechanism',
    icon: ShieldCheck,
    items: [
      ['Five EQAM dimensions', 'The proposed dimensions are semantic relevance, model confidence, completeness, source reliability, and evidence strength. No EQAM calculation is implemented.'],
      ['Adjusted Evidence Score', 'AES weighting and the proposed tau = 0.70 threshold require research-methodology approval; no AES calculation is implemented.'],
    ],
  },
  {
    title: 'MCDA',
    icon: SlidersHorizontal,
    items: [
      ['Framework-constrained AHP', 'AHP consistency checks and framework-constrained weighting are proposed only; no AHP implementation or verified official-weight source is included.'],
      ['Fixed-reference TOPSIS', 'Fixed-reference TOPSIS is a proposed method; ideal/anti-ideal anchors and calculation code require approval and implementation.'],
    ],
  },
  {
    title: 'Scoring & Aggregation',
    icon: Target,
    items: [
      ['RRS', 'Framework-specific Ranking Readiness Scores are intended outputs; no RRS calculation is implemented.'],
      ['ARRS', 'Equal framework aggregation is an unapproved proposal; no ARRS calculation is implemented.'],
      ['Best-fit rule', 'A maximum-score/5-point close-alternative rule is a proposed decision rule; it requires methodology approval and implementation.'],
    ],
  },
  {
    title: 'XAI & Decision Support',
    icon: Lightbulb,
    items: [
      ['Traceability', 'The design requires scores to link to source passages and metadata; no persisted provenance chain is implemented.'],
      ['Gap analysis', 'Criterion readiness and evidence-gap analysis are planned; no analysis engine is implemented.'],
      ['Dashboards and reports', 'Dashboard, ranking, XAI, framework, and validation reporting are planned views; they are not connected to a working assessment service.'],
    ],
  },
  {
    title: 'Validation, Testing & QA',
    icon: ClipboardCheck,
    items: [
      ['Baselines and ablation', 'Baseline and ablation comparisons are proposed evaluation activities; no experiments or results are implemented.'],
      ['Agreement statistics', "Fleiss' kappa and ICC are proposed expert-validation measures; no validation data or computed statistics are present."],
      ['Robustness and ISO quality', 'Sensitivity and ISO/IEC 25010 evaluation are planned; no test results or quality assessment are implemented.'],
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

const Login = () => (
  <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
    <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-xl">
      <div className="mb-6">
        <div className="mb-4 inline-flex rounded-lg bg-slate-900 p-3 text-white">
          <Award size={28} />
        </div>
        <h1 className="text-3xl font-black tracking-normal text-slate-950">Ranking Readiness DSS</h1>
        <p className="mt-2 text-sm text-slate-500">Workspace access is temporarily unavailable.</p>
      </div>
      <div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <div className="font-bold">Authentication service not configured</div>
        <p className="mt-2">Sign-in is disabled until server-side authentication, role permissions, and security review are complete. Do not enter account credentials on this page.</p>
      </div>
    </div>
  </div>
)

const Dashboard = () => (
  <section className="flex min-h-full items-center justify-center p-6">
    <div className="max-w-xl text-center">
      <div className="mx-auto mb-5 inline-flex rounded-lg bg-amber-100 p-4 text-amber-900">
        <AlertTriangle size={36} />
      </div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Assessment service not available</h2>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        No assessment backend or scoring engine is connected. The dashboard will not
        display placeholder scores, institution rankings, or generated evidence.
      </p>
    </div>
  </section>
)

const DocumentUpload = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Document Upload — Unavailable</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-600">
        Secure document intake is not implemented. No file will be selected, uploaded,
        transmitted, or stored by this page.
      </p>
    </div>
    <div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
      <div className="font-black">Do not submit institutional documents</div>
      <p className="mt-2">
        The backend upload endpoint, authentication, private storage policies, malware
        screening, and evidence-provenance pipeline have not been independently reviewed
        or authorized. File transfer is disabled until those controls are implemented
        and tested in an approved isolated environment.
      </p>
    </div>
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-bold text-slate-900">Planned supported document classes</h3>
      <ul className="mt-3 grid grid-cols-1 gap-2 text-sm text-slate-600 sm:grid-cols-2">
        {DOCUMENT_TYPES.map((type) => (
          <li key={type} className="rounded-md bg-slate-50 px-3 py-2">{type}</li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-slate-500">
        The list describes future scope only. It does not mean these file types can
        currently be uploaded or processed.
      </p>
    </div>
  </section>
)

const EvidenceView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Evidence & EQAM — Not Available</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-600">
        Document extraction, semantic retrieval, evidence verification, and EQAM
        calculation are not implemented or connected.
      </p>
    </div>
    <div role="status" className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
      No source passages, page references, confidence values, AES values, or accepted
      evidence records are available. This page will remain empty until the approved
      extraction and provenance pipeline is implemented.
    </div>
  </section>
)

const FrameworkAnalysis = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Framework Configuration — Proposed</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-600">
        The values below are currently hardcoded research configuration placeholders.
        They are not verified official ranking weights, do not calculate readiness,
        and must not be used for institutional decisions or research reporting.
      </p>
    </div>
    <div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
      <div className="font-black">Not an implemented scoring engine</div>
      <p className="mt-2">
        AHP, TOPSIS, EQAM, AES, RRS and ARRS calculations are not implemented in
        this frontend. The final criteria, weights, thresholds and formulas require
        approval against the research methodology and authoritative framework sources.
      </p>
    </div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      {FRAMEWORKS.map((framework) => (
        <div key={framework.name} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-black text-slate-950">{framework.name}</h3>
              <p className="mt-1 text-sm text-slate-500">{framework.focus}</p>
            </div>
            <span className="rounded-lg bg-amber-50 px-3 py-1 text-xs font-black text-amber-900">Proposed 25%</span>
          </div>
          <div className="space-y-3">
            {framework.indicators.map(([indicator, weight]) => (
              <div key={indicator}>
                <div className="mb-1 flex justify-between text-sm font-bold text-slate-700">
                  <span>{indicator}</span>
                  <span>{Math.round(weight * 100)}% · proposed</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-slate-100">
                  <div className="h-full rounded" style={{ width: `${weight * 100}%`, backgroundColor: framework.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </section>
)

const ExplainableAI = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Explainable AI — Not Available</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-600">
        No assessment result or explanation service is currently connected.
      </p>
    </div>
    <div role="status" className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
      Strengths, weaknesses, score contributions, and recommendations will not be
      fabricated. This view requires a validated assessment run and traceable evidence.
    </div>
  </section>
)

const ChecklistView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Proposed Requirements Checklist</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">This is a design checklist, not evidence of completed implementation. Items below describe intended capabilities and still require engineering, security review, and testing.</p>
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
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Proposed System Architecture</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">The modules below describe the target design. They are not deployed services or verified data flows in the current frontend-only repository.</p>
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
        <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><KeyRound size={20} /> Proposed Role Model — Not Enforced</h3>
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
        <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-slate-950"><TableProperties size={20} /> Planned Report Artifacts</h3>
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
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Proposed Validation Plan — Not Executed</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-500">The table lists planned evaluation activities. No baseline, ablation, expert-agreement, robustness, or ISO/IEC 25010 tests have been run in this recovery snapshot.</p>
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
                <td className="p-4"><span className="rounded bg-amber-50 px-2 py-1 text-xs font-black text-amber-800">Planned</span></td>
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

const HistoryView = () => (
  <section className="space-y-6 p-6 lg:p-8">
    <div>
      <h2 className="text-3xl font-black tracking-normal text-slate-950">Assessment History — Not Available</h2>
      <p className="mt-2 max-w-3xl text-sm text-slate-600">
        Persistent assessment history is not implemented because there is no approved
        backend or database integration.
      </p>
    </div>
    <div role="status" className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600">
      No assessment records are stored or displayed. This page will be enabled only
      after authenticated, institution-scoped persistence and audit logging are verified.
    </div>
  </section>
)

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
  const unavailableFeatures = [
    'Authentication and role-based access',
    'Document upload and extraction',
    'Assessment scoring and ranking',
    'Evidence review and explainable results',
    'Persistent assessment history',
  ]

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="*"
        element={
          <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
            <section className="w-full max-w-2xl rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="mb-5 inline-flex rounded-lg bg-amber-100 p-3 text-amber-900">
                <ShieldCheck size={28} />
              </div>
              <p className="text-xs font-black uppercase tracking-wider text-amber-700">
                Recovery workspace · Security hold
              </p>
              <h1 className="mt-2 text-3xl font-black text-slate-950">
                WURI Ranking Readiness DSS
              </h1>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                This workspace is currently unavailable. The backend, authentication
                service, database integration, and assessment pipeline have not yet
                completed independent review and authorized testing.
              </p>
              <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h2 className="font-bold text-amber-950">Features not yet available</h2>
                <ul className="mt-3 space-y-2 text-sm text-amber-900">
                  {unavailableFeatures.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <p className="mt-5 text-xs leading-5 text-slate-500">
                Do not upload institutional documents or enter account credentials.
                No demonstration scores or sample evidence are presented as research
                results.
              </p>
            </section>
          </main>
        }
      />
    </Routes>
  )
}

export default App
