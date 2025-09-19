from search import search_prompt

def main():
    print("Chat iniciado! Digite 'sair', 'exit' ou 'quit' para encerrar.")
    
    while True:
        q = input("\nPERGUNTA: ").strip()
        if q.lower() in ("sair", "exit", "quit"):
            print("Encerrando.")
            break
        if not q:
            print("Pergunta vazia. Digite algo.")
            continue
        try:
            search_prompt(q)
        except Exception as e:
            print("Erro durante o processamento:", e)

if __name__ == "__main__":
    main()