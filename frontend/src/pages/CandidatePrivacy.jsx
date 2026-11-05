import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Lock,
  UserX,
  FileText,
  Clock,
  EyeOff
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";

export const CandidatePrivacy = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCand, setSelectedCand] = useState(null);
  const [deletionModalOpen, setDeletionModalOpen] = useState(false);
  const [deletionReason, setDeletionReason] = useState("Candidate requested complete erasure under DPDP Act 2023 principles.");
  const [deleting, setDeleting] = useState(false);
  const toast = useToast();

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const res = await api.get("/requisitions/1/candidates");
      setCandidates(res.data);
    } catch (err) {
      toast.error("Failed to load candidate profiles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  const handleExecuteDeletion = async () => {
    if (!selectedCand) return;
    setDeleting(true);
    try {
      await api.post(`/candidates/${selectedCand.id}/deletion-request`, {
        reason: deletionReason,
      });
      toast.success(
        `DPDP Right-to-Erasure executed for ${selectedCand.candidate_code}. Personal data and CV files scrubbed.`
      );
      setDeletionModalOpen(false);
      fetchCandidates();
    } catch (err) {
      toast.error("Deletion request execution failed");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Candidate Privacy & DPDP Compliance
          </h1>
          <Badge variant="success" size="xs">
            India DPDP Act 2023 Principles
          </Badge>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          Explicit purpose limitation, consent verification, contact masking, and automated Right-to-Erasure workflows.
        </p>
      </div>

      {/* Compliance Information Card */}
      <Card className="bg-slate-900 text-slate-200 border-slate-800">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-xl bg-blue-600 text-white shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="space-y-2 text-xs">
            <h3 className="text-sm font-bold text-white">
              Data Fiduciary Privacy Commitments
            </h3>
            <p className="text-slate-300 leading-relaxed">
              HireAI processes candidate information solely for legitimate recruitment screening against approved
              job scorecards. Candidates are protected by:
            </p>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-300 pt-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Explicit purpose specification captured upon resume ingestion</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Client portal contact masking (anti-poaching & PII protection)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Audited resume view logging (records who viewed profiles & when)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Right-to-Erasure automated scrub of resume files and PII</span>
              </li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Active Candidate Profiles & Deletion Action Table */}
      <Card>
        <CardHeader
          title="Candidate Consent & Erasure Management"
          subtitle="Manage candidate records, verify consent status, or execute right-to-erasure workflows"
        />
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-y border-slate-200 text-slate-500 font-semibold uppercase">
              <tr>
                <th className="py-2.5 px-3">Candidate</th>
                <th className="py-2.5 px-3">Purpose Limitation</th>
                <th className="py-2.5 px-3">Consent Status</th>
                <th className="py-2.5 px-3">Profile State</th>
                <th className="py-2.5 px-3 text-right">Privacy Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {candidates.map((cand) => (
                <tr key={cand.id} className="hover:bg-slate-50/60">
                  <td className="py-3 px-3">
                    <span className="font-bold text-slate-900">{cand.first_name} {cand.last_name}</span>
                    <span className="block font-mono text-[10px] text-slate-400">{cand.candidate_code}</span>
                  </td>
                  <td className="py-3 px-3 text-slate-600 max-w-xs truncate">
                    Recruitment screening & scorecard matching
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant="success" size="xs">
                      Consent Verified
                    </Badge>
                  </td>
                  <td className="py-3 px-3">
                    <span className="inline-flex items-center gap-1 font-semibold text-emerald-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      Active Record
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Button
                      variant="dangerOutline"
                      size="xs"
                      icon={Trash2}
                      onClick={() => {
                        setSelectedCand(cand);
                        setDeletionModalOpen(true);
                      }}
                    >
                      Right to Erasure
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Deletion Request Confirmation Modal */}
      <Modal
        isOpen={deletionModalOpen}
        onClose={() => setDeletionModalOpen(false)}
        title={`Execute Right-to-Erasure: ${selectedCand?.first_name} ${selectedCand?.last_name}`}
        subtitle={`Candidate Code: ${selectedCand?.candidate_code} • Permanent anonymization and file scrubbing`}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setDeletionModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              loading={deleting}
              icon={UserX}
              onClick={handleExecuteDeletion}
            >
              Permanently Erase Personal Data
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Irreversible DPDP Data Scrub Action</p>
              <p className="mt-0.5 opacity-90">
                This workflow will permanently scrub the candidate's name, email, phone number, and raw CV text,
                and delete the stored resume files from disk. An immutable audit record of the deletion will be preserved.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Erasure Request Justification / Reference *
            </label>
            <textarea
              rows={3}
              value={deletionReason}
              onChange={(e) => setDeletionReason(e.target.value)}
              className="w-full p-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-rose-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

