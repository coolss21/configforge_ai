import React from "react";

export default function AssumptionsPanel({ assumptions, warnings }: { assumptions: string[], warnings: string[] }) {
  if ((!assumptions || assumptions.length === 0) && (!warnings || warnings.length === 0)) return null;
  
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold mb-4 text-slate-800">Assumptions & Warnings</h3>
      
      {warnings && warnings.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-semibold text-orange-600 mb-2">Warnings</p>
          <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
            {warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {assumptions && assumptions.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-blue-600 mb-2">Assumptions</p>
          <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
            {assumptions.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
