import subprocess
import os


def windows_path_to_wsl_path(windows_path):
    """
    Converte um caminho de arquivo Windows (ex: C:\\Users\\...) para o path correspondente no WSL (/mnt/c/Users/...)
    """
    drive, path_rest = os.path.splitdrive(windows_path)
    drive_letter = drive.rstrip(":").lower()
    wsl_path = "/mnt/" + drive_letter + path_rest.replace("\\", "/")
    return wsl_path


def run_esbmc(file_path, options=None):
    """
    Executa o ESBMC no WSL usando o caminho do código C salvo no Windows.
    """
    # Não é necessário importar subprocess e os novamente aqui, já estão no topo do arquivo
    # import subprocess
    # import os

    if options is None:
        options = []

    try:
        # Converte o caminho do arquivo C (Windows) para o path WSL
        wsl_input_path = windows_path_to_wsl_path(os.path.abspath(file_path))

        # Caminho absoluto para o esbmc no WSL
        # CORREÇÃO AQUI:
        # 1. Use barras normais (/) para caminhos WSL.
        # 2. Garanta que o caminho inclui o nome do executável 'esbmc' no final.
        # 3. Certifique-se de que este caminho reflete a localização EXATA do seu ESBMC no WSL.
        #    Se 'weslley' é seu usuário e você o construiu lá, deve ser algo como:
        esbmc_path_wsl = "/home/weslley/esbmc/build/src/esbmc/esbmc"

        # Comando final que será executado dentro do WSL
        command = ["wsl", esbmc_path_wsl, wsl_input_path] + options
        
        print(f"Executando comando: {' '.join(command)}")  # Log para depuração

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120  # Tempo máximo de execução
        )

        return result.stdout

    except subprocess.TimeoutExpired:
        return "Erro: Tempo limite de execução excedido ao rodar o ESBMC."

    except Exception as e:
        return f"Erro inesperado ao executar ESBMC via WSL: {str(e)}"