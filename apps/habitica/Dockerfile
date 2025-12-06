FROM node:20-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git python3 make g++ krb5-dev

# Clone Habitica repository
RUN git clone https://github.com/HabitRPG/habitica.git /app && \
    cd /app && \
    git checkout develop

# Install dependencies
RUN npm install

# Build client
RUN npm run build:client

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]

