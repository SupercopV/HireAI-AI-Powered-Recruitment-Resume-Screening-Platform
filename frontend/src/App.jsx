import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { AppShell } from "./components/layout/AppShell";

// Pages
import { Login } from "./pages/Login";
import { RecruiterDashboard } from "./pages/RecruiterDashboard";
import { RequisitionList } from "./pages/RequisitionList";
import { JobScorecardEditor } from "./pages/JobScorecardEditor";
import { BulkResumeUpload } from "./pages/BulkResumeUpload";
import { CandidateRanking } from "./pages/CandidateRanking";
import { ClientPortal } from "./pages/ClientPortal";
import { RecruitmentPipeline } from "./pages/RecruitmentPipeline";
import { CandidatePrivacy } from "./pages/CandidatePrivacy";
import { AuditLogs } from "./pages/AuditLogs";

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 text-slate-400 text-xs font-semibold">
        Verifying HireAI security session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // If client tries to access recruiter route, redirect to client portal
    if (user?.role === "client_hiring_manager") {
      return <Navigate to="/client/portal" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

const RootRedirect = () => {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return user?.role === "client_hiring_manager" ? (
    <Navigate to="/client/portal" replace />
  ) : (
    <Navigate to="/dashboard" replace />
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />

            {/* Authenticated Dashboard Shell */}
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<RootRedirect />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <RecruiterDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/requisitions"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <RequisitionList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/scorecards"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <JobScorecardEditor />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/upload"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <BulkResumeUpload />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidates"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <CandidateRanking />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/pipeline"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <RecruitmentPipeline />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/client/portal"
                element={
                  <ProtectedRoute allowedRoles={["client_hiring_manager", "recruiter", "admin"]}>
                    <ClientPortal />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/client/interviews"
                element={
                  <ProtectedRoute allowedRoles={["client_hiring_manager", "recruiter", "admin"]}>
                    <ClientPortal />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/privacy"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <CandidatePrivacy />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/audit-logs"
                element={
                  <ProtectedRoute allowedRoles={["recruiter", "admin"]}>
                    <AuditLogs />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}

