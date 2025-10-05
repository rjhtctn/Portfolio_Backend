# 🚀 PortfolioApp Backend (FastAPI + SQLite)

**PortfolioApp Backend**, kullanıcıların kendi portfolyolarını yönetebildiği, e-posta doğrulama ve şifre sıfırlama destekli, admin paneline sahip, **FastAPI tabanlı** modern bir REST API projesidir.
Tamamen **modüler mimariyle** geliştirilmiş, genişletilebilir ve bakımı kolay bir backend altyapısı sunar.

---

## ✨ Özellikler

### 🔐 JWT Authentication

* Kullanıcı kaydı → `/auth/register`
* E-posta doğrulama → `/auth/verify-email`
* Giriş → `/auth/login`
* Şifre sıfırlama → `/auth/forgot-password`, `/auth/reset-password`
* Token üretiminde e-posta + kullanıcı adı harmanlama
* Doğrulanmamış kullanıcılar giriş yapamaz

### 👤 Kullanıcı İşlemleri (`/users`)

* Profil bilgilerini görüntüleme ve güncelleme
* E-posta değişikliğinde yeni doğrulama e-postası ve otomatik çıkış
* Hesap silme (e-posta onaylı)
* Silinen kullanıcıya ait tüm portfolyolar otomatik kaldırılır
* Silme sonrası bilgilendirme e-postası gönderilir

### 🛠 Admin Panel (`/admin`)

* Tüm kullanıcıları listeleme
* Kullanıcı ekleme / düzenleme / silme
* Kullanıcıya özel portfolyoları görüntüleme
* İstenilen portfolyoyu silme
* Kullanıcı silindiğinde tüm portfolyoları da silinir

### 💼 Portfolio Yönetimi (`/portfolios`)

* Portfolio ekleme / listeleme / düzenleme / silme
* Her kullanıcı yalnızca kendi portfolyolarını yönetebilir
* Admin tüm portfolyolar üzerinde tam yetkilidir

### 📧 Asenkron E-posta Gönderimi

* Doğrulama, şifre sıfırlama ve hesap silme onayı için e-postalar
* `BackgroundTasks` ile non-blocking e-posta gönderimi
* Gmail SMTP veya özel sunucu desteği

---

## ⚙️ Kurulum

### 1️⃣ Depoyu klonla

```bash
git clone https://github.com/rjhtctn/portfolio_backend.git
cd portfolio_backend
```

### 2️⃣ Gerekli paketleri yükle

```bash
pip install fastapi uvicorn sqlalchemy pydantic[email] bcrypt python-jose[cryptography] python-dotenv passlib aiosmtplib email-validator
```

### 3️⃣ `.env` dosyasını oluştur

Proje kök dizinine `.env` dosyasını ekle:

```env
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_URL=sqlite:///./portfolio.db

BASE_URL=http://127.0.0.1:8000

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@mail.com
SMTP_PASS=your_email_pass
SENDER_NAME=PortfolioApp
```

💡 *Gmail kullanıyorsan “Uygulama Şifresi” oluşturup `SMTP_PASS` alanına eklemeyi unutma.*

---

## 🧩 Proje Yapısı

```
portfolio_backend/
│
├── core/
│   ├── config.py           # Ortak ayarlar (.env yükleme)
│   ├── database.py         # SQLAlchemy & Session yönetimi
│   ├── security.py         # JWT, hash, verify fonksiyonları
│   └── dependencies.py     # Token doğrulama (get_current_user)
│
├── models/
│   ├── user.py             # User modeli
│   └── portfolio.py        # Portfolio modeli
│
├── schemas/
│   ├── user_schema.py      # Pydantic şemaları
│   └── portfolio_schema.py # Portfolio CRUD şemaları
│
├── routers/
│   ├── auth.py             # Auth işlemleri
│   ├── users.py            # Kullanıcı işlemleri
│   ├── admin.py            # Admin işlemleri
│   └── portfolios.py       # Portfolio işlemleri
│
├── helpers/
│   └── email_sender.py     # Asenkron e-posta gönderimi
│
├── main.py                 # FastAPI uygulama başlatıcısı
└── .env                    # Yapılandırma
```

---

## 🧠 API Örnekleri

### 🔐 Kayıt Ol

```http
POST /auth/register
{
  "first_name": "example",
  "last_name": "example",
  "username": "example",
  "email": "example@example.com",
  "password": "example"
}
```

### 🔑 Giriş Yap

```http
POST /auth/login
{
  "username_or_email": "example@example.com",
  "password": "example"
}
```

### 💼 Portfolio Ekle

```http
POST /portfolios/
Authorization: Bearer <token>
{
  "title": "My FastAPI Backend",
  "description": "JWT, Auth, CRUD system",
  "detail": "Full-featured backend built with FastAPI.",
  "link": "https://github.com/rjhtctn/portfolio_backend"
}
```

---

## 🧑‍💻 Admin Yetkileri

| İşlem                      | Route                              | Açıklama                                      |
| -------------------------- | ---------------------------------- | --------------------------------------------- |
| 👥 Kullanıcı Listele       | `/admin/users`                     | Tüm kullanıcıları getirir                     |
| ➕ Kullanıcı Ekle           | `/admin/users`                     | Yeni kullanıcı oluşturur                      |
| 📝 Kullanıcı Güncelle      | `/admin/users/{id}`                | Kullanıcı bilgilerini düzenler                |
| ❌ Kullanıcı Sil            | `/admin/users/{id}`                | Kullanıcı + portfolyolarını siler             |
| 📂 Kullanıcı Portfolyoları | `/admin/portfolios/{user_id}`      | Belirli kullanıcının portfolyolarını listeler |
| 🗑 Portfolio Sil           | `/admin/portfolios/{portfolio_id}` | Belirli bir portfolyoyu siler                 |

---

## 🧠 Kullanılan Teknolojiler

| Teknoloji                       | Açıklama                          |
| ------------------------------- | --------------------------------- |
| 🐍 **Python 3.13**              | Güncel ve güçlü dil sürümü        |
| ⚡ **FastAPI**                   | Hızlı ve modern backend framework |
| 💄 **SQLite + SQLAlchemy ORM**  | Hafif ama güçlü veri yönetimi     |
| 🧆 **Pydantic v2**              | Veri doğrulama ve şema yönetimi   |
| 🔒 **JWT Authentication**       | Güvenli oturum yönetimi           |
| 📧 **Async Email (aiosmtplib)** | Arka planda e-posta gönderimi     |
| 🥩 **Dependency Injection**     | Temiz ve test edilebilir yapı     |

---

**Topics:**
`fastapi` · `sqlite` · `jwt-auth` · `async-email` · `admin-dashboard` · `rest-api` · `backend` · `python`
