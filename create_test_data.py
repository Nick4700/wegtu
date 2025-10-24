from app import create_app, db
from app.models import User, Design, Poll, PollOption, QRCode
import secrets

app = create_app()

with app.app_context():
    # Veritabanını oluştur
    db.create_all()
    
    # Test kullanıcıları oluştur
    users = []
    
    # Admin kullanıcı (Tier 3)
    admin = User(
        username='admin',
        email='admin@wegtu.com',
        tier=3,
        xp=1000,
        bio='Sistem yöneticisi'
    )
    admin.set_password('admin123')
    users.append(admin)
    
    # Tier 2 kullanıcı
    designer = User(
        username='designer',
        email='designer@wegtu.com',
        tier=2,
        xp=200,
        bio='Tasarımcı'
    )
    designer.set_password('designer123')
    users.append(designer)
    
    # Tier 1 kullanıcı
    voter = User(
        username='voter',
        email='voter@wegtu.com',
        tier=1,
        xp=50,
        bio='Aktif oy kullanıcısı'
    )
    voter.set_password('voter123')
    users.append(voter)
    
    # Tier 0 kullanıcı
    newbie = User(
        username='newbie',
        email='newbie@wegtu.com',
        tier=0,
        xp=0,
        bio='Yeni kullanıcı'
    )
    newbie.set_password('newbie123')
    users.append(newbie)
    
    # Kullanıcıları veritabanına ekle
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    
    # Test tasarımları oluştur
    designs = []
    for i in range(3):
        design = Design(
            title=f'Test Tasarım {i+1}',
            description=f'Bu {i+1}. test tasarımıdır.',
            image_path=f'test_design_{i+1}.jpg',
            category='tshirt',
            user_id=designer.id
        )
        designs.append(design)
        db.session.add(design)
    
    db.session.commit()
    
    # Test anketi oluştur
    poll = Poll(
        title='En Beğenilen T-Shirt Tasarımı',
        description='Hangi t-shirt tasarımını daha çok beğeniyorsunuz?',
        created_by_user_id=admin.id
    )
    db.session.add(poll)
    db.session.flush()  # Poll ID'sini al
    
    # Anket seçenekleri
    for design in designs:
        option = PollOption(
            poll_id=poll.id,
            design_id=design.id
        )
        db.session.add(option)
    
    # Test QR kodları oluştur
    for i in range(10):
        qr = QRCode(
            hash_id=secrets.token_urlsafe(16),
            xp_value=10 + (i * 5)  # 10, 15, 20, 25, 30, 35, 40, 45, 50, 55 XP
        )
        db.session.add(qr)
    
    db.session.commit()
    
    print("Test verileri başarıyla oluşturuldu!")
    print("\nTest Kullanıcıları:")
    print("- admin / admin123 (Tier 3)")
    print("- designer / designer123 (Tier 2)")
    print("- voter / voter123 (Tier 1)")
    print("- newbie / newbie123 (Tier 0)")
    print("\nTest QR Kodları:")
    qr_codes = QRCode.query.filter_by(is_used=False).all()
    for qr in qr_codes[:5]:  # İlk 5 QR kodunu göster
        print(f"- /qr/{qr.hash_id} (+{qr.xp_value} XP)")
