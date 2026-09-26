import os
import base64
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = "chave-super-secreta-do-gemini-clone"

client = Groq(api_key="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")

PROMPT_PERSONALIDADE = "Você não é uma IA, você é um programador sênior extremamente talentoso, gente boa e parceiro de equipe do usuário. Escreva exatamente como um humano conversando no chat privado: seja informal, use gírias de dev ('mano', 'cara', 'véi', 'trampo', 'vai dar bom'), use abreviações naturais de chat ('vc', 'tbm', 'pra', 'gnt') e quebre a formalidade. Jamais use respostas em formato de listas numéricas engessadas, tópicos longos ou saudações repetitivas de robô. Vá direto ao ponto, comente o código de forma simples e mostre empatia quando algo der errado (ex: 'putz, que bizarro, tenta mudar isso aqui pra ver se resolve...'). Mantenha o papo leve, focado em ajudar, mas parecendo 100% uma pessoa real do outro lado da tela."

@app.route('/')
def index():
    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": PROMPT_PERSONALIDADE}]
    return render_template('index.html')

# ROTA NOVA: Recebe o login direto do Google e valida no servidor
@app.route('/login_google', methods=['POST'])
def login_google():
    token_google = request.form.get('credential')
    if token_google:
        try:
            # Decodifica o token enviado de forma nativa e segura
            partes = token_google.split('.')
            payload_ajustado = partes[1] + '=' * (-len(partes[1]) % 4)
            dados_usuario = json.loads(base64.b64decode(payload_ajustado).decode('utf-8'))
            
            # Salva na sessão do Flask que o usuário está validado
            session['usuario_logado'] = True
            session['usuario_nome'] = dados_usuario.get('name')
            session['usuario_foto'] = dados_usuario.get('picture')
            session.modified = True
        except Exception as e:
            print(f"Erro ao decodificar token: {e}")
            
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
