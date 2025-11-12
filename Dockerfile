FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database persistence
RUN mkdir -p /app/data

# Environment variables (override via docker-compose or -e flag)
ENV TELEGRAM_BOT_TOKEN=""

# Run the bot
CMD ["python", "bot.py"]
