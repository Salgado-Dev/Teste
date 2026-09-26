import os
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "chave-definitiva-e-segura-do-gemini-clone"

# Configuração da API da Groq
GROQ_API_KEY = "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"

# Configurações do Google (Fixas e completas para não haver quebra de texto)
CLIENT_ID = "://googleusercontent.com"
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "COLE_SUA_CLIENT_SECRET_AQUI")
REDIRECT_URI = "https://onrender.com"

PROMPT_PERSONALIDADE = "Você não é uma IA, você é um programador sênior extremamente talentoso, gente boa e parceiro de equipe do usuário. Escreva exatamente como um humano conversando no chat privado: seja informal, use gírias de dev ('mano', 'cara', 'véi', 'trampo', 'vai dar bom'), use abreviações naturais de chat ('vc', 'tbm', 'pra', 'gnt') e quebre a formalidade. Jamais use respostas em formato de listas numéricas engessadas, tópicos longos ou saudações repetitivas de robô. Vá direto ao ponto, comente o código de forma simples e mostre empatia quando algo der errado."

@app.route('/')
def index():
    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": PROMPT_PERSONALIDADE}]
    return render_template('index.html')

# ETAPA 1: Redireciona usando montagem de parâmetros limpa (Evita erro de URL)
@app.route('/login')
def login():
    base_url = "https://google.com"
    parametros = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "https://googleapis.com https://googleapis.com",
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    # O urllib monta o link perfeitamente trocando espaços por %20 e amarrando no accounts.google.com
    google_auth_url = f"{base_url}?{urllib.parse.urlencode(parametros)}"
    return redirect(google_auth_url)

# ETAPA 2 e 3: Processa o código retornado e valida o usuário
@app.route('/auth')
def auth():
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não fornecido pelo Google.", 400
        
    try:
        token_url = "https://googleapis.com"
        token_data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        token_res = requests.post(token_url, data=token_data).json()
        access_token = token_res.get('access_token')
        
        if access_token:
            user_info_url = "https://googleapis.com"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info = requests.get(user_info_url, headers=headers).json()
            
            session['usuario_logado'] = True
            session['usuario_nome'] = user_info.get('name', 'Usuário')
            session['usuario_foto'] = user_info.get('picture', '')
            session.modified = True
            
    except Exception as e:
        print(f"Erro crítico no processamento do login: {e}")
        
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
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": historico,
            "temperature": 0.85,
            "max_completion_tokens": 2048,
            "top_p": 1,
            "stream": False
        }
        
        response = requests.post("https://groq.com", headers=headers, json=payload)
        dados_resposta = response.json()
        
        resposta_ia = dados_resposta['choices'][0]['message']['content']
        historico.append({"role": "assistant", "content": resposta_ia})
        
        session['historico'] = historico
        session.modified = True
        
        return jsonify({"resposta": resposta_ia})
    except Exception as e:
        return jsonify({"erro": f"Erro na comunicação com a API: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
