# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# The image runs production settings (ADR-028). Stated explicitly rather than
# inherited from manage.py's default, so the deployed module is visible here.
ENV DJANGO_SETTINGS_MODULE bakery.settings.base

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

# Collect static files. base.py requires these variables, so the build supplies
# placeholders for this one command (ADR-049). Keep them inline on this RUN line:
# through ENV they would persist into the running image, and a host that forgot a
# real value would boot on a placeholder instead of failing. They are public
# (`docker history`), so each is useless outside the build: a fake key, an
# .invalid host. 2.19 adds ALLOWED_HOSTS and DEBUG here.
RUN SECRET_KEY=build-only-placeholder \
    DATABASE_URL=postgres://build:build@build.invalid:5432/build \
    python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 bakery.wsgi:application"]