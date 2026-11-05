import React, { useState, useEffect } from "react";
import { Search, Sparkles, CheckCircle2, Building, RefreshCw, UserCheck } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import api from "../../services/api";

export const TopNav = ({ selectedReqId, onSelectReq }) => {
  const { user, login } = useAuth();
  const [requisitions, setRequisitions] = useState([]);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    const fetchReqs = async () => {
      try {
        const res = await api.get("/requisitions");
        setRequisitions(res.data);
        if (res.data.length > 0 && !selectedReqId && onSelectReq) {
          onSelectReq(res.data[0].id);
        }
      } catch (err) {
        console.error("Failed to load requisitions for top nav", err);
      }
    };
    fetchReqs();
  }, []);

  const handleRoleToggle = async () => {
    setSwitching(true);
    try {
      if (user?.role === "recruiter") {
        await login("client.hiring@fintechcorp.com", "password123");
      } else {
        await login("recruiter@hireai.com", "password123");
      }
      window.location.reload();
    } catch (e) {
      console.error("Role toggle error", e);
    } finally {
      setSwitching(false);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between gap-4 sticky top-0 z-20">
      {/* Requisition Switcher & Search */}
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        {onSelectReq && requisitions.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider hidden sm:inline">
              Requisition:
            </span>
            <select
              value={selectedReqId || ""}
              onChange={(e) => onSelectReq(Number(e.target.value))}
              className="bg-slate-50 border border-slate-200 text-slate-800 text-xs font-semibold rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              {requisitions.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.requisition_code} – {r.title} ({r.location})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right Controls: AI Status & Demo Switcher */}
      <div className="flex items-center gap-3">
        {/* System & AI Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-[11px] font-medium text-slate-600">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Groq AI + Python Engine Active</span>
        </div>

        {/* 1-Click Demo Role Toggle */}
        <button
          onClick={handleRoleToggle}
          disabled={switching}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-2xs transition-colors cursor-pointer"
          title="Switch between Recruiter and Client Hiring Manager account"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-blue-600 ${switching ? "animate-spin" : ""}`} />
          <span>Switch to {user?.role === "recruiter" ? "Client View" : "Recruiter View"}</span>
        </button>
      </div>
    </header>
  );
};

