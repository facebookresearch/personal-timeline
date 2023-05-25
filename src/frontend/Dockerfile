FROM node:18.16.0

WORKDIR /app

RUN yarn add primereact primeicons video-react react-timelines @react-google-maps/api @uiw/react-heat-map react-syntax-highlighter @babel/runtime

COPY src/frontend .

CMD ["yarn"]
CMD ["yarn", "start"]