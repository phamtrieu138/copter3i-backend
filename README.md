# Copter3i JIG Backend API

Backend Python (FastAPI) cho JIG kiểm tra quạt Copter3i.  
Nhận kết quả FCT từ C# app → lưu vào MySQL trên VPN server.

## Endpoints

| Method | URL | Mô tả |
|--------|-----|-------|
| GET | `/api/health` | Kiểm tra trạng thái server + DB |
| POST | `/api/fct/insert` | Insert batch 6 boards |
| POST | `/api/fct/insert-single` | Insert 1 board |
| GET | `/api/fct/records` | Lấy danh sách records |
| GET | `/api/fct/stats` | Thống kê OK/NG |

## Cài đặt

```bash
# Clone về VPN server
git clone https://github.com/<your-username>/copter3i-backend.git
cd copter3i-backend

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài packages
pip install -r requirements.txt

# Cấu hình database
cp .env.example .env
nano .env   # Điền thông tin MySQL
```

## Cấu hình `.env`

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=Copter_3i
DB_USER=copter_user
DB_PASSWORD=your_strong_password
```

## Chạy

```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Swagger UI

Truy cập `http://<VPN_IP>:8000/docs` để test API trực tiếp trên browser.
