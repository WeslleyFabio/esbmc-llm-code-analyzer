import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.esbmc_runner import run_esbmc
from app.output_parser import parse_esbmc_output, clean_esbmc_log
from app.llm_client import get_llm_response

load_dotenv()

app = FastAPI()


def wrap_long_lines(log_text, max_length=120):
    wrapped_lines = []
    for line in log_text.splitlines():
        while len(line) > max_length:
            wrapped_lines.append(line[:max_length])
            line = line[max_length:]
        wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


@app.post("/analyze/")
async def analyze_code(code: str = Form(...)):
    user_code_path = os.path.join("user_code", "user_code.c")
    with open(user_code_path, "w") as f:
        f.write(code)

    esbmc_output = run_esbmc(user_code_path)
    cleaned_log = clean_esbmc_log(esbmc_output)
    cleaned_log = wrap_long_lines(cleaned_log)
    parsed_output = parse_esbmc_output(esbmc_output)
    llm_response = get_llm_response(parsed_output)

    # Salva o resultado final no disco para o endpoint de download
    output_file = "user_code/result.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("==== Log ESBMC ====\n\n")
        f.write(esbmc_output + "\n\n")
        f.write("==== Texto da LLM ====\n\n")
        f.write(llm_response + "\n\n")
        f.write("==== By Rafael, Renan e Weslley ====\n")

    return JSONResponse({
        "esbmc_output": cleaned_log,
        "parsed_output": parsed_output,
        "llm_interpretation": llm_response
    })


@app.post("/download/")
async def download_result():
    output_file = "user_code/result.txt"
    if os.path.exists(output_file):
        return FileResponse(path=output_file, filename="resultado_analise.txt", media_type="text/plain")
    else:
        return JSONResponse({"error": "Arquivo de resultado não encontrado."}, status_code=404)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def frontend():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Secure C Analyzer</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h2>🔍 Análise de Segurança de Código C com ESBMC e LLM</h2>
            <textarea id="code" placeholder="Cole aqui seu código C..."></textarea>
            <div class="button-group">
                <button onclick="analyze()">▶️ Analisar Código</button>
                <button onclick="toggleLog()">📝 Ver Log ESBMC</button>
                <button onclick="download()">⬇️ Baixar Resultado</button>
            </div>            
            <pre id="esbmc_log"></pre>            
            <div id="response"></div>
        </div>

        <script>
            async function analyze() {
                document.getElementById('response').innerText = '⏳ Analisando...';
                const code = document.getElementById('code').value;
                const formData = new FormData();
                formData.append('code', code);

                try {
                    const res = await fetch('/analyze/', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();
                    const text = data.llm_interpretation;

                    let i = 0;
                    const target = document.getElementById('response');
                    target.innerText = '';

                    function typeWriter() {
                        if (i < text.length) {
                            target.innerText += text.charAt(i);
                            i++;
                            setTimeout(typeWriter, 20);
                        }
                    }
                    typeWriter();

                    document.getElementById('esbmc_log').innerText = data.esbmc_output;

                } catch (error) {
                    document.getElementById('response').innerText = '❌ Erro ao analisar: ' + error;
                }
            }

            function toggleLog() {
                const log = document.getElementById('esbmc_log');
                log.style.display = (log.style.display === 'none' || log.style.display === '') ? 'block' : 'none';
            }

            async function download() {
                try {
                    const response = await fetch('/download/', { method: 'POST' });
                    if (!response.ok) throw new Error('Falha ao baixar arquivo.');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'resultado_analise.txt';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } catch (error) {
                    alert('Erro no download: ' + error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
