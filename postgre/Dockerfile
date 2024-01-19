# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files to /app
COPY pyproject.toml poetry.lock /app/

# Install Poetry
RUN pip install poetry

# Install project dependencies using Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Add this line to your Dockerfile before the application starts
RUN apt-get update && apt-get install -y postgresql-client


# Copy the rest of the application code to /app
COPY . /app

# Set environment variables for PostgreSQL
ENV POSTGRES_DB postgres
ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD sujanm@9271
ENV POSTGRES_HOST 5432

# Create and populate the database
# RUN python -c "from postgre import create_table_if_not_exists; create_table_if_not_exists()"

# Make port 80 available to the world outside this container
EXPOSE 8080


# Define environment variable
ENV DSN "dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD host=$POSTGRES_HOST"

# Run the FastAPI application
CMD ["uvicorn", "app.postgre:app", "--host", "0.0.0.0", "--port", "8080"]
