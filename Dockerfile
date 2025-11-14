FROM python:3.11-slim

# Use Render’s working directory
WORKDIR /opt/render/project/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

# IMPORTANT: Use shell-form CMD to expand ${PORT}
CMD gunicorn "app:create_app()" --bind 0.0.0.0:${PORT} --workers 2
