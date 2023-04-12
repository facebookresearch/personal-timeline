const prod = {
    API_URL: 'http://yuliangli.sb:8085'
};

const dev = {
    API_URL: 'http://localhost:8085'
};

export const config = process.env.NODE_ENV === 'development' ? dev : prod;
