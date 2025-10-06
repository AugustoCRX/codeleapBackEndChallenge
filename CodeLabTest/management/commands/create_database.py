from django.core.management.base import BaseCommand
import os
import sys
import django
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import environ


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carrega as variáveis de ambiente do arquivo .env
env = environ.Env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print(BASE_DIR)

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

def create_db():
    """
    Cria o banco de dados e o usuário PostgreSQL com base nas configurações do Django.
    """
    try:

        db_name = env('DATABASE_NAME')
        db_user = env('DATABASE_USERNAME')
        db_password = env('DATABASE_PASSWORD')
        db_host = env("DATABASE_HOST")
        db_port = env("DATABASE_PORT")
        db_userpassword = env("DATABASE_USERPASSWORD")

        # Conexão com o banco de dados 'postgres' para criar o novo banco de dados e usuário
        conn = connect(
            dbname='postgres',
            user='postgres',  # Usuário com permissão para criar bancos de dados e roles
            password=db_userpassword,  # SENHA DO SUPERUSUÁRIO DO POSTGRESQL
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Verifica se o banco de dados já existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if cursor.fetchone():
            print(f"O banco de dados '{db_name}' já existe.")
        else:
            print(f"Criando o banco de dados '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print("Banco de dados criado com sucesso.")

        # Verifica se o usuário já existe
        cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{db_user}'")
        if cursor.fetchone():
            print(f"O usuário '{db_user}' já existe.")
        else:
            print(f"Criando o usuário '{db_user}'...")
            cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}'")
            print("Usuário criado com sucesso.")

        print(f"Concedendo todos os privilégios no banco de dados '{db_name}' para o usuário '{db_user}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}")
        print("Privilégios concedidos com sucesso.")

        cursor.close()
        conn.close()

    except ImportError:
        print("Erro: O Django não está instalado ou configurado corretamente.")
    except KeyError:
        print("Erro: As configurações do banco de dados não foram encontradas no arquivo settings.py.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

class Command(BaseCommand):
    help = 'Creates the PostgreSQL database and user'

    def handle(self, *args, **options):
        self.stdout.write('Starting database creation process...')
        create_db()
        self.stdout.write(self.style.SUCCESS('Database creation process completed'))
