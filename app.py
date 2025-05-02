from flask import Flask, request, jsonify
import os
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return 'Servidor Flask rodando!'

@app.route('/atualizar-banco', methods=['POST'])
def atualizar_banco():
    dados = request.get_json()
    arquivos = dados.get('arquivos', [])
    planilha_existente = dados.get('planilha', [])

    if not arquivos:
        return jsonify(erro='Nenhum dado CSV recebido.'), 400

    try:
        # Junta todos os DataFrames recebidos
        novos = pd.concat([pd.DataFrame(arq) for arq in arquivos], ignore_index=True)

        if planilha_existente:
            existente = pd.DataFrame(planilha_existente)
            datas_existentes = set(existente['MÊS'].unique())
            novos = novos[~novos['MÊS'].isin(datas_existentes)]
            resultado = pd.concat([existente, novos], ignore_index=True)
        else:
            resultado = novos

        # Aqui, apenas simulamos salvar e devolvemos resposta
        return jsonify(mensagem='Banco_de_Dados.xlsx atualizado!', total_linhas=len(resultado))

    except Exception as e:
        return jsonify(erro=f'Erro ao processar: {str(e)}'), 500

if __name__ == '__main__':
    app.run()
