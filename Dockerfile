FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# install python dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && pip install -r /code/requirements.txt

# project files
COPY . /code

# create data directory (will be overridden by volume at runtime)
RUN mkdir -p /app/data/mnt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
