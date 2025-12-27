"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [warning, setWarning] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSummary("");
    setWarning("");
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          err?.detail || "Something went wrong. Try another video."
        );
      }

      const data = await res.json();
      setSummary(data.summary);
      setWarning(data.warning || "");
    } catch (err: any) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col">
      {/* Navbar */}
      <header className="w-full border-b border-white/10">
        <nav className="max-w-5xl mx-auto py-4 px-4 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            YT Summarizer<span className="text-indigo-400">.</span>
          </h1>

          <button
            className="text-sm px-3 py-1 rounded bg-white/10 hover:bg-white/20 transition"
            onClick={() =>
              window.open("https://github.com", "_blank")
            }
          >
            GitHub
          </button>
        </nav>
      </header>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="max-w-2xl text-center space-y-4">
          <h2 className="text-4xl font-bold tracking-tight">
            Turn any YouTube video into a summary — instantly
          </h2>

          <p className="text-gray-300">
            Paste a YouTube link and get clean, concise bullet-points powered by AI.
          </p>

          {/* Card */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mt-6 shadow-xl backdrop-blur">
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full p-3 rounded-lg bg-black/30 border border-white/10 focus:outline-none focus:border-indigo-400"
                required
              />

              <button
                disabled={loading}
                className="w-full p-3 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 transition font-medium"
              >
                {loading ? "Summarizing..." : "Summarize Video"}
              </button>
            </form>

            {error && (
              <div className="mt-4 p-3 text-sm text-red-300 bg-red-950/40 border border-red-900 rounded-lg">
                {error}
              </div>
            )}

            {warning && (
              <div className="mt-4 p-3 text-sm text-yellow-300 bg-yellow-950/40 border border-yellow-900 rounded-lg">
                {warning}
              </div>
            )}

            {summary && (
              <div className="mt-6 p-4 bg-black/40 border border-white/10 rounded-lg text-sm whitespace-pre-wrap text-gray-100 text-left">
                {summary}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-4 text-center text-xs text-gray-400">
        Built with ❤️ — YouTube Summarizer • 2025
      </footer>
    </main>
  );
}
