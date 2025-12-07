FROM node:20-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git python3 make g++ krb5-dev

# Clone Habitica repository and use a stable tag
RUN git clone https://github.com/HabitRPG/habitica.git /app && \
    cd /app && \
    git fetch --tags && \
    git checkout $(git describe --tags --abbrev=0) || git checkout develop

# Install dependencies
RUN npm install

# Build will happen on first run if needed
# The app can run without pre-building in development mode

# Expose port
EXPOSE 3000

# Start the application
# Use node directly instead of npm start to avoid watch mode issues
CMD ["node", "./website/server/index.js"]

