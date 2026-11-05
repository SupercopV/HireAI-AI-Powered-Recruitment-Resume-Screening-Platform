import React, { useState, useEffect } from "react";
import {
  FileText,
  Search,
  Filter,
  Shield,
  Clock,
  User,
  RefreshCw
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { TableSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

export const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("all");
  const toast = useToast();

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = "/audit-logs?limit=100";
      if (filterType !== "all") url += `&resource_type=${filterType}`;
      const res = await api.get(url);
      setLogs(res.data);
    } catch (err) {
      toast.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filterType]);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Immutable Security Audit Trail
            </h1>
            <Badge variant="purple" size="xs">
              Compliance Log
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographically timestamped log tracking who viewed candidate profiles, screening actions, and decisions.
          </p>
        </div>

        <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchLogs}>
          Refresh Trail
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        {["all", "candidate", "submission", "requisition", "privacy", "auth"].map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
              filterType === type
                ? "bg-blue-600 text-white shadow-xs"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            {type === "all" ? "All Operations" : `${type} Events`}
          </button>
        ))}
      </div>

      {/* Audit Log Table */}
      {loading ? (
        <TableSkeleton rows={6} cols={5} />
      ) : logs.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No audit entries found"
          description="Security and operational actions will automatically appear in this immutable log."
        />
      ) : (
        <Card className="overflow-hidden p-0!">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Timestamp (UTC)</th>
                  <th className="py-2.5 px-3">User & Role</th>
                  <th className="py-2.5 px-3">Action Event</th>
                  <th className="py-2.5 px-3">Resource Target</th>
                  <th className="py-2.5 px-3">Details & Audit Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60">
                    <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span className="font-semibold text-slate-800 font-sans">
                        {log.user_email || "System"}
                      </span>
                      <span className="block text-[10px] text-slate-400 capitalize font-sans">
                        {log.user_role || "automated"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-blue-700 font-sans bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 whitespace-nowrap">
                      {log.resource_type}: <strong>{log.resource_id}</strong>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 max-w-xs truncate font-sans text-[11px]">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

