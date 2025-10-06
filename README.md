# CodeLeap Backend - API de Rede Social
API REST completa de rede social desenvolvida com Django REST Framework, incluindo autenticação JWT, posts, likes, comentários, notificações e muito mais.

## Tecnologias

Django 5.2.5
Django REST Framework 3.16.1
PostgreSQL (banco de dados)
JWT Authentication (Simple JWT)
DRF Spectacular (documentação OpenAPI)
Django Filter (filtros avançados)
Pillow (upload de imagens)
Coverage (cobertura de testes)

## Requisitos

Python 3.8+
PostgreSQL 12+
pip (gerenciador de pacotes Python)
Virtualenv (recomendado)

## Instalação
1. Clone o repositório
bashgit clone <url-do-repositorio>
cd <nome-da-pasta>
2. Crie e ative o ambiente virtual
bash# Windows
python -m venv venv
venv\Scripts\activate

## Linux/Mac
python3 -m venv venv
source venv/bin/activate
3. Instale as dependências
bashpip install -r requirements.txt
4. Configure as variáveis de ambiente
Crie um arquivo .env na raiz do projeto baseado no .env.exemple:
env# Django config
DJANGO_SECRET_KEY=sua-chave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,testserver

## Database config
DATABASE_ENGINE=postgresql

DATABASE_NAME=codeleap_db

DATABASE_USERNAME=codeleap_user

DATABASE_PASSWORD=sua_senha_aqui

DATABASE_HOST=localhost

DATABASE_PORT=5432

DATABASE_USERPASSWORD=senha_do_postgres_admin

5. Configure o PostgreSQL
Certifique-se de que o PostgreSQL está rodando e crie o banco de dados:
bash# Usando o comando customizado do Django
python manage.py create_database
Ou manualmente no PostgreSQL:
sqlCREATE DATABASE codeleap_db;
CREATE USER codeleap_user WITH PASSWORD 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON DATABASE codeleap_db TO codeleap_user;
6. Execute as migrações
bashpython manage.py makemigrations
python manage.py migrate
7. Crie um superusuário (opcional)
bashpython manage.py createsuperuser
8. Execute o servidor
bashpython manage.py runserver
Acesse: http://localhost:8000
## Executando os Testes
### Testes Avançados com Coverage
O projeto inclui um script personalizado que executa testes com formatação colorida e relatório de cobertura:
bashpython run_tests_advanced.py
Este script irá:

✅ Executar todos os testes com output formatado
📊 Gerar relatório de cobertura de código
📈 Mostrar estatísticas detalhadas
🎨 Apresentar resultados com cores (Pass ✅, Fail ❌, Error 💥)
📄 Criar relatório HTML em htmlcov/index.html

Abra o arquivo htmlcov/index.html no navegador
## Reset do Banco de Dados (Desenvolvimento)
Para resetar completamente o banco de dados em desenvolvimento:
bashpython dev_reset_script.py

ATENÇÃO: Este comando irá:

Deletar todas as tabelas
Remover todos os arquivos de migração
Limpar arquivos de mídia (avatars, posts)
Recriar as migrações
Aplicar as migrações

📚 Comandos Úteis
Django Management
bash# Criar migrações
python manage.py makemigrations

📝 Licença
Este projeto foi desenvolvido como parte do teste técnico da CodeLeap.
