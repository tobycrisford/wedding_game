#!/bin/bash

cd chat_app
python server.py &
python chat_generator.py &

wait
