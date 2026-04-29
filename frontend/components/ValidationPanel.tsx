import React from "react";

export default function ValidationPanel({ report, repair }: { report: any, repair: any }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold mb-2 text-slate-800 flex items-center justify-between">
        Validation & Repair
        <span className={`px-2 py-1 text-xs rounded-full ${report.is_valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {report.is_valid ? "VALID" : "INVALID"}
        </span>
      </h3>
      
      <div className="mt-4 text-sm text-slate-600">
        <p className="flex justify-between border-b border-slate-100 py-1">
          <span>Repair Rounds:</span>
          <span className="font-medium">{repair.repair_rounds}</span>
        </p>
        <p className="flex justify-between border-b border-slate-100 py-1">
          <span>Repaired Layers:</span>
          <span className="font-medium">{repair.repaired_layers.join(", ") || "None"}</span>
        </p>
      </div>

      {repair.repair_log && repair.repair_log.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Repair Log</p>
          <ul className="text-xs space-y-2">
            {repair.repair_log.map((log: any, idx: number) => (
              <li key={idx} className="bg-slate-50 p-2 rounded">
                <span className="font-medium">R{log.round} [{log.layer}]</span>: {log.success ? "Fixed" : "Failed"} errors ({log.error_codes.join(", ")})
              </li>
            ))}
          </ul>
        </div>
      )}

      {!report.is_valid && report.errors && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-red-500 uppercase tracking-wider mb-2">Unresolved Errors</p>
          <ul className="text-xs text-red-600 space-y-1 list-disc pl-4">
            {report.errors.map((e: any, i: number) => <li key={i}>{e.layer}: {e.message}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
