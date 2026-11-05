import React, { useState, useRef } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Copy,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  Users,
  FileSpreadsheet,
  Download
} from "lucide-react";
import api from "../services/api";
import { useToast } from "../context/ToastContext";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

export const BulkResumeUpload = () => {
  const { selectedReqId } = useOutletContext() || { selectedReqId: 1 };
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [retrying, setRetrying] = useState(false);
  const fileInputRef = useRef(null);
  const toast = useToast();
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (files) => {
    const validExtensions = ["pdf", "docx", "doc", "xlsx", "xls", "csv"];
    const validFiles = files.filter((f) => {
      const ext = f.name.toLowerCase().split(".").pop();
      return validExtensions.includes(ext);
    });

    if (validFiles.length < files.length) {
      toast.warning("Some files were skipped. Only PDF, DOCX, XLSX, and CSV files are supported.");
    }

    if (validFiles.length > 500) {
      toast.error("Maximum 500 CVs allowed per upload batch.");
      setSelectedFiles(validFiles.slice(0, 500));
    } else {
      setSelectedFiles(validFiles);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const res = await api.get("/upload-batches/template/excel", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "hireai_candidate_batch_template.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel template downloaded!");
    } catch (err) {
      toast.error("Failed to download template");
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.warning("Please select at least one CV file to upload");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const res = await api.post(`/requisitions/${selectedReqId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBatchResult(res.data);
      toast.success(
        `Batch ${res.data.batch_code} processed: ${res.data.parsed_count} parsed, ${res.data.duplicate_count} duplicates detected.`
      );
      setSelectedFiles([]);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Resume upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleRetryFailed = async () => {
    if (!batchResult?.id) return;
    setRetrying(true);
    try {
      const res = await api.post(`/upload-batches/${batchResult.id}/retry`);
      setBatchResult(res.data);
      toast.success("Retried failed files in batch");
    } catch (err) {
      toast.error("Retry failed");
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Bulk Resume & Spreadsheet Ingestion
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingest candidates via PDF/DOCX resumes or Excel/CSV spreadsheets. Max 500 CVs per batch.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            icon={Download}
            onClick={handleDownloadTemplate}
          >
            Download Excel Template
          </Button>
          {batchResult && (
            <Button
              variant="primary"
              size="sm"
              icon={ArrowRight}
              onClick={() => navigate("/candidates")}
            >
              View AI Shortlists
            </Button>
          )}
        </div>
      </div>

      {/* Drag and Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? "border-blue-500 bg-blue-50/60 scale-[1.005]"
            : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.xlsx,.xls,.csv"
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="w-14 h-14 mx-auto rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-xs">
          <UploadCloud className="w-7 h-7" />
        </div>
        <h3 className="text-sm font-semibold text-slate-900">
          Drop resume files or Excel spreadsheet here or click to browse
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Supports PDF, DOCX, and Excel spreadsheets (.xlsx, .csv). Upload up to 500 CVs per batch.
        </p>

        {selectedFiles.length > 0 && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-full text-xs font-semibold text-blue-700">
            <FileText className="w-4 h-4" />
            <span>{selectedFiles.length} files selected and ready to parse</span>
          </div>
        )}
      </div>

      {/* Upload Button */}
      {selectedFiles.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200">
          <div className="text-xs text-slate-600">
            <span className="font-semibold text-slate-900">{selectedFiles.length} CVs</span> queued for
            extraction and deterministic scoring.
          </div>
          <Button
            variant="primary"
            size="md"
            loading={uploading}
            icon={UploadCloud}
            onClick={handleUpload}
          >
            Process & Score Batch
          </Button>
        </div>
      )}

      {/* Batch Processing Results Summary */}
      {batchResult && (
        <Card className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  Batch Status: {batchResult.batch_code}
                </h3>
                <Badge variant="success" size="xs">
                  {batchResult.status}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Total files: {batchResult.total_files} | Processed: {batchResult.parsed_count}
              </p>
            </div>
            {batchResult.failed_count > 0 && (
              <Button
                variant="outline"
                size="xs"
                loading={retrying}
                icon={RefreshCw}
                onClick={handleRetryFailed}
              >
                Retry Failed Files ({batchResult.failed_count})
              </Button>
            )}
          </div>

          {/* KPI Mini-Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
              <span className="text-[10px] font-bold text-emerald-800 uppercase">Parsed & Scored</span>
              <p className="text-xl font-bold text-emerald-700 mt-1">{batchResult.parsed_count}</p>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
              <span className="text-[10px] font-bold text-amber-800 uppercase">Duplicate CVs</span>
              <p className="text-xl font-bold text-amber-700 mt-1">{batchResult.duplicate_count}</p>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
              <span className="text-[10px] font-bold text-rose-800 uppercase">Failed Extraction</span>
              <p className="text-xl font-bold text-rose-700 mt-1">{batchResult.failed_count}</p>
            </div>
          </div>

          {/* Files List Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-y border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">File Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">OCR Applied</th>
                  <th className="py-2.5 px-3">Details / Errors</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(batchResult.resumes || []).map((res) => (
                  <tr key={res.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-800 truncate max-w-xs">
                      {res.file_name}
                    </td>
                    <td className="py-2.5 px-3 uppercase text-slate-500 font-mono text-[10px]">
                      {res.file_type}
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge
                        variant={
                          res.parsing_status === "parsed"
                            ? "success"
                            : res.parsing_status === "duplicate"
                            ? "warning"
                            : "danger"
                        }
                        size="xs"
                      >
                        {res.parsing_status}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {res.ocr_applied ? "Yes (Tesseract)" : "No (Direct PyMuPDF/docx)"}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 truncate max-w-xs">
                      {res.parsing_error || "Parsed and candidate profile indexed"}
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

