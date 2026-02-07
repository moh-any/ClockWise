FROM node:25.6-slim

RUN mkdir /app

WORKDIR /app

COPY package*.json ./

RUN npm install 

COPY . . 

EXPOSE 3000 

CMD [ "npm" ,"start"]