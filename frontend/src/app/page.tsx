"use client";

import { useState } from "react";

export function getSeverityColor(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-950/60 text-red-400 border border-red-800/60";
    case "HIGH":
      return "bg-orange-950/60 text-orange-400 border border-orange-800/60";
    case "MEDIUM":
      return "bg-yellow-950/60 text-yellow-400 border border-yellow-800/60";
    case "LOW":
      return "bg-blue-950/60 text-blue-400 border border-blue-800/60";
    default:
      return "bg-gray-800 text-gray-300 border border-gray-700";
  }
}

export default function Dashboard() {
  // Input Modes
  const [scanMode, setScanMode] = useState<"snippet" | "github" | "zip">("snippet");
  const [code, setCode] = useState("import os\n\ndef ping(ip):\n    os.system('ping ' + ip)");
  const [githubUrl, setGithubUrl] = useState("");
  const [zipFile, setZipFile] = useState<File | null>(null);

  // System State
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Remediation State
  const [fixingId, setFixingId] = useState<number | null>(null);
  const [fixResult, setFixResult] = useState<any | null>(null);

  // Explanation State
  const [explainingId, setExplainingId] = useState<number | null>(null);
  const [explanations, setExplanations] = useState<Record<number, string>>({});

  const runScan = async () => {
    setLoading(true);
    setErrorMessage(null);
    setFixResult(null);
    setFindings([]);
    setExplanations({}); // Clear explanations on new scan

    try {
      let response;

      if (scanMode === "snippet") {
        response = await fetch("http://127.0.0.1:8000/api/v1/scan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code: code, file_name: "app.py" }),
        });
      } else if (scanMode === "github") {
        if (!githubUrl) throw new Error("Please enter a valid GitHub URL.");
        response = await fetch("http://127.0.0.1:8000/api/v1/scan/github", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repo_url: githubUrl }),
        });
      } else if (scanMode === "zip") {
        if (!zipFile) throw new Error("Please select a ZIP file first.");
        const formData = new FormData();
        formData.append("file", zipFile);
        
        response = await fetch("http://127.0.0.1:8000/api/v1/scan/zip", {
          method: "POST",
          body: formData,
        });
      }

      if (!response || !response.ok) {
        const errData = await response?.json().catch(() => ({}));
        throw new Error(errData?.detail || "Server error during scan");
      }
      
      const data = await response.json();
      setFindings(data.findings || []);
    } catch (error: any) {
      setErrorMessage(error.message || "Failed to reach backend.");
    } finally {
      setLoading(false);
    }
  };

  const getExplanation = async (findingId: number) => {
    // Toggle off if already loaded
    if (explanations[findingId]) {
      const updated = { ...explanations };
      delete updated[findingId];
      setExplanations(updated);
      return;
    }

    setExplainingId(findingId);
    setErrorMessage(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/findings/${findingId}/explain`, {
        method: "POST", // Matches the backend method
      });
      if (!response.ok) throw new Error("Failed to generate AI explanation");
      
      const data = await response.json();
      setExplanations((prev) => ({ ...prev, [findingId]: data.explanation }));
    } catch (error: any) {
      setErrorMessage("AI Explanation failed. Is Ollama running?");
    } finally {
      setExplainingId(null);
    }
  };

  const generateFix = async (findingId: number) => {
    setFixingId(findingId);
    setErrorMessage(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/findings/${findingId}/fix`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to generate AI fix");
      
      const data = await response.json();
      setFixResult(data);
    } catch (error: any) {
      setErrorMessage("AI Fix generation failed. Is Ollama running?");
    } finally {
      setFixingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="border-b border-gray-800 pb-4">
          <h1 className="text-3xl font-bold text-blue-400">PyShield AI Dashboard</h1>
          <p className="text-gray-400">Security Scanner & Remediation Platform</p>
        </header>

        {errorMessage && (
          <div className="p-4 bg-red-950/70 border border-red-800 text-red-300 rounded-lg text-sm">
            <strong>Error:</strong> {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column: Target Input Configuration */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Target Configuration</h2>
            
            <div className="flex space-x-1 bg-gray-900 p-1 rounded-lg w-fit border border-gray-800">
              <button 
                onClick={() => setScanMode("snippet")} 
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${scanMode === "snippet" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"}`}
              >
                Raw Snippet
              </button>
              <button 
                onClick={() => setScanMode("github")} 
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${scanMode === "github" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"}`}
              >
                GitHub Repo
              </button>
              <button 
                onClick={() => setScanMode("zip")} 
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${scanMode === "zip" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"}`}
              >
                ZIP Upload
              </button>
            </div>

            <div className="h-96">
              {scanMode === "snippet" && (
                <textarea
                  className="w-full h-full bg-gray-900 border border-gray-700 rounded-lg p-4 font-mono text-sm focus:outline-none focus:border-blue-500"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  spellCheck="false"
                />
              )}

              {scanMode === "github" && (
                <div className="w-full h-full bg-gray-900 border border-gray-700 rounded-lg p-6 flex flex-col justify-center space-y-4 text-center">
                  <div className="text-gray-400 text-sm">Enter a public GitHub repository URL to scan.</div>
                  <input 
                    type="url" 
                    placeholder="https://github.com/user/repo"
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-4 text-sm focus:outline-none focus:border-blue-500"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                  />
                </div>
              )}

              {scanMode === "zip" && (
                <div className="w-full h-full bg-gray-900 border border-gray-700 rounded-lg p-6 flex flex-col justify-center items-center space-y-4 text-center border-dashed">
                  <div className="text-gray-400 text-sm">Upload a ZIP archive containing Python files.</div>
                  <input 
                    type="file" 
                    accept=".zip"
                    onChange={(e) => setZipFile(e.target.files ? e.target.files[0] : null)}
                    className="block w-full text-sm text-gray-400
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-md file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-900/50 file:text-blue-300
                      hover:file:bg-blue-900/80 cursor-pointer"
                  />
                </div>
              )}
            </div>

            <button
              onClick={runScan}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg disabled:opacity-50 transition-colors"
            >
              {loading ? "Scanning Target..." : "Run Security Scan"}
            </button>
          </div>

          {/* Right Column: Findings Viewer */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Findings ({findings.length})</h2>
            <div className="space-y-4 h-96 overflow-y-auto pr-2">
              {findings.length === 0 && !loading && scanMode !== "snippet" && (
                <div className="text-gray-500 italic mt-10 text-center border border-dashed border-gray-700 p-8 rounded-lg">
                  No Python vulnerabilities found in this target.
                </div>
              )}
              {findings.map((finding, idx) => (
                <div key={idx} className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-lg flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-mono text-sm text-blue-300">{finding.rule_id}</span>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded ${getSeverityColor(finding.severity)}`}>
                        {finding.severity}
                      </span>
                    </div>
                    <p className="text-sm font-medium mb-2">{finding.message}</p>
                    <div className="text-xs text-gray-500 font-mono mb-4">
                      File: {finding.file} | Line: {finding.line}
                    </div>

                    {/* AI Explanation Box */}
                    {explanations[idx + 1] && (
                      <div className="mt-3 mb-4 p-3 bg-gray-950 border border-blue-900/40 rounded text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                        <strong className="text-blue-400 block mb-1 text-xs uppercase tracking-wide">AI Analysis:</strong>
                        {explanations[idx + 1]}
                      </div>
                    )}
                  </div>
                  
                  {/* Dual Buttons */}
                  <div className="flex gap-3 mt-2">
                    <button
                      onClick={() => getExplanation(idx + 1)}
                      disabled={explainingId === idx + 1}
                      className="flex-1 py-2 px-4 border border-blue-500/30 text-blue-400 rounded hover:bg-blue-900/20 text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                      {explainingId === idx + 1 ? "🧠 Analyzing..." : explanations[idx + 1] ? "Hide Analysis" : "📖 Explain"}
                    </button>
                    <button
                      onClick={() => generateFix(idx + 1)} 
                      disabled={fixingId === idx + 1}
                      className="flex-1 py-2 px-4 border border-purple-500/30 text-purple-400 rounded hover:bg-purple-900/20 text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                      {fixingId === idx + 1 ? "🧠 Generating Fix..." : "✨ Fix with AI"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Diff Viewer */}
        {fixResult && (
          <div className="mt-8 border border-gray-800 rounded-lg bg-gray-900 overflow-hidden shadow-2xl">
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex justify-between items-center">
              <h3 className="font-semibold text-gray-200">AI Remediation Diff</h3>
              <span className="text-xs font-mono text-gray-400 bg-gray-900 px-2 py-1 rounded">
                Status: {fixResult.status}
              </span>
            </div>
            <pre className="p-4 overflow-x-auto font-mono text-sm leading-relaxed text-gray-300">
              <code>
                {fixResult.diff.split('\n').map((line: string, i: number) => {
                  if (line.startsWith('+') && !line.startsWith('+++')) return <div key={i} className="text-green-400 bg-green-950/30 px-2">{line}</div>;
                  if (line.startsWith('-') && !line.startsWith('---')) return <div key={i} className="text-red-400 bg-red-950/30 px-2">{line}</div>;
                  return <div key={i} className="px-2">{line}</div>;
                })}
              </code>
            </pre>
          </div>
        )}

      </div>
    </div>
  );
}