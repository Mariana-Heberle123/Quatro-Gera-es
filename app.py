from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True)