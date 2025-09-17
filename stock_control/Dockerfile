# FROM python:3.8

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# WORKDIR /code

# COPY requirements.txt /code/
# RUN pip install --upgrade pip && pip install -r requirements.txt

# COPY . /code/

# # Ensure staticfiles directory and permissions
# RUN mkdir -p /code/staticfiles && chmod -R 755 /code/staticfiles

# # Copy and set execute permissions for the entrypoint
# COPY entrypoint.sh /code/entrypoint.sh
# RUN chmod +x /code/entrypoint.sh


# Use a Python image compatible with the Raspberry Pi's architecture
FROM python:3.8

# --- Build-time arguments for Git source ---
ARG GIT_REPO=https://github.com/anandarupmukherjee/InventoryManagementModular.git
ARG GIT_REF=main

# Set environment variables to prevent Python from writing pyc files to disc and buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_GIT_REPO=${GIT_REPO} \
    APP_GIT_REF=${GIT_REF}

# Install git so we can clone the required revision
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone the application source at the desired ref
RUN git clone ${GIT_REPO} /code && \
    cd /code && \
    git checkout ${GIT_REF}

# Set work directory to the Django project root
WORKDIR /code/stock_control

# Install Python dependencies from the cloned repo
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose build metadata for debugging
RUN echo "Checked out ${GIT_REF} from ${GIT_REPO}" > /code/.build-info

# RUN python manage.py collectstatic --noinput --verbosity 2
