FROM python:3.9-slim

WORKDIR /app
 
RUN apt-get update \
    && apt-get remove --purge -y python3.7

# Install Python
RUN apt-get install -y python3.6 \
    && ln -s /usr/bin/python3.6 /usr/bin/python3

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ErioGarciaDev/charter-prometheus-streamlit.git .

RUN pip3 install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]