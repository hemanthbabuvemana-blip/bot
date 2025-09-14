from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from datetime import datetime

from database.db_manager import DatabaseManager
from services.ml_service import MLService
from services.nlp_service import NLPService
from utils.file_handler import FileHandler

# Optional chatbot import
try:
    from services.chatbot_service import ChatbotService
    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False
    ChatbotService = None

app = FastAPI(title="ACTMS API", description="Anti-Corruption Tender Management System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = DatabaseManager()
ml_service = MLService()
nlp_service = NLPService()
chatbot_service = ChatbotService() if CHATBOT_AVAILABLE else None
file_handler = FileHandler()

# Pydantic models for request/response
class BidCreate(BaseModel):
    tender_id: int
    company_name: str
    contact_email: str
    bid_amount: float
    proposal: str

class ChatMessage(BaseModel):
    message: str

class DashboardResponse(BaseModel):
    total_tenders: int
    active_tenders: int
    total_bids: int
    total_alerts: int

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """Serve the main HTML file"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "ACTMS API is running. Place your HTML file at static/index.html"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/dashboard")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_tenders = db.get_tender_count()
        active_tenders = total_tenders  # All tenders are active by default
        total_bids = db.get_bid_count()
        total_alerts = db.get_alert_count()
        
        return DashboardResponse(
            total_tenders=total_tenders,
            active_tenders=active_tenders,
            total_bids=total_bids,
            total_alerts=total_alerts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenders")
async def get_tenders(status: Optional[str] = None):
    """Get all tenders or filtered by status"""
    try:
        tenders_df = db.get_tenders(status)
        return tenders_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tenders")
async def create_tender(
    title: str = Form(...),
    description: str = Form(...),
    department: str = Form(...),
    estimated_value: float = Form(...),
    deadline: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Create a new tender with optional file upload"""
    try:
        file_path = None
        extracted_info = None
        
        if file:
            # Save uploaded file
            file_path = file_handler.save_uploaded_file(file.filename, await file.read())
            
            # Extract information using NLP service
            extracted_info = nlp_service.extract_document_info(file_path)
            extracted_info = json.dumps(extracted_info)
        
        tender_id = db.insert_tender(
            title=title,
            description=description,
            department=department,
            estimated_value=estimated_value,
            deadline=deadline,
            file_path=file_path,
            extracted_info=extracted_info
        )
        
        return {"tender_id": tender_id, "message": "Tender created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bids")
async def get_bids(tender_id: Optional[int] = None):
    """Get all bids or filtered by tender_id"""
    try:
        bids_df = db.get_bids(tender_id)
        return bids_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bids")
async def create_bid(bid: BidCreate):
    """Create a new bid"""
    try:
        bid_id = db.insert_bid(
            tender_id=bid.tender_id,
            company_name=bid.company_name,
            contact_email=bid.contact_email,
            bid_amount=bid.bid_amount,
            proposal=bid.proposal
        )
        
        # Analyze bid for anomalies
        try:
            anomaly_score, is_suspicious = ml_service.analyze_bid({
                'bid_amount': bid.bid_amount,
                'proposal': bid.proposal,
                'company_name': bid.company_name
            })
            
            # Update bid with anomaly results
            db.update_bid_anomaly_score(bid_id, anomaly_score, is_suspicious)
            
            # Create alert if suspicious
            if is_suspicious:
                db.create_ai_alert(
                    alert_type="suspicious_bid",
                    severity="high",
                    message=f"Suspicious bid detected from {bid.company_name}",
                    related_entity_type="bid",
                    related_entity_id=bid_id
                )
        except Exception as ml_error:
            print(f"ML analysis failed: {ml_error}")
        
        return {"bid_id": bid_id, "message": "Bid submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """Get all active alerts"""
    try:
        alerts_df = db.get_ai_alerts()
        return alerts_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bids/suspicious")
async def get_suspicious_bids():
    """Get all suspicious bids"""
    try:
        suspicious_bids_df = db.get_suspicious_bids()
        return suspicious_bids_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/train")
async def train_ml_model():
    """Train the ML model with current bid data"""
    try:
        bids_df = db.get_bids()
        if len(bids_df) == 0:
            raise HTTPException(status_code=400, detail="No bid data available for training")
        
        success = ml_service.train_model(bids_df)
        if success:
            return {"message": "Model trained successfully"}
        else:
            raise HTTPException(status_code=500, detail="Model training failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/bid")
async def analyze_bid(bid_data: dict):
    """Analyze a bid for anomalies"""
    try:
        anomaly_score, is_suspicious = ml_service.analyze_bid(bid_data)
        return {
            "anomaly_score": anomaly_score,
            "is_suspicious": is_suspicious,
            "explanation": "High anomaly score indicates unusual bidding patterns"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatbotRequest(BaseModel):
    message: str
    history: Optional[List] = []

@app.post("/api/chatbot")
async def chat_with_bot(request: ChatbotRequest):
    """Chat with the AI assistant with conversation history support"""
    if not CHATBOT_AVAILABLE or chatbot_service is None:
        # Fallback response when chatbot is not available
        return {"response": "Hello! I'm currently in basic mode. You can ask me about tenders, bids, or system features. For more advanced assistance, the AI chatbot service needs to be configured."}
    
    try:
        response_data = chatbot_service.get_response(request.message, request.history)
        return {
            "response": response_data.get("response", response_data) if isinstance(response_data, dict) else response_data,
            "source": response_data.get("source", "AI Assistant") if isinstance(response_data, dict) else "AI Assistant",
            "confidence": response_data.get("confidence", 0.95) if isinstance(response_data, dict) else 0.95
        }
    except Exception as e:
        # Fallback to FAQ if chatbot service fails
        return {"response": f"Sorry, I'm having technical difficulties. Please try again later.", "source": "Error Handler", "confidence": 0.0}

# Alert management endpoints
@app.put("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Mark an alert as resolved"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Update alert status to resolved
        cursor.execute(
            "UPDATE ai_alerts SET status = 'resolved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (alert_id,)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Alert not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Alert marked as resolved successfully", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@app.get("/api/bids/{bid_id}")
async def get_bid_details(bid_id: int):
    """Get detailed information about a specific bid"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, t.title as tender_title 
            FROM bids b 
            LEFT JOIN tenders t ON b.tender_id = t.id 
            WHERE b.id = ?
        """, (bid_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="Bid not found")
        
        # Convert to dictionary
        columns = [description[0] for description in cursor.description]
        bid_data = dict(zip(columns, result))
        conn.close()
        
        return bid_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch bid details")

# Model training endpoints
@app.get("/api/model/status")
async def get_model_status():
    """Get ML model training status and information"""
    try:
        model_info = ml_service.get_model_info()
        bids_df = db.get_bids()
        total_bids = len(bids_df)
        
        return {
            "is_trained": model_info["is_trained"],
            "model_type": model_info["model_type"],
            "contamination_rate": model_info["contamination_rate"],
            "n_estimators": model_info["n_estimators"],
            "features_used": model_info["features_used"],
            "total_bids": total_bids,
            "can_train": total_bids >= 10
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get model status")

@app.post("/api/model/train")
async def train_model():
    """Train the ML model with current bid data"""
    try:
        bids_df = db.get_bids()
        
        if len(bids_df) < 10:
            raise HTTPException(status_code=400, detail="Need at least 10 bids to train the model")
        
        success = ml_service.train_model(bids_df)
        
        if not success:
            raise HTTPException(status_code=500, detail="Model training failed")
        
        # Run analysis on all existing bids
        anomaly_scores, is_anomaly = ml_service.detect_anomalies(bids_df)
        
        suspicious_count = 0
        if len(anomaly_scores) > 0:
            for idx, (_, bid) in enumerate(bids_df.iterrows()):
                db.update_bid_anomaly_score(
                    bid['id'], 
                    float(anomaly_scores[idx]), 
                    bool(is_anomaly[idx])
                )
                
                if is_anomaly[idx]:
                    suspicious_count += 1
                    db.create_ai_alert(
                        alert_type="Suspicious Bid",
                        severity="medium",
                        message=f"Suspicious bid detected during model retraining for bid ID {bid['id']}",
                        related_entity_type="bid",
                        related_entity_id=bid['id']
                    )
        
        return {
            "message": "Model trained successfully",
            "total_bids": len(bids_df),
            "suspicious_count": suspicious_count,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Model training failed")

@app.post("/api/model/test")
async def test_model_performance():
    """Test the trained ML model performance"""
    try:
        if not ml_service.is_trained:
            raise HTTPException(status_code=400, detail="Model is not trained yet")
        
        bids_df = db.get_bids()
        
        if len(bids_df) == 0:
            raise HTTPException(status_code=400, detail="No bid data available for testing")
        
        anomaly_scores, is_anomaly = ml_service.detect_anomalies(bids_df)
        
        if len(anomaly_scores) == 0:
            raise HTTPException(status_code=500, detail="Could not generate predictions")
        
        total_predictions = len(anomaly_scores)
        anomalies_detected = sum(is_anomaly)
        detection_rate = (anomalies_detected / total_predictions) * 100
        
        return {
            "total_predictions": total_predictions,
            "anomalies_detected": anomalies_detected,
            "detection_rate": round(detection_rate, 1),
            "score_range": {
                "min": float(min(anomaly_scores)),
                "max": float(max(anomaly_scores)),
                "avg": float(sum(anomaly_scores) / len(anomaly_scores))
            },
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Model testing failed")

# System metrics endpoint
@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get system overview metrics for dashboard"""
    try:
        tender_count = db.get_tender_count()
        bid_count = db.get_bid_count()
        alert_count = db.get_alert_count()
        
        alerts_df = db.get_ai_alerts()
        high_alerts = len(alerts_df[alerts_df['severity'] == 'high']) if len(alerts_df) > 0 else 0
        medium_alerts = len(alerts_df[alerts_df['severity'] == 'medium']) if len(alerts_df) > 0 else 0
        low_alerts = len(alerts_df[alerts_df['severity'] == 'low']) if len(alerts_df) > 0 else 0
        
        return {
            "active_tenders": tender_count,
            "total_bids": bid_count,
            "active_alerts": alert_count,
            "alert_breakdown": {
                "high": high_alerts,
                "medium": medium_alerts,
                "low": low_alerts
            },
            "system_status": "normal" if alert_count == 0 else "alerts_present"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@app.get("/api/faqs")
async def get_faqs():
    """Get frequently asked questions"""
    try:
        faqs_path = "data/faqs.json"
        if os.path.exists(faqs_path):
            with open(faqs_path, 'r') as f:
                faqs = json.load(f)
            return faqs
        return {"faqs": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Frontend compatibility aliases - fixes endpoint mismatches
@app.post("/api/ml/train")
async def train_model_alias():
    """Alias for /api/model/train to match frontend expectations"""
    return await train_model()

@app.post("/api/ml/test")  
async def test_model_alias():
    """Alias for /api/model/test to match frontend expectations"""
    return await test_model_performance()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)