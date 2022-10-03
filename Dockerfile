FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential wget
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && make install
RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz
RUN pip install TA-Lib poetry

COPY poetry.lock /app
COPY pyproject.toml /app

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY ./app /app