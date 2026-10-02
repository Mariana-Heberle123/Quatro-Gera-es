from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

app.secret_key = "padaria4geracoes"


def conectar_banco():
    conexao = sqlite3.connect("padaria.db")
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabela_vendas():
    conexao = conectar_banco()

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data_venda TEXT NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
    )

    conexao.commit()
    conexao.close()


criar_tabela_vendas()


@app.route("/")
def inicio():
    conexao = conectar_banco()
    produtos = conexao.execute(
        "SELECT * FROM produtos"
    ).fetchall()
    conexao.close()

    return render_template("index.html", produtos=produtos)


@app.route("/produtos")
def produtos():
    conexao = conectar_banco()
    produtos = conexao.execute(
        "SELECT * FROM produtos"
    ).fetchall()
    conexao.close()

    return render_template("produtos.html", produtos=produtos)


@app.route("/produto/<int:id>")
def produto_detalhes(id):
    conexao = conectar_banco()

    produto = conexao.execute(
        "SELECT * FROM produtos WHERE id = ?",
        (id,)
    ).fetchone()

    conexao.close()

    if not produto:
        return "Produto não encontrado", 404

    return render_template("produto.html", produto=produto)


@app.route("/adicionar/<int:id>")
def adicionar_carrinho(id):
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    conexao = conectar_banco()

    produto = conexao.execute(
        "SELECT quantidade FROM produtos WHERE id = ?",
        (id,)
    ).fetchone()

    conexao.close()

    if not produto:
        return "Produto não encontrado", 404

    id = str(id)

    quantidade_atual = int(carrinho.get(id, 0))

    if quantidade_atual < produto["quantidade"]:
        carrinho[id] = quantidade_atual + 1

    session["carrinho"] = carrinho

    return redirect(url_for("carrinho"))


@app.route("/diminuir/<int:id>")
def diminuir_carrinho(id):
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    id = str(id)

    if id in carrinho:
        carrinho[id] -= 1

        if carrinho[id] <= 0:
            del carrinho[id]

    session["carrinho"] = carrinho

    return redirect(url_for("carrinho"))


@app.route("/remover/<int:id>")
def remover_carrinho(id):
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    id = str(id)

    if id in carrinho:
        del carrinho[id]

    session["carrinho"] = carrinho

    return redirect(url_for("carrinho"))


@app.route("/carrinho")
def carrinho():
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    conexao = conectar_banco()

    produtos_carrinho = []
    total = 0

    for id, quantidade in carrinho.items():

        produto = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (int(id),)
        ).fetchone()

        if produto:

            subtotal = produto["preco"] * quantidade
            total += subtotal

            produtos_carrinho.append({
                "produto": produto,
                "quantidade": quantidade,
                "subtotal": subtotal
            })

    conexao.close()

    return render_template(
        "carrinho.html",
        produtos=produtos_carrinho,
        total=total
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        if email == "cliente@padaria.com" and senha == "123456":

            session["usuario"] = email

            return redirect(url_for("pagamento"))

        return render_template(
            "login.html",
            erro="E-mail ou senha incorretos."
        )

    return render_template("login.html")


@app.route("/pagamento")
def pagamento():

    if "usuario" not in session:
        return redirect(url_for("login"))

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    if not carrinho:
        return redirect(url_for("carrinho"))

    conexao = conectar_banco()

    produtos_pagamento = []
    total = 0

    for id, quantidade in carrinho.items():

        produto = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (int(id),)
        ).fetchone()

        if produto:

            if quantidade > produto["quantidade"]:

                conexao.close()

                return render_template(
                    "pagamento.html",
                    produtos=[],
                    total=0,
                    erro=f"Estoque insuficiente para {produto['nome']}."
                )

            subtotal = produto["preco"] * quantidade
            total += subtotal

            produtos_pagamento.append({
                "produto": produto,
                "quantidade": quantidade,
                "subtotal": subtotal
            })

    conexao.close()

    return render_template(
        "pagamento.html",
        produtos=produtos_pagamento,
        total=total
    )


@app.route("/processar_pagamento", methods=["POST"])
def processar_pagamento():

    if "usuario" not in session:
        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}

    carrinho = dict(carrinho)

    if not carrinho:
        return jsonify({
            "sucesso": False,
            "erro": "O carrinho está vazio."
        }), 400

    nome = request.form.get("nome", "").strip()
    numero = request.form.get("numero", "").strip()
    validade = request.form.get("validade", "").strip()
    cvv = request.form.get("cvv", "").strip()

    if not nome or not numero or not validade or not cvv:
        return jsonify({
            "sucesso": False,
            "erro": "Preencha todos os campos do pagamento."
        }), 400

    conexao = conectar_banco()

    try:

        produtos_pagamento = []

        for id, quantidade in carrinho.items():

            produto = conexao.execute(
                "SELECT * FROM produtos WHERE id = ?",
                (int(id),)
            ).fetchone()

            if not produto:
                conexao.rollback()
                return jsonify({
                    "sucesso": False,
                    "erro": "Produto não encontrado."
                }), 404

            if quantidade > produto["quantidade"]:
                conexao.rollback()
                return jsonify({
                    "sucesso": False,
                    "erro": f"Estoque insuficiente para {produto['nome']}."
                }), 400

            produtos_pagamento.append(
                (produto["id"], quantidade)
            )

        data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for produto_id, quantidade in produtos_pagamento:

            conexao.execute(
                """
                UPDATE produtos
                SET quantidade = quantidade - ?
                WHERE id = ?
                """,
                (quantidade, produto_id)
            )

            conexao.execute(
                """
                INSERT INTO vendas
                (produto_id, quantidade, data_venda)
                VALUES (?, ?, ?)
                """,
                (produto_id, quantidade, data_venda)
            )

        conexao.commit()

        session["carrinho"] = {}
        session.pop("usuario", None)

        return jsonify({
            "sucesso": True,
            "mensagem": "Pagamento aprovado! Compra concluída."
        })

    except Exception:

        conexao.rollback()

        return jsonify({
            "sucesso": False,
            "erro": "Não foi possível processar o pagamento."
        }), 500

    finally:

        conexao.close()


@app.route("/relatorios")
def relatorios():

    periodo = request.args.get("periodo", "semanal")

    dados_ficticios = {
        "diario": [37, 54, 42],
        "semanal": [128, 167, 145],
        "mensal": [512, 476, 589]
    }

    if periodo not in dados_ficticios:
        periodo = "semanal"

    conexao = conectar_banco()

    nomes_produtos = conexao.execute(
        "SELECT nome FROM produtos ORDER BY id"
    ).fetchall()

    vendas_reais = conexao.execute(
        """
        SELECT
            produtos.nome,
            COALESCE(SUM(vendas.quantidade), 0) AS total_vendido
        FROM produtos
        LEFT JOIN vendas
            ON produtos.id = vendas.produto_id
        GROUP BY produtos.id
        ORDER BY produtos.id
        """
    ).fetchall()

    conexao.close()

    nomes = [produto["nome"] for produto in nomes_produtos]

    possui_vendas_reais = any(
        venda["total_vendido"] > 0
        for venda in vendas_reais
    )

    if possui_vendas_reais:

        quantidades = [
            venda["total_vendido"]
            for venda in vendas_reais
        ]

    else:

        quantidades = dados_ficticios[periodo]

    return render_template(
        "relatorios.html",
        periodo=periodo,
        titulo_periodo="",
        nomes=nomes,
        quantidades=quantidades
    )


if __name__ == "__main__":
    app.run(debug=True)