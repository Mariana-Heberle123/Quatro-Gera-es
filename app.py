from flask import Flask, render_template, session, redirect, url_for
import sqlite3

app = Flask(__name__)

app.secret_key = "padaria4geracoes"


def conectar_banco():
    conexao = sqlite3.connect("padaria.db")
    conexao.row_factory = sqlite3.Row
    return conexao


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

    return render_template("produto.html", produto=produto)


@app.route("/adicionar/<int:id>")
def adicionar_carrinho(id):
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}
    else:
        carrinho = dict(carrinho)

    id = str(id)

    if id in carrinho:
        carrinho[id] += 1
    else:
        carrinho[id] = 1

    session["carrinho"] = carrinho

    return redirect(url_for("carrinho"))


@app.route("/diminuir/<int:id>")
def diminuir_carrinho(id):
    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {str(item): 1 for item in carrinho}
    else:
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
    else:
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
    else:
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


if __name__ == "__main__":
    app.run(debug=True)