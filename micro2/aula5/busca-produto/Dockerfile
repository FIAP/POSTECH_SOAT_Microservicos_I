FROM python:3.9-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala as dependências do projeto
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/main.py

# Expõe a porta 8080
EXPOSE 8080

# Inicia o serviço
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]