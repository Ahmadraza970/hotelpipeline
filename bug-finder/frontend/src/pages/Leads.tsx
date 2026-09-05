import { useEffect, useState } from "react";

type Lead = {
  id: string; hotel_name: string; city: string; contact_name?: string; email?: string; phone?: string; website?: string; audit_notes?: string; outreach_status: string; follow_up_date?: string; date_added?: string;
};

export function Leads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [city, setCity] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8765/leads.json").then(async r => {
      if (!r.ok) throw new Error("leads.json not found — is localhost:8765 running?");
      return r.json();
    }).then(setLeads).catch(e => setErr(e.message));
  }, []);

  const filtered = leads.filter(l => {
    if (status && l.outreach_status !== status) return false;
    if (city && !l.city.includes(city)) return false;
    if (q) {
      const hay = `${l.hotel_name} ${l.city} ${l.phone||""} ${l.email||""}`.toLowerCase();
      if (!hay.includes(q.toLowerCase())) return false;
    }
    return true;
  });

  const identified = leads.filter(l => l.outreach_status === "identified").length;
  const emailed = leads.filter(l => l.outreach_status === "emailed").length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="text-2xl font-bold text-white">Goa Hotel Leads — CRM <span className="text-sm font-normal text-slate-400">({leads.length} total, {identified} identified, {emailed} emailed)</span></h1>
      <p className="mt-1 text-xs text-slate-500">Scraping API: <code>http://localhost:8765/leads.json</code> · CSV: <code>/goa_leads_GOA_ONLY.csv</code> · Cron daily 9am · Staggered Sep 2/3/4</p>

      {err && <p className="mt-3 rounded bg-rose-900/30 p-2 text-sm text-rose-300">{err} — run <code>python -m http.server 8765 --directory goa_leads_site</code> from C:\Users\AHMAD RAJA\Desktop\hermes</p>}

      <div className="mt-4 flex flex-wrap gap-2">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search hotel / city / phone" className="flex-1 min-w-[180px] rounded bg-panel-2 border border-panel-2 px-3 py-1.5 text-sm text-white" />
        <select value={status} onChange={e=>setStatus(e.target.value)} className="rounded bg-panel-2 border border-panel-2 px-2 py-1.5 text-sm text-white">
          <option value="">All status</option><option value="identified">identified</option><option value="emailed">emailed</option>
        </select>
        <select value={city} onChange={e=>setCity(e.target.value)} className="rounded bg-panel-2 border border-panel-2 px-2 py-1.5 text-sm text-white">
          <option value="">All Goa (+ demo)</option><option value="Goa">Goa only</option><option value="Anjuna">Anjuna</option><option value="Calangute">Calangute</option><option value="Palolem">Palolem</option><option value="Arambol">Arambol</option><option value="Agonda">Agonda</option><option value="Panjim">Panjim</option>
        </select>
        <a href="http://localhost:8765/goa_leads_GOA_ONLY.csv" className="rounded bg-brand px-3 py-1.5 text-sm font-semibold text-white">Download GOA CSV</a>
        <a href="http://localhost:8765/" target="_blank" className="rounded bg-panel-2 px-3 py-1.5 text-sm text-slate-200">Open standalone site</a>
      </div>

      <div className="mt-3 overflow-auto rounded border border-panel">
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-xs text-slate-400">
            <tr><th className="px-2 py-2">#</th><th className="px-2 py-2">Hotel</th><th className="px-2 py-2">City</th><th className="px-2 py-2">Status</th><th className="px-2 py-2">Follow-up</th><th className="px-2 py-2">Phone</th><th className="px-2 py-2">Email</th><th className="px-2 py-2">Website</th></tr>
          </thead>
          <tbody className="text-slate-200">
            {filtered.map((l,i) => (
              <tr key={l.id} className="border-t border-panel-2 hover:bg-panel-2/40">
                <td className="px-2 py-1.5 text-xs text-slate-500">{i+1}</td>
                <td className="px-2 py-1.5 font-medium">{l.hotel_name}</td>
                <td className="px-2 py-1.5">{l.city}</td>
                <td className="px-2 py-1.5"><span className={`rounded px-1.5 py-0.5 text-xs font-bold ${l.outreach_status==='identified'?'bg-sky-900 text-sky-200':'bg-amber-900 text-amber-200'}`}>{l.outreach_status}</span></td>
                <td className="px-2 py-1.5 text-xs">{l.follow_up_date}</td>
                <td className="px-2 py-1.5 text-xs whitespace-nowrap">{l.phone || <span className="text-slate-500">—</span>}</td>
                <td className="px-2 py-1.5 text-xs truncate max-w-[160px]" title={l.email}>{l.email || <span className="text-slate-500">—</span>}</td>
                <td className="px-2 py-1.5 text-xs"><a href={l.website} target="_blank" className="text-brand hover:underline">{(l.website||"").replace('https://','').replace('http://','').slice(0,26)}</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-500">Tip: scraping — <code>fetch('http://localhost:8765/leads.json').then(r=&gt;r.json())</code> or <code>/goa_leads_GOA_ONLY.csv</code> — auto-updated via lead_manager.py</p>
    </div>
  );
}
