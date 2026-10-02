from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

app.secret_key = "padaria4geracoes"


# =========================================
# BANCO DE DADOS
# =========================================

def conectar_banco():
    conexao = sqlite3.connect("padaria.db")
    conexao.row_factory = sqlite3.Row
    return conexao


def adicionar_coluna_se_nao_existir(conexao, tabela, coluna, definicao):

    colunas = conexao.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    nomes_colunas = [
        coluna_banco["name"]
        for coluna_banco in colunas
    ]

    if coluna not in nomes_colunas:

        conexao.execute(
            f"""
            ALTER TABLE {tabela}
            ADD COLUMN {coluna} {definicao}
            """
        )


def criar_tabelas():

    conexao = conectar_banco()

    # Tabela de vendas
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data_venda TEXT NOT NULL,
            pedido_id INTEGER,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
    )

    # Tabela de pedidos
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

    # Tabela de itens dos pedidos
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

    # Colunas novas
    adicionar_coluna_se_nao_existir(
        conexao,
        "produtos",
        "custo_producao",
        "REAL DEFAULT 0"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "produtos",
        "avaliacao",
        "REAL DEFAULT 5.0"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "vendas",
        "pedido_id",
        "INTEGER"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "itens_pedido",
        "custo_producao",
        "REAL DEFAULT 0"
    )

    # Valores iniciais de produção para os produtos existentes
    conexao.execute(
        """
        UPDATE produtos
        SET custo_producao = 0.40
        WHERE nome = 'Pão francês'
        AND (custo_producao IS NULL OR custo_producao = 0)
        """
    )

    conexao.execute(
        """
        UPDATE produtos
        SET custo_producao = 3.50
        WHERE nome = 'Pão de forma'
        AND (custo_producao IS NULL OR custo_producao = 0)
        """
    )

    conexao.execute(
        """
        UPDATE produtos
        SET custo_producao = 2.80
        WHERE nome = 'Pão de milho'
        AND (custo_producao IS NULL OR custo_producao = 0)
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
        "SELECT * FROM produtos ORDER BY id"
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
        "SELECT * FROM produtos ORDER BY id"
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
        """
        SELECT quantidade
        FROM produtos
        WHERE id = ?
        """,
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

        carrinho[id] = (
            quantidade_atual + 1
        )

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
            """
            SELECT *
            FROM produtos
            WHERE id = ?
            """,
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
# LOGIN
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
            """
            SELECT *
            FROM produtos
            WHERE id = ?
            """,
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

        for id, quantidade in carrinho.items():

            produto = conexao.execute(
                """
                SELECT *
                FROM produtos
                WHERE id = ?
                """,
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
                {
                    "id": produto["id"],
                    "quantidade": quantidade,
                    "preco": produto["preco"],
                    "custo_producao": produto["custo_producao"]
                }
            )

        data_pedido = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Cria pedido
        cursor = conexao.execute(
            """
            INSERT INTO pedidos
            (
                data_pedido,
                total,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                data_pedido,
                total,
                "Concluído"
            )
        )

        pedido_id = cursor.lastrowid

        # Cria itens e atualiza estoque
        for item in produtos_pagamento:

            conexao.execute(
                """
                INSERT INTO itens_pedido
                (
                    pedido_id,
                    produto_id,
                    quantidade,
                    preco,
                    custo_producao
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    item["id"],
                    item["quantidade"],
                    item["preco"],
                    item["custo_producao"]
                )
            )

            conexao.execute(
                """
                UPDATE produtos
                SET quantidade = quantidade - ?
                WHERE id = ?
                """,
                (
                    item["quantidade"],
                    item["id"]
                )
            )

            # Registra venda ligada ao pedido
            conexao.execute(
                """
                INSERT INTO vendas
                (
                    produto_id,
                    quantidade,
                    data_venda,
                    pedido_id
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    item["id"],
                    item["quantidade"],
                    data_pedido,
                    pedido_id
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
# ADMINISTRADOR
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
            "erro": (
                "E-mail ou senha de administrador "
                "incorretos."
            )
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


@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# =========================================
# PRODUTOS DO ADMINISTRADOR
# =========================================

@app.route("/admin/produtos")
def admin_produtos():

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

    produtos = conexao.execute(
        """
        SELECT
            id,
            nome,
            preco,
            quantidade,
            custo_producao
        FROM produtos
        ORDER BY id
        """
    ).fetchall()

    conexao.close()

    lista = []

    for produto in produtos:

        lucro = (
            produto["preco"]
            - produto["custo_producao"]
        )

        lista.append(
            {
                "id": produto["id"],
                "nome": produto["nome"],
                "preco": produto["preco"],
                "quantidade": produto["quantidade"],
                "custo_producao": produto["custo_producao"],
                "lucro": lucro
            }
        )

    return jsonify(
        {
            "sucesso": True,
            "produtos": lista
        }
    )


@app.route(
    "/admin/produtos/<int:id>",
    methods=["PUT"]
)
def atualizar_produto_admin(id):

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

    dados = request.get_json(
        silent=True
    ) or {}

    nome = dados.get(
        "nome",
        ""
    ).strip()

    preco = dados.get(
        "preco"
    )

    custo_producao = dados.get(
        "custo_producao"
    )

    if not nome:

        return jsonify(
            {
                "sucesso": False,
                "erro": "Informe o nome do produto."
            }
        ), 400

    try:

        preco = float(preco)
        custo_producao = float(custo_producao)

    except (TypeError, ValueError):

        return jsonify(
            {
                "sucesso": False,
                "erro": (
                    "Preço e custo de produção "
                    "devem ser números."
                )
            }
        ), 400

    if preco < 0 or custo_producao < 0:

        return jsonify(
            {
                "sucesso": False,
                "erro": (
                    "Os valores não podem ser negativos."
                )
            }
        ), 400

    conexao = conectar_banco()

    produto = conexao.execute(
        """
        SELECT id
        FROM produtos
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if not produto:

        conexao.close()

        return jsonify(
            {
                "sucesso": False,
                "erro": "Produto não encontrado."
            }
        ), 404

    conexao.execute(
        """
        UPDATE produtos
        SET
            nome = ?,
            preco = ?,
            custo_producao = ?
        WHERE id = ?
        """,
        (
            nome,
            preco,
            custo_producao,
            id
        )
    )

    conexao.commit()
    conexao.close()

    return jsonify(
        {
            "sucesso": True,
            "mensagem": (
                "Produto atualizado com sucesso."
            )
        }
    )


# =========================================
# PEDIDOS DO ADMINISTRADOR
# =========================================

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

        # Devolve ao estoque
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

        # Retira a venda dos relatórios
        conexao.execute(
            """
            DELETE FROM vendas
            WHERE pedido_id = ?
            """,
            (pedido_id,)
        )

        # Marca como cancelado
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

    # Somente administrador
    if not session.get(
        "administrador",
        False
    ):

        return redirect(
            url_for("admin")
        )

    periodo = request.args.get(
        "periodo",
        "semanal"
    )

    if periodo not in [
        "diario",
        "semanal",
        "mensal"
    ]:

        periodo = "semanal"

    if periodo == "diario":
        intervalo = "-1 day"

    elif periodo == "mensal":
        intervalo = "-30 days"

    else:
        intervalo = "-7 days"

    conexao = conectar_banco()

    produtos = conexao.execute(
        """
        SELECT
            id,
            nome
        FROM produtos
        ORDER BY id
        """
    ).fetchall()

    dados = []

    for produto in produtos:

        resultado = conexao.execute(
            f"""
            SELECT
                COALESCE(
                    SUM(
                        itens_pedido.quantidade
                        * itens_pedido.preco
                    ),
                    0
                ) AS vendas,

                COALESCE(
                    SUM(
                        itens_pedido.quantidade
                        * itens_pedido.custo_producao
                    ),
                    0
                ) AS producao

            FROM itens_pedido

            INNER JOIN pedidos
                ON pedidos.id = itens_pedido.pedido_id

            WHERE itens_pedido.produto_id = ?

            AND pedidos.status != 'Cancelado'

            AND datetime(pedidos.data_pedido)
                >= datetime('now', 'localtime', ?)
            """,
            (
                produto["id"],
                intervalo
            )
        ).fetchone()

        vendas = float(
            resultado["vendas"] or 0
        )

        producao = float(
            resultado["producao"] or 0
        )

        lucro = vendas - producao

        dados.append(
            {
                "nome": produto["nome"],
                "vendas": round(vendas, 2),
                "producao": round(producao, 2),
                "lucro": round(lucro, 2)
            }
        )

    conexao.close()

    nomes = [
        item["nome"]
        for item in dados
    ]

    vendas = [
        item["vendas"]
        for item in dados
    ]

    producao = [
        item["producao"]
        for item in dados
    ]

    lucro = [
        item["lucro"]
        for item in dados
    ]

    return render_template(
        "relatorios.html",
        periodo=periodo,
        nomes=nomes,
        vendas=vendas,
        producao=producao,
        lucro=lucro
    )


# =========================================
# EXECUÇÃO
# =========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )