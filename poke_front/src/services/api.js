import { getToken, removeToken, removeUser } from '../utils/auth';

const API_BASE_URL = 'http://localhost:8000/api';

const handleResponse = async (response) => {
  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      removeUser();
      window.location.href = '/login';
      throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
    }
    
    let errorMessage = 'Error en la petición';
    let errorData = {};
    
    try {
      const text = await response.text();
      console.log('Error response text:', text);
      
      if (text) {
        errorData = JSON.parse(text);
        
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.non_field_errors) {
          errorMessage = errorData.non_field_errors[0];
        } else if (typeof errorData === 'object') {
          const firstError = Object.values(errorData)[0];
          if (Array.isArray(firstError)) {
            errorMessage = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMessage = firstError;
          }
        }
        
        if (errorData.room_code) {
          errorMessage += ` | Sala: ${errorData.room_code} | ID: ${errorData.battle_id}`;
        }
      } else {
        errorMessage = `Error ${response.status}: ${response.statusText}`;
      }
    } catch (e) {
      errorMessage = `Error ${response.status}: ${response.statusText}`;
    }
    
    const error = new Error(errorMessage);
    error.data = errorData;
    throw error;
  }
  
  return response.json();
};

export const apiRequest = async (endpoint, options = {}) => {
  const token = getToken();
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    return await handleResponse(response);
  } catch (error) {
    if (error.message.includes('Failed to fetch')) {
      throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose.');
    }
    throw error;
  }
};