#!/bin/bash

# init webserver in the background
airflow webserver --port 8080 > /airflow-webserver.log 2>&1 &

# init scheduler in the background
airflow scheduler > /airflow-scheduler.log 2>&1 &

# sleep a bit to ensure the scheduler is ready
sleep 10