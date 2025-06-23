import os
from esbmc_runner import run_esbmc

if __name__ == "__main__":
    # Caminho absoluto do arquivo test.c dentro do Windows
    file_path = os.path.abspath(os.path.join("..", "user_code", "test.c"))
    output = run_esbmc(file_path)
    print("\n===== SAÍDA DO ESBMC =====\n")
    print(output)
