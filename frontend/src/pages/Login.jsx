import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight, Shield, User, Building, Lock } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Button } from "../components/ui/Button";

export const Login = () => {
  const [email, setEmail] = useState("recruiter@hireai.com");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.full_name}!`);
      if (user.role === "client_hiring_manager") {
        navigate("/client/portal");
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      toast.error(
        err.response?.data?.detail || "Authentication failed. Please verify credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (role) => {
    if (role === "recruiter") {
      setEmail("recruiter@hireai.com");
      setPassword("password123");
    } else {
      setEmail("client.hiring@fintechcorp.com");
      setPassword("password123");
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-500/25 mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            HireAI
          </h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">
            Smarter Hiring. Faster Shortlists. Fairer Decisions.
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xl p-8">
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Work Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full mt-2"
              icon={ArrowRight}
            >
              Sign In to Platform
            </Button>
          </form>

          {/* Demo Accounts Quick-Select */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-3">
              One-Click Demo Credentials
            </p>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => fillDemoAccount("recruiter")}
                className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 text-xs font-medium text-slate-700 transition-all text-left cursor-pointer"
              >
                <User className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="truncate">
                  <p className="font-semibold truncate">Recruiter</p>
                  <p className="text-[10px] text-slate-400">Sarah Jenkins</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount("client")}
                className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-800 text-xs font-medium text-slate-700 transition-all text-left cursor-pointer"
              >
                <Building className="w-4 h-4 text-amber-600 shrink-0" />
                <div className="truncate">
                  <p className="font-semibold truncate">Client Manager</p>
                  <p className="text-[10px] text-slate-400">Rajesh Khanna</p>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Security & DPDP Compliance Footer */}
        <div className="flex items-center justify-center gap-2 text-xs text-slate-400 mt-6">
          <Shield className="w-3.5 h-3.5 text-slate-400" />
          <span>Role-Based Access Control • DPDP 2023 Compliant</span>
        </div>
      </div>
    </div>
  );
};

