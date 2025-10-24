from app import create_app, db
from app.models import QRCode
import secrets

app = create_app()

with app.app_context():
    # Yeni QR kodları oluştur
    qr_codes = []
    
    for i in range(5):  # 5 yeni QR kod oluştur
        qr = QRCode(
            hash_id=secrets.token_urlsafe(16),  # 16 karakter güvenli hash
            xp_value=20 + (i * 10)  # 20, 30, 40, 50, 60 XP
        )
        qr_codes.append(qr)
        db.session.add(qr)
    
    db.session.commit()
    
    print("Yeni QR kodları oluşturuldu:")
    for qr in qr_codes:
        print(f"- /qr/{qr.hash_id} (+{qr.xp_value} XP)")
