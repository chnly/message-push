FROM python:3.7.4-slim-stretch
ENV DEBIAN_FRONTEND noninteractive
COPY ./deploy/sources.list /etc/apt/sources.list
COPY ./deploy/localtime /etc/localtime
COPY ./message_push /app/message_push
COPY requirements.txt /app/message_push
WORKDIR /app/message_push
ENV PYTHONPATH "${PYTHONPATH}:/app"
RUN apt-get update && apt-get install -y apt-utils python3-dev python3-pip libpq-dev  curl apt-transport-https \
    && pip3 install -r requirements.txt -i "https://pypi.douban.com/simple/"
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]