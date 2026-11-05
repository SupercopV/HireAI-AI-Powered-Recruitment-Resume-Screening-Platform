import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Briefcase,
  Users,
  CheckCircle2,
  Clock,
  Calendar,
  UserCheck,
  TrendingUp,
  ArrowUpRight,
  Sparkles,
  UploadCloud,
  FileSpreadsheet
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";
import api from "../services/api";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { CardSkeleton, TableSkeleton } from "../components/ui/LoadingSkeleton";

export const RecruiterDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get("/dashboard/stats");
        setData(res.data);
      } catch (err) {
        console.error("Dashboard stats fetch error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <TableSkeleton rows={5} />
      </div>
    );
  }

  const m = data?.metrics || {};

  const metricCards = [
    { label: "Active Requisitions", value: m.total_active_requisitions || 0, icon: Briefcase, color: "text-blue-600 bg-blue-50 border-blue-200" },
    { label: "Total Candidates", value: m.total_candidates || 0, icon: Users, color: "text-indigo-600 bg-indigo-50 border-indigo-200" },
    { label: "Candidates Screened", value: m.candidates_screened || 0, icon: Sparkles, color: "text-purple-600 bg-purple-50 border-purple-200" },
    { label: "Shortlisted", value: m.candidates_shortlisted || 0, icon: CheckCircle2, color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
    { label: "Pending Client Reviews", value: m.pending_client_reviews || 0, icon: Clock, color: "text-amber-600 bg-amber-50 border-amber-200" },
    { label: "Interviews Scheduled", value: m.interviews_scheduled || 0, icon: Calendar, color: "text-cyan-600 bg-cyan-50 border-cyan-200" },
    { label: "Candidates Joined", value: m.candidates_joined || 0, icon: UserCheck, color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner with Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Recruiter Overview & Screening Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic explainable candidate scoring powered by Groq and rule-based evaluation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={UploadCloud}
            onClick={() => navigate("/upload")}
          >
            Bulk Upload CVs
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={FileSpreadsheet}
            onClick={() => navigate("/scorecards")}
          >
            Manage Scorecards
          </Button>
        </div>
      </div>

      {/* 7 Core KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3.5">
        {metricCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <Card key={i} className="p-4! hover:border-slate-300 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  {card.label}
                </span>
                <div className={`p-1.5 rounded-lg border ${card.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <p className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
                {card.value}
              </p>
            </Card>
          );
        })}
      </div>

      {/* Weekly Activity Chart & Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Chart */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Weekly Screening Activity"
            subtitle="Resumes parsed vs AI candidates screened over the past 7 days"
          />
          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.weekly_activity || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "none",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="screened" name="Screened" fill="#2563eb" radius={[4, 4, 0, 0]} />
                <Bar dataKey="uploaded" name="Uploaded" fill="#93c5fd" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Pipeline Distribution */}
        <Card>
          <CardHeader
            title="Candidate Pipeline Stages"
            subtitle="Current volume per lifecycle stage"
          />
          <div className="space-y-3 mt-4">
            {(data?.status_distribution || []).map((s, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="text-slate-600 font-medium">{s.stage}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (s.count / Math.max(1, m.total_candidates || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="font-bold text-slate-800 w-6 text-right">{s.count}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Requisitions Overview & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Requisitions */}
        <Card>
          <CardHeader
            title="Requisitions Overview"
            subtitle="Top live roles and matched candidate volume"
            action={
              <Link
                to="/requisitions"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                View all <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            }
          />
          <div className="divide-y divide-slate-100 mt-2">
            {(data?.requisitions_overview || []).map((r) => (
              <div key={r.id} className="py-3 flex items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{r.title}</span>
                    <Badge variant="primary" size="xs">
                      {r.requisition_code}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {r.department} • {r.location} • {r.experience}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-slate-700 bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
                    {r.candidates_count} candidates
                  </span>
                  <Link
                    to="/candidates"
                    className="text-xs font-semibold text-blue-600 hover:underline"
                  >
                    Shortlist
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Recent Candidate Activity */}
        <Card>
          <CardHeader
            title="Recent Pipeline Activity"
            subtitle="Latest candidate movements and screening events"
          />
          <div className="divide-y divide-slate-100 mt-2 max-h-72 overflow-y-auto">
            {(data?.recent_activity || []).map((a) => (
              <div key={a.id} className="py-2.5 flex items-start gap-3 text-xs">
                <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-800">
                    {a.candidate_name}{" "}
                    <span className="text-slate-400 font-normal">({a.candidate_code})</span>
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Moved to <span className="font-semibold text-slate-700">{a.to_stage}</span>:{" "}
                    {a.notes || "Status updated"}
                  </p>
                </div>
                <span className="text-[10px] text-slate-400 shrink-0">
                  {new Date(a.timestamp).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

