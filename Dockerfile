FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the Docker container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory (where your app files are) to the working directory in the container
COPY . /app/

# Expose the port that the Dash app will run on (usually 8050)
EXPOSE 8050

# Command to run the Dash app (modify if needed, depending on your entry point file)
CMD ["python", "dash_gui.py"]
