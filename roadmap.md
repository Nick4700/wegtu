Harika bir proje fikri. Belirttiğiniz teknolojiler (Flask, SQLAlchemy, SQLite, Jinja2) bu ölçekte bir proje için oldukça uygun. İşte bu giyim firması sitesi için talep ettiğiniz sırayı ve teknolojileri baz alarak hazırladığım detaylı roadmap:

-----

### Giyim Firması Tasarım Oylama Platformu: Geliştirme Yol Haritası

Bu roadmap, projenin temel kurulumundan başlayarak belirttiğiniz özelliklerin (Kayıt, Oylama, Forum, Tier, QR) Flask ve SQLAlchemy kullanarak adım adım nasıl inşa edileceğini açıklamaktadır.

#### Faz 0: Proje Kurulumu ve Çevre Ayarları

Kod yazmaya başlamadan önce temeli atmalıyız.

1.  **Sanal Ortam (Virtual Environment) Oluşturma:**
      * `python -m venv venv`
      * `source venv/bin/activate` (Linux/Mac) veya `venv\Scripts\activate` (Windows)
2.  **Gerekli Kütüphanelerin Kurulumu:**
      * `pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Werkzeug`
      * **Flask-Login:** Kullanıcı oturumlarını (giriş yapma, çıkış yapma) yönetmek için kritik öneme sahip.
      * **Flask-WTF:** Kayıt ve giriş formlarını güvenli bir şekilde (CSRF koruması dahil) oluşturmak ve doğrulamak için.
      * **Werkzeug:** Parola hashleme (`generate_password_hash`, `check_password_hash`) için kullanılacak.
3.  **Proje Yapısını Oluşturma:**
    ```
    /proje_klasoru
        /app
            /static
                /css
                /js
                /img
            /templates
                base.html
                index.html
                login.html
                register.html
            __init__.py     # Flask app fabrika fonksiyonu
            models.py       # SQLAlchemy modelleri
            routes.py       # Flask view/route'ları
            forms.py        # Flask-WTF formları
            config.py       # Konfigürasyon (DATABASE_URI, SECRET_KEY)
        run.py              # Uygulamayı başlatan dosya
        venv/               # Sanal ortam
    ```
4.  **Temel Veritabanı Modellerinin Tanımlanması (`app/models.py`):**
      * Bu aşamada sadece **Kullanıcı (User)** modelini tanımlayacağız.
    <!-- end list -->
    ```python
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import UserMixin
    from werkzeug.security import generate_password_hash, check_password_hash
    from . import db # __init__.py'dan import edilecek

    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), index=True, unique=True)
        email = db.Column(db.String(120), index=True, unique=True)
        password_hash = db.Column(db.String(256))
        
        # Tier Sistemi için temel alanlar
        tier = db.Column(db.Integer, default=0) # Tier 0: Aktif değil
        xp = db.Column(db.Integer, default=0)
        
        # Profil bilgileri (Tier 1'de açılacak)
        bio = db.Column(db.Text, nullable=True)
        profile_image = db.Column(db.String(120), nullable=True, default='default.jpg')

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)
    ```

-----

### Faz 1: Kayıt Ol - Giriş Yap (Kullanıcı Yönetimi)

**Hedef:** Kullanıcıların hesap oluşturmasını ve giriş yapmasını sağlamak.

1.  **Formların Oluşturulması (`app/forms.py`):**
      * `RegistrationForm` (Username, Email, Password, Confirm Password) oluşturun. `WTForms` kullanarak doğrulama (validation) kuralları (örn: `DataRequired`, `Email`, `EqualTo`) ekleyin.
      * `LoginForm` (Email/Username, Password, Remember Me) oluşturun.
2.  **Route'ların (URL) Tanımlanması (`app/routes.py`):**
      * **`/register` (GET, POST):**
          * `GET`: Kayıt formunu (`register.html`) göster.
          * `POST`: Formu doğrula. E-posta/kullanıcı adı zaten var mı diye DB'yi kontrol et. Yoksa, parolayı `set_password` ile hash'le, yeni `User` nesnesi oluştur (Tier=0 olarak), DB'ye kaydet (`db.session.add()`, `db.session.commit()`). Kullanıcıyı giriş sayfasına yönlendir.
      * **`/login` (GET, POST):**
          * `GET`: Giriş formunu (`login.html`) göster.
          * `POST`: Formu doğrula. Kullanıcıyı DB'de bul. Parolayı `check_password` ile kontrol et. Doğruysa `flask_login`'in `login_user(user)` fonksiyonunu kullanarak oturumu başlat.
      * **`/logout`:**
          * `logout_user()` fonksiyonunu çağır ve anasayfaya yönlendir.
      * **`/profile`:**
          * `@login_required` decorator'ı kullanarak sadece giriş yapmış kullanıcıların görmesini sağla. `current_user` objesini kullanarak temel profil bilgilerini (`profile.html`) göster.
3.  **Template'lerin (Jinja2) Oluşturulması (`app/templates/`):**
      * `base.html`: Tüm sayfalarda ortak olacak navigasyon (Giriş/Kayıt/Profil linkleri), başlık ve alt bilgileri içerir.
      * `register.html`, `login.html`: `Flask-WTF` ile oluşturulan formları Jinja2 kullanarak render et.
      * `profile.html`: `{{ current_user.username }}` gibi Jinja tag'leri ile kullanıcının bilgilerini göster.

-----

### Faz 2: Oylama Sistemi

**Hedef:** Tasarımların oylanabileceği bir sistem kurmak (Başlangıçta Admin tarafından oluşturulan, ileride Tier 3 tarafından).

*Not: Henüz tasarım yükleme (Tier 2) ve Admin paneli yok. Bu aşamada, oylama mekaniğini test etmek için veritabanına **manuel** olarak birkaç tasarım ve oylama (anket) ekleyeceğiz.*

1.  **Yeni Veritabanı Modelleri (`app/models.py`):**
    ```python
    # ... User modelinden sonra ...
    class Design(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100))
        image_path = db.Column(db.String(200)) # Yüklenecek resmin yolu
        user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Tasarımcı (Tier 2+)
        owner = db.relationship('User', backref='designs')

    class Poll(db.Model): # Oylama / Anket
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(150))
        is_active = db.Column(db.Boolean, default=True)
        # Oylamayı başlatan (Admin veya Tier 3)
        created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    class PollOption(db.Model): # Anketteki seçenekler (Tasarımlar)
        id = db.Column(db.Integer, primary_key=True)
        poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
        design_id = db.Column(db.Integer, db.ForeignKey('design.id'))
        poll = db.relationship('Poll', backref=db.backref('options', lazy='dynamic'))
        design = db.relationship('Design')

    class Vote(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        poll_option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'))
        # Oy ağırlığı, o anki tier'a göre kaydedilecek
        weight = db.Column(db.Integer, default=1) 
    ```
2.  **Oylama Mantığı (`app/routes.py`):**
      * **Test Verisi:** Flask shell (`flask shell`) kullanarak manuel 2-3 `User` (farklı tier'larda), 2-3 `Design` ve 1 `Poll` (bu tasarımları içeren `PollOption`'lar ile) oluşturun.
      * **Helper Fonksiyon (Oy Ağırlığı):**
        ```python
        def get_vote_weight(tier):
            if tier == 1: return 1
            if tier == 2: return 3
            if tier == 3: return 5
            return 0 # Tier 0 oy kullanamaz
        ```
      * **Route (`/poll/<int:poll_id>` (GET, POST)):**
          * `@login_required`
          * `GET`: `Poll` ve ilişkili `PollOption`'ları (ve `Design` detaylarını) DB'den çek. `poll.html` template'ine gönder.
          * `POST`:
            1.  Kullanıcının `current_user.tier < 1` olup olmadığını kontrol et. (Tier 0 oy veremez).
            2.  Kullanıcının bu `poll_id` için daha önce oy kullanıp kullanmadığını (`Vote` tablosunu) kontrol et.
            3.  Formdan gelen `poll_option_id`'yi al.
            4.  `weight = get_vote_weight(current_user.tier)` ile oy ağırlığını hesapla.
            5.  Yeni `Vote` nesnesi oluştur (`user_id`, `poll_option_id`, `weight`) ve DB'ye kaydet.
            6.  Sonuçlar sayfasına veya foruma yönlendir.
3.  **Template (`poll.html`):**
      * Anket başlığını ve `for` döngüsü içinde anket seçeneklerini (tasarım resimleri, başlıkları) göster.
      * Oy vermek için `radio` butonları içeren bir `<form>` oluştur.

-----

### Faz 3: Forum

**Hedef:** Oylamaların (Anketlerin) listelendiği ve tartışılabileceği bir alan oluşturmak.

1.  **Yeni Veritabanı Modeli (`app/models.py`):**
      * (Opsiyonel, ancak önerilir) Oylamalara yorum yapmak için:
    <!-- end list -->
    ```python
    class Comment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        body = db.Column(db.Text)
        timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    ```
2.  **Route'lar (`app/routes.py`):**
      * **`/forum` (GET):**
          * Tüm aktif `Poll`'ları (oylamaları) DB'den çek (örn: `Poll.query.filter_by(is_active=True).all()`).
          * `forum.html` template'ine bu listeyi gönder.
      * **`/forum/poll/<int:poll_id>` (GET, POST):**
          * Bu, Faz 2'deki `/poll/<int:poll_id>` rotasıyla birleştirilebilir.
          * `GET`: Oylama detaylarına ek olarak, bu `poll_id`'ye ait `Comment`'ları da DB'den çek ve template'e gönder.
          * `POST`: Gelen isteğin "oy verme" mi yoksa "yorum yapma" mı olduğunu kontrol et.
              * Yorum ise: Yeni `Comment` nesnesi oluştur, DB'ye kaydet ve sayfayı yenile.
3.  **Template'ler (`forum.html`, `poll.html` - Güncelleme):**
      * `forum.html`: `for` döngüsü ile tüm anketleri (`Poll`) listele. Her birine tıklandığında `/forum/poll/<id>`'ye link ver.
      * `poll.html`: Oylama mekanizmasının altına yorum yapma formu ve mevcut yorumların listesini ekle.

-----

### Faz 4: Tier Atlama Sistemi

**Hedef:** Kullanıcıların QR okutarak (Tier 1) ve XP kazanarak (Tier 2, 3) seviye atlamasını sağlamak.

1.  **Tier 1: Profil Düzenleme ve Aktivasyon**

      * *Aktivasyon kısmı Faz 5 (QR) ile entegre çalışacak.*
      * **Form (`app/forms.py`):**
          * `EditProfileForm` (Bio, Profile Image Upload, İletişim Bilgisi vb.)
      * **Route (`app/routes.py`):**
          * **`/profile/edit` (GET, POST):**
              * `@login_required`
              * `if current_user.tier < 1: abort(403)` (Sadece Tier 1+ düzenleyebilir).
              * `GET`: `EditProfileForm`'u `current_user` bilgileriyle doldurarak göster.
              * `POST`: Formu doğrula, `current_user` nesnesinin `bio`, `profile_image` vb. alanlarını güncelle ve DB'ye kaydet. (Resim yükleme için dosya kaydetme mantığı eklenmeli).

2.  **Tier 2: XP & Tasarım Yükleme**

      * **XP Mantığı:** XP kazandıran eylemlere (oy kullanma, yorum yapma, QR okutma) XP eklemesi entegre edilmeli.
      * **Tier Yükseltme Fonksiyonu (Helper):**
        ```python
        # app/utils.py (veya benzeri bir yardımcı dosya)
        TIER_2_XP = 100
        TIER_3_XP = 500

        def check_tier_upgrade(user):
            if user.tier == 1 and user.xp >= TIER_2_XP:
                user.tier = 2
                # Belki bir bildirim eklenebilir
            elif user.tier == 2 and user.xp >= TIER_3_XP:
                user.tier = 3
            db.session.add(user)
            db.session.commit()
        ```
        *Bu fonksiyon, XP kazandıran her işlemden sonra çağrılmalı (örn: Faz 5'teki QR okutma).*
      * **Tasarım Yükleme Formu (`app/forms.py`):**
          * `DesignUploadForm` (Title, Description, Image File, Category - Kategori için `SelectField` kullanılabilir).
      * **Route (`app/routes.py`):**
          * **`/design/upload` (GET, POST):**
              * `@login_required`
              * `if current_user.tier < 2: abort(403)` (Sadece Tier 2+ yükleyebilir).
              * `GET`: `DesignUploadForm`'u göster.
              * `POST`: Formu doğrula. Resim dosyasını al, güvenli bir isimle `static/uploads/designs` klasörüne kaydet.
              * Yeni `Design` nesnesi oluştur (title, `image_path` (kaydedilen yol), `user_id=current_user.id`, `category`). DB'ye kaydet.

3.  **Tier 3: Oylama Başlatma ve İstek Sistemi**

      * **Yeni Veritabanı Modeli (`app/models.py`):**
        ```python
        class DesignCheckRequest(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            requester_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Tier 2
            approver_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Tier 3
            status = db.Column(db.String(20), default='pending') # pending, approved
        ```
      * **Route'lar (`app/routes.py`):**
          * **`/user/<username>` (Public Profile):**
              * Kullanıcıyı `username`'e göre bul. `user_profile.html`'i render et.
              * **Template'de (`user_profile.html`):** Eğer `current_user.tier == 2` ve `görüntülenen_user.tier == 3` ise "Check my designs" butonunu göster.
          * **`/request_check/<int:tier3_user_id>` (POST):**
              * `@login_required`
              * `if current_user.tier != 2: abort(403)`
              * Yeni `DesignCheckRequest` oluştur (requester=current\_user, approver=tier3\_user\_id). DB'ye kaydet.
          * **`/poll/create` (GET, POST):**
              * `@login_required`
              * `if current_user.tier < 3: abort(403)`
              * `GET`: Oylama oluşturma formu (`create_poll.html`) göster. Bu formda, kullanıcının *kendi tasarımlarını* ve `DesignCheckRequest` ile onay aldığı *Tier 2 kullanıcılarının tasarımlarını* seçebileceği bir liste olmalı.
              * `POST`: Formdan (Anket Başlığı, Kategori, Seçilen Tasarımlar) bilgileri al.
              * Yeni `Poll` nesnesi oluştur (`created_by_user_id=current_user.id`).
              * Seçilen her tasarım için `PollOption` nesneleri oluştur ve `Poll`'a bağla.
              * DB'ye kaydet. Bu oylama otomatik olarak `/forum`'a düşmüş olacak.

-----

### Faz 5: QR Sistemi

**Hedef:** QR kod okutarak (belirli bir URL'e giderek) hesabın Tier 1'e yükseltilmesi ve XP kazanılması.

1.  **Yeni Veritabanı Modeli (`app/models.py`):**

    ```python
    class QRCode(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # /qr/xyz123abc -> Bu 'xyz123abc' kısmı (hash veya unique id)
        hash_id = db.Column(db.String(100), unique=True, index=True) 
        xp_value = db.Column(db.Integer, default=10) # QR'ın kazandıracağı XP
        is_used = db.Column(db.Boolean, default=False)
        used_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ```

    *Not: Bu `QRCode` tablosunu (içindeki `hash_id`'ler ile) sizin önceden doldurmanız gerekir (örn: bir script ile 1000 tane unique hash üretip DB'ye basmak).*

2.  **Route'lar (`app/routes.py`):**

      * **`/qr/<string:hash_id>` (GET):**
          * `@login_required` (Bu decorator, kullanıcı giriş yapmamışsa onu otomatik olarak `/login`'e yönlendirir ve giriş yaptıktan sonra bu sayfaya geri getirir).
          * 1.  `hash_id`'yi kullanarak `QRCode`'yi DB'de ara.
          * 2.  Bulamazsan veya `qr.is_used == True` ise: Hata sayfası göster (`qr_error.html` - "Geçersiz veya kullanılmış QR").
          * 3.  Bulunursa ve kullanılmamışsa: Onay sayfası göster (`qr_confirm.html`). "Bu ürünü hesabınıza tanımlamak istiyor musunuz? (+{qr.xp\_value} XP)"
      * **`/qr/claim/<string:hash_id>` (POST):**
          * `@login_required`
          * 1.  `QRCode`'yi `hash_id` ile tekrar bul ve `is_used` kontrolü yap (güvenlik için).
          * 2.  `qr.is_used = True` ve `qr.used_by_user_id = current_user.id` olarak güncelle.
          * 3.  Kullanıcıyı al: `user = current_user`
          * 4.  **Tier/XP Mantığı:**
            <!-- end list -->
              * `if user.tier == 0:`
                  * `user.tier = 1` \# Tier 1'e yükselt\!
                  * `user.xp += qr.xp_value`
                  * `db.session.add(user)`
                  * `db.session.add(qr)`
                  * `db.session.commit()`
              * `elif user.tier >= 1:`
                  * `user.xp += qr.xp_value`
                  * `db.session.add(user)`
                  * `db.session.add(qr)`
                  * `db.session.commit()`
          * 5.  Tier atlama kontrolünü çağır: `check_tier_upgrade(user)` (Faz 4'te tanımladığımız fonksiyon).
          * 6.  Kullanıcıyı "Başarılı\!" mesajıyla profiline yönlendir.

3.  **Template'ler (`qr_confirm.html`, `qr_error.html`):**

      * `qr_confirm.html`: `hash_id`'yi gizli bir alan olarak içeren ve `/qr/claim/<hash_id>` adresine POST yapan bir "Onayla" butonu.
      * `qr_error.html`: Hata mesajını gösteren basit bir sayfa.

-----

### Veritabanı Modelleri (Özet)

Proje sonunda `app/models.py` dosyanızda şu modeller olacak:

1.  `User` (Kullanıcı bilgileri, tier, xp, parola)
2.  `Design` (Tasarım bilgileri, resim yolu, sahibi)
3.  `Poll` (Oylama/Anket başlığı, durumu)
4.  `PollOption` (Oylamayı tasarıma bağlayan ara tablo)
5.  `Vote` (Kim, kime, hangi ağırlıkta oy verdi)
6.  `Comment` (Foruma/Oylamalara yapılan yorumlar)
7.  `DesignCheckRequest` (Tier 2 -\> Tier 3 tasarım inceleme isteği)
8.  `QRCode` (Fiziksel ürünlerdeki kodların veritabanı karşılığı)