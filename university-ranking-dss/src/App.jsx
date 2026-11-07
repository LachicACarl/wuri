import { AlertTriangle, Award, ShieldCheck } from 'lucide-react'
import { Route, Routes } from 'react-router-dom'

function App() {
  return (
    <Routes>
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
              <div role="alert" className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
                <div className="font-bold text-amber-950">Do not submit institutional documents or credentials</div>
                <p className="mt-2 text-sm leading-6 text-amber-900">
                  Secure document intake, authentication, private storage, extraction,
                  evidence provenance and scoring are not implemented. Do not upload
                  institutional files or enter account credentials.
                </p>
              </div>
              <p className="mt-5 text-xs leading-5 text-slate-500">
                No demonstration scores, sample evidence, or unverified ranking results
                are presented as research findings.
              </p>
            </section>
          </main>
        }
      />
    </Routes>
  )
}

export default App
