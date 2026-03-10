from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'gizli-anahtar-buraya'

with app.app_context():
    db.create_all()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urunler.db'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

IZIN_VERILEN_RESIM = {'png', 'jpg', 'jpeg', 'webp'}
IZIN_VERILEN_VIDEO = {'mp4', 'mov', 'avi', 'webm'}

db = SQLAlchemy(app)

ADMIN_SIFRE = "admin123"


class Urun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    fiyat = db.Column(db.Float, nullable=False)
    kategori = db.Column(db.String(100))
    resim = db.Column(db.String(300))
    video = db.Column(db.String(300))
    aktif = db.Column(db.Boolean, default=True)
    medyalar = db.relationship('UrunMedya', backref='urun', lazy=True, cascade='all, delete-orphan')


class UrunMedya(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    dosya_adi = db.Column(db.String(300), nullable=False)
    tur = db.Column(db.String(10))


def dosya_uzantisi(dosya_adi):
    return dosya_adi.rsplit('.', 1)[1].lower() if '.' in dosya_adi else ''


def admin_giris_gerekli(f):
    from functools import wraps
    @wraps(f)
    def kontrol(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_giris'))
        return f(*args, **kwargs)
    return kontrol


@app.route('/')
def anasayfa():
    urunler = Urun.query.filter_by(aktif=True).all()
    return render_template('anasayfa.html', urunler=urunler)


@app.route('/urun/<int:id>')
def urun_detay(id):
    urun = Urun.query.get_or_404(id)
    return render_template('urun_detay.html', urun=urun)


@app.route('/admin', methods=['GET', 'POST'])
def admin_giris():
    if request.method == 'POST':
        if request.form.get('sifre') == ADMIN_SIFRE:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        flash('Şifre yanlış!', 'hata')
    return render_template('admin_giris.html')


@app.route('/admin/cikis')
def admin_cikis():
    session.pop('admin', None)
    return redirect(url_for('anasayfa'))


@app.route('/admin/panel')
@admin_giris_gerekli
def admin_panel():
    urunler = Urun.query.order_by(Urun.id.desc()).all()
    return render_template('admin_panel.html', urunler=urunler)


@app.route('/admin/urun-ekle', methods=['GET', 'POST'])
@admin_giris_gerekli
def urun_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        fiyat = float(request.form['fiyat'])
        aciklama = request.form.get('aciklama', '')
        kategori = request.form.get('kategori', '')

        urun = Urun(ad=ad, fiyat=fiyat, aciklama=aciklama, kategori=kategori)
        db.session.add(urun)
        db.session.flush()

        resimler = request.files.getlist('resimler')
        for dosya in resimler:
            if not dosya.filename:
                continue
            uzanti = dosya_uzantisi(dosya.filename)
            if uzanti in IZIN_VERILEN_RESIM:
                dosya_adi = str(urun.id) + '_' + secure_filename(dosya.filename)
                dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', dosya_adi))
                db.session.add(UrunMedya(urun_id=urun.id, dosya_adi=dosya_adi, tur='resim'))

        videolar = request.files.getlist('videolar')
        for dosya in videolar:
            if not dosya.filename:
                continue
            uzanti = dosya_uzantisi(dosya.filename)
            if uzanti in IZIN_VERILEN_VIDEO:
                dosya_adi = str(urun.id) + '_' + secure_filename(dosya.filename)
                dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', dosya_adi))
                db.session.add(UrunMedya(urun_id=urun.id, dosya_adi=dosya_adi, tur='video'))

        db.session.commit()
        flash('Ürün eklendi!', 'basari')
        return redirect(url_for('admin_panel'))

    return render_template('urun_ekle.html')


@app.route('/admin/urun-sil/<int:id>')
@admin_giris_gerekli
def urun_sil(id):
    urun = Urun.query.get_or_404(id)
    db.session.delete(urun)
    db.session.commit()
    flash('Ürün silindi.', 'basari')
    return redirect(url_for('admin_panel'))


@app.route('/admin/urun-duzenle/<int:id>', methods=['GET', 'POST'])
@admin_giris_gerekli
def urun_duzenle(id):
    urun = Urun.query.get_or_404(id)
    if request.method == 'POST':
        urun.ad = request.form['ad']
        urun.fiyat = float(request.form['fiyat'])
        urun.aciklama = request.form.get('aciklama', '')
        urun.kategori = request.form.get('kategori', '')

        resimler = request.files.getlist('resimler')
        for dosya in resimler:
            if not dosya.filename:
                continue
            uzanti = dosya_uzantisi(dosya.filename)
            if uzanti in IZIN_VERILEN_RESIM:
                dosya_adi = str(urun.id) + '_' + secure_filename(dosya.filename)
                dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', dosya_adi))
                db.session.add(UrunMedya(urun_id=urun.id, dosya_adi=dosya_adi, tur='resim'))

        videolar = request.files.getlist('videolar')
        for dosya in videolar:
            if not dosya.filename:
                continue
            uzanti = dosya_uzantisi(dosya.filename)
            if uzanti in IZIN_VERILEN_VIDEO:
                dosya_adi = str(urun.id) + '_' + secure_filename(dosya.filename)
                dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', dosya_adi))
                db.session.add(UrunMedya(urun_id=urun.id, dosya_adi=dosya_adi, tur='video'))

        sil_idler = request.form.getlist('medya_sil')
        for mid in sil_idler:
            m = UrunMedya.query.get(int(mid))
            if m and m.urun_id == urun.id:
                db.session.delete(m)

        db.session.commit()
        flash('Ürün güncellendi!', 'basari')
        return redirect(url_for('admin_panel'))

    return render_template('urun_duzenle.html', urun=urun)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=3000)
