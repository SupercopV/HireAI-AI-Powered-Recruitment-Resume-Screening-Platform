import os
from PIL import Image, ImageDraw, ImageFont

def draw_rounded_rect(draw, coords, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def generate_architecture_diagram(output_path="docs/architecture_diagram.png"):
    width = 1600
    height = 1000
    img = Image.new("RGB", (width, height), color="#f8fafc")
    draw = ImageDraw.Draw(img)

    font_path = "C:\\Windows\\Fonts\\segoeui.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\segoeuib.ttf"
    if not os.path.exists(font_bold_path):
        font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"

    title_font = ImageFont.truetype(font_bold_path, 28)
    sub_font = ImageFont.truetype(font_path, 15)
    layer_title_font = ImageFont.truetype(font_bold_path, 17)
    box_title_font = ImageFont.truetype(font_bold_path, 14)
    box_body_font = ImageFont.truetype(font_path, 12)
    badge_font = ImageFont.truetype(font_bold_path, 11)

    # 1. Header Banner
    draw.rectangle([0, 0, width, 85], fill="#0f172a")
    draw.text((45, 18), "HireAI — High-Level System Architecture", font=title_font, fill="#ffffff")
    draw.text((45, 54), "Enterprise SaaS Recruitment Platform • React 19 + FastAPI + PostgreSQL + Groq LLM", font=sub_font, fill="#94a3b8")
    
    # Tag badge
    draw_rounded_rect(draw, (1380, 26, 1540, 58), 6, fill="#2563eb")
    draw.text((1402, 34), "PRODUCTION TDD", font=badge_font, fill="#ffffff")

    # Layer 1: Client Presentation Layer
    l1_top = 110
    draw_rounded_rect(draw, (40, l1_top, 1560, l1_top + 165), 10, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rectangle([40, l1_top, 1560, l1_top + 34], fill="#f1f5f9")
    draw.text((60, l1_top + 8), "1. PRESENTATION LAYER (React 19 + Vite + Tailwind CSS v4)", font=layer_title_font, fill="#1e293b")
    
    ui_boxes = [
        ("Recruiter Dashboard", "Requisition stats, weekly chart\nKPI metrics (Recharts, Lucide)", "#eff6ff", "#3b82f6"),
        ("Scorecard Editor", "AI JD parser & human edit\nConfigurable scoring weights", "#eff6ff", "#3b82f6"),
        ("Bulk CV Upload", "PDF, DOCX, XLSX, CSV\nBatch up to 500 & template download", "#eff6ff", "#3b82f6"),
        ("Candidate Ranking", "Deterministic match scores\nVerbatim CV evidence modal", "#eff6ff", "#3b82f6"),
        ("Client Portal", "Masked PII (anti-poaching)\nShortlist, reject with reason, interview", "#f0fdf4", "#16a34a"),
        ("Pipeline & Privacy", "11-stage Kanban drag/drop\nDPDP consent & erasure workflow", "#fef2f2", "#dc2626")
    ]
    box_w = 236
    spacing = 16
    start_x = 60
    for i, (title, desc, bg, border) in enumerate(ui_boxes):
        bx = start_x + i * (box_w + spacing)
        by = l1_top + 48
        draw_rounded_rect(draw, (bx, by, bx + box_w, by + 100), 8, fill=bg, outline=border, width=1)
        draw.text((bx + 12, by + 12), title, font=box_title_font, fill="#0f172a")
        draw.text((bx + 12, by + 38), desc, font=box_body_font, fill="#475569")

    # Connector Arrows Down
    for i in range(len(ui_boxes)):
        cx = start_x + i * (box_w + spacing) + box_w // 2
        draw.line([(cx, l1_top + 165), (cx, l1_top + 195)], fill="#94a3b8", width=2)
        draw.polygon([(cx - 4, l1_top + 190), (cx + 4, l1_top + 190), (cx, l1_top + 195)], fill="#64748b")

    # Layer 2: API Gateway & Security Layer
    l2_top = 305
    draw_rounded_rect(draw, (40, l2_top, 1560, l2_top + 130), 10, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rectangle([40, l2_top, 1560, l2_top + 34], fill="#f1f5f9")
    draw.text((60, l2_top + 8), "2. API GATEWAY & SECURITY LAYER (FastAPI + Pydantic v2)", font=layer_title_font, fill="#1e293b")

    gw_boxes = [
        ("REST Endpoints (11 Routers)", "/auth, /requisitions, /scorecards,\n/resumes, /candidates, /scoring, /pipeline", "#f8fafc", "#cbd5e1"),
        ("JWT Auth & Security", "HS256 tokens, bcrypt (12 rounds)\nRole tokens & secure cookie headers", "#f8fafc", "#cbd5e1"),
        ("Role-Based Access Control", "Recruiter vs Client Manager RBAC\nStrict tenant data isolation middleware", "#f8fafc", "#cbd5e1"),
        ("Audit & Validation", "Pydantic v2 strict schemas\nImmutable audit logging per mutation", "#f8fafc", "#cbd5e1")
    ]
    gw_w = 358
    gw_spacing = 18
    for i, (title, desc, bg, border) in enumerate(gw_boxes):
        bx = start_x + i * (gw_w + gw_spacing)
        by = l2_top + 46
        draw_rounded_rect(draw, (bx, by, bx + gw_w, by + 70), 8, fill=bg, outline=border, width=1)
        draw.text((bx + 14, by + 10), title, font=box_title_font, fill="#0f172a")
        draw.text((bx + 14, by + 32), desc, font=box_body_font, fill="#475569")

    # Connector Arrows Down
    for i in range(len(gw_boxes)):
        cx = start_x + i * (gw_w + gw_spacing) + gw_w // 2
        draw.line([(cx, l2_top + 130), (cx, l2_top + 160)], fill="#94a3b8", width=2)
        draw.polygon([(cx - 4, l2_top + 155), (cx + 4, l2_top + 155), (cx, l2_top + 160)], fill="#64748b")

    # Layer 3: Core Application & AI Engines
    l3_top = 465
    draw_rounded_rect(draw, (40, l3_top, 1560, l3_top + 225), 10, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rectangle([40, l3_top, 1560, l3_top + 34], fill="#f1f5f9")
    draw.text((60, l3_top + 8), "3. CORE INTELLIGENCE & BUSINESS LOGIC ENGINES", font=layer_title_font, fill="#1e293b")

    engine_boxes = [
        ("Groq AI Engine", "llama-3.3-70b-versatile\n• JD criteria extraction\n• Resume entity parsing\n• Offline deterministic fallback\n• Sub-second response latency", "#f5f3ff", "#8b5cf6"),
        ("Parsing & OCR Engine", "PyMuPDF (PDF) + python-docx (DOCX)\n• Tesseract OCR fallback for scanned CVs\n• openpyxl & CSV batch spreadsheet parser\n• File sanitization & SHA-256 deduplication", "#f0fdfa", "#14b8a6"),
        ("Deterministic Scoring (0–100)", "Python Arithmetic Calculation\n• Required Skills: 40 pts\n• Total Experience: 25 pts\n• Relevant Domain Exp: 15 pts\n• Good-to-have: 10 pts • Notice: 10 pts", "#fffbeb", "#f59e0b"),
        ("Verbatim Evidence Engine", "Evidence Extraction from Raw CV Text\n• Exact supporting sentence quotation\n• Zero fabricated quotations\n• Explicit 'Evidence not found' if absent\n• Strict non-rejection policy (AI ranks only)", "#eff6ff", "#2563eb"),
        ("Privacy & Consent Engine", "India DPDP Act 2023 Principles\n• Contact PII masking on client views\n• Consent purpose limitation & timestamping\n• Right-to-Erasure automated anonymization\n• Permanent disk file wipe on deletion", "#fdf2f8", "#ec4899")
    ]
    eng_w = 286
    eng_spacing = 16
    for i, (title, desc, bg, border) in enumerate(engine_boxes):
        bx = start_x + i * (eng_w + eng_spacing)
        by = l3_top + 46
        draw_rounded_rect(draw, (bx, by, bx + eng_w, by + 165), 8, fill=bg, outline=border, width=1)
        draw.text((bx + 12, by + 10), title, font=box_title_font, fill="#0f172a")
        draw.text((bx + 12, by + 34), desc, font=box_body_font, fill="#334155")

    # Connector Arrows Down
    for i in range(len(engine_boxes)):
        cx = start_x + i * (eng_w + eng_spacing) + eng_w // 2
        draw.line([(cx, l3_top + 225), (cx, l3_top + 255)], fill="#94a3b8", width=2)
        draw.polygon([(cx - 4, l3_top + 250), (cx + 4, l3_top + 250), (cx, l3_top + 255)], fill="#64748b")

    # Layer 4: Persistence Layer
    l4_top = 720
    draw_rounded_rect(draw, (40, l4_top, 1560, l4_top + 220), 10, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rectangle([40, l4_top, 1560, l4_top + 34], fill="#f1f5f9")
    draw.text((60, l4_top + 8), "4. DATA PERSISTENCE & STORAGE TIER", font=layer_title_font, fill="#1e293b")

    db_boxes = [
        ("PostgreSQL Database (16 Normalized Tables)", 
         "• Identity: users, organizations, audit_logs\n• Jobs: requisitions, job_scorecards\n• Candidates: candidates, resumes, upload_batches\n• Evaluation: candidate_scores, score_evidence", 
         "#f8fafc", "#4169e1"),
        ("Client Interactions & Pipeline State", 
         "• Submissions: client_submissions, client_feedbacks\n• Interviews: interviews (proposals & status)\n• Audit Trail: candidate_pipeline_histories (11 stages)\n• DPDP: candidate_consents, deletion_requests", 
         "#f8fafc", "#4169e1"),
        ("Alembic Migration & Cloud Compatibility", 
         "• Version-controlled DB schema migrations\n• Compatible with local PostgreSQL 14–18, Render PostgreSQL, Supabase, Neon Serverless\n• pool_pre_ping=True for resilient connection lifecycle", 
         "#f8fafc", "#0284c7"),
        ("Secure File Vault (Local / Object Store)", 
         "• Structured directory layout: uploads/req_{id}/\n• File extension & MIME type validation\n• SHA-256 integrity checks against tampering\n• Automated physical purge on DPDP erasure request", 
         "#f8fafc", "#059669")
    ]
    db_w = 358
    for i, (title, desc, bg, border) in enumerate(db_boxes):
        bx = start_x + i * (db_w + gw_spacing)
        by = l4_top + 46
        draw_rounded_rect(draw, (bx, by, bx + db_w, by + 155), 8, fill=bg, outline=border, width=1)
        draw.text((bx + 14, by + 10), title, font=box_title_font, fill="#0f172a")
        draw.text((bx + 14, by + 34), desc, font=box_body_font, fill="#334155")

    # Footer note
    draw.text((45, 960), "HireAI Architecture • Explaining deterministic scoring, verbatim CV quotation, RBAC isolation, and India DPDP Act 2023 alignment", font=sub_font, fill="#64748b")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Architecture diagram generated successfully at {output_path}")

if __name__ == "__main__":
    generate_architecture_diagram()

