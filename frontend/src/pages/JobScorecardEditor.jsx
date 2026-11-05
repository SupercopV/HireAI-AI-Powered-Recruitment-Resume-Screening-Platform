import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Sparkles,
  CheckCircle2,
  Sliders,
  Plus,
  Trash2,
  FileSpreadsheet,
  AlertCircle,
  Save,
  Check
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { CardSkeleton } from "../components/ui/LoadingSkeleton";

export const JobScorecardEditor = () => {
  const { selectedReqId } = useOutletContext() || { selectedReqId: 1 };
  const [requisition, setRequisition] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  // Scorecard editable fields
  const [mustHaveSkills, setMustHaveSkills] = useState([]);
  const [goodToHaveSkills, setGoodToHaveSkills] = useState([]);
  const [minExp, setMinExp] = useState(5.0);
  const [maxExp, setMaxExp] = useState(8.0);
  const [location, setLocation] = useState("Noida");
  const [maxNotice, setMaxNotice] = useState(60);
  const [ctcInfo, setCtcInfo] = useState("");
  const [weights, setWeights] = useState({
    required_skills: 40.0,
    experience_match: 25.0,
    relevant_experience: 15.0,
    good_to_have_skills: 10.0,
    notice_period: 10.0,
  });
  const [isApproved, setIsApproved] = useState(false);

  // Input tag helpers
  const [newMustHave, setNewMustHave] = useState("");
  const [newGoodToHave, setNewGoodToHave] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const reqRes = await api.get(`/requisitions/${selectedReqId}`);
      setRequisition(reqRes.data);

      try {
        const cardRes = await api.get(`/requisitions/${selectedReqId}/scorecard`);
        const c = cardRes.data;
        setScorecard(c);
        setMustHaveSkills(c.must_have_skills || []);
        setGoodToHaveSkills(c.good_to_have_skills || []);
        setMinExp(c.min_experience || 0.0);
        setMaxExp(c.max_experience || 10.0);
        setLocation(c.location || "Noida");
        setMaxNotice(c.max_notice_period || 60);
        setCtcInfo(c.ctc_info || "");
        setWeights(c.weights || {
          required_skills: 40.0,
          experience_match: 25.0,
          relevant_experience: 15.0,
          good_to_have_skills: 10.0,
          notice_period: 10.0,
        });
        setIsApproved(c.is_approved || false);
      } catch (err) {
        console.log("No existing scorecard, initialized default");
      }
    } catch (err) {
      toast.error("Failed to load requisition data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedReqId) loadData();
  }, [selectedReqId]);

  const handleAIAnalyze = async () => {
    if (!requisition?.description) {
      toast.warning("Requisition has no job description text to analyze");
      return;
    }
    setAnalyzing(true);
    try {
      const res = await api.post(`/requisitions/${selectedReqId}/analyze-jd`, {
        job_description_text: requisition.description,
        job_title: requisition.title,
      });
      const data = res.data;
      setMustHaveSkills(data.must_have_skills || []);
      setGoodToHaveSkills(data.good_to_have_skills || []);
      setMinExp(data.min_experience || minExp);
      setMaxExp(data.max_experience || maxExp);
      setLocation(data.location || location);
      setMaxNotice(data.max_notice_period || maxNotice);
      setCtcInfo(data.ctc_info || ctcInfo);
      setIsApproved(false);
      toast.success(
        "Groq AI extracted scorecard criteria! Review and adjust below before approving."
      );
    } catch (err) {
      toast.error(err.response?.data?.detail || "AI analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSaveScorecard = async (approveStatus = false) => {
    const totalWeight = Object.values(weights).reduce((a, b) => a + Number(b), 0);
    if (Math.round(totalWeight) !== 100) {
      toast.warning(`Total weights must sum exactly to 100 points (Current: ${totalWeight})`);
      return;
    }

    setSaving(true);
    try {
      const payload = {
        must_have_skills: mustHaveSkills,
        good_to_have_skills: goodToHaveSkills,
        min_experience: minExp,
        max_experience: maxExp,
        location,
        max_notice_period: maxNotice,
        ctc_info: ctcInfo,
        weights,
        is_approved: approveStatus,
      };
      const res = await api.put(`/requisitions/${selectedReqId}/scorecard`, payload);
      setScorecard(res.data);
      setIsApproved(res.data.is_approved);
      toast.success(
        approveStatus
          ? "Scorecard approved and locked for candidate ranking!"
          : "Scorecard draft saved successfully!"
      );
    } catch (err) {
      toast.error("Failed to save scorecard");
    } finally {
      setSaving(false);
    }
  };

  const addMustHave = () => {
    if (newMustHave.trim() && !mustHaveSkills.includes(newMustHave.trim())) {
      setMustHaveSkills([...mustHaveSkills, newMustHave.trim()]);
      setNewMustHave("");
    }
  };

  const addGoodToHave = () => {
    if (newGoodToHave.trim() && !goodToHaveSkills.includes(newGoodToHave.trim())) {
      setGoodToHaveSkills([...goodToHaveSkills, newGoodToHave.trim()]);
      setNewGoodToHave("");
    }
  };

  if (loading) return <CardSkeleton />;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Job Description Scorecard
            </h1>
            <Badge variant={isApproved ? "success" : "warning"} size="xs">
              {isApproved ? `v${scorecard?.version || 1} Approved` : "Draft / Needs Review"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Role: <span className="font-semibold text-slate-700">{requisition?.title}</span> (
            {requisition?.requisition_code}) • Base: {requisition?.location}
          </p>
        </div>

        {/* AI Extraction & Save Actions */}
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            loading={analyzing}
            icon={Sparkles}
            onClick={handleAIAnalyze}
          >
            Extract Criteria via Groq AI
          </Button>
          <Button
            variant="primary"
            size="sm"
            loading={saving}
            icon={Check}
            onClick={() => handleSaveScorecard(true)}
          >
            Approve Scorecard
          </Button>
        </div>
      </div>

      {/* Human-in-the-loop Notification Banner */}
      <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/60 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-900 leading-relaxed">
          <p className="font-semibold">Human-in-the-Loop AI Verification Guarantee</p>
          <p className="mt-0.5 opacity-90">
            AI extracts requirements directly from the job description text into structured JSON.
            Recruiters must verify and edit criteria before saving. Scoring is computed deterministically
            in Python based on approved weights.
          </p>
        </div>
      </div>

      {/* Scorecard Editor Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Skills & Experience */}
        <div className="lg:col-span-2 space-y-6">
          {/* Must-Have Skills Card */}
          <Card>
            <CardHeader
              title="Must-Have Required Skills (Weight: 40 pts)"
              subtitle="Mandatory qualifications. Candidates missing these will receive lower skill match scores."
            />
            <div className="mt-4">
              <div className="flex flex-wrap gap-2 mb-3">
                {mustHaveSkills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-200 text-blue-800 rounded-lg text-xs font-semibold"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => setMustHaveSkills(mustHaveSkills.filter((_, i) => i !== idx))}
                      className="text-blue-400 hover:text-blue-700 cursor-pointer"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newMustHave}
                  onChange={(e) => setNewMustHave(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addMustHave())}
                  placeholder="Type a required skill (e.g. Spring Boot) and press Enter..."
                  className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <Button variant="secondary" size="sm" icon={Plus} onClick={addMustHave}>
                  Add
                </Button>
              </div>
            </div>
          </Card>

          {/* Good-To-Have Skills Card */}
          <Card>
            <CardHeader
              title="Good-to-Have Secondary Skills (Weight: 10 pts)"
              subtitle="Bonus qualifications that elevate candidate ranking."
            />
            <div className="mt-4">
              <div className="flex flex-wrap gap-2 mb-3">
                {goodToHaveSkills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 border border-slate-200 text-slate-800 rounded-lg text-xs font-medium"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => setGoodToHaveSkills(goodToHaveSkills.filter((_, i) => i !== idx))}
                      className="text-slate-400 hover:text-slate-700 cursor-pointer"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newGoodToHave}
                  onChange={(e) => setNewGoodToHave(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addGoodToHave())}
                  placeholder="Type a secondary skill (e.g. Kafka) and press Enter..."
                  className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <Button variant="secondary" size="sm" icon={Plus} onClick={addGoodToHave}>
                  Add
                </Button>
              </div>
            </div>
          </Card>

          {/* Experience & Notice Details */}
          <Card>
            <CardHeader
              title="Experience & Logistics Match Criteria"
              subtitle="Numerical thresholds for deterministic evaluation."
            />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase mb-1">
                  Min Exp (Yrs)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={minExp}
                  onChange={(e) => setMinExp(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase mb-1">
                  Max Exp (Yrs)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={maxExp}
                  onChange={(e) => setMaxExp(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase mb-1">
                  Max Notice (Days)
                </label>
                <input
                  type="number"
                  value={maxNotice}
                  onChange={(e) => setMaxNotice(parseInt(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase mb-1">
                  CTC Budget
                </label>
                <input
                  type="text"
                  value={ctcInfo}
                  onChange={(e) => setCtcInfo(e.target.value)}
                  placeholder="e.g. 18-28 LPA"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Configurable Scoring Weights */}
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Scoring Weights (Total: 100)"
              subtitle="Configurable distribution for deterministic scoring."
            />
            <div className="space-y-4 mt-4">
              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-700">Required Skills</span>
                  <span className="font-bold text-blue-600">{weights.required_skills} pts</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="60"
                  value={weights.required_skills}
                  onChange={(e) =>
                    setWeights({ ...weights, required_skills: parseFloat(e.target.value) })
                  }
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-700">Total Experience Match</span>
                  <span className="font-bold text-blue-600">{weights.experience_match} pts</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="40"
                  value={weights.experience_match}
                  onChange={(e) =>
                    setWeights({ ...weights, experience_match: parseFloat(e.target.value) })
                  }
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-700">Relevant Domain Exp</span>
                  <span className="font-bold text-blue-600">{weights.relevant_experience} pts</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={weights.relevant_experience}
                  onChange={(e) =>
                    setWeights({ ...weights, relevant_experience: parseFloat(e.target.value) })
                  }
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-700">Good-to-Have Skills</span>
                  <span className="font-bold text-blue-600">{weights.good_to_have_skills} pts</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={weights.good_to_have_skills}
                  onChange={(e) =>
                    setWeights({ ...weights, good_to_have_skills: parseFloat(e.target.value) })
                  }
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-700">Notice Period Fit</span>
                  <span className="font-bold text-blue-600">{weights.notice_period} pts</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={weights.notice_period}
                  onChange={(e) =>
                    setWeights({ ...weights, notice_period: parseFloat(e.target.value) })
                  }
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold">
                <span>Total Score Weight</span>
                <span
                  className={
                    Math.round(Object.values(weights).reduce((a, b) => a + Number(b), 0)) === 100
                      ? "text-emerald-600"
                      : "text-rose-600"
                  }
                >
                  {Object.values(weights).reduce((a, b) => a + Number(b), 0)} / 100
                </span>
              </div>
            </div>
          </Card>

          {/* Save Draft Button */}
          <Button
            variant="outline"
            size="md"
            className="w-full"
            loading={saving}
            icon={Save}
            onClick={() => handleSaveScorecard(false)}
          >
            Save Scorecard Draft
          </Button>
        </div>
      </div>
    </div>
  );
};

