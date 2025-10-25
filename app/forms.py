from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, SubmitField, RadioField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])
    submit = SubmitField('Kayıt Ol')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Bu kullanıcı adı zaten alınmış. Lütfen farklı bir kullanıcı adı seçin.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu e-posta adresi zaten kayıtlı. Lütfen farklı bir e-posta adresi kullanın.')

class LoginForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember_me = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class EditProfileForm(FlaskForm):
    bio = TextAreaField('Hakkımda', validators=[Length(max=500)])
    profile_image = FileField('Profil Resmi', validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Sadece resim dosyaları yüklenebilir!')])
    submit = SubmitField('Profili Güncelle')

class DesignUploadForm(FlaskForm):
    title = StringField('Tasarım Başlığı', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Açıklama', validators=[Length(max=500)])
    category = SelectField('Kategori', choices=[
        ('', 'Kategori Seçin'),
        ('tshirt', 'T-Shirt'),
        ('hoodie', 'Hoodie'),
        ('pants', 'Pantolon'),
        ('dress', 'Elbise'),
        ('accessory', 'Aksesuar'),
        ('other', 'Diğer')
    ], validators=[DataRequired()])
    image = FileField('Tasarım Resmi', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Sadece resim dosyaları yüklenebilir!')])
    submit = SubmitField('Tasarımı Yükle')

class CreatePollForm(FlaskForm):
    title = StringField('Anket Başlığı', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Açıklama', validators=[Length(max=500)])
    submit = SubmitField('Anket Oluştur')

class AddDesignsToPollForm(FlaskForm):
    designs = SelectField('Tasarımlar', coerce=int, validators=[DataRequired()], choices=[])
    submit = SubmitField('Tasarım Ekle')

class CommentForm(FlaskForm):
    body = TextAreaField('Yorum', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Yorum Yap')

class VoteForm(FlaskForm):
    poll_option = RadioField('Seçenek', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Oy Ver')

class EventForm(FlaskForm):
    title = StringField('Etkinlik Başlığı', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Açıklama', validators=[Length(max=1000)])
    location = StringField('Konum', validators=[Length(max=200)])
    event_date = DateTimeField('Etkinlik Tarihi', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    ticket_xp_reward = IntegerField('Bilet XP Ödülü', validators=[DataRequired()], default=20)
    submit = SubmitField('Etkinlik Oluştur')
