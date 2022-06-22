FROM python:3.7
COPY requirements.txt .
COPY ./get_data_endpoints.py .
RUN python3 -m pip install -r \
    requirements.txt --quiet --no-cache-dir \
    && rm -f requirements.txt
CMD ["python", "get_data_endoints.py"]