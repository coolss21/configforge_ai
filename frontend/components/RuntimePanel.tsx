import React from "react";

export default function RuntimePanel({ report }: { report: any }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold mb-2 text-slate-800 flex items-center justify-between">
        Runtime Simulation
        <span className={`px-2 py-1 text-xs rounded-full ${report.executable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {report.executable ? "EXECUTABLE" : "FAILED"}
        </span>
      </h3>

      <div className="mt-4 text-sm text-slate-600">
        <p className="flex justify-between border-b border-slate-100 py-1">
          <span>DB Created:</span>
          <span className="font-medium">{report.database_created ? "Yes" : "No"}</span>
        </p>
        <p className="flex justify-between border-b border-slate-100 py-1">
          <span>Tables:</span>
          <span className="font-medium">{report.tables_created.length}</span>
        </p>
        <p className="flex justify-between border-b border-slate-100 py-1">
          <span>API Routes:</span>
          <span className="font-medium">{report.api_routes_registered.length}</span>
        </p>
      </div>

      {report.simulation_results && report.simulation_results.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Simulation</p>
          <ul className="text-xs space-y-2">
            {report.simulation_results.map((sim: any, idx: number) => (
              <li key={idx} className="bg-slate-50 p-2 rounded">
                <span className="font-medium">{sim.operation}</span>: {sim.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.errors && report.errors.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-red-500 uppercase tracking-wider mb-2">Errors</p>
          <ul className="text-xs text-red-600 space-y-1 list-disc pl-4">
            {report.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
