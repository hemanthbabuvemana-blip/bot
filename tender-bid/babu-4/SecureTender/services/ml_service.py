import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os
from datetime import datetime

class MLService:
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% outliers
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.text_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.is_trained = False
        self.model_path = "models/"
        
        # Create models directory if it doesn't exist
        os.makedirs(self.model_path, exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def extract_numerical_features(self, bids_df):
        """Extract numerical features from bids data"""
        features = []
        
        for _, bid in bids_df.iterrows():
            feature_vector = [
                bid['bid_amount'],
                len(bid['proposal']) if pd.notna(bid['proposal']) else 0,
                len(bid['company_name']) if pd.notna(bid['company_name']) else 0,
            ]
            
            # Add time-based features
            if pd.notna(bid['submitted_at']):
                try:
                    submit_time = pd.to_datetime(bid['submitted_at'])
                    feature_vector.extend([
                        submit_time.hour,
                        submit_time.weekday(),
                    ])
                except:
                    feature_vector.extend([12, 2])  # Default values
            else:
                feature_vector.extend([12, 2])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def extract_text_features(self, bids_df):
        """Extract text features from proposal content"""
        proposals = []
        for _, bid in bids_df.iterrows():
            proposal_text = bid['proposal'] if pd.notna(bid['proposal']) else ""
            company_name = bid['company_name'] if pd.notna(bid['company_name']) else ""
            combined_text = f"{proposal_text} {company_name}"
            proposals.append(combined_text)
        
        if not self.is_trained:
            text_features = self.text_vectorizer.fit_transform(proposals)
        else:
            text_features = self.text_vectorizer.transform(proposals)
        
        return text_features.toarray()
    
    def prepare_features(self, bids_df):
        """Prepare features for anomaly detection"""
        if len(bids_df) == 0:
            return np.array([])
        
        # Extract numerical features
        numerical_features = self.extract_numerical_features(bids_df)
        
        # Extract text features
        text_features = self.extract_text_features(bids_df)
        
        # Combine features
        if text_features.size > 0:
            combined_features = np.hstack([numerical_features, text_features])
        else:
            combined_features = numerical_features
        
        return combined_features
    
    def train_model(self, bids_df):
        """Train the anomaly detection model"""
        if len(bids_df) < 10:  # Need minimum data to train
            return False
        
        features = self.prepare_features(bids_df)
        
        if features.size == 0:
            return False
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Train isolation forest
        self.isolation_forest.fit(scaled_features)
        self.is_trained = True
        
        # Save the model
        self.save_model()
        
        return True
    
    def detect_anomalies(self, bids_df):
        """Detect anomalies in bids"""
        if not self.is_trained or len(bids_df) == 0:
            return np.array([]), np.array([])
        
        features = self.prepare_features(bids_df)
        
        if features.size == 0:
            return np.array([]), np.array([])
        
        try:
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Predict anomalies
            anomaly_predictions = self.isolation_forest.predict(scaled_features)
            anomaly_scores = self.isolation_forest.decision_function(scaled_features)
            
            # Convert predictions to boolean (True for anomaly)
            is_anomaly = anomaly_predictions == -1
            
            return anomaly_scores, is_anomaly
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return np.array([]), np.array([])
    
    def analyze_single_bid(self, bid_data):
        """Analyze a single bid for anomalies"""
        if not self.is_trained:
            return 0.0, False
        
        # Convert single bid to DataFrame format
        bid_df = pd.DataFrame([bid_data])
        
        anomaly_scores, is_anomaly = self.detect_anomalies(bid_df)
        
        if len(anomaly_scores) > 0:
            return float(anomaly_scores[0]), bool(is_anomaly[0])
        else:
            return 0.0, False
    
    def get_anomaly_explanation(self, bid_data, anomaly_score):
        """Provide explanation for anomaly detection"""
        explanations = []
        
        # Check bid amount patterns
        if bid_data.get('bid_amount', 0) <= 0:
            explanations.append("Invalid bid amount (zero or negative)")
        
        # Check proposal length
        proposal_length = len(bid_data.get('proposal', ''))
        if proposal_length < 50:
            explanations.append("Very short proposal (less than 50 characters)")
        elif proposal_length > 5000:
            explanations.append("Unusually long proposal (over 5000 characters)")
        
        # Check company name
        company_name = bid_data.get('company_name', '')
        if len(company_name) < 3:
            explanations.append("Suspicious company name (too short)")
        
        # Check submission timing
        try:
            if 'submitted_at' in bid_data:
                submit_time = pd.to_datetime(bid_data['submitted_at'])
                if submit_time.hour < 6 or submit_time.hour > 22:
                    explanations.append("Unusual submission time (outside business hours)")
        except:
            pass
        
        if not explanations:
            if anomaly_score < -0.1:
                explanations.append("Pattern deviates significantly from normal bidding behavior")
            else:
                explanations.append("Mild deviation from typical bid patterns")
        
        return explanations
    
    def save_model(self):
        """Save the trained model"""
        try:
            joblib.dump(self.isolation_forest, os.path.join(self.model_path, 'isolation_forest.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            joblib.dump(self.text_vectorizer, os.path.join(self.model_path, 'text_vectorizer.pkl'))
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load existing trained model"""
        try:
            if all(os.path.exists(os.path.join(self.model_path, f)) for f in 
                   ['isolation_forest.pkl', 'scaler.pkl', 'text_vectorizer.pkl']):
                
                self.isolation_forest = joblib.load(os.path.join(self.model_path, 'isolation_forest.pkl'))
                self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.pkl'))
                self.text_vectorizer = joblib.load(os.path.join(self.model_path, 'text_vectorizer.pkl'))
                self.is_trained = True
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        
        return False
    
    def get_model_info(self):
        """Get information about the current model"""
        return {
            'is_trained': self.is_trained,
            'model_type': 'Isolation Forest',
            'contamination_rate': self.isolation_forest.contamination,
            'n_estimators': self.isolation_forest.n_estimators,
            'features_used': ['bid_amount', 'proposal_length', 'company_name_length', 
                            'submission_hour', 'submission_weekday', 'text_features']
        }
