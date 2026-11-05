import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Users,
  Search,
  Filter,
  FileText,
  Eye,
  CheckCircle2,
  Send,
  Sparkles,
  Shield,
  RotateCcw,
  Check,
  AlertCircle,
  ExternalLink,
  ChevronDown
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card } from "../components/ui/Card";
import { Badge, ScoreBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { TableSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { CandidateEvidenceModal } from "./CandidateEvidenceModal";

export const CandidateRanking = () => {
  const { selectedReqId } = useOutletContext() || { selectedReqId: 1 };
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scoringAll, setScoringAll] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [gradeFilter, setGradeFilter] = useState("all");
  const [minScoreFilter, setMinScoreFilter] = useState("");
  const toast = useToast();

  // Modals state
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  // Resume preview modal
  const [resumeModalOpen, setResumeModalOpen] = useState(false);
  const [resumeContent, setResumeContent] = useState("");
  const [resumeLoading, setResumeLoading] = useState(false);

  // Submit to client modal
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [submitNotes, setSubmitNotes] = useState("");
  const [submittingToClient, setSubmittingToClient] = useState(false);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      let url = `/requisitions/${selectedReqId}/candidates`;
      const params = [];
      if (searchTerm) params.push(`search=${encodeURIComponent(searchTerm)}`);
      if (gradeFilter !== "all") params.push(`match_grade=${encodeURIComponent(gradeFilter)}`);
      if (minScoreFilter) params.push(`min_score=${encodeURIComponent(minScoreFilter)}`);
      if (params.length > 0) url += `?${params.join("&")}`;

      const res = await api.get(url);
      setCandidates(res.data);
    } catch (err) {
      toast.error("Failed to load ranked candidates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedReqId) {
      fetchCandidates();
    }
  }, [selectedReqId, gradeFilter]);

  const handleScoreAll = async () => {
    setScoringAll(true);
    try {
      const res = await api.post(`/requisitions/${selectedReqId}/score-all`);
      toast.success(res.data.message || "Re-calculated deterministic candidate scores!");
      fetchCandidates();
    } catch (err) {
      toast.error("Scoring execution failed");
    } finally {
      setScoringAll(false);
    }
  };

  const handleViewResume = async (cand) => {
    setSelectedCandidate(cand);
    setResumeModalOpen(true);
    setResumeLoading(true);
    try {
      const res = await api.get(`/candidates/${cand.id}`);
      setResumeContent(res.data.raw_text || "No resume text content available.");
    } catch (err) {
      toast.error("Failed to fetch resume");
    } finally {
      setResumeLoading(false);
    }
  };

  const handleOpenSubmitModal = (cand) => {
    setSelectedCandidate(cand);
    setSubmitNotes(`Strong technical fit for requisition. Evaluated score: ${cand.latest_score?.total_score || 0}/100.`);
    setSubmitModalOpen(true);
  };

  const handleSubmitToClient = async () => {
    if (!selectedCandidate) return;
    setSubmittingToClient(true);
    try {
      await api.post("/client/submissions", {
        requisition_id: selectedReqId,
        candidate_id: selectedCandidate.id,
        client_org_id: 2, // FinTech Global Corp
        recruiter_notes: submitNotes,
      });
      toast.success(
        `Candidate ${selectedCandidate.candidate_code} submitted to Client Hiring Manager!`
      );
      setSubmitModalOpen(false);
      fetchCandidates();
    } catch (err) {
      toast.error("Submission failed");
    } finally {
      setSubmittingToClient(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              AI-Ranked Candidate Shortlist
            </h1>
            <Badge variant="primary" size="xs">
              {candidates.length} Total Profiles
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ranked deterministically against approved job scorecard. Ranked by total score descending.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          loading={scoringAll}
          icon={RotateCcw}
          onClick={handleScoreAll}
        >
          Re-Score All Profiles
        </Button>
      </div>

      {/* Fairness & Explainability Guarantee Alert */}
      <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/70 flex items-start gap-3">
        <Shield className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <div className="text-xs text-emerald-950 leading-relaxed">
          <p className="font-semibold">Algorithmic Fairness & Transparency Guarantee</p>
          <p className="mt-0.5 opacity-90">
            Scores are computed strictly on job-related qualifications: Required Skills (40), Experience (25),
            Relevant Domain (15), Secondary Skills (10), and Notice Period (10).
            Candidate name, gender, age, photo, marital status, and personal attributes are strictly excluded.
            AI never automatically rejects low-scoring candidates; all profiles remain searchable.
          </p>
        </div>
      </div>

      {/* Search & Grade Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchCandidates()}
            placeholder="Search by candidate code, name, role, or skill..."
            className="w-full pl-10 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Grade Filters */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={gradeFilter}
            onChange={(e) => setGradeFilter(e.target.value)}
            className="px-3 py-2 bg-white rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="all">All Match Grades</option>
            <option value="High Match">High Match (≥ 80)</option>
            <option value="Moderate Match">Moderate Match (50–79)</option>
            <option value="Low Match">Low Match (&lt; 50)</option>
          </select>

          <Button variant="secondary" size="sm" onClick={fetchCandidates}>
            Filter
          </Button>
        </div>
      </div>

      {/* Candidate Table */}
      {loading ? (
        <TableSkeleton rows={6} cols={6} />
      ) : candidates.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No candidates match your search"
          description="Try broadening your filter criteria or re-score candidates."
        />
      ) : (
        <Card className="overflow-hidden p-0!">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-3">Role & Experience</th>
                  <th className="py-3 px-3">Match Score</th>
                  <th className="py-3 px-3">Matching Skills</th>
                  <th className="py-3 px-3">Missing Skills</th>
                  <th className="py-3 px-3">Notice</th>
                  <th className="py-3 px-3">Stage</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {candidates.map((cand) => {
                  const score = cand.latest_score?.total_score || 0;
                  const grade = cand.latest_score?.match_grade;
                  const matchingSkills = cand.latest_score?.matching_skills || [];
                  const missingSkills = cand.latest_score?.missing_skills || [];

                  return (
                    <tr key={cand.id} className="hover:bg-slate-50/60 transition-colors">
                      {/* Name & ID */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">
                          {cand.first_name} {cand.last_name}
                        </div>
                        <div className="font-mono text-[10px] text-slate-400">
                          {cand.candidate_code}
                        </div>
                      </td>

                      {/* Role & Experience */}
                      <td className="py-3.5 px-3">
                        <div className="font-medium text-slate-800">{cand.current_role}</div>
                        <div className="text-[11px] text-slate-500">
                          {cand.total_experience_years} yrs total ({cand.relevant_experience_years || cand.total_experience_years} rel)
                        </div>
                      </td>

                      {/* Match Score Badge */}
                      <td className="py-3.5 px-3">
                        <ScoreBadge score={score} grade={grade} />
                      </td>

                      {/* Matching Skills Chips */}
                      <td className="py-3.5 px-3 max-w-xs">
                        <div className="flex flex-wrap gap-1">
                          {matchingSkills.slice(0, 3).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded text-[10px] font-semibold"
                            >
                              {s}
                            </span>
                          ))}
                          {matchingSkills.length > 3 && (
                            <span className="text-[10px] text-slate-400 font-semibold">
                              +{matchingSkills.length - 3}
                            </span>
                          )}
                          {matchingSkills.length === 0 && (
                            <span className="text-[10px] text-slate-400">None</span>
                          )}
                        </div>
                      </td>

                      {/* Missing Skills Chips */}
                      <td className="py-3.5 px-3 max-w-xs">
                        <div className="flex flex-wrap gap-1">
                          {missingSkills.slice(0, 2).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-rose-50 border border-rose-200 text-rose-800 rounded text-[10px]"
                            >
                              {s}
                            </span>
                          ))}
                          {missingSkills.length === 0 && (
                            <span className="text-[10px] text-emerald-600 font-medium">None</span>
                          )}
                        </div>
                      </td>

                      {/* Notice Period */}
                      <td className="py-3.5 px-3 text-slate-700 font-medium">
                        {cand.notice_period_days} days
                      </td>

                      {/* Stage Badge */}
                      <td className="py-3.5 px-3">
                        <Badge
                          variant={
                            cand.current_stage === "Submitted to Client"
                              ? "primary"
                              : cand.current_stage === "Client Approved" || cand.current_stage === "Interview Scheduled"
                              ? "success"
                              : cand.current_stage === "Rejected"
                              ? "danger"
                              : "default"
                          }
                          size="xs"
                        >
                          {cand.current_stage}
                        </Badge>
                      </td>

                      {/* Action Buttons */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          {/* View Resume Button */}
                          <button
                            type="button"
                            onClick={() => handleViewResume(cand)}
                            title="View original extracted CV"
                            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:bg-slate-50 transition-colors cursor-pointer"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </button>

                          {/* View Explainable Evidence Button */}
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedCandidate(cand);
                              setEvidenceModalOpen(true);
                            }}
                            title="View explainable scoring evidence quotes"
                            className="px-2.5 py-1 rounded-lg border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-[11px] transition-colors cursor-pointer"
                          >
                            Evidence
                          </button>

                          {/* Submit to Client Action */}
                          <Button
                            variant="primary"
                            size="xs"
                            icon={Send}
                            onClick={() => handleOpenSubmitModal(cand)}
                          >
                            Submit
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Candidate Explainable Evidence Modal */}
      <CandidateEvidenceModal
        isOpen={evidenceModalOpen}
        onClose={() => setEvidenceModalOpen(false)}
        candidate={selectedCandidate}
        requisitionId={selectedReqId}
      />

      {/* Resume Original Preview Modal */}
      <Modal
        isOpen={resumeModalOpen}
        onClose={() => setResumeModalOpen(false)}
        title={`Original Resume: ${selectedCandidate?.first_name} ${selectedCandidate?.last_name}`}
        subtitle={`Candidate Code: ${selectedCandidate?.candidate_code}`}
        maxWidth="max-w-2xl"
        footer={
          <Button variant="secondary" size="sm" onClick={() => setResumeModalOpen(false)}>
            Close
          </Button>
        }
      >
        {resumeLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
            Loading resume file text...
          </div>
        ) : (
          <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs max-h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
            {resumeContent}
          </div>
        )}
      </Modal>

      {/* Submit to Client Modal */}
      <Modal
        isOpen={submitModalOpen}
        onClose={() => setSubmitModalOpen(false)}
        title="Submit Candidate to Client"
        subtitle={`Target Organization: FinTech Global Corp • Candidate: ${selectedCandidate?.first_name} ${selectedCandidate?.last_name} (${selectedCandidate?.candidate_code})`}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setSubmitModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={submittingToClient}
              icon={Send}
              onClick={handleSubmitToClient}
            >
              Confirm Submission
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900">
            Candidate's personal contact details (email, phone number) will be automatically masked
            in the client portal view for DPDP compliance.
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Recruiter Endorsement & Screening Notes *
            </label>
            <textarea
              rows={4}
              value={submitNotes}
              onChange={(e) => setSubmitNotes(e.target.value)}
              placeholder="Add your recruiter assessment, interview availability, and strengths..."
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

