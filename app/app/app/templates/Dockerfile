# Use a imagem base do Python
FROM python:3.10-slim

# Definir o diretório de trabalho no contêiner
WORKDIR /usr/src/app

# Copiar os arquivos de dependências e instalar
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Baixar e instalar o modelo de linguagem do spaCy para português
RUN python -m spacy download pt_core_news_sm

# Copiar o restante do código da aplicação
COPY . .

# Expor a porta que a aplicação vai rodar
EXPOSE 8000

# Comando para rodar a aplicação quando o contêiner iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
