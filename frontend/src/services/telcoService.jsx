import api from './api';

const telcoService = {
    connect: async (data) => {
        const response = await api.post('/api/v1/telco/connect', data);
        return response.data;
    },

    verify: async (data) => {
        const response = await api.post('/api/v1/telco/verify', data);
        return response.data;
    },

    pull: async (data) => {
        const response = await api.post('/api/v1/telco/pull', data);
        return response.data;
    }
};

export default telcoService;
