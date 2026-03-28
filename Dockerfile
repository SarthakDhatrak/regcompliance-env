FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user
USER user

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "env.main:app", "--host", "0.0.0.0", "--port", "7860"]
