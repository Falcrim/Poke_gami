import { getToken, removeToken, removeUser } from '../utils/auth';

const API_BASE_URL = 'http://localhost:8000/api';

const handleResponse = async (response) => {
  if (!response.ok) {
    // Si es error 401 (Unauthorized), limpiar el token
    if (response.status === 401) {
      removeToken();
      removeUser();
      window.location.href = '/login';
      throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
    }
    
    let errorMessage = 'Error en la petición';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      
      // Manejar errores de Django REST Framework
      if (errorData.non_field_errors) {
        errorMessage = errorData.non_field_errors[0];
      } else if (typeof errorData === 'object') {
        // Para errores de validación de campos
        const firstError = Object.values(errorData)[0];
        if (Array.isArray(firstError)) {
          errorMessage = firstError[0];
        } else if (typeof firstError === 'string') {
          errorMessage = firstError;
        }
      }
    } catch (e) {
      // Si no se puede parsear la respuesta de error
      errorMessage = `Error ${response.status}: ${response.statusText}`;
    }
    
    throw new Error(errorMessage);
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