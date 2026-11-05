import React from "react";

export const Badge = ({ children, variant = "default", size = "sm", className = "" }) => {
  const variantStyles = {
    default: "bg-slate-100 text-slate-800 border-slate-200",
    primary: "bg-blue-50 text-blue-700 border-blue-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    purple: "bg-purple-50 text-purple-700 border-purple-200",
    high: "bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold",
    moderate: "bg-blue-50 text-blue-700 border-blue-200 font-semibold",
    low: "bg-slate-100 text-slate-600 border-slate-200 font-semibold",
  };

  const sizeStyles = {
    xs: "px-1.5 py-0.5 text-xs",
    sm: "px-2.5 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full border ${variantStyles[variant] || variantStyles.default} ${sizeStyles[size] || sizeStyles.sm} ${className}`}
    >
      {children}
    </span>
  );
};

export const ScoreBadge = ({ score, grade }) => {
  let variant = "low";
  if (score >= 80) variant = "high";
  else if (score >= 50) variant = "moderate";

  return (
    <div className="flex items-center gap-1.5">
      <Badge variant={variant} size="sm">
        <span className="font-bold">{score}</span>
        <span className="text-[10px] opacity-75">/100</span>
      </Badge>
      {grade && (
        <span className="text-xs text-slate-500 font-medium hidden sm:inline">
          {grade}
        </span>
      )}
    </div>
  );
};

