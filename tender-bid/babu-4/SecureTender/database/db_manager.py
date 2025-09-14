import sqlite3
import os
import json
from datetime import datetime
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path="actms.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tenders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            department TEXT,
            estimated_value REAL,
            deadline DATE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            extracted_info TEXT
        )
        ''')
        
        # Bids table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_id INTEGER,
            company_name TEXT NOT NULL,
            contact_email TEXT,
            bid_amount REAL NOT NULL,
            proposal TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'submitted',
            anomaly_score REAL DEFAULT 0.0,
            is_suspicious BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (tender_id) REFERENCES tenders (id)
        )
        ''')
        
        # Audit logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            user_info TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
        ''')
        
        # AI alerts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            severity TEXT,
            message TEXT,
            related_entity_type TEXT,
            related_entity_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def insert_tender(self, title, description, department, estimated_value, deadline, file_path=None, extracted_info=None):
        """Insert a new tender"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert tender
            cursor.execute('''
            INSERT INTO tenders (title, description, department, estimated_value, deadline, file_path, extracted_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, department, estimated_value, deadline, file_path, extracted_info))
            
            tender_id = cursor.lastrowid
            
            # Log the action using the same connection
            cursor.execute('''
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
            ''', ("CREATE", "tender", tender_id, f"Created tender: {title}"))
            
            conn.commit()
            return tender_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def insert_bid(self, tender_id, company_name, contact_email, bid_amount, proposal):
        """Insert a new bid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert bid
            cursor.execute('''
            INSERT INTO bids (tender_id, company_name, contact_email, bid_amount, proposal)
            VALUES (?, ?, ?, ?, ?)
            ''', (tender_id, company_name, contact_email, bid_amount, proposal))
            
            bid_id = cursor.lastrowid
            
            # Log the action using the same connection
            cursor.execute('''
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
            ''', ("CREATE", "bid", bid_id, f"Submitted bid by {company_name}"))
            
            conn.commit()
            return bid_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_bid_anomaly_score(self, bid_id, anomaly_score, is_suspicious):
        """Update bid with anomaly detection results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE bids 
        SET anomaly_score = ?, is_suspicious = ?
        WHERE id = ?
        ''', (anomaly_score, is_suspicious, bid_id))
        
        conn.commit()
        conn.close()
    
    def log_audit_action(self, action, entity_type, entity_id, details):
        """Log an audit action"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
        ''', (action, entity_type, entity_id, details))
        
        conn.commit()
        conn.close()
    
    def create_ai_alert(self, alert_type, severity, message, related_entity_type=None, related_entity_id=None):
        """Create an AI alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ai_alerts (alert_type, severity, message, related_entity_type, related_entity_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, severity, message, related_entity_type, related_entity_id))
        
        conn.commit()
        conn.close()
    
    def get_tenders(self, status=None):
        """Get all tenders or filtered by status"""
        conn = self.get_connection()
        
        if status:
            query = "SELECT * FROM tenders WHERE status = ? ORDER BY created_at DESC"
            df = pd.read_sql_query(query, conn, params=(status,))
        else:
            query = "SELECT * FROM tenders ORDER BY created_at DESC"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_bids(self, tender_id=None):
        """Get all bids or filtered by tender_id"""
        conn = self.get_connection()
        
        if tender_id:
            query = '''
            SELECT b.*, t.title as tender_title 
            FROM bids b 
            JOIN tenders t ON b.tender_id = t.id 
            WHERE b.tender_id = ?
            ORDER BY b.submitted_at DESC
            '''
            df = pd.read_sql_query(query, conn, params=(tender_id,))
        else:
            query = '''
            SELECT b.*, t.title as tender_title 
            FROM bids b 
            JOIN tenders t ON b.tender_id = t.id 
            ORDER BY b.submitted_at DESC
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_suspicious_bids(self):
        """Get all suspicious bids"""
        conn = self.get_connection()
        
        query = '''
        SELECT b.*, t.title as tender_title 
        FROM bids b 
        JOIN tenders t ON b.tender_id = t.id 
        WHERE b.is_suspicious = TRUE
        ORDER BY b.anomaly_score DESC
        '''
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_ai_alerts(self, status='active'):
        """Get AI alerts"""
        conn = self.get_connection()
        
        query = "SELECT * FROM ai_alerts WHERE status = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(status,))
        
        conn.close()
        return df
    
    def get_tender_count(self):
        """Get total number of active tenders"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tenders WHERE status = 'active'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_bid_count(self):
        """Get total number of bids"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bids")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_alert_count(self):
        """Get total number of active alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ai_alerts WHERE status = 'active'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_tender_by_id(self, tender_id):
        """Get a specific tender by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenders WHERE id = ?", (tender_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_audit_logs(self):
        """Get all audit logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
        results = cursor.fetchall()
        conn.close()
        return results
    
    def clear_all_data(self):
        """Clear all data from the database (keeps table structure)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear all tables in the correct order (due to foreign key constraints)
            cursor.execute("DELETE FROM ai_alerts")
            cursor.execute("DELETE FROM bids") 
            cursor.execute("DELETE FROM tenders")
            cursor.execute("DELETE FROM audit_logs")
            
            # Log the clear operation
            cursor.execute('''
            INSERT INTO audit_logs (action, entity_type, details)
            VALUES (?, ?, ?)
            ''', ("CLEAR_ALL", "system", "All system data cleared"))
            
            conn.commit()
            return True, "All data cleared successfully"
        except Exception as e:
            conn.rollback()
            return False, f"Error clearing data: {str(e)}"
        finally:
            conn.close()
    
    def clear_table_data(self, table_name):
        """Clear data from a specific table"""
        valid_tables = ['tenders', 'bids', 'audit_logs', 'ai_alerts']
        if table_name not in valid_tables:
            return False, f"Invalid table name. Valid tables: {valid_tables}"
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Log the clear operation
            cursor.execute('''
            INSERT INTO audit_logs (action, entity_type, details)
            VALUES (?, ?, ?)
            ''', ("CLEAR_TABLE", table_name, f"Cleared all data from {table_name} table"))
            
            conn.commit()
            return True, f"{table_name} data cleared successfully"
        except Exception as e:
            conn.rollback()
            return False, f"Error clearing {table_name}: {str(e)}"
        finally:
            conn.close()
