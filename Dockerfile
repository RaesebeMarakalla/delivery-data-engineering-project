FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "-lc", "python python/generate_sample_data.py && python python/etl_pipeline.py --dry-run && python python/business_insights.py && tail -f /dev/null"]
