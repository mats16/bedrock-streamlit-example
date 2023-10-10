FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run"]
CMD ["main.py"]
