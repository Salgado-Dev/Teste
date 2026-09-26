import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "chave-super-secreta-do-gemini-clone"
# Força o Authlib a aceitar o redirecionamento do Render sem travar em HTTP
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuração do cliente Groq
client = Groq(api_key="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")

# Configuração do OAuth do Google no Backend
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='847378218961-kvtn9kk0ibmpvpsrho7rvr9ktocjuh2r.apps.googleusercontent.com',
    client_secret=os.environ.get("), # Pode deixar em branco se não configurou no painel, o fluxo básico passa
    server_metadata_url='https://google.com',
    client_kwargs={'scope': 'openid email profile'}
)

PROMPT_PERSONALIDADE = "Você não é uma IA, você é um programador sênior extremamente talentoso, gente boa e parceiro de equipe do usuário. Escreva exatamente como um humano conversando no chat privado: seja informal, use gírias de dev ('mano', 'cara', 'véi', 'trampo', 'vai dar bom'), use abreviações naturais de chat ('vc', 'tbm', 'pra', 'gnt') e quebre a formalidade. Jamais use respostas em formato de listas numéricas engessadas, tópicos longos ou saudações repetitivas de robô. Vá direto ao ponto, comente o código de forma simples e mostre empatia quando algo der errado."

@app.route('/')
def index():
    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": PROMPT_PERSONALIDADE}]
    return render_template('index.html')

# ROTA QUE DIRECIONA PRO GOOGLE (O antivírus não bloqueia link direto)
@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

# ROTA QUE RECEBE O RETORNO DO GOOGLE
@app.route('/auth')
def auth():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            session['usuario_logado'] = True
            session['usuario_nome'] = user_info.get('name')
            session['usuario_foto'] = user_info.get('picture')
            session.modified = True
    except Exception as e:
        print(f"Erro na autenticação: {e}")
    return redirect(url_for('index'))

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    dados = request.get_json()
    pergunta_usuario = dados.get('mensagem', '').strip()
    
    if not pergunta_usuario:
        return jsonify({"erro": "Mensagem vazia"}), 400

    historico = session.get('historico', [{"role": "system", "content": PROMPT_PERSONALIDADE}])
    historico.append({"role": "user", "content": pergunta_usuario})
    
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=historico,
            temperature=0.85,
            max_completion_tokens=2048,
            top_p=1,
            stream=False 
        )
        
        resposta_ia = completion.choices.message.content
        historico.append({"role": "assistant", "content": resposta_ia})
        
        session['historico'] = historico
        session.modified = True
        
        return jsonify({"resposta": resposta_ia})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
