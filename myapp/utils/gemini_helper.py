import google.generativeai as genai
from django.conf import settings
from myapp.models import AIGenerationLog, Category, SubCategory
import re
import time

class GeminiQuizGenerator:
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-2.5-pro')
    
    def generate_quiz_questions(self, category, subcategory, difficulty, num_questions=10, user=None):
        """
        Generate quiz questions using Gemini AI with fallback to dummy data
        """
        prompt = self._build_prompt(category, subcategory, difficulty, num_questions)
        
        try:
            # Try to use Gemini API with timeout
            response = self.model.generate_content(prompt)
            print("=== GEMINI RESPONSE ===")
            print(response.text)
            print("======================")
            
            questions = self._parse_response(response.text, num_questions)
            
            if questions:
                self._log_generation(category, subcategory, difficulty, num_questions, user, prompt)
                return questions
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            # Fallback to dummy data
            return self._generate_fallback_questions(num_questions, category, subcategory, difficulty)
        
        # If Gemini returns no questions, use fallback
        return self._generate_fallback_questions(num_questions, category, subcategory, difficulty)
    
    def _generate_fallback_questions(self, num_questions, category, subcategory, difficulty):
        """Generate fallback questions when Gemini fails"""
        questions = []
        for i in range(num_questions):
            questions.append({
                'text': f'{difficulty} question {i+1} about {subcategory}: What is the main topic?',
                'option1': 'Primary subject matter',  # Changed to match model fields
                'option2': 'Secondary topic', 
                'option3': 'Related concept',
                'option4': 'Unrelated theme',
                'correct_answer': 'A'  # This should be the letter A, B, C, or D
            })
        return questions
    
    def _build_prompt(self, category, subcategory, difficulty, num_questions):
        """Build the prompt for Gemini AI"""
        return f"""
Generate exactly {num_questions} multiple-choice quiz questions about {subcategory} under {category} category. Difficulty: {difficulty}.
FORMAT REQUIREMENTS:
- Each question must follow this EXACT format:
Question: [question text here]
A) [option A text]
B) [option B text]
C) [option C text]
D) [option D text]
Correct: [letter A-D]
- Questions should be diverse and appropriate for {difficulty} level
- Each question must have exactly 4 options
- The correct answer must be one of A, B, C, or D
- Do not include any additional text, explanations, or numbering
- Make sure each option is a complete, meaningful answer
"""
    
    def _parse_response(self, response_text, num_questions):
        """Parse Gemini response into structured questions"""
        questions = []
        lines = response_text.strip().split('\n')
        current_question = {}
        
        print("=== PARSING RESPONSE ===")
        for i, line in enumerate(lines):
            print(f"Line {i}: {line}")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Question:'):
                # Save the previous question if it exists and has all required fields
                if current_question and 'text' in current_question and 'correct_answer' in current_question:
                    # Check if all options are present
                    if all(key in current_question for key in ['option1', 'option2', 'option3', 'option4']):
                        questions.append(current_question)
                
                # Start a new question
                current_question = {
                    'text': line.replace('Question:', '').strip(),
                    'option1': '',
                    'option2': '',
                    'option3': '',
                    'option4': '',
                    'correct_answer': ''
                }
            elif line.startswith('A)'):
                current_question['option1'] = line.replace('A)', '').strip()
            elif line.startswith('B)'):
                current_question['option2'] = line.replace('B)', '').strip()
            elif line.startswith('C)'):
                current_question['option3'] = line.replace('C)', '').strip()
            elif line.startswith('D)'):
                current_question['option4'] = line.replace('D)', '').strip()
            elif line.startswith('Correct:'):
                correct_answer = line.replace('Correct:', '').strip()
                if correct_answer in ['A', 'B', 'C', 'D']:
                    current_question['correct_answer'] = correct_answer
        
        # Add the last question if it has all required fields
        if current_question and 'text' in current_question and 'correct_answer' in current_question:
            # Check if all options are present
            if all(key in current_question for key in ['option1', 'option2', 'option3', 'option4']):
                questions.append(current_question)
        
        print(f"=== PARSED {len(questions)} QUESTIONS ===")
        for i, q in enumerate(questions):
            print(f"Question {i+1}: {q['text']}")
            print(f"  A: {q['option1']}")
            print(f"  B: {q['option2']}")
            print(f"  C: {q['option3']}")
            print(f"  D: {q['option4']}")
            print(f"  Correct: {q['correct_answer']}")
        print("==============================")
        
        return questions[:num_questions]
    
    def _log_generation(self, category, subcategory, difficulty, num_questions, user, prompt):
        """Log AI generation activity"""
        try:
            cat_obj = Category.objects.filter(name=category).first()
            subcat_obj = SubCategory.objects.filter(name=subcategory, category=cat_obj).first() if cat_obj else None
            
            AIGenerationLog.objects.create(
                category=cat_obj,
                subcategory=subcat_obj,
                difficulty=difficulty,
                questions_generated=num_questions,
                generated_by=user,
                prompt_used=prompt
            )
        except Exception as e:
            print(f"Error logging generation: {e}")


    def generate_chat_response(self, user_message, user=None):
        """
        Generate a chatbot response using Gemini AI.
        Fallbacks to a default message if Gemini fails.
        """
        try:
            prompt = f"You are a helpful quiz assistant. The user says: {user_message}"

            # Call Gemini API
            response = self.model.generate_content(prompt)

            # Extract plain text
            reply_text = response.text if response and hasattr(response, "text") else None

            return reply_text or "🤖 Sorry, I couldn’t generate a response."
        
        except Exception as e:
            print(f"Gemini chat error: {e}")
            return "⚠️ Oops, something went wrong while generating a response."

# Singleton instance
gemini_generator = GeminiQuizGenerator()