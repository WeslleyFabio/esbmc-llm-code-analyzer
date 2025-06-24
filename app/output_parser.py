def parse_esbmc_output(output_text):
    """
    Faz o parse da saída do ESBMC para capturar o status geral e as mensagens de erro (vulnerabilidades detectadas).
    Agora foca em capturar apenas o tipo real de erro (exemplo: divisão por zero, ponteiro nulo, etc.).
    """
    result = {
        "status": "",
        "errors": []
    }

    lines = output_text.splitlines()
    status_detected = False
    capture_next = False

    for line in lines:
        if "VERIFICATION FAILED" in line:
            result["status"] = "Falha na verificação"
            status_detected = True
        elif "VERIFICATION SUCCESSFUL" in line:
            result["status"] = "Verificação bem-sucedida"
            status_detected = True

        # Se achou a linha "Violated property:", ativa flag para capturar a próxima linha de erro real
        if "Violated property:" in line:
            capture_next = True
            continue

        if capture_next:
            # Só pega a próxima linha **se ela for realmente o tipo de erro** (não pegar linha de caminho com 'file')
            if not line.strip().startswith("file") and line.strip() != "":
                result["errors"].append(line.strip())
                capture_next = False  # Só pega uma linha por vez
            elif line.strip() == "":
                capture_next = False  # Se linha em branco, também para

    if not status_detected:
        result["status"] = "Status desconhecido"

    return result


def clean_esbmc_log(log_text):
    """
    Remove linhas de unwinding loop para deixar o log mais legível no frontend.
    """
    filtered_lines = []
    for line in log_text.splitlines():
        if not line.startswith("Unwinding loop"):
            filtered_lines.append(line)
    return "\n".join(filtered_lines)
