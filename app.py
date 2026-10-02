from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

app.secret_key = "padaria4geracoes"


def conectar_banco():
    conexao = sqlite3.connect("padaria.db")
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabelas():
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

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_pedido TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Concluído'
        )
        """
    )

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
    )

    conexao.commit()
    conexao.close()


criar_tabelas()


# =========================================
# INÍCIO
# =========================================

@app.route("/")
def inicio():

    conexao = conectar_banco()

    produtos = conexao.execute(
        "SELECT * FROM produtos"
    ).fetchall()

    conexao.close()

    return render_template(
        "index.html",
        produtos=produtos
    )


# =========================================
# PRODUTOS
# =========================================

@app.route("/produtos")
def produtos():

    conexao = conectar_banco()

    produtos = conexao.execute(
        "SELECT * FROM produtos"
    ).fetchall()

    conexao.close()

    return render_template(
        "produtos.html",
        produtos=produtos
    )


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

    return render_template(
        "produto.html",
        produto=produto
    )


# =========================================
# CARRINHO
# =========================================

@app.route("/adicionar/<int:id>")
def adicionar_carrinho(id):

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

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

    quantidade_atual = int(
        carrinho.get(id, 0)
    )

    if quantidade_atual < produto["quantidade"]:
        carrinho[id] = quantidade_atual + 1

    session["carrinho"] = carrinho

    return redirect(
        url_for("carrinho")
    )


@app.route("/diminuir/<int:id>")
def diminuir_carrinho(id):

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

    carrinho = dict(carrinho)

    id = str(id)

    if id in carrinho:

        carrinho[id] -= 1

        if carrinho[id] <= 0:
            del carrinho[id]

    session["carrinho"] = carrinho

    return redirect(
        url_for("carrinho")
    )


@app.route("/remover/<int:id>")
def remover_carrinho(id):

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

    carrinho = dict(carrinho)

    id = str(id)

    if id in carrinho:
        del carrinho[id]

    session["carrinho"] = carrinho

    return redirect(
        url_for("carrinho")
    )


@app.route("/carrinho")
def carrinho():

    carrinho = session.get("carrinho", {})

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

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

            subtotal = (
                produto["preco"]
                * quantidade
            )

            total += subtotal

            produtos_carrinho.append(
                {
                    "produto": produto,
                    "quantidade": quantidade,
                    "subtotal": subtotal
                }
            )

    conexao.close()

    return render_template(
        "carrinho.html",
        produtos=produtos_carrinho,
        total=total
    )


# =========================================
# LOGIN DO CLIENTE
# =========================================

@app.route("/login")
def login():

    return render_template(
        "login.html"
    )


# =========================================
# PAGAMENTO
# =========================================

@app.route("/pagamento")
def pagamento():

    carrinho = session.get(
        "carrinho",
        {}
    )

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

    carrinho = dict(carrinho)

    if not carrinho:

        return redirect(
            url_for("carrinho")
        )

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
                    erro=(
                        f"Estoque insuficiente para "
                        f"{produto['nome']}."
                    )
                )

            subtotal = (
                produto["preco"]
                * quantidade
            )

            total += subtotal

            produtos_pagamento.append(
                {
                    "produto": produto,
                    "quantidade": quantidade,
                    "subtotal": subtotal
                }
            )

    conexao.close()

    return render_template(
        "pagamento.html",
        produtos=produtos_pagamento,
        total=total
    )


@app.route(
    "/processar_pagamento",
    methods=["POST"]
)
def processar_pagamento():

    carrinho = session.get(
        "carrinho",
        {}
    )

    if isinstance(carrinho, list):
        carrinho = {
            str(item): 1
            for item in carrinho
        }

    carrinho = dict(carrinho)

    if not carrinho:

        return jsonify(
            {
                "sucesso": False,
                "erro": "O carrinho está vazio."
            }
        ), 400

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    numero = request.form.get(
        "numero",
        ""
    ).strip()

    validade = request.form.get(
        "validade",
        ""
    ).strip()

    cvv = request.form.get(
        "cvv",
        ""
    ).strip()

    if (
        not nome
        or not numero
        or not validade
        or not cvv
    ):

        return jsonify(
            {
                "sucesso": False,
                "erro": (
                    "Preencha todos os campos "
                    "do pagamento."
                )
            }
        ), 400

    conexao = conectar_banco()

    try:

        produtos_pagamento = []
        total = 0

        # Verifica estoque e calcula total
        for id, quantidade in carrinho.items():

            produto = conexao.execute(
                "SELECT * FROM produtos WHERE id = ?",
                (int(id),)
            ).fetchone()

            if not produto:

                conexao.rollback()

                return jsonify(
                    {
                        "sucesso": False,
                        "erro": "Produto não encontrado."
                    }
                ), 404

            if quantidade > produto["quantidade"]:

                conexao.rollback()

                return jsonify(
                    {
                        "sucesso": False,
                        "erro": (
                            f"Estoque insuficiente "
                            f"para {produto['nome']}."
                        )
                    }
                ), 400

            subtotal = (
                produto["preco"]
                * quantidade
            )

            total += subtotal

            produtos_pagamento.append(
                (
                    produto["id"],
                    quantidade,
                    produto["preco"]
                )
            )

        data_pedido = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Cria o pedido
        cursor = conexao.execute(
            """
            INSERT INTO pedidos
            (data_pedido, total, status)
            VALUES (?, ?, ?)
            """,
            (
                data_pedido,
                total,
                "Concluído"
            )
        )

        pedido_id = cursor.lastrowid

        # Salva os itens e atualiza o estoque
        for produto_id, quantidade, preco in produtos_pagamento:

            conexao.execute(
                """
                INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco)
                VALUES (?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    produto_id,
                    quantidade,
                    preco
                )
            )

            conexao.execute(
                """
                UPDATE produtos
                SET quantidade = quantidade - ?
                WHERE id = ?
                """,
                (
                    quantidade,
                    produto_id
                )
            )

            # Mantém o registro de vendas
            conexao.execute(
                """
                INSERT INTO vendas
                (produto_id, quantidade, data_venda)
                VALUES (?, ?, ?)
                """,
                (
                    produto_id,
                    quantidade,
                    data_pedido
                )
            )

        conexao.commit()

        session["carrinho"] = {}

        return jsonify(
            {
                "sucesso": True,
                "mensagem": (
                    "Pagamento aprovado! "
                    "Compra concluída."
                ),
                "pedido_id": pedido_id
            }
        )

    except Exception:

        conexao.rollback()

        return jsonify(
            {
                "sucesso": False,
                "erro": (
                    "Não foi possível "
                    "processar o pagamento."
                )
            }
        ), 500

    finally:

        conexao.close()


# =========================================
# LOGIN DO ADMINISTRADOR
# =========================================

ADMIN_EMAIL = "admin@padaria.com"
ADMIN_SENHA = "admin123"


@app.route(
    "/admin/login",
    methods=["POST"]
)
def admin_login():

    dados = request.get_json(
        silent=True
    ) or {}

    email = dados.get(
        "email",
        ""
    ).strip().lower()

    senha = dados.get(
        "senha",
        ""
    )

    if (
        email == ADMIN_EMAIL
        and senha == ADMIN_SENHA
    ):

        session["administrador"] = True

        return jsonify(
            {
                "sucesso": True
            }
        )

    return jsonify(
        {
            "sucesso": False,
            "erro": "E-mail ou senha de administrador incorretos."
        }
    ), 401


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "administrador",
        None
    )

    return redirect(
        url_for("admin")
    )


# =========================================
# ÁREA DO ADMINISTRADOR
# =========================================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


@app.route("/admin/pedidos")
def admin_pedidos():

    if not session.get(
        "administrador",
        False
    ):

        return jsonify(
            {
                "sucesso": False,
                "erro": "Acesso não autorizado."
            }
        ), 401

    conexao = conectar_banco()

    pedidos = conexao.execute(
        """
        SELECT
            id,
            data_pedido,
            total,
            status
        FROM pedidos
        ORDER BY id DESC
        """
    ).fetchall()

    resultado = []

    for pedido in pedidos:

        itens = conexao.execute(
            """
            SELECT
                itens_pedido.produto_id,
                produtos.nome,
                itens_pedido.quantidade,
                itens_pedido.preco
            FROM itens_pedido
            INNER JOIN produtos
                ON produtos.id = itens_pedido.produto_id
            WHERE itens_pedido.pedido_id = ?
            """,
            (pedido["id"],)
        ).fetchall()

        lista_itens = []

        for item in itens:

            lista_itens.append(
                {
                    "produto_id": item["produto_id"],
                    "nome": item["nome"],
                    "quantidade": item["quantidade"],
                    "preco": item["preco"]
                }
            )

        resultado.append(
            {
                "id": pedido["id"],
                "data_pedido": pedido["data_pedido"],
                "total": pedido["total"],
                "status": pedido["status"],
                "itens": lista_itens
            }
        )

    conexao.close()

    return jsonify(
        {
            "sucesso": True,
            "pedidos": resultado
        }
    )


# =========================================
# CANCELAR PEDIDO
# =========================================

@app.route(
    "/admin/cancelar/<int:pedido_id>",
    methods=["POST"]
)
def cancelar_pedido(pedido_id):

    if not session.get(
        "administrador",
        False
    ):

        return jsonify(
            {
                "sucesso": False,
                "erro": "Acesso não autorizado."
            }
        ), 401

    conexao = conectar_banco()

    try:

        pedido = conexao.execute(
            """
            SELECT *
            FROM pedidos
            WHERE id = ?
            """,
            (pedido_id,)
        ).fetchone()

        if not pedido:

            return jsonify(
                {
                    "sucesso": False,
                    "erro": "Pedido não encontrado."
                }
            ), 404

        if pedido["status"] == "Cancelado":

            return jsonify(
                {
                    "sucesso": False,
                    "erro": "Este pedido já foi cancelado."
                }
            ), 400

        itens = conexao.execute(
            """
            SELECT
                produto_id,
                quantidade
            FROM itens_pedido
            WHERE pedido_id = ?
            """,
            (pedido_id,)
        ).fetchall()

        # Devolve os produtos ao estoque
        for item in itens:

            conexao.execute(
                """
                UPDATE produtos
                SET quantidade = quantidade + ?
                WHERE id = ?
                """,
                (
                    item["quantidade"],
                    item["produto_id"]
                )
            )

        # Marca o pedido como cancelado
        conexao.execute(
            """
            UPDATE pedidos
            SET status = 'Cancelado'
            WHERE id = ?
            """,
            (pedido_id,)
        )

        conexao.commit()

        return jsonify(
            {
                "sucesso": True,
                "mensagem": (
                    f"Pedido #{pedido_id} "
                    "cancelado com sucesso. "
                    "O estoque foi devolvido."
                )
            }
        )

    except Exception:

        conexao.rollback()

        return jsonify(
            {
                "sucesso": False,
                "erro": (
                    "Não foi possível "
                    "cancelar o pedido."
                )
            }
        ), 500

    finally:

        conexao.close()


# =========================================
# RELATÓRIOS
# =========================================

@app.route("/relatorios")
def relatorios():

    periodo = request.args.get(
        "periodo",
        "semanal"
    )

    dados_ficticios = {
        "diario": [37, 54, 42],
        "semanal": [128, 167, 145],
        "mensal": [512, 476, 589]
    }

    if periodo not in dados_ficticios:
        periodo = "semanal"

    conexao = conectar_banco()

    nomes_produtos = conexao.execute(
        """
        SELECT nome
        FROM produtos
        ORDER BY id
        """
    ).fetchall()

    vendas_reais = conexao.execute(
        """
        SELECT
            produtos.nome,
            COALESCE(
                SUM(vendas.quantidade),
                0
            ) AS total_vendido
        FROM produtos
        LEFT JOIN vendas
            ON produtos.id = vendas.produto_id
        GROUP BY produtos.id
        ORDER BY produtos.id
        """
    ).fetchall()

    conexao.close()

    nomes = [
        produto["nome"]
        for produto in nomes_produtos
    ]

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

        quantidades = dados_ficticios[
            periodo
        ]

    return render_template(
        "relatorios.html",
        periodo=periodo,
        titulo_periodo="",
        nomes=nomes,
        quantidades=quantidades
    )


# =========================================
# EXECUÇÃO
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )