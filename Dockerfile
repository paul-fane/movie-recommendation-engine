# Dockerfile
FROM python:3.9


# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
COPY requirements.ml.txt /app/
RUN pip install -r requirements.txt
RUN pip install -r requirements.ml.txt

# Copy the project
COPY ./src /app/