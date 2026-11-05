import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";

export const AppShell = () => {
  const [selectedReqId, setSelectedReqId] = useState(1);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content View */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopNav selectedReqId={selectedReqId} onSelectReq={setSelectedReqId} />
        
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet context={{ selectedReqId, setSelectedReqId }} />
        </main>
      </div>
    </div>
  );
};

