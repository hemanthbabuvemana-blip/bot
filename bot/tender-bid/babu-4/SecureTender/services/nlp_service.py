import spacy
import re
from datetime import datetime
import json

class NLPService:
    def __init__(self):
        # Try to load spaCy model, fallback to basic processing if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except OSError:
            print("spaCy model not found. Using basic text processing.")
            self.spacy_available = False
            self.nlp = None
    
    def extract_tender_info(self, text):
        """Extract key information from tender documents"""
        if not text:
            return {}
        
        extracted_info = {}
        
        # Extract monetary values
        extracted_info['monetary_values'] = self._extract_monetary_values(text)
        
        # Extract dates
        extracted_info['dates'] = self._extract_dates(text)
        
        # Extract entities (if spaCy is available)
        if self.spacy_available:
            extracted_info['entities'] = self._extract_entities_spacy(text)
        else:
            extracted_info['entities'] = self._extract_entities_basic(text)
        
        # Extract requirements and specifications
        extracted_info['requirements'] = self._extract_requirements(text)
        
        # Extract contact information
        extracted_info['contact_info'] = self._extract_contact_info(text)
        
        # Extract technical specifications
        extracted_info['technical_specs'] = self._extract_technical_specs(text)
        
        # Calculate text statistics
        extracted_info['text_stats'] = self._calculate_text_stats(text)
        
        return extracted_info
    
    def _extract_monetary_values(self, text):
        """Extract monetary values from text"""
        # Patterns for different currency formats
        patterns = [
            r'\$[\d,]+\.?\d*',  # $1,000.00
            r'USD\s*[\d,]+\.?\d*',  # USD 1000
            r'[\d,]+\.?\d*\s*(?:dollars?|USD|\$)',  # 1000 dollars
            r'₹[\d,]+\.?\d*',  # ₹1,000
            r'INR\s*[\d,]+\.?\d*',  # INR 1000
            r'€[\d,]+\.?\d*',  # €1,000
            r'EUR\s*[\d,]+\.?\d*',  # EUR 1000
        ]
        
        monetary_values = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            monetary_values.extend(matches)
        
        return list(set(monetary_values))  # Remove duplicates
    
    def _extract_dates(self, text):
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # DD Month YYYY
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_entities_spacy(self, text):
        """Extract named entities using spaCy"""
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        
        # Remove duplicates
        for label in entities:
            entities[label] = list(set(entities[label]))
        
        return entities
    
    def _extract_entities_basic(self, text):
        """Basic entity extraction without spaCy"""
        entities = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            entities['EMAIL'] = list(set(emails))
        
        # Extract phone numbers
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities['PHONE'] = list(set(phones))
        
        # Extract potential organization names (capitalized words)
        org_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        orgs = re.findall(org_pattern, text)
        if orgs:
            entities['ORG'] = list(set(orgs[:10]))  # Limit to first 10
        
        return entities
    
    def _extract_requirements(self, text):
        """Extract requirements and specifications"""
        requirement_keywords = [
            'must', 'shall', 'required', 'mandatory', 'necessary',
            'should', 'need', 'specification', 'requirement'
        ]
        
        requirements = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword.lower() in sentence.lower() for keyword in requirement_keywords):
                if len(sentence) > 20 and len(sentence) < 200:  # Filter reasonable length
                    requirements.append(sentence)
        
        return requirements[:10]  # Limit to first 10 requirements
    
    def _extract_contact_info(self, text):
        """Extract contact information"""
        contact_info = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['emails'] = list(set(emails))
        
        # Extract phone numbers (more comprehensive)
        phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
            r'\+?[0-9]{1,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',  # International
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        if phones:
            contact_info['phones'] = list(set(phones))
        
        # Extract addresses (basic pattern)
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\.?'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        if addresses:
            contact_info['addresses'] = list(set(addresses))
        
        return contact_info
    
    def _extract_technical_specs(self, text):
        """Extract technical specifications"""
        # Look for technical terms and specifications
        tech_patterns = [
            r'\d+\s*(?:GB|MB|TB|MHz|GHz|kg|lbs|meters?|feet|inches?)',  # Units
            r'(?:Model|Version|Type|Series)\s*:?\s*[A-Za-z0-9\-]+',  # Model numbers
            r'[A-Za-z0-9\-]+\s*(?:compatibility|compatible|support)',  # Compatibility
        ]
        
        technical_specs = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technical_specs.extend(matches)
        
        return list(set(technical_specs))[:15]  # Limit and remove duplicates
    
    def _calculate_text_stats(self, text):
        """Calculate basic text statistics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'character_count': len(text),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }
    
    def analyze_bid_proposal(self, proposal_text):
        """Analyze bid proposal for quality and completeness"""
        if not proposal_text:
            return {'quality_score': 0, 'issues': ['Empty proposal']}
        
        analysis = {
            'quality_score': 0,
            'issues': [],
            'strengths': [],
            'word_count': len(proposal_text.split()),
            'readability': 'Unknown'
        }
        
        # Check proposal length
        word_count = len(proposal_text.split())
        if word_count < 50:
            analysis['issues'].append('Proposal too short (less than 50 words)')
        elif word_count > 2000:
            analysis['issues'].append('Proposal very long (over 2000 words)')
        else:
            analysis['strengths'].append('Appropriate proposal length')
            analysis['quality_score'] += 20
        
        # Check for key sections
        key_sections = ['experience', 'approach', 'timeline', 'cost', 'team']
        found_sections = []
        
        for section in key_sections:
            if section.lower() in proposal_text.lower():
                found_sections.append(section)
                analysis['quality_score'] += 15
        
        if found_sections:
            analysis['strengths'].append(f'Contains key sections: {", ".join(found_sections)}')
        else:
            analysis['issues'].append('Missing key proposal sections (experience, approach, timeline, etc.)')
        
        # Check for contact information
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', proposal_text):
            analysis['strengths'].append('Contains contact information')
            analysis['quality_score'] += 10
        else:
            analysis['issues'].append('No contact information found')
        
        # Check for specific details
        if re.search(r'\d+', proposal_text):
            analysis['strengths'].append('Contains specific numbers/details')
            analysis['quality_score'] += 10
        
        # Basic readability assessment
        sentences = re.split(r'[.!?]+', proposal_text)
        avg_sentence_length = word_count / len(sentences) if sentences else 0
        
        if avg_sentence_length < 10:
            analysis['readability'] = 'Very Easy'
        elif avg_sentence_length < 15:
            analysis['readability'] = 'Easy'
        elif avg_sentence_length < 20:
            analysis['readability'] = 'Moderate'
        elif avg_sentence_length < 25:
            analysis['readability'] = 'Difficult'
        else:
            analysis['readability'] = 'Very Difficult'
        
        # Cap quality score at 100
        analysis['quality_score'] = min(analysis['quality_score'], 100)
        
        return analysis
    
    def extract_key_phrases(self, text, max_phrases=10):
        """Extract key phrases from text"""
        if not text:
            return []
        
        # Simple key phrase extraction using word frequency
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        # Extract potential phrases (2-3 words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [word for word in words if word not in stop_words]
        
        # Create bigrams and trigrams
        phrases = []
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            phrases.append(bigram)
            
            if i < len(words) - 2:
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                phrases.append(trigram)
        
        # Count phrase frequency
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Sort by frequency and return top phrases
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, freq in sorted_phrases[:max_phrases] if freq > 1]
