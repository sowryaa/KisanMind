import axios from 'axios';

const BACKEND_URL = 'https://kisanmind-production.up.railway.app';

const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getWeather = async (district) => {
  try {
    const response = await api.get(`/api/weather/?district=${encodeURIComponent(district)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching weather:', error);
    return { error: 'Failed to fetch weather data' };
  }
};

export const getPrices = async (commodity = '', district = '') => {
  try {
    const response = await api.get(`/api/prices/?commodity=${encodeURIComponent(commodity)}&district=${encodeURIComponent(district)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching mandi prices:', error);
    return { error: 'Failed to fetch price data' };
  }
};

export const authGoogle = async (token) => {
  try {
    const response = await api.post('/api/auth/google', { token });
    return response.data;
  } catch (error) {
    console.error('Error during Google authentication:', error);
    throw error;
  }
};

export const getOfflineData = async (type) => {
  try {
    const response = await fetch(`/api/offline/${type}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching offline data:', error);
    return null;
  }
};
