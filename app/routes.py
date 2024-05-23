from app import app
from datetime import datetime,timezone
from flask import render_template, session, redirect, url_for, request
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import os
from authlib.integrations.flask_client import OAuth

#CONFIGURAÇÃO DE BANCO
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ruralreport.db"
db = SQLAlchemy(app)
class Chamado(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(256))
    lugar = db.Column(db.String(50))
    categoria = db.Column(db.String(50))
    urgencia = db.Column(db.String(50))
    descricao = db.Column(db.String(500))
    data_chamado = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self,email,lugar,categoria,urgencia,descricao):
        self.email = email
        self.lugar = lugar
        self.categoria = categoria
        self.urgencia = urgencia
        self.descricao = descricao


# oauth config
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='601891060733-73ovp9d1j465g1gb1drpnt1jmpe82ol3.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  
    client_kwargs={'scope': 'email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

#CONFIGURAÇÃO DO FLASK MAIL
app.secret_key = "123456789"
app.config['SECRET KEY'] = "123456789"
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = "eduardo.alvesp02@gmail.com"
app.config['MAIL_PASSWORD'] = "jxyogzripqqndakc"
app.config['MAIL_DEFAULT_SENDER'] = "eduardo.alvesp02@gmail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

#ROTAS
@app.route('/')
@app.route('/')
@app.route('/',defaults ={"lugar":None})
@app.route('/index/<lugar>')
@app.route('/index',defaults ={"lugar":None})

def index(lugar):
    return render_template('index.html',lugar=lugar)


@app.route('/verificar',methods=['POST','GET'])
def verificar():
    session['lugar'] = request.form.get('lugar')
    if 'email' in session:
        return redirect(url_for('form'))
    else:
        return redirect(url_for('login'))
    
@app.route('/trocaConta',methods=['POST'])
def trocaConta():
    session.pop('email')
    lugar = request.form.get('lugar')
    return redirect(url_for('index',lugar=lugar))

#ROTA DE LOGIN DO GOOGLE
@app.route('/login')
def login():

    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    resp.raise_for_status()
    user_info = resp.json()
    # do something with the token and profile
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    return redirect('/form')
#FIM DA ROTA DE LOGIN DO GOOGLE

@app.route('/form', methods=['POST','GET'])
def form():
    if 'email' not in session:
        return redirect(url_for('index'))
    return render_template('form.html')

@app.route('/valores', methods=['POST'])
def valores():
    db.create_all()
    lugar = session["lugar"]
    email = session['email']
    name = session['name']
    categoria = request.form.get("categoria")
    urgencia  = request.form.get("urgencia")
    descricao = request.form.get("descricao")
#BANCO DE DADOS ------------

    chamado = Chamado(email,lugar,categoria,urgencia,descricao)
    db.session.add(chamado)
    db.session.commit()
#EMAIL -------
    msg = Message(
        subject= f'REPORT {lugar}',
        recipients= ['eduardo.alvesp02@gmail.com'],
        body= f''' 
        O seguinte report foi preenchido:
        ENVIADO POR -
        NOME: {name}
        EMAIL: {email}
        INFORMAÇÕES DO REPORT -
        LUGAR: {lugar}
        CATEGORIA: {categoria}
        URGENCIA: {urgencia}
        DESCRIÇÃO: {descricao}
       '''
    )   
    mail.send(msg)
    return redirect(url_for('enviado'))

@app.route('/enviado')
def enviado():
    if 'email' not in session:
        return redirect(url_for('index'))
    return render_template('enviado.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dados')
def dados():
    chamados = Chamado.query.all()
    return render_template('dados.html',chamados=chamados)

