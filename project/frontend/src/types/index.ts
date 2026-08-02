export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PredictionRequest {
  latitude: number;
  longitude: number;
  current_speed: number;
}

export interface Prediction {
  id: string;
  latitude: number;
  longitude: number;
  temperature: number | null;
  humidity: number | null;
  rainfall: number | null;
  visibility: number | null;
  wind_speed: number | null;
  road_condition: string | null;
  traffic_density: string | null;
  current_speed: number | null;
  recommended_speed: number;
  risk_level: 'Low' | 'Medium' | 'High';
  confidence_score: number;
  explanation: string;
  shap_values: Record<string, number>;
  created_at: string;
}

export interface LivePrediction {
  recommended_speed: number;
  risk_level: 'Low' | 'Medium' | 'High';
  confidence_score: number;
  explanation: string;
}
