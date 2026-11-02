FROM node:22-alpine

WORKDIR /app

RUN apk add --no-cache su-exec

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["npm", "run", "dev"]
