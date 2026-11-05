import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Briefcase,
  Plus,
  Search,
  MapPin,
  Clock,
  IndianRupee,
  Users,
  FileSpreadsheet,
  UploadCloud,
  ChevronRight
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { TableSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

export const RequisitionList = () => {
  const [requisitions, setRequisitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const toast = useToast();
  const navigate = useNavigate();

  // Create requisition form state
  const [formData, setFormData] = useState({
    title: "",
    department: "Engineering",
    location: "Noida",
    experience_min: 5.0,
    experience_max: 8.0,
    ctc_min_lpa: 15.0,
    ctc_max_lpa: 25.0,
    employment_type: "Full-Time",
    max_notice_period_days: 60,
    description: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchRequisitions = async () => {
    try {
      const res = await api.get("/requisitions");
      setRequisitions(res.data);
    } catch (err) {
      toast.error("Failed to load requisitions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequisitions();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.title || !formData.description) {
      toast.warning("Title and description are required");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/requisitions", formData);
      toast.success(`Requisition ${res.data.requisition_code} created!`);
      setIsModalOpen(false);
      setFormData({
        title: "",
        department: "Engineering",
        location: "Noida",
        experience_min: 5.0,
        experience_max: 8.0,
        ctc_min_lpa: 15.0,
        ctc_max_lpa: 25.0,
        employment_type: "Full-Time",
        max_notice_period_days: 60,
        description: "",
      });
      fetchRequisitions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create requisition");
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = requisitions.filter(
    (r) =>
      r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.requisition_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Job Requisitions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Create requisitions, define AI scorecards, and monitor shortlists.
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          icon={Plus}
          onClick={() => setIsModalOpen(true)}
        >
          Create Requisition
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter requisitions by title, requisition code, or location..."
          className="w-full pl-10 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Requisitions Grid */}
      {loading ? (
        <TableSkeleton rows={4} cols={5} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No requisitions found"
          description="Create your first requisition to start scoring resumes."
          actionLabel="Create Requisition"
          onAction={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((req) => (
            <Card key={req.id} hover className="flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="primary" size="xs">
                        {req.requisition_code}
                      </Badge>
                      <Badge variant="success" size="xs">
                        {req.status}
                      </Badge>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-2">
                      {req.title}
                    </h3>
                  </div>
                  <span className="text-xs font-semibold px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-slate-700">
                    {req.candidates_count || 0} CVs
                  </span>
                </div>

                <p className="text-xs text-slate-500 line-clamp-2 mt-2 leading-relaxed">
                  {req.description}
                </p>

                {/* Metadata Pills */}
                <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{req.location}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>Notice: max {req.max_notice_period_days} days</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                    <span>Exp: {req.experience_min}–{req.experience_max} yrs</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <IndianRupee className="w-3.5 h-3.5 text-slate-400" />
                    <span>CTC: {req.ctc_min_lpa}–{req.ctc_max_lpa} LPA</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <Link
                  to="/scorecards"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 hover:text-blue-600 transition-colors"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Scorecard
                </Link>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="xs"
                    icon={UploadCloud}
                    onClick={() => navigate("/upload")}
                  >
                    Upload CVs
                  </Button>
                  <Button
                    variant="primary"
                    size="xs"
                    icon={Users}
                    onClick={() => navigate("/candidates")}
                  >
                    Shortlist
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Requisition Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Requisition"
        subtitle="Specify job requirements to configure automated scorecard extraction"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={submitting}
              onClick={handleCreate}
            >
              Save Requisition
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Job Title *
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. Senior Java Developer"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Base Location
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Min Experience (Yrs)
              </label>
              <input
                type="number"
                step="0.5"
                value={formData.experience_min}
                onChange={(e) => setFormData({ ...formData, experience_min: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Max Experience (Yrs)
              </label>
              <input
                type="number"
                step="0.5"
                value={formData.experience_max}
                onChange={(e) => setFormData({ ...formData, experience_max: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Max Notice (Days)
              </label>
              <input
                type="number"
                value={formData.max_notice_period_days}
                onChange={(e) => setFormData({ ...formData, max_notice_period_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                CTC Range (LPA)
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="number"
                  placeholder="Min"
                  value={formData.ctc_min_lpa}
                  onChange={(e) => setFormData({ ...formData, ctc_min_lpa: parseFloat(e.target.value) })}
                  className="w-full px-2 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <span className="text-slate-400 text-xs">-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={formData.ctc_max_lpa}
                  onChange={(e) => setFormData({ ...formData, ctc_max_lpa: parseFloat(e.target.value) })}
                  className="w-full px-2 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Full Job Description Text *
            </label>
            <textarea
              required
              rows={5}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Paste the full job description here. Groq AI will analyze it to generate structured must-have and good-to-have scorecard criteria..."
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

