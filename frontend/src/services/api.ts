import axios, { AxiosInstance } from 'axios';
import { toast } from 'sonner';

// Types
export interface User {
  user_id: string;
  email: string;
  full_name?: string;
  preferences?: any;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export interface Trip {
  trip_id: string;
  destination: string;
  status: string;
  current_stage?: string;
  created_at: string;
  updated_at: string;
  constraints?: any;
  itinerary?: any[];
  discovered_pois?: any[];
}

export interface CreateTripRequest {
  user_message: string;
}

export interface CreateTripResponse {
  trip_id: string;
  constraints: any;
  message: string;
  pois_found: number;
}

export interface POIResponse {
  place_id: string;
  name: string;
  description?: string;
  editorial_summary?: string;
  why_recommended?: string;
  photo_reference?: string;
  ai_score?: number;
  price_level?: number;
  rating?: number;
  category?: string[];
  formatted_address?: string;
  location?: { lat: number; lng: number };
}

export interface TripPOIsResponse {
  trip_id: string;
  destination: string;
  pois: POIResponse[];
  total_pois: number;
}

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    // Use environment variable for API URL, fallback to localhost
    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
    
    this.api = axios.create({
      baseURL: apiUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add interceptor to attach token
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Add interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';

        if (error.response) {
          switch (error.response.status) {
            case 401:
              toast.error('Authentication expired', { description: 'Please login again.' });
              // Optionally clear token here
              this.setToken(null);
              break;
            case 403:
              toast.error('Access Denied', { description: 'You do not have permission to perform this action.' });
              break;
            case 404:
              toast.error('Not Found', { description: 'The requested resource was not found.' });
              break;
            case 422:
              toast.error('Validation Error', { description: message });
              break;
            case 500:
              toast.error('Server Error', { description: 'Something went wrong on the server. Please try again later.' });
              break;
            default:
              toast.error('Error', { description: message });
          }
        } else if (error.request) {
          toast.error('Network Error', { description: 'Please check your internet connection.' });
        } else {
          toast.error('Error', { description: message });
        }

        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('auth_token');
  }

  // --- Auth Endpoints (V2) ---

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/v2/auth/login', { email, password });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async register(email: string, password: string, fullName?: string): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/v2/auth/register', {
      email,
      password,
      full_name: fullName
    });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/v2/users/me');
    return response.data;
  }

  // --- Trip Endpoints (V1 - Agent) ---

  async createTrip(userMessage: string): Promise<CreateTripResponse> {
    // Use V1 endpoint to trigger the agent graph
    const response = await this.api.post<CreateTripResponse>('/v1/trips', {
      user_message: userMessage
    });
    return response.data;
  }

  async getTripPOIs(tripId: string): Promise<TripPOIsResponse> {
    const response = await this.api.get<TripPOIsResponse>(`/v1/trips/${tripId}/pois`);
    return response.data;
  }

  // --- Trip Management (V2 - Persistence) ---

  async getTrip(tripId: string): Promise<Trip> {
    // Use V2 endpoint for full details including itinerary
    try {
      const response = await this.api.get<Trip>(`/v2/trips/${tripId}`);
      return response.data;
    } catch (error) {
      // Fallback to V1 if V2 fails
      console.warn("V2 getTrip failed, trying V1", error);
      const v1Response = await this.api.get(`/v1/trips/${tripId}`);
      return v1Response.data;
    }
  }

  async listTrips(): Promise<Trip[]> {
    const response = await this.api.get<Trip[]>('/v2/trips');
    return response.data;
  }


  // --- Planning Endpoints (V2) ---

  async startPlanning(data: any): Promise<any> {
    const response = await this.api.post('/v2/planning/start', data);
    return response.data;
  }

  async discoverPlaces(sessionId: string, vibe: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/places/discover`, { vibe });
    return response.data;
  }

  async selectPlaces(sessionId: string, placeIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/places/select`, {
      selected_place_ids: placeIds
    });
    return response.data;
  }

  async searchAccommodations(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/accommodations/search`);
    return response.data;
  }

  async selectAccommodation(sessionId: string, hotelIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/accommodations/select`, {
      selected_hotel_ids: hotelIds
    });
    return response.data;
  }

  async searchDining(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/dining/search`);
    return response.data;
  }

  async searchActivities(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/activities/search`);
    return response.data;
  }

  async searchShopping(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/shopping/search`);
    return response.data;
  }

  async searchTransport(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/transport/search`);
    return response.data;
  }

  async selectTransport(sessionId: string, selectedIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/transport/select`, {
      selected_transport_ids: selectedIds
    });
    return response.data;
  }

  async selectDining(sessionId: string, selectedIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/dining/select`, {
      selected_dining_ids: selectedIds
    });
    return response.data;
  }

  async selectActivities(sessionId: string, selectedIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/activities/select`, {
      selected_activity_ids: selectedIds
    });
    return response.data;
  }

  async selectShopping(sessionId: string, selectedIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/shopping/select`, {
      selected_shopping_ids: selectedIds
    });
    return response.data;
  }

  async selectWellness(sessionId: string, selectedIds: string[]): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/wellness/select`, {
      selected_wellness_ids: selectedIds
    });
    return response.data;
  }

  async searchWellness(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/wellness/search`);
    return response.data;
  }

  async generateItinerary(sessionId: string): Promise<any> {
    const response = await this.api.post(`/v2/planning/${sessionId}/itinerary/generate`);
    return response.data;
  }
}

export const api = new ApiService();
