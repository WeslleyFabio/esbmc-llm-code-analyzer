from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.esbmc_runner import run_esbmc
from app.output_parser import parse_esbmc_output
from app.llm_client import get_llm_response
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Endpoint da API para análise


@app.post("/analyze/")
async def analyze_code(code: str = Form(...)):
    # 1. Salvar o código recebido
    with open("user_code/user_code.c", "w") as f:
        f.write(code)

    # 2. Rodar o ESBMC
    esbmc_output = run_esbmc("user_code/user_code.c")

    # 3. Parsear a saída
    parsed_output = parse_esbmc_output(esbmc_output)

    # 4. Chamar a LLM com o resumo
    llm_response = get_llm_response(parsed_output)

    return {
        "esbmc_raw": esbmc_output,
        "parsed_output": parsed_output,
        "llm_interpretation": llm_response
    }

# Servir arquivos estáticos (se quiser adicionar CSS/JS futuramente)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Endpoint do Frontend simples


@app.get("/", response_class=HTMLResponse)
async def frontend():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure C Analyzer</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h2>Análise de Segurança de Código C com ESBMC e LLM</h2>
            <textarea id="code" placeholder="Cole aqui seu código C..."></textarea><br>
            <button onclick="analyze()">Analisar Código</button>
            <div id="response"></div>
        </div>

        <script>
            async function analyze() {
                document.getElementById('response').innerText = 'Analisando...';
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
                } catch (error) {
                    document.getElementById('response').innerText = 'Erro ao analisar: ' + error;
                }
            }
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
