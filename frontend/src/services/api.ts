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

/** One frame from the itinerary SSE stream. */
export interface ItineraryStreamEvent {
  type: 'stages' | 'stage' | 'complete' | 'error';
  /** Sent once, first: the full stage list so the UI can draw the checklist. */
  stages?: { id: string; label: string }[];
  /** Sent on each transition: which stage, and whether it started or finished. */
  stage?: string;
  status?: 'active' | 'done';
  itinerary?: any;
  detail?: string;
}

/** A row in the trips list, as the backend returns it. */
export interface SavedTripSummaryDTO {
  id: string;
  destination: string | null;
  dates: string | null;
  days: number;
  saved_at: string;
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
              toast.error('You have been signed out', { description: 'Your session expired. Sign in again to continue.' });
              // Optionally clear token here
              this.setToken(null);
              break;
            case 403:
              toast.error('Not allowed', { description: 'Your account cannot do that.' });
              break;
            case 404:
              toast.error('We could not find that', { description: 'It may have expired. Start a new trip to continue.' });
              break;
            case 422:
              toast.error('Check your details', { description: message });
              break;
            case 500:
              toast.error('The planner hit a problem', { description: 'A provider may be busy. Try again in a moment.' });
              break;
            default:
              toast.error('That did not work', { description: message });
          }
        } else if (error.request) {
          toast.error('We could not reach the server', { description: 'Check your connection, or that the backend is running.' });
        } else {
          toast.error('That did not work', { description: message });
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

  async getPlanningSession(sessionId: string): Promise<any> {
    const response = await this.api.get(`/v2/planning/${sessionId}`);
    return response.data;
  }

  // --- Saved trips -----------------------------------------------------------
  // Account-backed storage for "My trips". Guests fall back to localStorage;
  // see lib/planning-storage.

  async listSavedTrips(): Promise<SavedTripSummaryDTO[]> {
    const response = await this.api.get<SavedTripSummaryDTO[]>('/v2/saved-trips');
    return response.data;
  }

  async saveTrip(sessionId: string, trip: any): Promise<void> {
    await this.api.put(`/v2/saved-trips/${sessionId}`, { session_id: sessionId, trip });
  }

  async getSavedTrip(sessionId: string): Promise<any | null> {
    try {
      const response = await this.api.get(`/v2/saved-trips/${sessionId}`);
      return response.data?.trip ?? null;
    } catch {
      return null;
    }
  }

  async deleteSavedTrip(sessionId: string): Promise<void> {
    await this.api.delete(`/v2/saved-trips/${sessionId}`);
  }

  /**
   * Generate the itinerary over SSE, reporting each stage as it starts and
   * finishes. Resolves with the finished itinerary.
   *
   * Uses fetch rather than EventSource: EventSource cannot send an
   * Authorization header, and we are not putting a bearer token in a URL.
   * Falls back to the plain non-streaming endpoint if the stream is
   * unavailable, so an older backend still works.
   */
  async streamItinerary(
    sessionId: string,
    onEvent: (event: ItineraryStreamEvent) => void,
    signal?: AbortSignal
  ): Promise<any> {
    const token = this.getToken();
    let response: Response;

    try {
      response = await fetch(`${this.api.defaults.baseURL}/v2/planning/${sessionId}/itinerary/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal,
      });
    } catch {
      return this.generateItinerary(sessionId);
    }

    if (!response.ok || !response.body) {
      if (response.status === 404) {
        const error: any = new Error('Session not found');
        error.response = { status: 404 };
        throw error;
      }
      return this.generateItinerary(sessionId);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let itinerary: any = null;
    let streamError: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line; a partial frame stays in the
      // buffer until the rest of it arrives.
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';

      for (const frame of frames) {
        const line = frame.split('\n').find((l) => l.startsWith('data:'));
        if (!line) continue;
        let event: ItineraryStreamEvent;
        try {
          event = JSON.parse(line.slice(5).trim());
        } catch {
          continue;
        }
        onEvent(event);
        if (event.type === 'complete') itinerary = event.itinerary;
        if (event.type === 'error') streamError = event.detail ?? 'Itinerary generation failed';
      }
    }

    if (streamError) throw new Error(streamError);
    if (!itinerary) throw new Error('Itinerary generation ended without a result');
    return itinerary;
  }
}

export const api = new ApiService();
