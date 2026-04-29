import React, { useState } from "react";

export default function JsonOutputViewer({ data }: { data: any }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "configforge_output.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="bg-[#1e1e1e] rounded-xl shadow-sm border border-slate-800 overflow-hidden flex flex-col h-[600px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-[#252526]">
        <h3 className="text-sm font-medium text-slate-300">Final Validated Configuration</h3>
        <div className="flex space-x-2">
          <button 
            onClick={handleCopy}
            className="text-xs px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded transition-colors"
          >
            {copied ? "Copied!" : "Copy JSON"}
          </button>
          <button 
            onClick={handleDownload}
            className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
          >
            Download JSON
          </button>
        </div>
      </div>
      <div className="p-4 overflow-auto flex-1 custom-scrollbar">
        <pre className="text-xs text-[#d4d4d4] font-mono leading-relaxed">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
