FROM python:3.12

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# Fetches the model/tokenizer into the HF cache
COPY load_generation_pipeline.py load_generation_pipeline.py
RUN python load_generation_pipeline.py

COPY *.py .
COPY static .
COPY templates .
COPY secrets.txt secrets.txt

COPY app_launch.sh app_launch.sh
RUN chmod +x app_launch.sh
CMD ["./app_launch.sh"]
