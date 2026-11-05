import React, { useState, useEffect } from "react";
import {
  FileText,
  Shield,
  CheckCircle2,
  AlertCircle,
  Quote,
  Sparkles,
  ExternalLink,
  Info
} from "lucide-react";
import api from "../services/api";
import { Modal } from "../components/ui/Modal";
import { Badge, ScoreBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

export const CandidateEvidenceModal = ({ isOpen, onClose, candidate, requisitionId }) => {
  const [scoreData, setScoreData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvidence = async () => {
      if (!candidate?.id) return;
      setLoading(true);
      try {
        const res = await api.get(`/candidates/${candidate.id}/score?requisition_id=${requisitionId}`);
        setScoreData(res.data);
      } catch (err) {
        console.error("Failed to load candidate score evidence", err);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && candidate) {
      fetchEvidence();
    }
  }, [isOpen, candidate, requisitionId]);

  if (!candidate) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Explainable Scoring Audit: ${candidate.first_name} ${candidate.last_name}`}
      subtitle={`Candidate Code: ${candidate.candidate_code} • Current Role: ${candidate.current_role}`}
      maxWidth="max-w-3xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Shield className="w-4 h-4 text-emerald-600" />
            <span>Fairness-Compliant: Evaluated on job criteria only.</span>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close Evidence Audit
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Total Score Summary Card */}
        <div className="bg-slate-900 text-white rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Total Match Score
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                {scoreData?.match_grade || "Scored"}
              </span>
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-extrabold tracking-tight">
                {scoreData?.total_score || candidate.latest_score?.total_score || 0}
              </span>
              <span className="text-slate-400 text-sm font-medium">/ 100 points</span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              {scoreData?.ai_reasoning || "Deterministic scoring based on scorecard weights."}
            </p>
          </div>

          <div className="sm:border-l sm:border-slate-800 sm:pl-5 space-y-1 text-xs">
            <div className="flex justify-between gap-4 text-slate-300">
              <span>Required Skills:</span>
              <span className="font-bold text-white">{scoreData?.required_skills_score || 0}/40</span>
            </div>
            <div className="flex justify-between gap-4 text-slate-300">
              <span>Total Experience:</span>
              <span className="font-bold text-white">{scoreData?.experience_score || 0}/25</span>
            </div>
            <div className="flex justify-between gap-4 text-slate-300">
              <span>Relevant Experience:</span>
              <span className="font-bold text-white">{scoreData?.relevant_experience_score || 0}/15</span>
            </div>
            <div className="flex justify-between gap-4 text-slate-300">
              <span>Good-to-Have:</span>
              <span className="font-bold text-white">{scoreData?.good_to_have_score || 0}/10</span>
            </div>
            <div className="flex justify-between gap-4 text-slate-300">
              <span>Notice Period:</span>
              <span className="font-bold text-white">{scoreData?.notice_period_score || 0}/10</span>
            </div>
          </div>
        </div>

        {/* 5 Explainable Scoring Criteria with EXACT Original CV Quotations */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Explainable Criteria & Verbatim CV Evidence
          </h4>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 animate-pulse">
              Loading verified quotes from original resume text...
            </div>
          ) : (scoreData?.evidence_items || []).length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
              No evidence items recorded yet. Click Re-score to compute.
            </div>
          ) : (
            (scoreData?.evidence_items || []).map((ev, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-200/90 bg-white hover:border-slate-300 transition-all space-y-2.5"
              >
                {/* Header: Criterion & Score */}
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900">{ev.criterion_name}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {ev.awarded_score} / {ev.max_score} pts
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-xs text-slate-600 leading-relaxed">{ev.explanation}</p>

                {/* Verbatim Supporting Evidence from CV */}
                <div className="rounded-lg bg-slate-50 p-3 border border-slate-200/70 text-xs">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    <Quote className="w-3.5 h-3.5 text-blue-600" />
                    <span>Exact CV Evidence Quotation</span>
                  </div>
                  <p className="font-mono text-[11px] text-slate-800 italic bg-white p-2 rounded border border-slate-200">
                    {ev.evidence_quote}
                  </p>
                </div>

                {/* Missing Info Warning if any */}
                {ev.missing_info && (
                  <div className="flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50 px-2.5 py-1.5 rounded-lg border border-amber-200">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{ev.missing_info}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </Modal>
  );
};

