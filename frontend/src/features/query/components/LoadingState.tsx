export function LoadingState() {
  return (
    <div className="w-full rounded-xl border border-slate-700 bg-slate-800/40 p-6">
      <div className="space-y-3">
        <div className="flex items-center gap-3 text-slate-400">
          <svg className="h-5 w-5 animate-spin text-indigo-400" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm">Analizando tu consulta...</span>
        </div>

        {/* Skeleton lines */}
        <div className="space-y-2 pl-8">
          <div className="h-3 w-3/4 animate-pulse rounded bg-slate-700" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-slate-700" />
        </div>
      </div>
    </div>
  )
}
