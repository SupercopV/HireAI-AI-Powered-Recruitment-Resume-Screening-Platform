import React, { useState, useEffect } from "react";
import {
  UserCheck,
  CheckCircle2,
  XCircle,
  Calendar,
  MessageSquare,
  FileText,
  ShieldCheck,
  Sparkles,
  Building,
  Clock,
  Briefcase
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Card } from "../components/ui/Card";
import { Badge, ScoreBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { TableSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

export const ClientPortal = () => {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  // Modals state
  const [selectedSub, setSelectedSub] = useState(null);
  const [shortlistModalOpen, setShortlistModalOpen] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Form states
  const [shortlistFeedback, setShortlistFeedback] = useState("Candidate approved for technical interview.");
  const [rejectionReason, setRejectionReason] = useState("");
  const [rejectionFeedback, setRejectionFeedback] = useState("");
  const [interviewTime, setInterviewTime] = useState("");
  const [interviewerName, setInterviewerName] = useState("Rajesh Khanna (Technical Lead)");

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const res = await api.get("/client/submissions");
      setSubmissions(res.data);
    } catch (err) {
      toast.error("Failed to load client submissions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const handleShortlist = async () => {
    if (!selectedSub) return;
    setActionLoading(true);
    try {
      await api.post(`/client/submissions/${selectedSub.submission_id}/shortlist`, {
        feedback_text: shortlistFeedback,
      });
      toast.success(`Candidate ${selectedSub.candidate_code} shortlisted!`);
      setShortlistModalOpen(false);
      fetchSubmissions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Shortlisting failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedSub) return;
    if (!rejectionReason.trim() || rejectionReason.trim().length < 3) {
      toast.warning("Mandatory rejection reason must be provided (min 3 chars).");
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/client/submissions/${selectedSub.submission_id}/reject`, {
        rejection_reason: rejectionReason,
        feedback_text: rejectionFeedback,
      });
      toast.success(`Candidate ${selectedSub.candidate_code} rejection recorded.`);
      setRejectModalOpen(false);
      setRejectionReason("");
      fetchSubmissions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Rejection failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleScheduleInterview = async () => {
    if (!selectedSub) return;
    if (!interviewTime) {
      toast.warning("Please choose a proposed interview date and time");
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/client/submissions/${selectedSub.submission_id}/interview`, {
        proposed_interview_time: new Date(interviewTime).toISOString(),
        interviewer_name: interviewerName,
        round_name: "Technical Round 1",
      });
      toast.success(`Interview proposed for ${new Date(interviewTime).toLocaleString()}!`);
      setInterviewModalOpen(false);
      fetchSubmissions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Interview scheduling failed");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Client Candidate Review Portal
            </h1>
            <Badge variant="purple" size="xs">
              FinTech Global Corp
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Candidates curated and submitted by Apex Staffing agency with masked contact info.
          </p>
        </div>
      </div>

      {/* Privacy Guarantee Alert */}
      <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/70 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-950 leading-relaxed">
          <p className="font-semibold">Candidate Privacy & Contact Masking Active</p>
          <p className="mt-0.5 opacity-90">
            In compliance with India's DPDP Act 2023 principles and anti-poaching policies, personal contact
            information (email address and phone numbers) is masked. Candidate skills, experience, verified
            evaluations, and recruiter notes are fully accessible.
          </p>
        </div>
      </div>

      {/* Candidate Submissions List */}
      {loading ? (
        <TableSkeleton rows={4} cols={5} />
      ) : submissions.length === 0 ? (
        <EmptyState
          icon={UserCheck}
          title="No candidates submitted yet"
          description="Candidates submitted by your recruitment agency partner will appear here for review."
        />
      ) : (
        <div className="space-y-4">
          {submissions.map((sub) => {
            const score = sub.latest_score?.total_score || 0;
            const grade = sub.latest_score?.match_grade;
            const status = sub.submission_status;

            return (
              <Card key={sub.id} hover className="p-6!">
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                  {/* Left: Candidate Details */}
                  <div className="space-y-3 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h3 className="text-base font-bold text-slate-900">{sub.masked_name}</h3>
                      <Badge variant="primary" size="xs">
                        {sub.candidate_code}
                      </Badge>
                      <ScoreBadge score={score} grade={grade} />
                      <Badge
                        variant={
                          status === "shortlisted"
                            ? "success"
                            : status === "rejected"
                            ? "danger"
                            : status === "interview_requested"
                            ? "primary"
                            : "warning"
                        }
                        size="xs"
                      >
                        {status.replace("_", " ").toUpperCase()}
                      </Badge>
                    </div>

                    <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                      <span>Role: <strong className="text-slate-700">{sub.current_role}</strong></span>
                      <span>Total Exp: <strong className="text-slate-700">{sub.total_experience_years} yrs</strong></span>
                      <span>Notice Period: <strong className="text-slate-700">{sub.notice_period_days} days</strong></span>
                      <span>Contact: <strong className="font-mono text-slate-600">{sub.masked_phone}</strong> ({sub.masked_email})</span>
                    </div>

                    {/* Professional Summary */}
                    {sub.summary && (
                      <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200/60">
                        {sub.summary}
                      </p>
                    )}

                    {/* Recruiter Endorsement Notes */}
                    {sub.recruiter_notes && (
                      <div className="text-xs bg-blue-50/60 p-3 rounded-lg border border-blue-200/80">
                        <span className="font-bold text-blue-900">Recruiter Notes: </span>
                        <span className="text-blue-950">{sub.recruiter_notes}</span>
                      </div>
                    )}

                    {/* Skills Chips */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {sub.skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-slate-100 border border-slate-200 text-slate-700 rounded text-xs font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right: Client Action Buttons */}
                  <div className="flex flex-row lg:flex-col items-center lg:items-stretch gap-2 shrink-0 border-t lg:border-t-0 lg:border-l border-slate-100 pt-4 lg:pt-0 lg:pl-6">
                    <Button
                      variant="success"
                      size="sm"
                      icon={CheckCircle2}
                      onClick={() => {
                        setSelectedSub(sub);
                        setShortlistModalOpen(true);
                      }}
                    >
                      Shortlist Profile
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      icon={Calendar}
                      onClick={() => {
                        setSelectedSub(sub);
                        setInterviewModalOpen(true);
                      }}
                    >
                      Propose Interview
                    </Button>

                    <Button
                      variant="dangerOutline"
                      size="sm"
                      icon={XCircle}
                      onClick={() => {
                        setSelectedSub(sub);
                        setRejectModalOpen(true);
                      }}
                    >
                      Reject Profile
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Shortlist Confirmation Modal */}
      <Modal
        isOpen={shortlistModalOpen}
        onClose={() => setShortlistModalOpen(false)}
        title={`Shortlist Candidate: ${selectedSub?.candidate_code}`}
        subtitle={`Candidate Profile: ${selectedSub?.masked_name}`}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setShortlistModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="success"
              size="sm"
              loading={actionLoading}
              icon={CheckCircle2}
              onClick={handleShortlist}
            >
              Confirm Shortlist
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <label className="block text-xs font-semibold text-slate-700 uppercase">
            Hiring Manager Feedback & Comments
          </label>
          <textarea
            rows={3}
            value={shortlistFeedback}
            onChange={(e) => setShortlistFeedback(e.target.value)}
            className="w-full p-3 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
      </Modal>

      {/* Rejection Modal with MANDATORY Rejection Reason */}
      <Modal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title={`Reject Candidate: ${selectedSub?.candidate_code}`}
        subtitle="Under HireAI audit rules, a mandatory rejection reason is required for fairness and transparency"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setRejectModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              loading={actionLoading}
              icon={XCircle}
              onClick={handleReject}
            >
              Confirm Rejection
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-rose-700 uppercase mb-1">
              Mandatory Rejection Reason *
            </label>
            <input
              type="text"
              required
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Notice period of 90 days exceeds maximum acceptable threshold."
              className="w-full px-3 py-2 border border-rose-300 rounded-xl text-xs focus:ring-2 focus:ring-rose-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Additional Technical Feedback for Recruiter (Optional)
            </label>
            <textarea
              rows={3}
              value={rejectionFeedback}
              onChange={(e) => setRejectionFeedback(e.target.value)}
              placeholder="Provide constructive feedback for future profile calibrations..."
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>

      {/* Propose Interview Modal */}
      <Modal
        isOpen={interviewModalOpen}
        onClose={() => setInterviewModalOpen(false)}
        title={`Schedule Technical Interview: ${selectedSub?.candidate_code}`}
        subtitle={`Candidate: ${selectedSub?.masked_name}`}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setInterviewModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={actionLoading}
              icon={Calendar}
              onClick={handleScheduleInterview}
            >
              Schedule Interview
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Proposed Date & Time *
            </label>
            <input
              type="datetime-local"
              required
              value={interviewTime}
              onChange={(e) => setInterviewTime(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Lead Interviewer Name
            </label>
            <input
              type="text"
              value={interviewerName}
              onChange={(e) => setInterviewerName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

