FROM python:alpine AS sources

WORKDIR /app/bubbles4py

COPY . .

RUN python setup.py install

ENTRYPOINT [ "python", "-m", "bubbles"]
CMD ["-d", "MemDriver" ]

EXPOSE 49449
