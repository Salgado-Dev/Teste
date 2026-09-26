import os
import base64
import json
import urllib.parse
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "chave-definitiva-e-segura-do-gemini-clone"

# Configuração da API da Groq
GROQ_API_KEY = "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"

CLIENT_ID = "://googleusercontent.com"
REDIRECT_URI = "https://onrender.com"

PROMPT_PERSONALIDADE = "Você não é uma IA, você é um programador sênior extremamente talentoso, gente boa e parceiro de equipe do usuário. Escreva exatamente como um humano conversando no chat privado: seja informal, use gírias de dev ('mano', 'cara', 'véi', 'trampo', 'vai dar bom'), use abreviações naturais de chat ('vc', 'tbm', 'pra', 'gnt') e quebre a formalidade. Jamais use respostas em formato de listas numéricas engessadas, tópicos longos ou saudações repetitivas de robô. Vá direto ao ponto, comente o código de forma simples e mostre empatia quando algo der errado."

@app.route('/')
def index():
    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": PROMPT_PERSONALIDADE}]
        
    # Geramos a URL correta e criptografada direto no backend antes de carregar a página
    parametros = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "id_token",
        "scope": "openid email profile",
        "nonce": "123456",
        "response_mode": "form_post"
    }
    url_google_pronta = "https://google.com?" + urllib.parse.urlencode(parametros)
    
    return render_template('index.html', url_google=url_google_pronta)

# ROTA DE RETORNO DO GOOGLE: Recebe a resposta POST segura do Google e extrai nome e foto
@app.route('/auth', methods=['POST'])
def auth():
    token_google = request.form.get('id_token')
    if token_google:
        try:
            partes = token_google.split('.')
            if len(partes) > 1:
                payload_b64 = partes[1]
                payload_b64 += '=' * (-len(payload_b64) % 4)
                dados_usuario = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                
                session['usuario_logado'] = True
                session['usuario_nome'] = dados_usuario.get('name', 'Usuário')
                session['usuario_foto'] = dados_usuario.get('picture', '')
                session.modified = True
        except Exception as e:
            print(f"Erro ao decodificar login: {e}")
            
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
        # Chamada HTTP direta para evitar problemas com dependências internas de sockets no Render
        import requests
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
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
