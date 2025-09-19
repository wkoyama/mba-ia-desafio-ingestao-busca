import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Configurações do banco
PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = int(os.environ.get("PGPORT", 5432))
PGUSER = os.environ.get("PGUSER", "postgres")
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres")
PGDATABASE = os.environ.get("PGDATABASE", "langchain_db")

def check_database():
    """Verifica se o banco existe e lista as tabelas"""
    try:
        # Primeiro, conecta ao banco postgres para verificar se langchain_db existe
        print("🔍 Conectando ao PostgreSQL...")
        conn = psycopg2.connect(
            host=PGHOST,
            port=PGPORT,
            user=PGUSER,
            password=PGPASSWORD,
            database="postgres"
        )
        cur = conn.cursor()
        
        # Verifica se o banco langchain_db existe
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PGDATABASE,))
        exists = cur.fetchone()
        
        if not exists:
            print(f"❌ Banco '{PGDATABASE}' não existe!")
            print("Criando o banco...")
            conn.autocommit = True
            cur.execute(f"CREATE DATABASE {PGDATABASE}")
            print(f"✅ Banco '{PGDATABASE}' criado com sucesso!")
        else:
            print(f"✅ Banco '{PGDATABASE}' existe!")
        
        conn.close()
        
        # Agora conecta ao banco langchain_db para listar tabelas
        print(f"\n📋 Conectando ao banco '{PGDATABASE}'...")
        conn = psycopg2.connect(
            host=PGHOST,
            port=PGPORT,
            user=PGUSER,
            password=PGPASSWORD,
            database=PGDATABASE
        )
        cur = conn.cursor()
        
        # Lista todas as tabelas
        print("\n🔍 Executando query para listar tabelas...")
        cur.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"\n📋 Tabelas no banco '{PGDATABASE}':")
        if tables:
            for table_name, table_type in tables:
                print(f"  - {table_name} ({table_type})")
                
                # Para cada tabela, mostra a estrutura
                print(f"    Estrutura da tabela '{table_name}':")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = cur.fetchall()
                
                for col_name, col_type, nullable in columns:
                    null_info = "NULL" if nullable == "YES" else "NOT NULL"
                    print(f"      - {col_name}: {col_type} ({null_info})")
                
                # Conta registros na tabela
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"    Total de registros: {count}")
                
                # Se tem dados, mostra alguns exemplos
                if count > 0:
                    print(f"    Primeiros 3 registros de '{table_name}':")
                    cur.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    rows = cur.fetchall()
                    for i, row in enumerate(rows, 1):
                        print(f"      {i}. {row}")
                print()
        else:
            print("  (Nenhuma tabela encontrada)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return False

if __name__ == "__main__":
    check_database()
