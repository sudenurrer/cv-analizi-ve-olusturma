#  CV Analiz ve Oluşturma Sistemi

##  Proje Hakkında
Bu proje, yazılım sektöründeki adayların (Frontend, Backend vb.) CV’lerini analiz ederek mevcut yetkinliklerini değerlendirir, 
eksik becerileri tespit eder ve somut gelişim önerileri sunar. Ayrıca kullanıcıların ATS uyumlu profesyonel CV oluşturmasını amaçlar.

##  Özellikler
-  CV Analizi 
-  Eksik becerilerin tespiti
-  ATS uyumluluk analizi
-  PDF formatında CV oluşturma
   
##  Kullanılan Teknolojiler
- Python
- FastAPI
- Visual Studio Code
- ReportLab / FPDF (PDF oluşturma)
- HTML, CSS, JavaScript


##  Çalışma Mantığı
Sistem, kullanıcı tarafından yüklenen CV içerisindeki metinleri analiz ederek:
- Mevcut teknik becerileri belirler
- Eksik veya geliştirilmesi gereken alanları tespit eder
- İlgili yazılım alanına göre öneriler sunar
- CV’nin doluluk oranını değerlendirir


##  Sistem Mimarisi
Proje, istemci-sunucu (client-server) mimarisi ile geliştirilmiştir.  
Frontend üzerinden alınan veriler, FastAPI backend’e gönderilir ve analiz sonuçları kullanıcıya sunulur.


##  Projenin Amacı
Adayların eksik yetkinliklerini fark etmelerini sağlamak ve iş başvuru süreçlerini daha etkili hale getirmek.

