import os
from flask import Flask, render_template, request, jsonify, session
from groq import Groq

app = Flask(__name__)
app.secret_key = "uma-chave-qualquer-para-o-chat"

# Usando a sua chave direto aqui como você preferiu
client = Groq(api_key="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")

@app.route('/')
def index():
    session['historico'] = [
        {"role": "system", "content": "Você é um assistente virtual prestativo, amigável e focado em ajudar o usuário desenvolvedor."}
    ]
    return render_template('index.html')

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    dados = request.get_json()
    pergunta_usuario = dados.get('mensagem', '').strip()
    
    if not pergunta_usuario:
        return jsonify({"erro": "Mensagem vazia"}), 400

    if 'historico' not in session:
        session['historico'] = [{"role": "system", "content": "Você é um assistente virtual prestativo, amigável e focado em ajudar o usuário desenvolvedor."}]

    historico = session['historico']
    historico.append({"role": "user", "content": pergunta_usuario})
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=historico,
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            stream=False 
        )
        
        resposta_ia = completion.choices[0].message.content
        historico.append({"role": "assistant", "content": resposta_ia})
        
        session['historico'] = historico
        session.modified = True
        
        return jsonify({"resposta": resposta_ia})
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
