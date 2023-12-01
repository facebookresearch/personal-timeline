FROM node:18.16.0

WORKDIR /app 


COPY src/frontend .
COPY sample_data public/digital_data

# RUN ln -s /app/personal-data/app_data /app/public/digital_data/app_data

# To load the images the soft link should be to the entire personal-data folder
RUN ln -s /app/personal-data /app/public/digital_data
RUN yarn install
RUN yarn add react react-scripts primereact primeicons video-react react-timelines @react-google-maps/api @uiw/react-heat-map react-syntax-highlighter @babel/runtime

CMD ["yarn", "start"]