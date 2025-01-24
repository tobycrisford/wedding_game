FROM python:3.12

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# Fetches the model/tokenizer into the HF cache
COPY load_generation_pipeline.py load_generation_pipeline.py
RUN python load_generation_pipeline.py

COPY *.py ./chat_app/.
COPY static ./chat_app/static/.
COPY templates ./chat_app/templates/.
COPY server_config.json ./chat_app/server_config.json

COPY app_launch.sh ./chat_app/app_launch.sh
RUN chmod +x chat_app/app_launch.sh
CMD ["./chat_app/app_launch.sh"]
