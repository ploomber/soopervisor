#!/bin/bash

airflow webserver --port 8080 &

airflow scheduler &
