# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Create and set permissions for the uploads directory
RUN mkdir -p /app/src/uploads && chmod -R 777 /app/src/uploads
RUN chmod -R a+w /app/database

# Copy the entrypoint script and ensure it's executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port 5000 for the Flask app
EXPOSE 5000

# Set the Flask app environment variable
ENV FLASK_APP=src/main.py

# Use the start script as the container entrypoint
RUN ls -lah /start.sh
ENTRYPOINT ["/start.sh"]
