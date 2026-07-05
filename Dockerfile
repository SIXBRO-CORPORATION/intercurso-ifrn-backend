FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install uv
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]