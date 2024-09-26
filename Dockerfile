# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variable to prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Set environment variable to buffer the stdout and stderr to the terminal
ENV PYTHONUNBUFFERED=1

# Create and set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Ensure ffmpeg is installed (for pydub to handle mp3 conversion)
RUN apt-get update && apt-get install -y ffmpeg flac && apt-get clean

# Expose port 5000 to the outside world
EXPOSE 5000

# Define a volume for persistent data (access files from host)
VOLUME ["/app/data"]

# Run the Flask app when the container launches
CMD ["python", "app.py"]
