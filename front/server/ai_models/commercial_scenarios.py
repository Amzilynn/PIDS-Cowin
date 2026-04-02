import time
import random
from datetime import datetime
import json

# ==================== SCENARIO 1: DELEGATE-DOCTOR CONVERSATION ====================

class MedicalCommercialScenario:
    """Simulates medical commercial conversations"""
    
    def __init__(self):
        self.conversation_log = []
        self.emotion_analysis = {
            'doctor': [],
            'delegate': []
        }
        
    def delegate_doctor_conversation(self):
        """Scenario 1: Medical Delegate discussing with Doctor"""
        
        print("\n" + "="*80)
        print("SCENARIO 1: MEDICAL COMMERCIAL CONVERSATION")
        print("Participants: Medical Delegate (Sarah) & Doctor (Dr. Williams)")
        print("Context: Introduction of new cardiac medication")
        print("="*80)
        
        conversation = []
        
        # Initial greeting
        print("\n[SCENE START: Doctor's Office, 9:30 AM]")
        time.sleep(1)
        
        # Delegate introduction
        delegate_1 = "Good morning, Dr. Williams. I'm Sarah from MedTech Pharmaceuticals. I appreciate you taking the time to meet with me today."
        print(f"\n[Delegate Sarah]: {delegate_1}")
        conversation.append(('delegate', delegate_1, self._analyze_speech(delegate_1, 'delegate')))
        time.sleep(1.5)
        
        doctor_1 = "Good morning, Sarah. I have about 15 minutes before my next patient. What new developments do you have for us?"
        print(f"\n[Dr. Williams]: {doctor_1}")
        conversation.append(('doctor', doctor_1, self._analyze_speech(doctor_1, 'doctor')))
        time.sleep(1.5)
        
        # Product introduction
        delegate_2 = "Thank you, Doctor. I'm here to discuss our new cardiac medication, CardioCare-X. It's the first once-daily combination therapy for hypertension and hyperlipidemia."
        print(f"\n[Delegate Sarah]: {delegate_2}")
        conversation.append(('delegate', delegate_2, self._analyze_speech(delegate_2, 'delegate')))
        time.sleep(1.5)
        
        doctor_2 = "Interesting. I've seen several combination therapies. What makes this one different? What's the clinical data supporting it?"
        print(f"\n[Dr. Williams]: {doctor_2}")
        conversation.append(('doctor', doctor_2, self._analyze_speech(doctor_2, 'doctor')))
        time.sleep(1.5)
        
        # Clinical data presentation
        delegate_3 = "Great question. We have Phase III trial data showing 32% better LDL reduction compared to standard therapy, with a 28% reduction in cardiovascular events. The safety profile is excellent - similar to placebo in terms of adverse events."
        print(f"\n[Delegate Sarah]: {delegate_3}")
        conversation.append(('delegate', delegate_3, self._analyze_speech(delegate_3, 'delegate')))
        time.sleep(2)
        
        doctor_3 = "Those are impressive numbers. What about drug interactions? Many of my patients are on multiple medications."
        print(f"\n[Dr. Williams]: {doctor_3}")
        conversation.append(('doctor', doctor_3, self._analyze_speech(doctor_3, 'doctor')))
        time.sleep(1.5)
        
        # Addressing concerns
        delegate_4 = "Excellent point. CardioCare-X has minimal CYP450 interactions, which is a key advantage. It's safe with statins, anticoagulants, and most common cardiac medications. We have a comprehensive interaction database available for physicians."
        print(f"\n[Delegate Sarah]: {delegate_4}")
        conversation.append(('delegate', delegate_4, self._analyze_speech(delegate_4, 'delegate')))
        time.sleep(2)
        
        doctor_4 = "That's reassuring. What about cost? Will this be accessible to patients? Insurance coverage?"
        print(f"\n[Dr. Williams]: {doctor_4}")
        conversation.append(('doctor', doctor_4, self._analyze_speech(doctor_4, 'doctor')))
        time.sleep(1.5)
        
        # Cost and access
        delegate_5 = "We've ensured broad formulary access. It's already covered by Medicare, Medicaid, and most major insurers. The copay assistance program makes it affordable - as low as $10 per month for eligible patients."
        print(f"\n[Delegate Sarah]: {delegate_5}")
        conversation.append(('delegate', delegate_5, self._analyze_speech(delegate_5, 'delegate')))
        time.sleep(1.5)
        
        doctor_5 = "Those are important considerations. I'm particularly interested in the cardiovascular outcomes data. Can you share the full trial results?"
        print(f"\n[Dr. Williams]: {doctor_5}")
        conversation.append(('doctor', doctor_5, self._analyze_speech(doctor_5, 'doctor')))
        time.sleep(1.5)
        
        # Closing and next steps
        delegate_6 = "Absolutely! I have copies of the published studies here for you. We're also hosting a CME dinner next Thursday discussing the latest advances in cardiovascular care. Dr. Anderson from Stanford will be speaking. Would you be interested?"
        print(f"\n[Delegate Sarah]: {delegate_6}")
        conversation.append(('delegate', delegate_6, self._analyze_speech(delegate_6, 'delegate')))
        time.sleep(1.5)
        
        doctor_6 = "That sounds valuable. Yes, please send me the details. And I'd like some samples to try on appropriate patients."
        print(f"\n[Dr. Williams]: {doctor_6}")
        conversation.append(('doctor', doctor_6, self._analyze_speech(doctor_6, 'doctor')))
        time.sleep(1.5)
        
        delegate_7 = "Wonderful! I'll leave you with a starter kit including samples, patient education materials, and my contact information. Thank you for your time, Doctor."
        print(f"\n[Delegate Sarah]: {delegate_7}")
        conversation.append(('delegate', delegate_7, self._analyze_speech(delegate_7, 'delegate')))
        time.sleep(1)
        
        doctor_7 = "Thank you, Sarah. I'll review the materials and be in touch."
        print(f"\n[Dr. Williams]: {doctor_7}")
        conversation.append(('doctor', doctor_7, self._analyze_speech(doctor_7, 'doctor')))
        
        print("\n[SCENE END: Successful meeting, doctor shows interest in product]")
        
        return conversation
    
    def _analyze_speech(self, text, speaker):
        """Simulate emotion analysis of speech"""
        emotions = {
            'professional': ['clinical data', 'research', 'study', 'efficacy', 'safety'],
            'positive': ['excellent', 'great', 'impressive', 'wonderful', 'valuable'],
            'curious': ['interesting', 'tell me', 'what about', 'how does'],
            'concerned': ['cost', 'safety', 'interaction', 'coverage']
        }
        
        analysis = {
            'text': text,
            'word_count': len(text.split()),
            'professional_terms': sum(1 for word in emotions['professional'] if word in text.lower()),
            'positive_sentiment': sum(1 for word in emotions['positive'] if word in text.lower()),
            'curiosity_level': sum(1 for word in emotions['curious'] if word in text.lower()),
            'concern_level': sum(1 for word in emotions['concerned'] if word in text.lower())
        }
        
        # Emotional state simulation
        if analysis['positive_sentiment'] > 0:
            analysis['emotion'] = 'engaged' if analysis['curiosity_level'] > 0 else 'positive'
        elif analysis['concern_level'] > 0:
            analysis['emotion'] = 'cautious'
        elif analysis['curiosity_level'] > 0:
            analysis['emotion'] = 'interested'
        else:
            analysis['emotion'] = 'neutral'
            
        analysis['confidence'] = random.uniform(0.7, 0.95)
        
        self.emotion_analysis[speaker].append(analysis)
        return analysis
    
    def analyze_conversation(self, conversation):
        """Analyze the entire conversation"""
        print("\n" + "="*80)
        print("CONVERSATION ANALYSIS")
        print("="*80)
        
        # Count turns
        delegate_turns = sum(1 for turn in conversation if turn[0] == 'delegate')
        doctor_turns = sum(1 for turn in conversation if turn[0] == 'doctor')
        
        print(f"\nConversation Statistics:")
        print(f"- Delegate turns: {delegate_turns}")
        print(f"- Doctor turns: {doctor_turns}")
        print(f"- Total exchanges: {len(conversation)}")
        
        # Analyze emotions
        delegate_emotions = [analysis['emotion'] for _, _, analysis in conversation if _ == 'delegate']
        doctor_emotions = [analysis['emotion'] for _, _, analysis in conversation if _ == 'doctor']
        
        print(f"\nEmotion Distribution:")
        print(f"Delegate: {self._emotion_distribution(delegate_emotions)}")
        print(f"Doctor: {self._emotion_distribution(doctor_emotions)}")
        
        # Key topics discussed
        topics = self._extract_topics(conversation)
        print(f"\nKey Topics Discussed:")
        for topic, count in topics.items():
            print(f"- {topic}: {count} mentions")
        
        # Success metrics
        success_indicators = self._evaluate_success(conversation)
        print(f"\nSuccess Metrics:")
        for metric, value in success_indicators.items():
            print(f"- {metric}: {value}")
        
        return {
            'statistics': {'delegate_turns': delegate_turns, 'doctor_turns': doctor_turns},
            'emotions': {'delegate': delegate_emotions, 'doctor': doctor_emotions},
            'topics': topics,
            'success_metrics': success_indicators
        }
    
    def _emotion_distribution(self, emotions):
        """Calculate emotion distribution"""
        from collections import Counter
        counts = Counter(emotions)
        return dict(counts)
    
    def _extract_topics(self, conversation):
        """Extract key topics from conversation"""
        topics = {
            'clinical_data': 0,
            'safety': 0,
            'efficacy': 0,
            'cost': 0,
            'insurance': 0,
            'samples': 0,
            'next_steps': 0
        }
        
        for _, text, _ in conversation:
            text_lower = text.lower()
            if 'data' in text_lower or 'trial' in text_lower:
                topics['clinical_data'] += 1
            if 'safety' in text_lower or 'interaction' in text_lower:
                topics['safety'] += 1
            if 'efficacy' in text_lower or 'outcome' in text_lower:
                topics['efficacy'] += 1
            if 'cost' in text_lower or 'price' in text_lower:
                topics['cost'] += 1
            if 'insurance' in text_lower or 'coverage' in text_lower or 'copay' in text_lower:
                topics['insurance'] += 1
            if 'sample' in text_lower:
                topics['samples'] += 1
            if 'cme' in text_lower or 'dinner' in text_lower or 'follow' in text_lower:
                topics['next_steps'] += 1
        
        return topics
    
    def _evaluate_success(self, conversation):
        """Evaluate conversation success"""
        metrics = {}
        
        # Check if doctor agreed to next steps
        next_steps_agreed = any('cme' in text.lower() or 'sample' in text.lower() 
                                for _, text, _ in conversation if _ == 'doctor')
        metrics['Next Steps Agreed'] = 'Yes' if next_steps_agreed else 'No'
        
        # Check positive sentiment
        positive_responses = sum(1 for _, text, _ in conversation 
                                if any(word in text.lower() for word in ['excellent', 'great', 'impressive']))
        metrics['Positive Responses'] = positive_responses
        
        # Check if product details were successfully communicated
        product_mentioned = sum(1 for _, text, _ in conversation 
                               if 'cardiocare' in text.lower() or 'medication' in text.lower())
        metrics['Product Mentions'] = product_mentioned
        
        # Overall success score
        success_score = 0
        if next_steps_agreed:
            success_score += 40
        if positive_responses >= 2:
            success_score += 30
        if product_mentioned >= 3:
            success_score += 30
        
        metrics['Success Score'] = f"{success_score}/100"
        
        if success_score >= 70:
            metrics['Result'] = "Excellent meeting - strong interest and next steps confirmed"
        elif success_score >= 50:
            metrics['Result'] = "Good meeting - some interest, follow-up needed"
        else:
            metrics['Result'] = "Needs improvement - more engagement required"
        
        return metrics

# ==================== SCENARIO 2: DELEGATE-AI CONVERSATION ====================

class MedicalAIAssistant:
    """AI Assistant for medical delegate support"""
    
    def __init__(self):
        self.knowledge_base = {
            'product_info': {
                'CardioCare-X': {
                    'indications': 'Treatment of hypertension and hyperlipidemia',
                    'mechanism': 'Combination ACE inhibitor and statin',
                    'clinical_data': '32% LDL reduction, 28% cardiovascular event reduction',
                    'safety': 'Minimal drug interactions, similar to placebo side effects',
                    'cost': '$10 copay with assistance program'
                }
            },
            'clinical_guidelines': {
                'hypertension': 'ACC/AHA guidelines recommend combination therapy for stage 2 hypertension',
                'hyperlipidemia': 'ESC/EAS guidelines emphasize LDL reduction goals'
            },
            'reimbursement': {
                'medicare': 'Covered under Part D',
                'medicaid': 'Covered in all 50 states',
                'commercial': 'Tier 2 preferred formulary status'
            }
        }
        
        self.conversation_context = {}
        self.sentiment_scores = []
        
    def process_query(self, delegate_query, context=None):
        """Process delegate query and return AI response"""
        
        print(f"\n[Delegate]: {delegate_query}")
        
        # Analyze query intent
        intent = self._analyze_intent(delegate_query)
        
        # Generate response based on intent
        response = self._generate_response(delegate_query, intent)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(delegate_query)
        self.sentiment_scores.append(sentiment)
        
        print(f"[AI Assistant]: {response}")
        
        return {
            'query': delegate_query,
            'response': response,
            'intent': intent,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_intent(self, query):
        """Analyze the intent of the query"""
        query_lower = query.lower()
        
        intents = {
            'product_info': ['what is', 'tell me about', 'explain', 'product', 'medication'],
            'clinical_data': ['data', 'trial', 'study', 'efficacy', 'outcome', 'results'],
            'safety': ['safety', 'side effect', 'interaction', 'adverse', 'risk'],
            'reimbursement': ['cost', 'price', 'insurance', 'coverage', 'copay', 'medicare'],
            'dosing': ['dose', 'dosage', 'administration', 'take', 'frequency'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'better'],
            'objection_handling': ['but', 'however', 'concern', 'worried']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def _generate_response(self, query, intent):
        """Generate AI response based on intent"""
        
        responses = {
            'product_info': "CardioCare-X is a once-daily combination therapy containing an ACE inhibitor and a statin. It's indicated for patients with both hypertension and hyperlipidemia, offering convenient dual therapy in a single pill.",
            
            'clinical_data': "The Phase III CARDIO-3 trial demonstrated superior efficacy: 32% greater LDL reduction compared to standard therapy, 28% reduction in MACE (major adverse cardiovascular events), and excellent safety profile with discontinuation rates similar to placebo.",
            
            'safety': "CardioCare-X has a favorable safety profile. Key advantages include minimal CYP450 interactions, making it safe with most common medications. The most common side effects (cough, muscle pain) occur in <5% of patients, similar to placebo rates.",
            
            'reimbursement': "The product has broad formulary access. It's covered by Medicare Part D, Medicaid in all states, and major commercial insurers with Tier 2 preferred status. The copay assistance program reduces patient out-of-pocket to as low as $10/month.",
            
            'dosing': "Standard dosing is one tablet once daily, with or without food. Starting dose is 10/20mg, titrated based on response. No dose adjustment needed for renal or hepatic impairment. The fixed-dose combination improves adherence.",
            
            'comparison': "Compared to other combination therapies, CardioCare-X offers unique advantages: once-daily dosing, proven cardiovascular outcomes data, minimal drug interactions, and broader formulary access. The 28% MACE reduction is among the best in class.",
            
            'objection_handling': "I understand your concern. Let me address that: The safety data from over 5,000 patients shows excellent tolerability. The combination approach actually improves adherence and outcomes. Would you like to review specific data points?",
            
            'general': "I'm here to help with any questions about CardioCare-X. I can provide information on clinical data, safety, dosing, reimbursement, or comparative effectiveness. What specific information would be most helpful?"
        }
        
        return responses.get(intent, responses['general'])
    
    def _analyze_sentiment(self, text):
        """Analyze sentiment of delegate query"""
        positive_words = ['excellent', 'great', 'good', 'impressive', 'effective', 'benefit']
        negative_words = ['concern', 'worried', 'problem', 'issue', 'cost', 'expensive', 'risk']
        
        text_lower = text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            sentiment = 'positive'
            confidence = min(0.7 + positive_score * 0.1, 0.95)
        elif negative_score > positive_score:
            sentiment = 'negative'
            confidence = min(0.7 + negative_score * 0.1, 0.95)
        else:
            sentiment = 'neutral'
            confidence = 0.7
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_score': positive_score,
            'negative_score': negative_score
        }
    
    def simulate_conversation(self):
        """Simulate a complete delegate-AI conversation"""
        
        print("\n" + "="*80)
        print("SCENARIO 2: DELEGATE-AI ASSISTANT CONVERSATION")
        print("Context: Medical Delegate preparing for doctor meetings")
        print("="*80)
        
        conversation_history = []
        
        # Delegate questions to AI
        queries = [
            "What is CardioCare-X and what are its indications?",
            "What clinical data supports its use? Show me the trial results.",
            "What about safety and drug interactions?",
            "How much will it cost patients? Will insurance cover it?",
            "How does it compare to other combination therapies?",
            "I'm concerned about patient adherence with a new medication.",
            "What's the dosing and administration?",
            "Can you summarize the key selling points for doctors?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n--- Exchange {i} ---")
            result = self.process_query(query)
            conversation_history.append(result)
            time.sleep(1)
        
        # Add challenging questions
        print("\n--- Challenging Questions ---")
        challenging_queries = [
            "But doctors might be concerned about switching patients from their current therapy.",
            "What if a patient has multiple comorbidities and is on many medications?",
            "Is there any long-term safety data beyond 1 year?",
            "How do you handle formulary restrictions?"
        ]
        
        for query in challenging_queries:
            print(f"\n[Delegate]: {query}")
            result = self.process_query(query)
            conversation_history.append(result)
            time.sleep(1)
        
        return conversation_history
    
    def analyze_ai_conversation(self, conversation_history):
        """Analyze the AI conversation"""
        
        print("\n" + "="*80)
        print("AI CONVERSATION ANALYSIS")
        print("="*80)
        
        # Analyze intents
        intents = [conv['intent'] for conv in conversation_history]
        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        print(f"\nQuery Intents Distribution:")
        for intent, count in intent_counts.items():
            print(f"- {intent}: {count} queries")
        
        # Analyze sentiment trends
        sentiments = [conv['sentiment']['sentiment'] for conv in conversation_history]
        sentiment_counts = {
            'positive': sentiments.count('positive'),
            'neutral': sentiments.count('neutral'),
            'negative': sentiments.count('negative')
        }
        
        print(f"\nSentiment Analysis:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(sentiments)) * 100
            print(f"- {sentiment}: {count} ({percentage:.1f}%)")
        
        # Confidence scores
        avg_confidence = sum(conv['sentiment']['confidence'] for conv in conversation_history) / len(conversation_history)
        print(f"\nAverage Sentiment Confidence: {avg_confidence:.2%}")
        
        # Key topics covered
        topics_covered = set(intents)
        print(f"\nTopics Covered: {', '.join(topics_covered)}")
        
        # AI performance metrics
        response_times = [0.5 for _ in conversation_history]  # Simulated
        print(f"\nAI Performance:")
        print(f"- Total queries handled: {len(conversation_history)}")
        print(f"- Average response time: {sum(response_times)/len(response_times):.1f} seconds")
        print(f"- Unique intents identified: {len(intent_counts)}")
        
        # Delegate engagement score
        engagement_score = (sentiment_counts['positive'] * 1.0 + 
                          sentiment_counts['neutral'] * 0.5) / len(conversation_history)
        print(f"- Delegate Engagement Score: {engagement_score:.2%}")
        
        # Recommendations
        print(f"\nRecommendations for Delegate:")
        if sentiment_counts['negative'] > 2:
            print("- Address safety and cost concerns proactively in doctor meetings")
        if 'objection_handling' in intents:
            print("- Prepare objection handling scripts for common concerns")
        if 'comparison' in intents:
            print("- Develop competitive comparison materials for reference")
        if sentiment_counts['positive'] > 5:
            print("- Delegate shows strong product understanding, focus on advanced clinical data")
        
        return {
            'intents': intent_counts,
            'sentiments': sentiment_counts,
            'avg_confidence': avg_confidence,
            'engagement_score': engagement_score,
            'topics_covered': topics_covered
        }

# ==================== SCENARIO 3: INTEGRATED ROLE-PLAY ====================

class IntegratedMedicalRolePlay:
    """Combined scenario with both conversations"""
    
    def __init__(self):
        self.medical_scenario = MedicalCommercialScenario()
        self.ai_assistant = MedicalAIAssistant()
        
    def run_complete_scenario(self):
        """Run complete integrated scenario"""
        
        print("\n" + "🎭"*40)
        print("COMPLETE MEDICAL COMMERCIAL SCENARIO")
        print("Delegate prepares with AI → Meets with Doctor → Analyzes results")
        print("🎭"*40)
        
        # Phase 1: Delegate prepares with AI
        print("\n" + "📋 PHASE 1: DELEGATE PREPARATION WITH AI ASSISTANT")
        print("-"*60)
        
        ai_conversation = self.ai_assistant.simulate_conversation()
        ai_analysis = self.ai_assistant.analyze_ai_conversation(ai_conversation)
        
        input("\nPress Enter to continue to doctor meeting...")
        
        # Phase 2: Delegate meets with doctor
        print("\n" + "👨‍⚕️ PHASE 2: DELEGATE-DOCTOR MEETING")
        print("-"*60)
        
        doctor_conversation = self.medical_scenario.delegate_doctor_conversation()
        doctor_analysis = self.medical_scenario.analyze_conversation(doctor_conversation)
        
        # Phase 3: Combined analysis
        print("\n" + "📊 PHASE 3: INTEGRATED ANALYSIS")
        print("-"*60)
        
        self.generate_integrated_report(ai_analysis, doctor_analysis)
        
        # Phase 4: Recommendations
        print("\n" + "💡 PHASE 4: ACTIONABLE RECOMMENDATIONS")
        print("-"*60)
        
        self.generate_recommendations(ai_analysis, doctor_analysis, doctor_conversation)
    
    def generate_integrated_report(self, ai_analysis, doctor_analysis):
        """Generate integrated analysis report"""
        
        print("\nINTEGRATED ANALYSIS REPORT")
        print("="*60)
        
        print("\nAI Assistant Performance:")
        print(f"- Prepared delegate on {len(ai_analysis['intents'])} key topics")
        print(f"- Delegate engagement score: {ai_analysis['engagement_score']:.1%}")
        
        print("\nDoctor Meeting Outcomes:")
        print(f"- Success score: {doctor_analysis['success_metrics']['Success Score']}")
        print(f"- Key outcome: {doctor_analysis['success_metrics']['Result']}")
        
        # Correlation analysis
        print("\nCorrelation Analysis:")
        topics_covered = set(ai_analysis['topics_covered'])
        doctor_topics = set(doctor_analysis['topics'].keys())
        
        relevant_topics = topics_covered.intersection(doctor_topics)
        print(f"- Topics discussed both in AI prep and doctor meeting: {len(relevant_topics)}")
        
        if doctor_analysis['success_metrics']['Positive Responses'] >= 2:
            print("- Positive correlation: AI preparation led to successful meeting")
        else:
            print("- Opportunity: Additional preparation needed on key topics")
    
    def generate_recommendations(self, ai_analysis, doctor_analysis, conversation):
        """Generate actionable recommendations"""
        
        print("\nKEY RECOMMENDATIONS:")
        print("-"*60)
        
        # Topic-based recommendations
        doctor_topics = doctor_analysis['topics']
        
        if doctor_topics.get('cost', 0) > 0 and doctor_topics.get('safety', 0) > 0:
            print("✓ Develop cost-benefit analysis materials combining safety and economics")
        
        if doctor_topics.get('clinical_data', 0) >= 2:
            print("✓ Create detailed clinical data summary for future reference")
        
        if doctor_topics.get('next_steps', 0) > 0:
            print("✓ Schedule follow-up meeting to discuss samples and patient cases")
        
        # Sentiment-based recommendations
        doctor_emotions = doctor_analysis['emotions']['doctor']
        
        if 'cautious' in doctor_emotions:
            print("✓ Address remaining concerns with additional safety data")
        
        if 'engaged' in doctor_emotions:
            print("✓ Leverage positive engagement to request patient case studies")
        
        # AI training recommendations
        if ai_analysis['engagement_score'] < 0.7:
            print("✓ Additional AI training recommended for challenging queries")
        
        print("\nNEXT STEPS:")
        print("1. Send follow-up email with requested clinical data")
        print("2. Schedule CME dinner attendance confirmation")
        print("3. Provide starter kit with samples and materials")
        print("4. Set reminder for 2-week follow-up call")

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    print("\n" + "🏥"*40)
    print("MEDICAL COMMERCIAL SCENARIO SIMULATOR")
    print("Delegate-Doctor & Delegate-AI Interactions")
    print("🏥"*40)
    
    while True:
        print("\n" + "="*50)
        print("SELECT SCENARIO:")
        print("="*50)
        print("1. Delegate-Doctor Conversation (Medical Commercial)")
        print("2. Delegate-AI Assistant Conversation (Training Mode)")
        print("3. Integrated Complete Scenario (AI Prep + Doctor Meeting)")
        print("4. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            scenario = MedicalCommercialScenario()
            conversation = scenario.delegate_doctor_conversation()
            scenario.analyze_conversation(conversation)
            
        elif choice == '2':
            ai = MedicalAIAssistant()
            conversation = ai.simulate_conversation()
            ai.analyze_ai_conversation(conversation)
            
        elif choice == '3':
            role_play = IntegratedMedicalRolePlay()
            role_play.run_complete_scenario()
            
        elif choice == '4':
            print("\nExiting scenario simulator...")
            break
            
        else:
            print("\nInvalid choice. Please select 1-4.")
        
        print("\n" + "-"*60)
        input("Press Enter to return to menu...")

# ==================== SUPPLEMENTARY FUNCTIONS ====================

def generate_conversation_transcript(conversation):
    """Generate formatted transcript of conversation"""
    
    transcript = []
    transcript.append("\n" + "="*80)
    transcript.append("CONVERSATION TRANSCRIPT")
    transcript.append("="*80)
    
    for speaker, text, analysis in conversation:
        timestamp = datetime.now().strftime("%H:%M:%S")
        transcript.append(f"\n[{timestamp}] {speaker.upper()}:")
        transcript.append(f"{text}")
        transcript.append(f"[Emotion: {analysis['emotion']} | Confidence: {analysis['confidence']:.2%}]")
    
    transcript.append("\n" + "="*80)
    
    return "\n".join(transcript)

def save_scenario_to_file(scenario_type, conversation, analysis):
    """Save scenario to file"""
    
    filename = f"{scenario_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"SCENARIO TYPE: {scenario_type}\n")
        f.write(f"DATE: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        
        f.write("CONVERSATION LOG:\n")
        f.write("-"*80 + "\n")
        
        for speaker, text, analysis in conversation:
            f.write(f"\n{speaker.upper()}:\n")
            f.write(f"{text}\n")
            f.write(f"Analysis: {analysis}\n")
        
        f.write("\n\nANALYSIS:\n")
        f.write("-"*80 + "\n")
        f.write(json.dumps(analysis, indent=2))
    
    print(f"\nScenario saved to: {filename}")

if __name__ == "__main__":
    main()
