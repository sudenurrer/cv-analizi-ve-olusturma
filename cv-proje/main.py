from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import uuid, os, re, tempfile, threading

app = FastAPI(title="CV Analiz API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


PRIMARY_FONT = "Helvetica"
BOLD_FONT    = "Helvetica-Bold"

def _setup_turkish_font():
    global PRIMARY_FONT, BOLD_FONT

    import matplotlib as _mpl
    mpl_ttf_dir = os.path.join(os.path.dirname(_mpl.__file__), "mpl-data", "fonts", "ttf")

    candidates = [
        
        (os.path.join(mpl_ttf_dir, "DejaVuSans.ttf"),
         os.path.join(mpl_ttf_dir, "DejaVuSans-Bold.ttf")),
        
        ("C:\\Windows\\Fonts\\arial.ttf",
         "C:\\Windows\\Fonts\\arialbd.ttf"),
        
        ("/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/Library/Fonts/Arial.ttf",
         "/Library/Fonts/Arial Bold.ttf"),
        
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/opt/homebrew/share/fonts/dejavu-fonts-ttf/DejaVuSans.ttf",
         "/opt/homebrew/share/fonts/dejavu-fonts-ttf/DejaVuSans-Bold.ttf"),
    ]

    for reg_path, bold_path in candidates:
        if not os.path.exists(reg_path):
            continue
        try:
            pdfmetrics.registerFont(TTFont("TR-Regular", reg_path))
            PRIMARY_FONT = "TR-Regular"
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont("TR-Bold", bold_path))
                BOLD_FONT = "TR-Bold"
            else:
                BOLD_FONT = "TR-Regular"
            print(f"[Font] OK: {reg_path}")
            return
        except Exception as e:
            print(f"[Font] Atlandı ({reg_path}): {e}")

    print("[Font] UYARI: Türkçe destekli font bulunamadı, Helvetica kullanılıyor.")

_setup_turkish_font()



roles = {
    "Backend Gelistirici":        ["python", "java", "node", "api", "sql", "django", "flask", "fastapi", "docker", "postgresql", "redis", "mongodb", "c#", "dotnet"],
    "Frontend Gelistirici":       ["html", "css", "javascript", "react", "vue", "angular", "typescript", "tailwind", "sass", "nextjs", "redux", "webpack"],
    "Veri Bilimci":               ["python", "machine learning", "pandas", "numpy", "sql", "tensorflow", "pytorch", "scikit-learn", "deep learning", "nlp", "statistics"],
    "DevOps Muhendisi":           ["docker", "kubernetes", "linux", "aws", "azure", "git", "ci", "cd", "jenkins", "terraform", "ansible", "nginx"],
    "AI Muhendisi":               ["python", "tensorflow", "pytorch", "keras", "opencv", "computer vision", "llm", "bert", "gpt", "neural networks"],
    "Siber Guvenlik Uzmani":      ["linux", "network", "firewall", "penetration testing", "wireshark", "metasploit", "cryptography", "soc", "siem"],
    "Mobil Uygulama Gelistirici": ["swift", "kotlin", "flutter", "react native", "dart", "android studio", "xcode", "firebase", "ios", "android"],
    "Veri Analisti":              ["sql", "excel", "power bi", "tableau", "python", "data visualization", "statistics", "reporting", "looker"],
    "QA Test Muhendisi":          ["selenium", "cypress", "appium", "junit", "pytest", "test automation", "postman", "qa", "jira"],
    "Oyun Gelistirici":           ["c#", "c++", "unity", "unreal engine", "directx", "shaders", "3d modeling", "game design", "blender"],
}


role_display = {
    "Backend Gelistirici":        "Backend Geliştirici",
    "Frontend Gelistirici":       "Frontend Geliştirici",
    "Veri Bilimci":               "Veri Bilimci",
    "DevOps Muhendisi":           "DevOps Mühendisi",
    "AI Muhendisi":               "AI Mühendisi",
    "Siber Guvenlik Uzmani":      "Siber Güvenlik Uzmanı",
    "Mobil Uygulama Gelistirici": "Mobil Uygulama Geliştirici",
    "Veri Analisti":              "Veri Analisti",
    "QA Test Muhendisi":          "QA Test Mühendisi",
    "Oyun Gelistirici":           "Oyun Geliştirici",
}

report_storage: dict = {}
storage_lock = threading.Lock()
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def safe_remove(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def safe_text(text: str) -> str:
    """Font TR-Regular yüklüyse metni olduğu gibi döndür.
    Helvetica fallback'teyse Türkçe harfleri ASCII'ye çevir."""
    if PRIMARY_FONT != "Helvetica":
        return text
    table = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(table)



#  PDF RAPOR ÇİZİMİ

def draw_styled_report(c, data, w, h):
    T = safe_text  

    c.setFillColor(colors.HexColor("#0f1e2a"))
    c.rect(0, h - 120, w, 120, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(BOLD_FONT, 20)
    c.drawString(50, h - 55, T("KARİYER ANALİZ VE GELİŞİM RAPORU"))
    c.setFont(PRIMARY_FONT, 9)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawString(50, h - 75, f"Rapor ID: {data['report_id']}")

    # ATS Kartı
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.roundRect(50, h - 220, 240, 80, 10, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont(BOLD_FONT, 10)
    c.drawString(70, h - 160, T("ATS UYUMLULUK SKORU"))
    score_color = colors.HexColor("#10b981") if data['ats_score'] > 60 else colors.red
    c.setFillColor(score_color)
    c.setFont(BOLD_FONT, 28)
    c.drawString(70, h - 200, f"%{data['ats_score']}")

    # Rol Kartı
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.roundRect(305, h - 220, 240, 80, 10, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont(BOLD_FONT, 10)
    c.drawString(325, h - 160, T("EN UYGUN ROL"))
    c.setFillColor(colors.HexColor("#101356"))
    c.setFont(BOLD_FONT, 14)
    c.drawString(325, h - 195, T(role_display.get(data['best_role'], data['best_role'])))
    c.setFont(PRIMARY_FONT, 11)
    c.drawString(325, h - 212, f"Uyum: %{data['best_score']}")

    # Teknik Yetkinlikler
    y = h - 270
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont(BOLD_FONT, 14)
    c.drawString(50, y, T("TEKNİK YETKİNLİKLER"))
    c.line(50, y - 5, 200, y - 5)

    y -= 50
    c.setFillColor(colors.HexColor("#ecfdf5"))
    c.roundRect(50, y - 40, 500, 55, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#065f46"))
    c.setFont(BOLD_FONT, 10)
    c.drawString(65, y, T("MEVCUT BECERİLER"))
    c.setFont(PRIMARY_FONT, 9)
    found_text = ", ".join(data['found_skills']).upper() if data['found_skills'] else T("Eşleşen yetenek bulunamadı.")
    c.drawString(65, y - 20, found_text[:95] + ("..." if len(found_text) > 95 else ""))

    y -= 80
    c.setFillColor(colors.HexColor("#fef2f2"))
    c.roundRect(50, y - 60, 500, 75, 5, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#991b1b"))
    c.setFont(BOLD_FONT, 11)
    c.drawString(65, y, T("EKSİK YETENEKLER"))
    c.setFont(PRIMARY_FONT, 10)
    missing_text = ", ".join(data['missing_skills']).upper() if data['missing_skills'] else T("Tüm kriterler karşılanıyor!")
    if len(missing_text) > 85:
        c.drawString(65, y - 20, missing_text[:85])
        c.drawString(65, y - 35, missing_text[85:170])
    else:
        c.drawString(65, y - 20, missing_text)

    if data.get('temp_img') and os.path.exists(data['temp_img']):
        c.drawImage(data['temp_img'], 50, h - 760, width=500, height=230)

    y2 = h - 800
    c.setFont(BOLD_FONT, 11)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawString(50, y2, T("TÜM ROL UYUM SKORLARI"))
    c.line(50, y2 - 4, 220, y2 - 4)
    y2 -= 20
    c.setFont(PRIMARY_FONT, 9)
    for role, score in sorted(data['role_scores'].items(), key=lambda x: x[1], reverse=True):
        bar_w = int(score * 2.5)
        bar_color = colors.HexColor("#0f1e2a") if role == data['best_role'] else colors.HexColor("#cbd5e1")
        c.setFillColor(bar_color)
        c.rect(180, y2 - 2, bar_w, 10, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(50, y2, T(role_display.get(role, role)))
        c.drawString(185 + bar_w, y2, f"%{score}")
        y2 -= 18



#  CV PDF ÇİZİMİ

class CVData(BaseModel):
    name: str
    email: str
    phone: str
    summary: str
    experience: List[str]
    education: List[str]
    skills: List[str]
    projects: List[str]


def draw_cv_pdf(c, data: CVData, w, h):
    T = safe_text
    y = h - 50

    c.setFillColor(colors.HexColor("#000000"))
    c.setFont(BOLD_FONT, 22)
    c.drawCentredString(w / 2, y, T(data.name.upper()))

    y -= 25
    c.setFillColor(colors.black)
    c.setFont(PRIMARY_FONT, 10)
    c.drawCentredString(w / 2, y, f"{data.email} | {data.phone}")

    y -= 15
    c.setStrokeColor(colors.HexColor("#0f1e2a"))
    c.setLineWidth(1.5)
    c.line(50, y, w - 50, y)
    c.setLineWidth(1)

    def draw_section(title, items, current_y):
        current_y -= 25
        c.setFillColor(colors.HexColor("#0f1e2a"))
        c.setFont(BOLD_FONT, 12)
        c.drawString(50, current_y, T(title.upper()))
        current_y -= 4
        c.setStrokeColor(colors.HexColor("#0f1e2a"))
        c.line(50, current_y, w - 50, current_y)
        current_y -= 16
        c.setFillColor(colors.black)
        c.setFont(PRIMARY_FONT, 10)

        if isinstance(items, str):
            words = items.split(' ')
            line = ''
            for word in words:
                test = (line + ' ' + word).strip()
                if c.stringWidth(test, PRIMARY_FONT, 10) < (w - 100):
                    line = test
                else:
                    c.drawString(60, current_y, T(line))
                    current_y -= 14
                    line = word
            if line:
                c.drawString(60, current_y, T(line))
                current_y -= 14
        else:
            for item in items:
                display = f"• {T(item)}"
                if c.stringWidth(display, PRIMARY_FONT, 10) < (w - 110):
                    c.drawString(60, current_y, display)
                    current_y -= 16
                else:
                    c.drawString(60, current_y, display[:90])
                    current_y -= 14
                    c.drawString(70, current_y, display[90:180])
                    current_y -= 16
        return current_y

    y = draw_section(T("Özet"),       data.summary,    y)
    y = draw_section(T("Eğitim"),     data.education,  y)
    y = draw_section(T("Deneyim"),    data.experience, y)
    y = draw_section(T("Projeler"),   data.projects,   y)
    y = draw_section(T("Yetenekler"), data.skills,     y)



#   CV ANALİZİ

@app.post("/analyze")
async def analyze_cv(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yüklenebilir.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Dosya boyutu 5 MB'ı geçemez.")

    temp_img = None
    report_path = None

    try:
        text = ""
        with fitz.open(stream=content, filetype="pdf") as pdf:
            for page in pdf:
                text += page.get_text()
        text_lower = text.lower()

        role_scores = {
            r: round((len([s for s in sk if s in text_lower]) / len(sk)) * 100)
            for r, sk in roles.items()
        }
        best_role      = max(role_scores, key=role_scores.get)
        best_score     = role_scores[best_role]
        found_skills   = [s for s in roles[best_role] if s in text_lower]
        missing_skills = [s for s in roles[best_role] if s not in text_lower]

        keyword_score = best_score * 0.5
        has_email    = 15 if re.search(r'[\w.-]+@[\w.-]+\.\w+', text) else 0
        has_phone    = 10 if re.search(r'(\+?\d[\d\s\-]{7,})', text) else 0
        has_year     = 10 if re.search(r'\b(20\d{2}|19\d{2})\b', text) else 0
        has_linkedin = 10 if 'linkedin' in text_lower else 0
        has_github   =  5 if 'github'   in text_lower else 0
        ats_score = min(round(keyword_score + has_email + has_phone + has_year + has_linkedin + has_github), 100)

        report_id = str(uuid.uuid4())
        temp_img  = os.path.join(tempfile.gettempdir(), f"temp_{report_id}.png")

        sorted_scores = dict(sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:6])
        fig, ax = plt.subplots(figsize=(7, 4), facecolor='#f8fafc')
        bar_colors = ["#0A0436" if r == best_role else '#94a3b8' for r in sorted_scores]
        labels = [role_display.get(r, r) for r in sorted_scores.keys()]
        ax.barh(labels, list(sorted_scores.values()), color=bar_colors)
        ax.set_title('Pozisyon Uyumluluk Analizi (%)', fontsize=11, fontweight='bold', pad=12)
        ax.set_xlim(0, 100)
        ax.set_facecolor('#f8fafc')
        plt.tight_layout()
        plt.savefig(temp_img, format='png', dpi=150, facecolor='#f8fafc')
        plt.close(fig)

        report_path = os.path.join(tempfile.gettempdir(), f"report_{report_id}.pdf")
        c = canvas.Canvas(report_path, pagesize=A4)
        draw_styled_report(c, {
            "report_id":      report_id[:8].upper(),
            "best_role":      best_role,
            "best_score":     best_score,
            "ats_score":      ats_score,
            "found_skills":   found_skills,
            "missing_skills": missing_skills,
            "temp_img":       temp_img,
            "role_scores":    role_scores,
        }, A4[0], A4[1])
        c.save()
        safe_remove(temp_img)

        with storage_lock:
            report_storage[report_id] = report_path

        
        return {
            "best_role":      role_display.get(best_role, best_role),
            "best_score":     best_score,
            "ats_score":      ats_score,
            "found_skills":   found_skills,
            "missing_skills": missing_skills,
            "report_id":      report_id,
            "role_scores":    {role_display.get(k, k): v for k, v in role_scores.items()},
        }

    except HTTPException:
        raise
    except Exception as e:
        safe_remove(temp_img)
        safe_remove(report_path)
        return JSONResponse(status_code=500, content={"error": str(e)})



#  RAPOR İNDİR
@app.get("/download-report/{report_id}")
async def download_report(report_id: str):
    with storage_lock:
        path = report_storage.get(report_id)
    if path and os.path.exists(path):
        return FileResponse(path, filename="Kariyer_Analiz_Raporu.pdf", media_type='application/pdf')
    raise HTTPException(status_code=404, detail="Rapor bulunamadı veya süresi doldu.")



# CV OLUŞTUR
@app.post("/generate-cv")
async def generate_cv(data: CVData):
    if not data.name.strip() or not data.email.strip():
        raise HTTPException(status_code=400, detail="İsim ve e-posta zorunludur.")
    cv_path = None
    try:
        cv_path = os.path.join(tempfile.gettempdir(), f"cv_{uuid.uuid4()}.pdf")
        c = canvas.Canvas(cv_path, pagesize=A4)
        draw_cv_pdf(c, data, A4[0], A4[1])
        c.save()
        safe_name = re.sub(r'[^\w\s-]', '', data.name).strip().replace(' ', '_')
        return FileResponse(cv_path, filename=f"{safe_name}_CV.pdf", media_type='application/pdf')
    except Exception as e:
        safe_remove(cv_path)
        return JSONResponse(status_code=500, content={"error": str(e)})
