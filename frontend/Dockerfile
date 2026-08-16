FROM node:24-alpine AS development

WORKDIR /app

RUN chown node:node /app

USER node

COPY --chown=node:node package.json ./
RUN npm install --no-audit --no-fund

COPY --chown=node:node . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
