from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

BANCO = "padaria.db"


def conectar_banco():

    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    return conexao


# =========================================
# INÍCIO
# =========================================

@app.route("/api")
def inicio_api():

    return jsonify(
        {
            "nome": "API Padaria 4 Gerações",
            "status": "online",
            "versao": "1.1",
            "endpoints": [
                "GET /api/produtos",
                "GET /api/produtos/<id>",
                "POST /api/produtos",
                "PUT /api/produtos/<id>",
                "DELETE /api/produtos/<id>",
                "GET /api/pedidos"
            ]
        }
    )


# =========================================
# LISTAR PRODUTOS
# =========================================

@app.route(
    "/api/produtos",
    methods=["GET"]
)
def listar_produtos():

    conexao = conectar_banco()

    produtos = conexao.execute(
        """
        SELECT
            id,
            nome,
            preco,
            quantidade,
            descricao,
            categoria,
            imagem,
            avaliacao,
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
                "descricao": produto["descricao"],
                "categoria": produto["categoria"],
                "imagem": produto["imagem"],
                "avaliacao": produto["avaliacao"],
                "custo_producao": produto["custo_producao"],
                "lucro": lucro
            }
        )

    return jsonify(lista)


# =========================================
# BUSCAR PRODUTO
# =========================================

@app.route(
    "/api/produtos/<int:id>",
    methods=["GET"]
)
def buscar_produto(id):

    conexao = conectar_banco()

    produto = conexao.execute(
        """
        SELECT *
        FROM produtos
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    conexao.close()

    if not produto:

        return jsonify(
            {
                "erro": "Produto não encontrado."
            }
        ), 404

    return jsonify(
        {
            "id": produto["id"],
            "nome": produto["nome"],
            "preco": produto["preco"],
            "quantidade": produto["quantidade"],
            "descricao": produto["descricao"],
            "categoria": produto["categoria"],
            "imagem": produto["imagem"],
            "avaliacao": produto["avaliacao"],
            "custo_producao": produto["custo_producao"],
            "lucro": (
                produto["preco"]
                - produto["custo_producao"]
            )
        }
    )


# =========================================
# CRIAR PRODUTO
# =========================================

@app.route(
    "/api/produtos",
    methods=["POST"]
)
def criar_produto():

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify(
            {
                "erro": "Envie os dados em JSON."
            }
        ), 400

    nome = dados.get("nome")
    preco = dados.get("preco")
    quantidade = dados.get("quantidade")
    descricao = dados.get(
        "descricao",
        ""
    )
    categoria = dados.get(
        "categoria",
        ""
    )
    imagem = dados.get(
        "imagem",
        ""
    )
    avaliacao = dados.get(
        "avaliacao",
        5.0
    )
    custo_producao = dados.get(
        "custo_producao",
        0
    )

    if (
        nome is None
        or preco is None
        or quantidade is None
    ):

        return jsonify(
            {
                "erro": (
                    "Nome, preço e quantidade "
                    "são obrigatórios."
                )
            }
        ), 400

    try:

        preco = float(preco)

        quantidade = int(
            quantidade
        )

        avaliacao = float(
            avaliacao
        )

        custo_producao = float(
            custo_producao
        )

    except (ValueError, TypeError):

        return jsonify(
            {
                "erro": (
                    "Preço, quantidade, "
                    "avaliação e custo devem "
                    "ser numéricos."
                )
            }
        ), 400

    conexao = conectar_banco()

    cursor = conexao.execute(
        """
        INSERT INTO produtos
        (
            nome,
            preco,
            quantidade,
            descricao,
            categoria,
            imagem,
            avaliacao,
            custo_producao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            preco,
            quantidade,
            descricao,
            categoria,
            imagem,
            avaliacao,
            custo_producao
        )
    )

    conexao.commit()

    novo_id = cursor.lastrowid

    conexao.close()

    return jsonify(
        {
            "mensagem":
                "Produto criado com sucesso.",
            "id":
                novo_id
        }
    ), 201


# =========================================
# ATUALIZAR PRODUTO
# =========================================

@app.route(
    "/api/produtos/<int:id>",
    methods=["PUT"]
)
def atualizar_produto(id):

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify(
            {
                "erro":
                    "Envie os dados em JSON."
            }
        ), 400

    conexao = conectar_banco()

    produto = conexao.execute(
        """
        SELECT *
        FROM produtos
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if not produto:

        conexao.close()

        return jsonify(
            {
                "erro":
                    "Produto não encontrado."
            }
        ), 404

    nome = dados.get(
        "nome",
        produto["nome"]
    )

    preco = dados.get(
        "preco",
        produto["preco"]
    )

    quantidade = dados.get(
        "quantidade",
        produto["quantidade"]
    )

    descricao = dados.get(
        "descricao",
        produto["descricao"]
    )

    categoria = dados.get(
        "categoria",
        produto["categoria"]
    )

    imagem = dados.get(
        "imagem",
        produto["imagem"]
    )

    avaliacao = dados.get(
        "avaliacao",
        produto["avaliacao"]
    )

    custo_producao = dados.get(
        "custo_producao",
        produto["custo_producao"]
    )

    try:

        preco = float(preco)
        quantidade = int(quantidade)
        avaliacao = float(avaliacao)
        custo_producao = float(
            custo_producao
        )

    except (ValueError, TypeError):

        conexao.close()

        return jsonify(
            {
                "erro":
                    "Os valores numéricos "
                    "são inválidos."
            }
        ), 400

    conexao.execute(
        """
        UPDATE produtos
        SET
            nome = ?,
            preco = ?,
            quantidade = ?,
            descricao = ?,
            categoria = ?,
            imagem = ?,
            avaliacao = ?,
            custo_producao = ?
        WHERE id = ?
        """,
        (
            nome,
            preco,
            quantidade,
            descricao,
            categoria,
            imagem,
            avaliacao,
            custo_producao,
            id
        )
    )

    conexao.commit()

    conexao.close()

    return jsonify(
        {
            "mensagem":
                "Produto atualizado com sucesso."
        }
    )


# =========================================
# EXCLUIR PRODUTO
# =========================================

@app.route(
    "/api/produtos/<int:id>",
    methods=["DELETE"]
)
def excluir_produto(id):

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
                "erro":
                    "Produto não encontrado."
            }
        ), 404

    conexao.execute(
        """
        DELETE FROM produtos
        WHERE id = ?
        """,
        (id,)
    )

    conexao.commit()

    conexao.close()

    return jsonify(
        {
            "mensagem":
                "Produto excluído com sucesso."
        }
    )


# =========================================
# PEDIDOS
# =========================================

@app.route(
    "/api/pedidos",
    methods=["GET"]
)
def listar_pedidos():

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
                produtos.nome,
                itens_pedido.quantidade,
                itens_pedido.preco,
                itens_pedido.custo_producao
            FROM itens_pedido

            INNER JOIN produtos
                ON produtos.id =
                   itens_pedido.produto_id

            WHERE itens_pedido.pedido_id = ?
            """,
            (pedido["id"],)
        ).fetchall()

        lista_itens = []

        for item in itens:

            lista_itens.append(
                {
                    "produto":
                        item["nome"],

                    "quantidade":
                        item["quantidade"],

                    "preco":
                        item["preco"],

                    "custo_producao":
                        item["custo_producao"]
                }
            )

        resultado.append(
            {
                "id":
                    pedido["id"],

                "data":
                    pedido["data_pedido"],

                "total":
                    pedido["total"],

                "status":
                    pedido["status"],

                "itens":
                    lista_itens
            }
        )

    conexao.close()

    return jsonify(resultado)


# =========================================
# INICIAR API
# =========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )