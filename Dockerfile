# Use the official Python 3.10.0 Alpine base image
FROM python:3.10.0-alpine

# Set the working directory in the container
WORKDIR /app

# Install dependencies for NLTK and other packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    build-base

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (punkt)
RUN python -m nltk.downloader punkt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Command to run the Flask app
CMD ["python", "app.py"]
