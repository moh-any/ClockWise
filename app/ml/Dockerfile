FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends build-essential

RUN pip install --upgrade pip

RUN mkdir /app 

WORKDIR /app 

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "cw-ml-service", "--port", "8000"]