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
class Admin(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(256))
    def __init__(self,email):
        self.email = email
class Lugar(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    nome = db.Column(db.String(256))
    bloco = db.Column(db.String(256))
    tipo = db.Column(db.String(256))
    andar = db.Column(db.String(256))
    chamados = db.relationship('Chamado',backref='lugares')
    def __init__(self,nome,bloco,tipo,andar):
        self.nome = nome
        self.bloco = bloco
        self.tipo = tipo
        self.andar =  andar
class Chamado(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    lugar_id = db.Column(db.Integer, db.ForeignKey('lugar.id'))
    email = db.Column(db.String(256))
    categoria = db.Column(db.String(50))
    sub_categoria = db.Column(db.String(50))
    urgencia = db.Column(db.String(50))
    descricao = db.Column(db.String(500))
    data_chamado = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self,lugar_id,email,categoria,sub_categoria,urgencia,descricao):
        self.lugar_id = lugar_id
        self.email = email
        self.categoria = categoria
        self.sub_categoria = sub_categoria
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
    if lugar == None:
        return render_template('index.html',lugar=lugar)
    lugares = Lugar.query.all()
    for l in lugares:
        if l.id == int(lugar):
            lugar = int(lugar)
            return render_template('index.html',lugar=lugar)

    lugar = None
    return render_template('index.html',lugar=lugar)


@app.route('/verificar',methods=['POST','GET'])
def verificar():
    session['lugar'] = request.form.get('lugar')
    lugar = Lugar.query.filter_by(id=session['lugar']).first()
    session['lugar_nome'] = lugar.nome
    session['lugar_bloco'] = lugar.bloco
    session['lugar_tipo'] = lugar.tipo
    session['lugar_andar'] = lugar.andar

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
    sub_categoria = request.form.get("sub_categoria")
    urgencia  = '0';
    descricao = request.form.get("descricao")
#BANCO DE DADOS ------------
    chamado = Chamado(int(session["lugar"]),email,categoria,sub_categoria,urgencia,descricao)
    db.session.add(chamado)
    db.session.commit()
#EMAIL -------
    msg = Message(
        subject= f'REPORT {session['lugar_nome']}',
        recipients= ['eduardo.alvesp02@gmail.com'],
        body= f''' 
        O seguinte report foi preenchido:
        ENVIADO POR -
        NOME: {name}
        EMAIL: {email}
        INFORMAÇÕES DO REPORT -
        LUGAR: {session['lugar_nome']}
        BLOCO: {session['lugar_bloco']}
        ANDAR: {session['lugar_andar']}
        CATEGORIA: {categoria}
        SUBCATEGORIA: {sub_categoria}
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
    admflag = 0
    admins = Admin.query.all()
    for a in admins:
        if(a.email == session['email']):
            admflag = 1
    chamados_query = Chamado.query
    ordem = request.args.get('ordem')
    filtro_email = request.args.get('filtro_email')
    filtro_lugar = request.args.get('filtro_lugar')
    filtro_tipo = request.args.get('filtro_tipo')
    filtro_status = request.args.get('filtro_status')
    if filtro_email:
        chamados_query = chamados_query.filter(Chamado.email.ilike(f'%{filtro_email}%'))

    if filtro_lugar:
        chamados_query = chamados_query.join(Chamado.lugares).filter(Lugar.nome.ilike(f'%{filtro_lugar}%'))

    if filtro_tipo:
        chamados_query = chamados_query.join(Chamado.lugares).filter(Lugar.tipo.ilike(f'%{filtro_tipo}%'))

    if filtro_status:
        chamados_query = chamados_query.filter(Chamado.status == filtro_status)    

    if ordem:
        if ordem == 'id':
            chamados_query = chamados_query.order_by(Chamado.id)
        if ordem == 'email':
            chamados_query = chamados_query.order_by(Chamado.email)
        if ordem =='status':
            chamados_query = chamados_query.order_by(Chamado.status)
        if ordem =='lugar':
            chamados = Chamado.query.join(Chamado.lugares).order_by(Lugar.nome)
        if ordem =='bloco':
            chamados = Chamado.query.join(Chamado.lugares).order_by(Lugar.bloco)
        if ordem =='tipo':
            chamados = Chamado.query.join(Chamado.lugares).order_by(Lugar.tipo)
        if ordem =='andar':
            chamados = Chamado.query.join(Chamado.lugares).order_by(Lugar.andar)
        if ordem =='categoria':
            chamados_query = chamados_query.order_by(Chamado.categoria)
        if ordem =='sub_categoria':
            chamados_query = chamados_query.order_by(Chamado.sub_categoria)
        if ordem =='data':
            chamados_query = chamados_query.order_by(Chamado.data_chamado)

    chamados = chamados_query.all()
    lugares = Lugar.query.all()
    return render_template('dados.html',chamados=chamados,admins=admins,admflag=admflag,lugares=lugares)

@app.route('/chamadoAtt', methods=['POST'])
def chamadoAtt():
    id = request.form.get('chamado_id')
    email = request.form.get('chamado_email')
    chamado = Chamado.query.get(id)
    chamado.status = not chamado.status
    db.session.commit()
    msg = Message(
        subject= f'CHAMADO FECHADO',
        recipients= [email],
        body= f''' 
       O seguinte chamado feito por você foi fechado: 
       {chamado.lugares.nome} 
       {chamado.categoria}
       {chamado.data_chamado}

       Obrigado pela contribuição!
       '''
    )   
    mail.send(msg)
    return redirect(url_for('dados'))

