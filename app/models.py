from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Tier Sistemi için temel alanlar
    tier = db.Column(db.Integer, default=0)  # Tier 0: Aktif değil
    xp = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)  # Admin kontrolü
    
    # Profil bilgileri (Tier 1'de açılacak)
    bio = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(120), nullable=True, default='default.jpg')
    
    # İlişkiler
    designs = db.relationship('Design', backref='owner', lazy='dynamic')
    votes = db.relationship('Vote', backref='voter', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    created_polls = db.relationship('Poll', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # İlişkiler
    poll_options = db.relationship('PollOption', backref='design', lazy='dynamic')
    
    def __repr__(self):
        return f'<Design {self.title}>'

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # İlişkiler
    options = db.relationship('PollOption', backref='poll', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='poll', lazy='dynamic')
    comments = db.relationship('Comment', backref='poll', lazy='dynamic')
    
    def __repr__(self):
        return f'<Poll {self.title}>'

class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    design_id = db.Column(db.Integer, db.ForeignKey('design.id'), nullable=False)
    
    # İlişkiler
    votes = db.relationship('Vote', backref='option', lazy='dynamic')
    
    def __repr__(self):
        return f'<PollOption {self.id}>'

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    poll_option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)
    weight = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: bir kullanıcı bir ankete sadece bir kez oy verebilir
    __table_args__ = (db.UniqueConstraint('user_id', 'poll_id', name='unique_user_poll_vote'),)
    
    def __repr__(self):
        return f'<Vote {self.id}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class DesignCheckRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    requester = db.relationship('User', foreign_keys=[requester_id], backref='requests_made')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='requests_received')
    
    def __repr__(self):
        return f'<DesignCheckRequest {self.id}>'

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    xp_value = db.Column(db.Integer, default=10)
    is_used = db.Column(db.Boolean, default=False)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    used_by = db.relationship('User', backref='qr_codes_used')
    
    def __repr__(self):
        return f'<QRCode {self.hash_id}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    ticket_xp_reward = db.Column(db.Integer, default=20)  # Bilet kesince kazanılacak XP
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # İlişkiler
    creator = db.relationship('User', backref='created_events')
    ticket_holders = db.relationship('EventTicket', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.title}>'

class EventTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    user = db.relationship('User', backref='tickets')
    
    # Unique constraint: bir kullanıcı bir etkinliğe sadece bir kez bilet alabilir
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='unique_user_event_ticket'),)
    
    def __repr__(self):
        return f'<EventTicket {self.ticket_number}>'
