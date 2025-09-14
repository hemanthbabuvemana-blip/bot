import random
import pandas as pd
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

class TestDataGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        
    def generate_test_bids(self, num_bids=10):
        """Generate test bids for AI model training"""
        
        # Sample company names
        companies = [
            "TechSolutions Corp", "InnovateIT Ltd", "SecureCloud Systems", 
            "DataDrive Technologies", "CyberSafe Solutions", "CloudFirst Inc",
            "SmartTech Partners", "DigitalEdge Corp", "NextGen Systems",
            "TechFlow Solutions", "InfoSec Dynamics", "CloudCore Technologies"
        ]
        
        # Sample email domains
        email_domains = ["tech.com", "solutions.net", "corp.io", "systems.org", "inc.com"]
        
        # Sample proposal templates
        proposal_templates = [
            "We propose a comprehensive solution with {years} years of experience in {domain}. Our approach includes {feature1}, {feature2}, and {feature3} with guaranteed delivery within timeline.",
            "Our company offers cutting-edge {technology} solutions with expertise in {domain}. We provide {feature1}, {feature2}, and 24/7 support for optimal performance.",
            "We specialize in {domain} with proven track record of {years} years. Our solution features {technology}, {feature1}, and comprehensive {feature2} implementation.",
            "Professional {technology} implementation with focus on {domain}. Our team delivers {feature1}, advanced {feature2}, and ongoing maintenance support.",
            "Enterprise-grade {technology} solution for {domain} requirements. We offer {feature1}, robust {feature2}, and scalable architecture design."
        ]
        
        # Sample parameters for proposals
        technologies = ["cloud computing", "AI integration", "blockchain technology", "IoT systems", "machine learning"]
        domains = ["cybersecurity", "data analytics", "infrastructure management", "digital transformation", "automation"]
        features = ["real-time monitoring", "advanced encryption", "automated deployment", "performance optimization", "compliance management"]
        
        # Get available tenders
        tenders_df = self.db.get_tenders()
        if tenders_df.empty:
            print("No tenders available. Please create tenders first.")
            return []
            
        created_bids = []
        
        for i in range(num_bids):
            # Select random tender
            tender = tenders_df.sample(1).iloc[0]  # Get random tender row
            tender_id = int(tender['id'])  # Ensure integer type
            tender_value = float(tender['estimated_value']) if 'estimated_value' in tender and pd.notna(tender['estimated_value']) else 100000.0
            
            # Generate company details
            company_name = random.choice(companies)
            email_domain = random.choice(email_domains)
            contact_email = f"contact@{company_name.lower().replace(' ', '').replace('&', '')}.{email_domain}"
            
            # Generate bid amount with some variation
            base_amount = float(tender_value) if tender_value else 100000
            # Add randomness: some bids are suspiciously low (potential red flags)
            if i % 7 == 0:  # Make some bids suspiciously low
                bid_amount = base_amount * random.uniform(0.3, 0.6)  # 30-60% of estimated value
            elif i % 5 == 0:  # Some bids are very high
                bid_amount = base_amount * random.uniform(1.5, 2.0)  # 150-200% of estimated value
            else:  # Normal competitive bids
                bid_amount = base_amount * random.uniform(0.8, 1.2)  # 80-120% of estimated value
                
            # Generate proposal
            template = random.choice(proposal_templates)
            proposal = template.format(
                years=random.randint(3, 20),
                technology=random.choice(technologies),
                domain=random.choice(domains),
                feature1=random.choice(features),
                feature2=random.choice(features),
                feature3=random.choice(features)
            )
            
            try:
                # Insert bid using the fixed database method
                bid_id = self.db.insert_bid(
                    tender_id=tender_id,
                    company_name=company_name,
                    contact_email=contact_email,
                    bid_amount=bid_amount,
                    proposal=proposal
                )
                
                created_bids.append({
                    'bid_id': bid_id,
                    'company_name': company_name,
                    'bid_amount': bid_amount,
                    'tender_id': tender_id
                })
                
                print(f"✅ Created bid {bid_id}: {company_name} - ${bid_amount:,.2f}")
                
            except Exception as e:
                print(f"❌ Error creating bid for {company_name}: {str(e)}")
                
        return created_bids

def main():
    """Main function to generate test data"""
    generator = TestDataGenerator()
    
    print("🚀 Generating test bids for AI model training...")
    bids = generator.generate_test_bids(8)  # Generate 8 more bids (we have 4, need 10+ total)
    
    print(f"\n📊 Generated {len(bids)} test bids successfully!")
    print("The AI model should now have enough data for training.")
    
if __name__ == "__main__":
    main()