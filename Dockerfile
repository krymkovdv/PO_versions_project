FROM python:alpine3.22

WORKDIR /app

COPY requirements.txt .

# RUN sed -i 's|http://dl-cdn.alpinelinux.org/alpine|http://mirror.yandex.ru/mirrors/alpine|g' /etc/apk/repositories && apk update

# -- Добавляем сертификат ПТЗ --
# COPY _.sptz.ru.crt /usr/local/share/ca-certificates/
# COPY www.kirovets-ptz.com.crt /usr/local/share/ca-certificates/
# RUN update-ca-certificates

# RUN apk update
# RUN apk add --no-cache bash

RUN pip install --no-cache-dir -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

COPY . .

EXPOSE 4000

CMD ["uvicorn", "app.main:app", "--port", "4000", "--reload", "--host", "0.0.0.0"]