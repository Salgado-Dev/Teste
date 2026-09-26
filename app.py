import os
import requests
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = "chave-definitiva-e-segura-do-gemini-clone"

# Configuração da API da Groq
GROQ_API_KEY = "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"

PROMPT_PERSONALIDADE = "Você não é uma IA, você é um programador sênior extremamente talentoso, gente boa e parceiro de equipe do usuário. Escreva exatamente como um humano conversando no chat privado: seja informal, use gírias de dev ('mano', 'cara', 'véi', 'trampo', 'vai dar bom'), use abreviações naturais de chat ('vc', 'tbm', 'pra', 'gnt') e quebre a formalidade. Jamais use respostas em formato de listas numéricas engessadas, tópicos longos ou saudações repetitivas de robô. Vá direto ao ponto, comente o código de forma simples e mostre empatia quando algo der errado."

@app.route('/')
def index():
    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": PROMPT_PERSONALIDADE}]
    return render_template('index.html')

# ROTA NOVA: O JavaScript envia o nome e a foto do usuário logado via Firebase
@app.route('/definir_sessao', methods=['POST'])
def definir_sessao():
    dados = request.get_json()
    session['usuario_logado'] = True
    session['usuario_nome'] = dados.get('nome', 'Usuário')
    session['usuario_foto'] = dados.get('foto', '')
    session.modified = True
    return jsonify({"status": "sucesso"})

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
        
        resposta_ia = dados_resposta['choices']['message']['content']
        historico.append({"role": "assistant", "content": resposta_ia})
        
        session['historico'] = historico
        session.modified = True
        
        return jsonify({"resposta": resposta_ia})
    except Exception as e:
        return jsonify({"erro": f"Erro na comunicação com a API: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
