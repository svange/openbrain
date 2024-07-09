# Use an official Python runtime as a parent image
FROM python:3.11

RUN pip install poetry

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app

COPY . .

# Install any needed packages specified in requirements.txt
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi -E gradio

# install jq for .ebextensions/secrets.config script
#RUN apt-get update && \
#    apt-get install -y jq

EXPOSE 80

# Define environment variable
ENV PYTHONPATH=/usr/src/app:/usr/src/app/ob-tuner:/usr/src/app/openbrain:$PYTHONPATH
# Run app.py when the container launches
WORKDIR /usr/src/app/openbrain
CMD ["python", "app.py"]
