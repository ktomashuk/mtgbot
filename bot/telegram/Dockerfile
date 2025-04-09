# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container at /usr/src/app
COPY ../.. .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Define the command to run your application
CMD ["python", "-u", "-m", "bot.telegram.bot"]
