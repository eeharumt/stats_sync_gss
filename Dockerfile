FROM python:slim
RUN apt-get update && apt-get install -y cron
WORKDIR /app
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY src .
COPY env.sh .
CMD bash env.sh
COPY crontab /etc/cron.d/stats-sync-job
RUN chmod 0644 /etc/cron.d/stats-sync-job
RUN crontab /etc/cron.d/stats-sync-job
CMD cron && tail -f /var/log/cron.log
# CMD python main.py