from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import secrets
from . import db
from .models import User, Design, Poll, PollOption, Vote, Comment, DesignCheckRequest, QRCode, Event, EventTicket
from .forms import RegistrationForm, LoginForm, EditProfileForm, DesignUploadForm, CreatePollForm, CommentForm, VoteForm, AddDesignsToPollForm, EventForm

# Blueprint'ler
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# Helper fonksiyonlar
def get_vote_weight(tier):
    """Tier'a göre oy ağırlığını hesapla"""
    if tier == 1:
        return 1
    elif tier == 2:
        return 3
    elif tier == 3:
        return 5
    else:
        return 0  # Tier 0 oy kullanamaz

def check_tier_upgrade(user):
    """Tier atlama kontrolü"""
    TIER_2_XP = 100
    TIER_3_XP = 500
    
    if user.tier == 1 and user.xp >= TIER_2_XP:
        user.tier = 2
        flash('Tebrikler! Tier 2\'ye yükseldiniz!', 'success')
    elif user.tier == 2 and user.xp >= TIER_3_XP:
        user.tier = 3
        flash('Tebrikler! Tier 3\'e yükseldiniz!', 'success')
    
    db.session.add(user)
    db.session.commit()

def allowed_file(filename):
    """Dosya uzantısı kontrolü"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ana sayfa route'ları
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/forum')
def forum():
    from datetime import datetime, date
    from flask import request
    
    # Filtreleme parametresi
    filter_type = request.args.get('filter', 'all')  # all, polls, events
    
    # Sayfalama parametresi
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    today = date.today()
    
    # Tüm içerikleri birleştir ve tarihe göre sırala
    all_items = []
    
    # Anketleri ekle
    if filter_type in ['all', 'polls', 'forum']:
        polls = Poll.query.filter_by(is_active=True).all()
        for poll in polls:
            poll.option_count = poll.options.count()
            poll.is_today = poll.created_at.date() == today
            
            # Eğer seçenek yoksa, bu bir forum postudur
            item_type = 'forum' if poll.option_count == 0 else 'poll'
            
            # Filtreleme kontrolü
            if filter_type == 'forum' and item_type != 'forum':
                continue
            if filter_type == 'polls' and item_type == 'forum':
                continue
            
            all_items.append({
                'type': item_type,
                'item': poll,
                'date': poll.created_at
            })
    
    # Etkinlikleri ekle
    if filter_type in ['all', 'events']:
        events = Event.query.filter_by(is_active=True).all()
        for event in events:
            # Kullanıcının bilet alıp almadığını kontrol et
            if current_user.is_authenticated:
                event.has_ticket = EventTicket.query.filter_by(event_id=event.id, user_id=current_user.id).first() is not None
            else:
                event.has_ticket = False
            all_items.append({
                'type': 'event',
                'item': event,
                'date': event.event_date
            })
    
    # Tarihe göre sırala (en yeni üstte)
    all_items.sort(key=lambda x: x['date'], reverse=True)
    
    # Pagination
    total_items = len(all_items)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = all_items[start:end]
    
    # Pagination bilgileri
    has_prev = page > 1
    has_next = end < total_items
    total_pages = (total_items + per_page - 1) // per_page
    
    return render_template('forum.html', 
                         items=paginated_items,
                         filter_type=filter_type,
                         page=page,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_pages=total_pages,
                         today=today)

@main_bp.route('/poll/<int:poll_id>', methods=['GET', 'POST'])
@login_required
def poll_detail(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Oy verme formu
    vote_form = VoteForm()
    vote_form.poll_option.choices = [(option.id, option.design.title) for option in poll.options]
    
    # Yorum formu
    comment_form = CommentForm()
    
    if request.method == 'POST':
        if 'vote' in request.form and vote_form.validate_on_submit():
            # Kullanıcının tier kontrolü
            if current_user.tier < 1:
                flash('Oy verebilmek için en az Tier 1 olmalısınız.', 'error')
                return redirect(url_for('main.poll_detail', poll_id=poll_id))
            
            # Daha önce oy kullanmış mı kontrolü
            existing_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll_id).first()
            if existing_vote:
                flash('Bu ankete zaten oy kullandınız.', 'error')
                return redirect(url_for('main.poll_detail', poll_id=poll_id))
            
            # Yeni oy oluştur
            weight = get_vote_weight(current_user.tier)
            vote = Vote(
                user_id=current_user.id,
                poll_id=poll_id,
                poll_option_id=vote_form.poll_option.data,
                weight=weight
            )
            
            db.session.add(vote)
            db.session.commit()
            
            # XP kazandır
            current_user.xp += 5
            check_tier_upgrade(current_user)
            
            flash('Oyunuz başarıyla kaydedildi!', 'success')
            return redirect(url_for('main.poll_detail', poll_id=poll_id))
        
        elif 'comment' in request.form and comment_form.validate_on_submit():
            comment = Comment(
                body=comment_form.body.data,
                user_id=current_user.id,
                poll_id=poll_id
            )
            
            db.session.add(comment)
            db.session.commit()
            
            # XP kazandır
            current_user.xp += 2
            check_tier_upgrade(current_user)
            
            flash('Yorumunuz eklendi!', 'success')
            return redirect(url_for('main.poll_detail', poll_id=poll_id))
    
    # Kullanıcının oy kullanıp kullanmadığını kontrol et
    user_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll_id).first()
    has_voted = user_vote is not None
    
    # Oylama sonuçlarını hesapla
    results = {}
    for option in poll.options:
        votes = option.votes.all()
        total_weight = sum(vote.weight for vote in votes)
        results[option.id] = {
            'design': option.design,
            'total_weight': total_weight,
            'vote_count': len(votes)
        }
    
    # Yorumları getir
    comments = Comment.query.filter_by(poll_id=poll_id).order_by(Comment.timestamp.desc()).all()
    
    # Seçenek sayısını kontrol et
    option_count = poll.options.count()
    is_forum_post = option_count == 0
    
    return render_template('poll_detail.html', 
                         poll=poll, 
                         vote_form=vote_form, 
                         comment_form=comment_form,
                         has_voted=has_voted,
                         results=results,
                         comments=comments,
                         is_forum_post=is_forum_post)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from .forms import EditProfileForm
    
    # Kullanıcı istatistiklerini hesapla
    current_user.design_count = current_user.designs.count()
    current_user.vote_count = current_user.votes.count()
    
    # Profil düzenleme formu
    form = EditProfileForm()
    if form.validate_on_submit():
        if current_user.tier < 1:
            flash('Profil düzenlemek için Tier 1 olmalısınız.', 'error')
            return redirect(url_for('main.profile'))
        
        current_user.bio = form.bio.data
        
        if form.profile_image.data:
            file = form.profile_image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = secrets.token_hex(8) + '_' + filename
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', unique_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                current_user.profile_image = unique_filename
        
        db.session.commit()
        flash('Profiliniz güncellendi!', 'success')
        return redirect(url_for('main.profile'))
    
    elif request.method == 'GET':
        form.bio.data = current_user.bio
    
    return render_template('profile.html', user=current_user, form=form)

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.tier < 1:
        abort(403)
    
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        
        if form.profile_image.data:
            file = form.profile_image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Benzersiz dosya adı oluştur
                unique_filename = secrets.token_hex(8) + '_' + filename
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', unique_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                current_user.profile_image = unique_filename
        
        db.session.commit()
        flash('Profiliniz güncellendi!', 'success')
        return redirect(url_for('main.profile'))
    
    elif request.method == 'GET':
        form.bio.data = current_user.bio
    
    return render_template('edit_profile.html', form=form)

@main_bp.route('/design/upload', methods=['GET', 'POST'])
@login_required
def upload_design():
    if current_user.tier < 2:
        abort(403)
    
    form = DesignUploadForm()
    if form.validate_on_submit():
        file = form.image.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = secrets.token_hex(8) + '_' + filename
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'designs', unique_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            design = Design(
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                image_path=unique_filename,
                user_id=current_user.id
            )
            
            db.session.add(design)
            db.session.commit()
            
            flash('Tasarımınız başarıyla yüklendi!', 'success')
            return redirect(url_for('main.profile'))
    
    return render_template('upload_design.html', form=form)

@main_bp.route('/poll/create', methods=['GET', 'POST'])
@login_required
def create_poll():
    if current_user.tier < 3:
        abort(403)
    
    form = CreatePollForm()
    if form.validate_on_submit():
        poll = Poll(
            title=form.title.data,
            description=form.description.data,
            created_by_user_id=current_user.id
        )
        
        db.session.add(poll)
        db.session.commit()
        
        flash('Anketiniz oluşturuldu! Şimdi tasarımları ekleyebilirsiniz.', 'success')
        return redirect(url_for('main.add_designs_to_poll', poll_id=poll.id))
    
    return render_template('create_poll.html', form=form)

@main_bp.route('/poll/<int:poll_id>/add-designs', methods=['GET', 'POST'])
@login_required
def add_designs_to_poll(poll_id):
    if current_user.tier < 3:
        abort(403)
    
    poll = Poll.query.get_or_404(poll_id)
    
    # Sadece anket oluşturan kişi tasarım ekleyebilir
    if poll.created_by_user_id != current_user.id:
        abort(403)
    
    # Mevcut tasarımları getir (kendi tasarımları + onaylanmış tasarımlar)
    available_designs = Design.query.filter(
        (Design.user_id == current_user.id) | 
        (Design.id.in_([req.requester_id for req in DesignCheckRequest.query.filter_by(
            approver_id=current_user.id, 
            status='approved'
        ).all()]))
    ).all()
    
    # Zaten ankete eklenmiş tasarımları filtrele
    existing_design_ids = [option.design_id for option in poll.options]
    available_designs = [d for d in available_designs if d.id not in existing_design_ids]
    
    form = AddDesignsToPollForm()
    form.designs.choices = [(design.id, f"{design.title} - {design.owner.username}") for design in available_designs]
    
    if form.validate_on_submit():
        design_id = form.designs.data
        design = Design.query.get(design_id)
        
        if design:
            # Tasarımı ankete ekle
            option = PollOption(
                poll_id=poll_id,
                design_id=design_id
            )
            db.session.add(option)
            db.session.commit()
            
            flash(f'{design.title} tasarımı ankete eklendi!', 'success')
            return redirect(url_for('main.add_designs_to_poll', poll_id=poll_id))
    
    # Ankete eklenmiş tasarımları getir
    added_designs = [option.design for option in poll.options]
    
    return render_template('add_designs_to_poll.html', 
                         poll=poll, 
                         form=form, 
                         added_designs=added_designs,
                         available_designs=available_designs)

# Kimlik doğrulama route'ları
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            tier=0,
            xp=0
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Geçersiz e-posta veya şifre.', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('main.index'))

# QR kod route'ları
@main_bp.route('/qr/<string:hash_id>')
def qr_scan(hash_id):
    qr = QRCode.query.filter_by(hash_id=hash_id).first()
    
    if not qr:
        flash('Geçersiz QR kod.', 'error')
        return render_template('qr_error.html')
    
    if qr.is_used:
        flash('Bu QR kod daha önce kullanılmış.', 'error')
        return render_template('qr_error.html')
    
    # Eğer kullanıcı giriş yapmamışsa, onay sayfasını göster
    if not current_user.is_authenticated:
        return render_template('qr_confirm.html', qr=qr, requires_login=True)
    
    # Giriş yapmışsa direkt onay sayfasını göster
    return render_template('qr_confirm.html', qr=qr, requires_login=False)

@main_bp.route('/qr/claim/<string:hash_id>', methods=['POST'])
@login_required
def qr_claim(hash_id):
    qr = QRCode.query.filter_by(hash_id=hash_id).first()
    
    if not qr or qr.is_used:
        flash('Geçersiz veya kullanılmış QR kod.', 'error')
        return redirect(url_for('main.index'))
    
    # QR kodunu kullanılmış olarak işaretle
    qr.is_used = True
    qr.used_by_user_id = current_user.id
    qr.used_at = db.func.now()
    
    # Tier/XP mantığı
    if current_user.tier == 0:
        current_user.tier = 1
        current_user.xp += qr.xp_value
        flash(f'Tebrikler! Tier 1\'e yükseldiniz ve {qr.xp_value} XP kazandınız!', 'success')
    else:
        current_user.xp += qr.xp_value
        flash(f'{qr.xp_value} XP kazandınız!', 'success')
    
    db.session.add(current_user)
    db.session.add(qr)
    db.session.commit()
    
    # Tier atlama kontrolü
    check_tier_upgrade(current_user)
    
    return redirect(url_for('main.profile'))

# Etkinlik route'ları
@main_bp.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    # Admin kontrolü
    if not current_user.is_admin:
        abort(403)
    
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            event_date=form.event_date.data,
            ticket_xp_reward=form.ticket_xp_reward.data,
            created_by_user_id=current_user.id
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Etkinlik başarıyla oluşturuldu!', 'success')
        return redirect(url_for('main.forum'))
    
    return render_template('create_event.html', form=form)

@main_bp.route('/event/<int:event_id>/buy-ticket', methods=['POST'])
@login_required
def buy_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Kullanıcının zaten bilet alıp almadığını kontrol et
    existing_ticket = EventTicket.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    if existing_ticket:
        flash('Bu etkinlik için zaten bilet aldınız!', 'error')
        return redirect(url_for('main.forum'))
    
    # Bilet numarası oluştur
    import random
    ticket_number = f"TKT-{event_id}-{current_user.id}-{random.randint(1000, 9999)}"
    
    # Bilet oluştur
    ticket = EventTicket(
        event_id=event_id,
        user_id=current_user.id,
        ticket_number=ticket_number
    )
    
    db.session.add(ticket)
    
    # XP kazandır
    current_user.xp += event.ticket_xp_reward
    
    db.session.add(current_user)
    db.session.commit()
    
    # Tier atlama kontrolü
    check_tier_upgrade(current_user)
    
    flash(f'Biletiniz kesildi! {event.ticket_xp_reward} XP kazandınız!', 'success')
    return redirect(url_for('main.forum'))

# Admin silme route'ları
@main_bp.route('/poll/<int:poll_id>/delete', methods=['POST'])
@login_required
def delete_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Admin kontrolü
    if not current_user.is_admin:
        abort(403)
    
    # Anketi sil
    db.session.delete(poll)
    db.session.commit()
    
    flash('Anket başarıyla silindi!', 'success')
    return redirect(url_for('main.forum'))

@main_bp.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Admin kontrolü
    if not current_user.is_admin:
        abort(403)
    
    # Etkinliği sil
    db.session.delete(event)
    db.session.commit()
    
    flash('Etkinlik başarıyla silindi!', 'success')
    return redirect(url_for('main.forum'))
