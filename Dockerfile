FROM python:3-alpine3.8

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip


RUN curl https://sh.rustup.rs -sSf | sh

RUN pip install cargo
SHELL [ "/bin/sh", "-s", ".", "$HOME/.cargo/env"]

RUN pip install -r requirements.txt
EXPOSE 3000
CMD python ./app.py