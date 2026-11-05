import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  FileSpreadsheet,
  UploadCloud,
  Users,
  GitPullRequest,
  ShieldCheck,
  FileText,
  Building2,
  LogOut,
  Sparkles,
  UserCheck,
  CalendarCheck
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export const Sidebar = () => {
  const { user, logout, isRecruiter, isClient } = useAuth();
  const navigate = useNavigate();

  const recruiterNav = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Requisitions", path: "/requisitions", icon: Briefcase },
    { name: "JD Scorecards", path: "/scorecards", icon: FileSpreadsheet },
    { name: "Bulk CV Upload", path: "/upload", icon: UploadCloud },
    { name: "AI Shortlists", path: "/candidates", icon: Users },
    { name: "Pipeline Kanban", path: "/pipeline", icon: GitPullRequest },
    { name: "Client Portal View", path: "/client/portal", icon: UserCheck },
    { name: "Privacy & DPDP", path: "/privacy", icon: ShieldCheck },
    { name: "Audit Trail", path: "/audit-logs", icon: FileText },
  ];

  const clientNav = [
    { name: "Candidate Shortlists", path: "/client/portal", icon: UserCheck },
    { name: "Interviews", path: "/client/interviews", icon: CalendarCheck },
  ];

  const navItems = isClient ? clientNav : recruiterNav;

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-white tracking-tight text-base">HireAI</span>
            <span className="text-[10px] bg-blue-500/20 text-blue-400 font-semibold px-1.5 py-0.5 rounded border border-blue-500/30">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 truncate max-w-[140px]">
            {user?.organization_name || "Enterprise Portal"}
          </p>
        </div>
      </div>

      {/* Role Pill Banner */}
      <div className="px-5 py-3 border-b border-slate-800/50 bg-slate-950/40">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Current Role</span>
          <span className={`px-2 py-0.5 rounded-full font-medium text-[11px] ${
            isClient
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
              : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
          }`}>
            {isClient ? "Client Hiring Mgr" : "Recruiter"}
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          {isClient ? "Client Review Center" : "Recruitment Operations"}
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-blue-600 text-white font-semibold shadow-xs"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </div>

      {/* User Footer Profile */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/30">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-200 shrink-0">
              {user?.full_name?.charAt(0) || "U"}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name}</p>
              <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            title="Sign out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors cursor-pointer shrink-0"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};

