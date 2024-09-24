from flask import Flask, request, jsonify
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


# Carrega as variáveis de ambiente do arquivo .cred (se disponível)
load_dotenv('.cred')


# Configurações para conexão com o banco de dados usando variáveis de ambiente
config = {
    'host': os.getenv('DB_HOST', 'localhost'),  # Obtém o host do banco de dados da variável de ambiente
    'user': os.getenv('DB_USER'),  # Obtém o usuário do banco de dados da variável de ambiente
    'password': os.getenv('DB_PASSWORD'),  # Obtém a senha do banco de dados da variável de ambiente
    'database': os.getenv('DB_NAME', 'db_desafio'),  # Obtém o nome do banco de dados da variável de ambiente
    'port': int(os.getenv('DB_PORT', 3306)),  # Obtém a porta do banco de dados da variável de ambiente
    'ssl_ca': os.getenv('SSL_CA_PATH')  # Caminho para o certificado SSL
}


# Função para conectar ao banco de dados
def connect_db():
    """Estabelece a conexão com o banco de dados usando as configurações fornecidas."""
    try:
        # Tenta estabelecer a conexão com o banco de dados usando mysql-connector-python
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as err:
        # Em caso de erro, imprime a mensagem de erro
        print(f"Erro: {err}")
        return None

# -------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# Clientes

@app.route('/clientes', methods=['POST'])
def post_clientes():
    success = False

    # entrada de dados recebida via requisição HTTP POST (json)
    entrada_dados = request.json
    nome = entrada_dados.get('nome')
    email = entrada_dados.get('email')
    cpf = entrada_dados.get('cpf')
    senha = entrada_dados.get('senha')

    # Validação básica dos dados
    if not all([nome, cpf, email, senha]):
        return {'erro': 'Todos os campos são obrigatórios.'}, 400

    conn = connect_db()
    cliente_id = None
    if conn.is_connected():
        try:
            cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
            sql = "INSERT INTO tbl_clientes (nome, cpf, email, senha) VALUES (%s, %s, %s, %s)"  # Comando SQL para inserir um aluno
            values = (nome, cpf, email, senha)  # Dados a serem inseridos

            # Executa o comando SQL com os valores fornecidos
            print(f"Executando SQL: {sql} com valores: {values}")
            cursor.execute(sql, values)
            
            # Confirma a transação no banco de dados
            conn.commit()

            # Obtém o ID do registro recém-inserido
            cliente_id = cursor.lastrowid
            success = True
            
        except Error as err:
            # Em caso de erro na inserção, imprime a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    
    if success:
        resp = {"id": cliente_id, "nome": nome, "cpf": cpf, "email": email, "senha": senha}
        return resp, 201
    else:
        resp = {"erro": "Erro ao inserir cliente", "message": error}
        return resp, 500
    

@app.route('/clientes', methods=['GET'])
def get_clientes():
    lista_cliente = []
    success = False
    conn = connect_db()  # Conecta ao banco de dados
    if conn.is_connected():
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_clientes"  # Comando SQL para selecionar todos os clientes

        try:
            # Executa o comando SQL
            cursor.execute(sql)
            # Recupera todos os registros da consulta
            clientes = cursor.fetchall()
            
            for cliente in clientes:
                lista_cliente.append({
                    "ID": cliente['id'],
                    "Nome": cliente['nome'],
                    "Email": cliente['email'],
                    "CPF": cliente['cpf'],
                    "Senha": cliente['senha']
                })
            success = True
        except Error as err:
            # Em caso de erro na busca, captura a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        error = 'Falha na conexão com o banco de dados.'

    if success:
        resp = {'clientes': lista_cliente}
        return resp, 200
    else:
        resp = {"erro": "Erro ao buscar clientes", "message": error}
        return resp, 500


@app.route('/clientes/<int:cliente_id>', methods=['GET'])
def get_cliente_id(cliente_id):
    json_cliente = {"cliente": {}}
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_clientes WHERE id = %s"  # Comando SQL para buscar um aluno pelo ID

        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (cliente_id,))
            # Recupera o resultado da consulta
            cliente = cursor.fetchone()
            # Verifica se o aluno foi encontrado e imprime seus detalhes
            if cliente:
                json_cliente["cliente"] = {"ID": cliente['id'], "Nome": cliente['nome'], "CPF": cliente['cpf'], "Senha": cliente['senha'], 'Email': cliente['email']}
                return json_cliente
            else:
                return "Usuario não encontrado!"
        except Error as err:
            error = str(err)
            resp = {"error": f"Erro ao inserir aluno: {error}", 'message': error}  
            return resp, 500      
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/clientes/<int:cliente_id>', methods=['PUT'])
def put_cliente(cliente_id):
    
    nome = request.json.get('nome')
    cpf = request.json.get('cpf')
    email = request.json.get('email')
    senha = request.json.get('senha')

    # Validação básica dos dados
    if not all([nome, cpf, email, senha]):
        return {'erro': 'Todos os campos são obrigatórios.'}, 400

    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()
        sql = """
        UPDATE tbl_clientes
        SET nome = %s, cpf = %s, email = %s, senha = %s
        WHERE id = %s
        """
        values = (nome, cpf, email, senha, cliente_id)

        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount:
                # Retorna uma resposta de sucesso
                return {'mensagem': 'Cliente atualizado com sucesso!'}, 200
            else:
                # Cliente não encontrado
                return {'erro': 'Cliente não encontrado.'}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna uma mensagem de erro
            return {'erro': f'Erro ao atualizar cliente: {err}'}, 500
        finally:
            cursor.close()
            conn.close()
    else:
        return {'erro': 'Falha na conexão com o banco de dados.'}, 500


@app.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        sql = "DELETE FROM tbl_clientes WHERE id = %s"  # Comando SQL para deletar um aluno pelo ID

        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (cliente_id,))
            # Confirma a transação no banco de dados
            conn.commit()
            # Verifica se alguma linha foi afetada (deletada)
            if cursor.rowcount:
                return {'mensagem': 'Cliente deletado com sucesso!'}, 200
            
            else:
                return {'error': 'Cliente não encontrado.'}, 404
            
        except Error as err:
            # Em caso de erro na deleção, imprime a mensagem de erro
            error = str(err)
            return {'error': f'Erro ao deletar cliente: {error}'}, 500
        
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()



# Fornecedores

@app.route('/fornecedores', methods=['POST'])
def post_fornecedor():
    success = False

    # entrada de dados recebida via requisição HTTP POST (json)
    entrada_dados = request.json
    nome = entrada_dados.get('nome')
    email = entrada_dados.get('email')
    cnpj = entrada_dados.get('cnpj')


    conn = connect_db()
    fornecedor_id = None
    if conn.is_connected():
        try:
            cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
            sql = "INSERT INTO tbl_fornecedores (nome, cnpj, email) VALUES (%s, %s, %s)"  # Comando SQL para inserir um aluno
            values = (nome, cnpj, email)  # Dados a serem inseridos


            # Executa o comando SQL com os valores fornecidos
            print(f"Executando SQL: {sql} com valores: {values}")
            cursor.execute(sql, values)
           
            # Confirma a transação no banco de dados
            conn.commit()


            # Obtém o ID do registro recém-inserido
            fornecedor_id = cursor.lastrowid
            success = True
           
        except Error as err:
            # Em caso de erro na inserção, imprime a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
   
    if success:
        resp = {"id": fornecedor_id, "nome": nome, "cnpj": cnpj, "email": email}
        return resp, 201
    else:
        resp = {"erro": "Erro ao inserir fornecedore", "message": error}
        return resp, 500


@app.route('/fornecedores', methods=['GET'])
def get_fornecedores():
    lista_fornecedores = []
    success = False
    conn = connect_db()  # Conecta ao banco de dados
    if conn.is_connected():
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_fornecedores"  # Comando SQL para selecionar todos os clientes


        try:
            # Executa o comando SQL
            cursor.execute(sql)
            # Recupera todos os registros da consulta
            fornecedores = cursor.fetchall()
           
            for fornecedor in fornecedores:
                lista_fornecedores.append({
                    "ID": fornecedor['id'],
                    "Nome": fornecedor['nome'],
                    "Email": fornecedor['email'],
                    "CNPJ": fornecedor['cnpj'],
                })
            success = True
        except Error as err:
            # Em caso de erro na busca, captura a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        error = 'Falha na conexão com o banco de dados.'


    if success:
        resp = {'fornecedores': lista_fornecedores}
        return resp, 200
    else:
        resp = {"erro": "Erro ao buscar fornecedores", "message": error}
        return resp, 500


@app.route('/fornecedores/<int:fornecedor_id>', methods=['GET'])
def get_fornecedor_id(fornecedor_id):
    json_fornecedor = {"fornecedor": {}}
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_fornecedores WHERE id = %s"  # Comando SQL para buscar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (fornecedor_id,))
            # Recupera o resultado da consulta
            fornecedor = cursor.fetchone()
            # Verifica se o aluno foi encontrado e imprime seus detalhes
            if fornecedor:
                json_fornecedor["fornecedor"] = {
                    "ID": fornecedor['id'], 
                    "Nome": fornecedor['nome'], 
                    "CNPJ": fornecedor['cnpj'], 
                    'Email': fornecedor['email']
                    }
                
                return json_fornecedor
            else:
                return "fornecedor não encontrado!"
        except Error as err:
            error = str(err)
            resp = {"error": f"Erro ao inserir fornecedor: {error}", 'message': error}  
            return resp, 500      
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/fornecedores/<int:fornecedor_id>', methods=['PUT'])
def put_fornecedor(fornecedor_id):
   
    nome = request.json.get('nome')
    cnpj = request.json.get('cnpj')
    email = request.json.get('email')


    # Validação básica dos dados
    if not all([nome, cnpj, email]):
        return {'erro': 'Todos os campos são obrigatórios.'}, 400


    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()
        sql = """
        UPDATE tbl_fornecedores
        SET nome = %s, cnpj = %s, email = %s
        WHERE id = %s
        """
        values = (nome, cnpj, email, fornecedor_id)


        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount:
                # Retorna uma resposta de sucesso
                return {'mensagem': 'fornecedor atualizado com sucesso!'}, 200
            else:
                # Cliente não encontrado
                return {'erro': 'fornecedor não encontrado.'}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna uma mensagem de erro
            return {'erro': f'Erro ao atualizar fornecedor: {err}'}, 500
        finally:
            cursor.close()
            conn.close()
    else:
        return {'erro': 'Falha na conexão com o banco de dados.'}, 500


@app.route('/fornecedores/<int:fornecedor_id>', methods=['DELETE'])
def delete_fornecedor(fornecedor_id):
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        sql = "DELETE FROM tbl_fornecedores WHERE id = %s"  # Comando SQL para deletar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (fornecedor_id,))
            # Confirma a transação no banco de dados
            conn.commit()
            # Verifica se alguma linha foi afetada (deletada)
            if cursor.rowcount:
                return {'mensagem': 'fornecedor deletado com sucesso!'}, 200
           
            else:
                return {'error': 'fornecedor não encontrado.'}, 404
           
        except Error as err:
            # Em caso de erro na deleção, imprime a mensagem de erro
            error = str(err)
            return {'error': f'Erro ao deletar fornecedor: {error}'}, 500
       
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()




# Produtos

@app.route('/produtos', methods=['POST'])
def post_produto():
    success = False


    # entrada de dados recebida via requisição HTTP POST (json)
    entrada_dados = request.json
    nome = entrada_dados.get('nome')
    descricao = entrada_dados.get('descricao')
    qtd_em_estoque = entrada_dados.get('qtd_em_estoque')
    preco = entrada_dados.get('preco')
    fornecedor_id = entrada_dados.get('fornecedor_id')
    custo_no_fornecedor = entrada_dados.get('custo_no_fornecedor')




    conn = connect_db()
    produto_id = None
    if conn.is_connected():
        try:
            cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
            sql = "INSERT INTO tbl_produtos (nome, qtd_em_estoque, descricao, preco, fornecedor_id, custo_no_fornecedor) VALUES (%s, %s, %s, %s, %s, %s)"  # Comando SQL para inserir um aluno
            values = (nome, qtd_em_estoque, descricao, preco, fornecedor_id, custo_no_fornecedor)  # Dados a serem inseridos


            # Executa o comando SQL com os valores fornecidos
            print(f"Executando SQL: {sql} com valores: {values}")
            cursor.execute(sql, values)
           
            # Confirma a transação no banco de dados
            conn.commit()


            # Obtém o ID do registro recém-inserido
            produto_id = cursor.lastrowid
            success = True
           
        except Error as err:
            # Em caso de erro na inserção, imprime a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
   
    if success:
        resp = {"id": produto_id, "nome": nome, "qtd_em_estoque": qtd_em_estoque, "descricao": descricao, "preco": preco, "fornecedor_id": fornecedor_id, "custo_no_fornecedor": custo_no_fornecedor}
        return resp, 201
    else:
        resp = {"erro": "Erro ao inserir produto", "message": error}
        return resp, 500


@app.route('/produtos', methods=['GET'])
def get_produtos():
    lista_produtos = []
    success = False
    conn = connect_db()  # Conecta ao banco de dados
    if conn.is_connected():
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_produtos"  # Comando SQL para selecionar todos os clientes


        try:
            # Executa o comando SQL
            cursor.execute(sql)
            # Recupera todos os registros da consulta
            produtos = cursor.fetchall()
           
            for produto in produtos:
                lista_produtos.append({
                    "ID": produto['id'],
                    "Nome": produto['nome'],
                    "Descricao": produto['descricao'],
                    "Preco": produto['preco'],
                    "Qtd_em_estoque": produto['qtd_em_estoque'],
                    "Fornecedor_ID": produto['fornecedor_id'],
                    "Custo_no_Fornecedor": produto['custo_no_fornecedor']
                })

            success = True
        except Error as err:
            # Em caso de erro na busca, captura a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        error = 'Falha na conexão com o banco de dados.'


    if success:
        resp = {'produtos': lista_produtos}
        return resp, 200
    else:
        resp = {"erro": "Erro ao buscar produtos", "message": error}
        return resp, 500


@app.route('/produtos/<int:produto_id>', methods=['GET'])
def get_produto_id(produto_id):
    json_produto = {"produto": {}}
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_produtos WHERE id = %s"  # Comando SQL para buscar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (produto_id,))
            # Recupera o resultado da consulta
            produto = cursor.fetchone()
            # Verifica se o aluno foi encontrado e imprime seus detalhes
            if produto:
                json_produto["produto"] = {
                    "ID": produto['id'],
                    "Nome": produto['nome'],
                    "Descricao": produto['descricao'],
                    "Preco": produto['preco'],
                    "Qtd_em_estoque": produto['qtd_em_estoque'],
                    "Fornecedor_ID": produto['fornecedor_id'],
                    "Custo_no_Fornecedor": produto['custo_no_fornecedor']
                    }
               
                return json_produto


            else:
                return "produto não encontrado!"
        except Error as err:
            error = str(err)
            resp = {"error": f"Erro ao inserir produto: {error}", 'message': error}  
            return resp, 500      
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/produtos/<int:produto_id>', methods=['PUT'])
def put_produto(produto_id):
   
    entrada_dados = request.json

    nome = entrada_dados.get('nome')
    descricao = entrada_dados.get('descricao')
    qtd_em_estoque = entrada_dados.get('qtd_em_estoque')
    preco = entrada_dados.get('preco')
    fornecedor_id = entrada_dados.get('fornecedor_id')
    custo_no_fornecedor = entrada_dados.get('custo_no_fornecedor')


    # Validação básica dos dados
    if not all([nome, descricao, qtd_em_estoque, preco, fornecedor_id, custo_no_fornecedor, produto_id,]):
        return {'erro': 'Todos os campos são obrigatórios.'}, 400


    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()
        sql = """
        UPDATE tbl_produtos
        SET nome = %s, descricao = %s, qtd_em_estoque = %s, fornecedor_id = %s, preco = %s, custo_no_fornecedor = %s
        WHERE id = %s
        """
        values = (nome, descricao, qtd_em_estoque, fornecedor_id, preco, custo_no_fornecedor, produto_id)


        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount:
                # Retorna uma resposta de sucesso
                return {'mensagem': 'produto atualizado com sucesso!'}, 200
            else:
                # Cliente não encontrado
                return {'erro': 'produto não encontrado.'}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna uma mensagem de erro
            return {'erro': f'Erro ao atualizar produto: {err}'}, 500
        finally:
            cursor.close()
            conn.close()
    else:
        return {'erro': 'Falha na conexão com o banco de dados.'}, 500

@app.route('/produtos/<int:produto_id>', methods=['DELETE'])
def delete_produto(produto_id):
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        sql = "DELETE FROM tbl_produtos WHERE id = %s"  # Comando SQL para deletar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (produto_id,))
            # Confirma a transação no banco de dados
            conn.commit()
            # Verifica se alguma linha foi afetada (deletada)
            if cursor.rowcount:
                return {'mensagem': 'produto deletado com sucesso!'}, 200
           
            else:
                return {'error': 'produto não encontrado.'}, 404
           
        except Error as err:
            # Em caso de erro na deleção, imprime a mensagem de erro
            error = str(err)
            return {'error': f'Erro ao deletar produto: {error}'}, 500
       
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


# Carrinho

@app.route('/carrinhos', methods=['POST'])
def post_carrinho():
    success = False

    # entrada de dados recebida via requisição HTTP POST (json)
    entrada_dados = request.json
    produto_id = entrada_dados.get('produto_id')
    quantidade = entrada_dados.get('quantidade')


    conn = connect_db()
    carrinho_id = None
    if conn.is_connected():
        try:
            cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
            sql = "INSERT INTO tbl_carrinho (produto_id, quantidade) VALUES (%s, %s)"  # Comando SQL para inserir um aluno
            values = (produto_id, quantidade)  # Dados a serem inseridos


            # Executa o comando SQL com os valores fornecidos
            print(f"Executando SQL: {sql} com valores: {values}")
            cursor.execute(sql, values)
           
            # Confirma a transação no banco de dados
            conn.commit()


            # Obtém o ID do registro recém-inserido
            carrinho_id = cursor.lastrowid
            success = True
           
        except Error as err:
            # Em caso de erro na inserção, imprime a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
   
    if success:
        resp = {"id": carrinho_id, "produto_id": produto_id, "quantidade": quantidade}
        return resp, 201
    else:
        resp = {"erro": "Erro ao inserir carrinho", "message": error}
        return resp, 500


@app.route('/carrinhos', methods=['GET'])
def get_carrinhos():
    lista_carrinhos = []
    success = False
    conn = connect_db()  # Conecta ao banco de dados
    if conn.is_connected():
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_carrinho"  # Comando SQL para selecionar todos os clientes


        try:
            # Executa o comando SQL
            cursor.execute(sql)
            # Recupera todos os registros da consulta
            carrinhos = cursor.fetchall()
           
            for carrinho in carrinhos:
                lista_carrinhos.append({
                    "ID": carrinho['id'],
                    "Produto_ID": carrinho['produto_id'],
                    "Quantidade": carrinho['quantidade']
                })
            success = True
        except Error as err:
            # Em caso de erro na busca, captura a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        error = 'Falha na conexão com o banco de dados.'


    if success:
        resp = {'carrinhos': lista_carrinhos}
        return resp, 200
    else:
        resp = {"erro": "Erro ao buscar carrinhos", "message": error}
        return resp, 500


@app.route('/carrinhos/<int:carrinho_id>', methods=['GET'])
def get_carrinho_id(carrinho_id):
    json_carrinho = {"carrinho": {}}
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_carrinho WHERE id = %s"  # Comando SQL para buscar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (carrinho_id,))
            # Recupera o resultado da consulta
            carrinho = cursor.fetchone()
            # Verifica se o aluno foi encontrado e imprime seus detalhes
            if carrinho:
                json_carrinho["carrinho"] = {
                    "ID": carrinho['id'],
                    "Produto_id": carrinho['produto_id'],
                    "Quantidade": carrinho['quantidade']
                    }
               
                return json_carrinho


            else:
                return "carrinho não encontrado!"
        except Error as err:
            error = str(err)
            resp = {"error": f"Erro ao inserir carrinho: {error}", 'message': error}  
            return resp, 500      
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/carrinhos/<int:carrinho_id>', methods=['PUT'])
def put_carrinho(carrinho_id):
   
    produto_id = request.json.get('produto_id')
    quantidade = request.json.get('quantidade')


    # Validação básica dos dados
    if not all([produto_id, quantidade]):
        return {'erro': 'Todos os campos são obrigatórios.'}, 400


    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()
        sql = """
        UPDATE tbl_carrinho
        SET produto_id = %s, quantidade = %s
        WHERE id = %s
        """
        values = (produto_id, quantidade, carrinho_id)


        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount:
                # Retorna uma resposta de sucesso
                return {'mensagem': 'carrinho atualizado com sucesso!'}, 200
            else:
                # Cliente não encontrado
                return {'erro': 'carrinho não encontrado.'}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna uma mensagem de erro
            return {'erro': f'Erro ao atualizar carrinho: {err}'}, 500
        finally:
            cursor.close()
            conn.close()
    else:
        return {'erro': 'Falha na conexão com o banco de dados.'}, 500


@app.route('/carrinhos/<int:carrinho_id>', methods=['DELETE'])
def delete_carrinho(carrinho_id):
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        sql = "DELETE FROM tbl_carrinho WHERE id = %s"  # Comando SQL para deletar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (carrinho_id,))
            # Confirma a transação no banco de dados
            conn.commit()
            # Verifica se alguma linha foi afetada (deletada)
            if cursor.rowcount:
                return {'mensagem': 'carrinho deletado com sucesso!'}, 200
           
            else:
                return {'error': 'carrinho não encontrado.'}, 404
           
        except Error as err:
            # Em caso de erro na deleção, imprime a mensagem de erro
            error = str(err)
            return {'error': f'Erro ao deletar carrinho: {error}'}, 500
       
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/carrinhos/cliente/<int:cliente_id>', methods=['GET'])
def lista_carrinhos_por_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return ({'error': 'Erro ao conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
        SELECT tbl_carrinho.id, tbl_carrinho.produto_id, tbl_carrinho.quantidade
        FROM tbl_carrinho
        INNER JOIN tbl_pedidos ON tbl_carrinho.id = tbl_pedidos.carrinho_id
        WHERE tbl_pedidos.cliente_id = %s
        """
        cursor.execute(sql, (cliente_id,))
        carrinhos = cursor.fetchall()

        if carrinhos:
            return jsonify(carrinhos), 200
        else:
            return jsonify({'message': 'Nenhum carrinho encontrado para este cliente'}), 404

    except Error as err:
        return jsonify({'error': f"Erro ao listar carrinhos: {err}"}), 400

    finally:
        cursor.close()
        conn.close()

# Pedidos

@app.route('/pedidos', methods=['POST'])
def post_pedido():
    success = False


    # entrada de dados recebida via requisição HTTP POST (json)
    entrada_dados = request.json
    cliente_id = entrada_dados.get('cliente_id')
    carrinho_id = entrada_dados.get('carrinho_id')
    data_hora = entrada_dados.get('data_hora')
    status = entrada_dados.get('status')




    conn = connect_db()
    pedido_id = None
    if conn.is_connected():
        try:
            cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
            sql = "INSERT INTO tbl_pedidos (cliente_id, data_hora, carrinho_id, status) VALUES (%s, %s, %s, %s)"  # Comando SQL para inserir um aluno
            values = (cliente_id, data_hora, carrinho_id, status)  # Dados a serem inseridos


            # Executa o coma    ndo SQL com os valores fornecidos
            print(f"Executando SQL: {sql} com valores: {values}")
            cursor.execute(sql, values)
           
            # Confirma a transação no banco de dados
            conn.commit()


            # Obtém o ID do registro recém-inserido
            pedido_id = cursor.lastrowid
            success = True
           
        except Error as err:
            # Em caso de erro na inserção, imprime a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
   
    if success:
        resp = {"id": pedido_id, "cliente_id": cliente_id, "data_hora": data_hora, "carrinho_id": carrinho_id, "status": status}
        return resp, 201
    else:
        resp = {"erro": "Erro ao inserir pedido", "message": error}
        return resp, 500
   

@app.route('/pedidos', methods=['GET'])
def get_pedidos():
    lista_pedidos = []
    success = False
    conn = connect_db()  # Conecta ao banco de dados
    if conn.is_connected():
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_pedidos"  # Comando SQL para selecionar todos os clientes


        try:
            # Executa o comando SQL
            cursor.execute(sql)
            # Recupera todos os registros da consulta
            pedidos = cursor.fetchall()
           
            for pedido in pedidos:
                lista_pedidos.append({
                    "ID": pedido['id'],
                    "Cliente_ID": pedido['cliente_id'],
                    "carrinho_id": pedido['carrinho_id'],
                    "data_hora": pedido['data_hora'],
                    "status": pedido['status']
                })
            success = True
        except Error as err:
            # Em caso de erro na busca, captura a mensagem de erro
            error = str(err)
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        error = 'Falha na conexão com o banco de dados.'


    if success:
        resp = {'pedidos': lista_pedidos}
        return resp, 200
    else:
        resp = {"erro": "Erro ao buscar pedidos", "message": error}
        return resp, 500


@app.route('/pedidos/<int:pedido_id>', methods=['GET'])
def get_pedido_id(pedido_id):
    json_pedido = {"pedido": {}}
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL
        sql = "SELECT * FROM tbl_pedidos WHERE id = %s"  # Comando SQL para buscar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (pedido_id,))
            # Recupera o resultado da consulta
            pedido = cursor.fetchone()
            # Verifica se o aluno foi encontrado e imprime seus detalhes
            if pedido:
                json_pedido["pedido"] = {
                    "ID": pedido['id'],
                    "Cliente_ID": pedido['cliente_id'],
                    "carrinho_id": pedido['carrinho_id'],
                    "data_hora": pedido['data_hora'],
                    "status": pedido['status']
                    }
               
                return json_pedido


            else:
                return "pedido não encontrado!"
        except Error as err:
            error = str(err)
            resp = {"error": f"Erro ao inserir pedido: {error}", 'message': error}  
            return resp, 500      
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/pedidos/<int:pedido_id>', methods=['PUT'])
def put_pedido(pedido_id):
   
    cliente_id = request.json.get('cliente_id')
    carrinho_id = request.json.get('carrinho_id')
    data_hora = request.json.get('data_hora')
    status = request.json.get('status')


    # Validação básica dos dados
    if not all([cliente_id, carrinho_id]):
        return {'erro': 'ID do cliente e do carrinho sao obrigatorios'}, 400


    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()
        sql = """
        UPDATE tbl_pedidos
        SET cliente_id = %s, carrinho_id = %s, data_hora = %s, status = %s
        WHERE id = %s
        """
        values = (cliente_id, carrinho_id, data_hora, status, pedido_id)


        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount:
                # Retorna uma resposta de sucesso
                return {'mensagem': 'pedido atualizado com sucesso!'}, 200
            else:
                # Cliente não encontrado
                return {'erro': 'pedido não encontrado.'}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna uma mensagem de erro
            return {'erro': f'Erro ao atualizar pedido: {err}'}, 500
        finally:
            cursor.close()
            conn.close()
    else:
        return {'erro': 'Falha na conexão com o banco de dados.'}, 500



@app.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        sql = "DELETE FROM tbl_pedidos WHERE id = %s"  # Comando SQL para deletar um aluno pelo ID


        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (pedido_id,))
            # Confirma a transação no banco de dados
            conn.commit()
            # Verifica se alguma linha foi afetada (deletada)
            if cursor.rowcount:
                return {'mensagem': 'pedido deletado com sucesso!'}, 200
           
            else:
                return {'error': 'pedido não encontrado.'}, 404
           
        except Error as err:
            # Em caso de erro na deleção, imprime a mensagem de erro
            error = str(err)
            return {'error': f'Erro ao deletar pedido: {error}'}, 500
       
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()


@app.route('/pedidos/cliente/<int:cliente_id>', methods=['GET'])
def busca_pedidos_por_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM tbl_pedido WHERE cliente_id = %s"
        cursor.execute(sql, (cliente_id,))
        pedidos = cursor.fetchall()

        if pedidos:
            return jsonify(pedidos), 200
        else:
            return jsonify({'message': 'Nenhum pedido encontrado para este cliente'}), 404

    except Error as err:
        return jsonify({'error': f"Erro ao buscar pedidos: {err}"}), 400

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)


