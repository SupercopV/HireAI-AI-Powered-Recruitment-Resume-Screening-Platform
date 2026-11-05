import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import {
  GitPullRequest,
  Search,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
  Filter,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card } from "../components/ui/Card";
import { Badge, ScoreBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { TableSkeleton } from "../components/ui/LoadingSkeleton";

export const RecruitmentPipeline = () => {
  const { selectedReqId } = useOutletContext() || { selectedReqId: 1 };
  const [pipelineData, setPipelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const toast = useToast();

  // Stage transition modal
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [transitionModalOpen, setTransitionModalOpen] = useState(false);
  const [targetStage, setTargetStage] = useState("");
  const [transitionNotes, setTransitionNotes] = useState("");
  const [transitioning, setTransitioning] = useState(false);

  // History timeline modal
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [historyTimeline, setHistoryTimeline] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchPipeline = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/requisitions/${selectedReqId}/pipeline`);
      setPipelineData(res.data);
    } catch (err) {
      toast.error("Failed to load pipeline stages");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedReqId) fetchPipeline();
  }, [selectedReqId]);

  const handleOpenTransition = (cand, currentStage) => {
    setSelectedCandidate({ ...cand, currentStage });
    setTargetStage(currentStage);
    setTransitionNotes("");
    setTransitionModalOpen(true);
  };

  const handleExecuteTransition = async () => {
    if (!selectedCandidate || !targetStage) return;
    setTransitioning(true);
    try {
      await api.patch(`/candidates/${selectedCandidate.id}/pipeline`, {
        to_stage: targetStage,
        notes: transitionNotes,
      });
      toast.success(
        `Candidate ${selectedCandidate.candidate_code} moved to ${targetStage}!`
      );
      setTransitionModalOpen(false);
      fetchPipeline();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Status transition failed");
    } finally {
      setTransitioning(false);
    }
  };

  const handleViewHistory = async (cand) => {
    setSelectedCandidate(cand);
    setHistoryModalOpen(true);
    setHistoryLoading(true);
    try {
      const res = await api.get(`/candidates/${cand.id}/pipeline-history`);
      setHistoryTimeline(res.data);
    } catch (err) {
      toast.error("Failed to load history");
    } finally {
      setHistoryLoading(false);
    }
  };

  const allStages = [
    "Sourced",
    "Parsed",
    "Screened",
    "Shortlisted",
    "Submitted to Client",
    "Client Approved",
    "Interview Scheduled",
    "Interviewed",
    "Offered",
    "Joined",
    "Rejected",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Recruitment Lifecycle Kanban
            </h1>
            <Badge variant="primary" size="xs">
              11 Controlled Stages
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Role: {pipelineData?.requisition_title || "Selected Requisition"} • Track candidates through offer & joining.
          </p>
        </div>

        <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchPipeline}>
          Refresh Pipeline
        </Button>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter candidates across stages..."
          className="w-full pl-10 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Horizontal Scrollable Kanban Columns */}
      {loading ? (
        <TableSkeleton rows={4} cols={5} />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-6 pt-1 select-none">
          {(pipelineData?.stages || []).map((col) => {
            const filteredCands = (col.candidates || []).filter(
              (c) =>
                c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.candidate_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.current_role.toLowerCase().includes(searchTerm.toLowerCase())
            );

            return (
              <div
                key={col.stage_name}
                className="w-72 shrink-0 bg-slate-100/70 rounded-2xl p-3 border border-slate-200/80 flex flex-col max-h-[75vh]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between px-2 py-1.5 mb-2">
                  <span className="text-xs font-bold text-slate-800">{col.stage_name}</span>
                  <span className="w-5 h-5 rounded-full bg-slate-200/80 text-[11px] font-bold text-slate-700 flex items-center justify-center">
                    {filteredCands.length}
                  </span>
                </div>

                {/* Candidate Cards in Column */}
                <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
                  {filteredCands.map((cand) => (
                    <div
                      key={cand.id}
                      className="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs hover:border-blue-400 hover:shadow-xs transition-all cursor-pointer space-y-2"
                      onClick={() => handleOpenTransition(cand, col.stage_name)}
                    >
                      <div className="flex items-start justify-between gap-1">
                        <div>
                          <p className="text-xs font-bold text-slate-900">{cand.name}</p>
                          <p className="font-mono text-[10px] text-slate-400">{cand.candidate_code}</p>
                        </div>
                        <ScoreBadge score={cand.score} />
                      </div>

                      <div className="text-[11px] text-slate-500">
                        {cand.current_role} • {cand.total_experience_years} yrs
                      </div>

                      {/* Skill tags */}
                      <div className="flex flex-wrap gap-1">
                        {cand.skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.2 bg-slate-50 border border-slate-200 text-slate-600 rounded text-[9px] font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>

                      {/* Card Footer: History Link */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                        <span>Notice: {cand.notice_period_days}d</span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewHistory(cand);
                          }}
                          className="text-blue-600 hover:underline font-semibold"
                        >
                          Timeline
                        </button>
                      </div>
                    </div>
                  ))}
                  {filteredCands.length === 0 && (
                    <div className="p-4 text-center text-[11px] text-slate-400 border border-dashed border-slate-200 rounded-xl">
                      Empty stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Transition Stage Modal */}
      <Modal
        isOpen={transitionModalOpen}
        onClose={() => setTransitionModalOpen(false)}
        title={`Move Candidate: ${selectedCandidate?.name}`}
        subtitle={`Current Stage: ${selectedCandidate?.currentStage} • Code: ${selectedCandidate?.candidate_code}`}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setTransitionModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={transitioning}
              icon={ArrowRight}
              onClick={handleExecuteTransition}
            >
              Update Stage
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Target Pipeline Stage *
            </label>
            <select
              value={targetStage}
              onChange={(e) => setTargetStage(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {allStages.map((stg) => (
                <option key={stg} value={stg}>
                  {stg}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Transition Notes / Reasons
            </label>
            <textarea
              rows={3}
              value={transitionNotes}
              onChange={(e) => setTransitionNotes(e.target.value)}
              placeholder="e.g. Candidate completed Technical Round 1 with positive client feedback..."
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>

      {/* Pipeline Activity Timeline Modal */}
      <Modal
        isOpen={historyModalOpen}
        onClose={() => setHistoryModalOpen(false)}
        title={`Stage History & Audit Timeline: ${selectedCandidate?.name}`}
        subtitle={`Candidate Code: ${selectedCandidate?.candidate_code}`}
        footer={
          <Button variant="secondary" size="sm" onClick={() => setHistoryModalOpen(false)}>
            Close Timeline
          </Button>
        }
      >
        {historyLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
            Loading timeline events...
          </div>
        ) : historyTimeline.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">No events recorded.</div>
        ) : (
          <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {historyTimeline.map((item) => (
              <div key={item.id} className="flex items-start gap-4 pl-2 relative">
                <div className="w-2.5 h-2.5 rounded-full bg-blue-600 ring-4 ring-white shrink-0 mt-1" />
                <div className="flex-1 bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-xs">
                  <div className="flex items-center justify-between font-semibold text-slate-900">
                    <span>
                      {item.from_stage ? `${item.from_stage} → ` : ""}
                      <span className="text-blue-700 font-bold">{item.to_stage}</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-normal">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600 mt-1">{item.notes || "No notes entered"}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

