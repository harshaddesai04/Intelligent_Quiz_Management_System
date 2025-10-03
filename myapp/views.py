from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.http import JsonResponse
import json
from .forms import CustomUserCreationForm, ProfileForm
from .models import Profile, Category, SubCategory, Quiz, Question, QuizHistory, UserAnswer
from myapp.utils.gemini_helper import gemini_generator

# ---------------- Landing Page ----------------
def landing_view(request):
    return render(request, 'landing.html')

# ---------------- Register ----------------
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            authenticated_user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"]
            )
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, "Registration successful!")
                return redirect("home")
            else:
                messages.error(request, "Authentication failed. Please login.")
                return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "register.html", {"form": form})

# ---------------- Login ----------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ---------------- Logout ----------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

# ---------------- Dashboard ----------------
@login_required
def dashboard_view(request):
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'categories': categories})

# ---------------- Profile ----------------
@login_required
def profile_view(request):
    profile = request.user.profile
    avatar_url = profile.avatar.url if profile.avatar else '/static/default-avatar.jpeg'
    return render(request, 'profile.html', {'profile': profile, 'avatar_url': avatar_url})

# ---------------- Edit Profile ----------------
@login_required
def edit_profile(request):
    profile = request.user.profile
    avatar_url = profile.avatar.url if profile.avatar else '/static/default-avatar.jpeg'
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile_obj = form.save(commit=False)
            username = request.POST.get('username')
            if username and username != request.user.username:
                request.user.username = username
                request.user.save()
            profile_obj.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'edit_profile.html', {'form': form, 'avatar_url': avatar_url})

# ---------------- Quiz Selection ----------------
@login_required
def quiz_selection_view(request):
    categories = Category.objects.prefetch_related('subcategories').all()
    return render(request, 'quiz_selection.html', {'categories': categories})

# ---------------- Get Subcategories ----------------
@login_required
def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

# ---------------- Generate Quiz ----------------
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GenerateQuizView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            subcategory_id = data.get('subcategory_id')
            difficulty = data.get('difficulty', 'M')
            num_questions = data.get('num_questions', 10)
            
            category = get_object_or_404(Category, id=category_id)
            subcategory = get_object_or_404(SubCategory, id=subcategory_id)
            
            questions_data = gemini_generator.generate_quiz_questions(
                category.name,
                subcategory.name,
                difficulty,
                num_questions,
                request.user
            )
            
            if not questions_data:
                return JsonResponse({'error': 'Failed to generate questions'}, status=500)
            
            quiz = Quiz.objects.create(
                title=f"AI Generated Quiz - {subcategory.name}",
                description=f"Automatically generated quiz about {subcategory.name}",
                category=category,
                subcategory=subcategory,
                difficulty=difficulty,
                is_ai_generated=True
            )
            
            print(f"=== SAVING {len(questions_data)} QUESTIONS TO DATABASE ===")
            for i, q_data in enumerate(questions_data):
                print(f"Processing question {i+1}:")
                print(f"  Text: {q_data['text']}")
                print(f"  Option1: '{q_data.get('option1', '')}'")
                print(f"  Option2: '{q_data.get('option2', '')}'")
                print(f"  Option3: '{q_data.get('option3', '')}'")
                print(f"  Option4: '{q_data.get('option4', '')}'")
                print(f"  Correct Answer: '{q_data.get('correct_answer', '')}'")
                
                # Check if any option is empty
                if not all([q_data.get('option1'), q_data.get('option2'), q_data.get('option3'), q_data.get('option4')]):
                    print(f"  WARNING: Some options are empty for question {i+1}")
                
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data['text'],
                    option1=q_data.get('option1', ''),
                    option2=q_data.get('option2', ''),
                    option3=q_data.get('option3', ''),
                    option4=q_data.get('option4', ''),
                    correct_answer=q_data.get('correct_answer', ''),
                    difficulty=difficulty,
                    is_ai_generated=True
                )
                
                print(f"  Saved with ID {question.id}")
                print(f"  Database values after save:")
                print(f"    Option1: '{question.option1}'")
                print(f"    Option2: '{question.option2}'")
                print(f"    Option3: '{question.option3}'")
                print(f"    Option4: '{question.option4}'")
                print(f"    Correct Answer: '{question.correct_answer}'")
                print("-----")
            
            return JsonResponse({
                'success': True,
                'quiz_id': quiz.id,
                'message': f'Generated {len(questions_data)} questions'
            })
            
        except Exception as e:
            print(f"ERROR in GenerateQuizView: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

# ---------------- Get Next Question ----------------
@login_required
def get_next_question(request, quiz_history_id):
    quiz_history = get_object_or_404(QuizHistory, id=quiz_history_id, user=request.user)
    answered_ids = quiz_history.user_answers.values_list('question_id', flat=True)
    next_question = quiz_history.quiz.questions.exclude(id__in=answered_ids).first()
    
    if not next_question:
        return JsonResponse({'completed': True})
    
    question_data = {
        'id': next_question.id,
        'text': next_question.text,
        'options': {
            'A': next_question.option1,
            'B': next_question.option2,
            'C': next_question.option3,
            'D': next_question.option4
        }
    }
    
    return JsonResponse(question_data)


# ---------------- Take Quiz ----------------
@login_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions_queryset = quiz.questions.all()  # Fetch questions
    
    # DEBUG: Print to terminal
    print(f"=== LOADING QUIZ {quiz_id} ===")
    print(f"Number of questions: {questions_queryset.count()}")
    
    if not questions_queryset.exists():
        messages.error(request, "This quiz has no questions.")
        return redirect('quiz_selection')
    
    quiz_history = QuizHistory.objects.create(
        user=request.user,
        quiz=quiz,
        total_questions=questions_queryset.count(),
        selected_difficulty=quiz.difficulty,
        started_at=timezone.now()
    )
    
    # Convert queryset to list to ensure it's evaluated
    questions_list = list(questions_queryset)
    
    # Print the options for each question
    for q in questions_list:
        print(f"Question from DB - ID: {q.id}")
        print(f"  Text: {q.text}")
        print(f"  Option1: '{q.option1}'")
        print(f"  Option2: '{q.option2}'")
        print(f"  Option3: '{q.option3}'")
        print(f"  Option4: '{q.option4}'")
        print(f"  Correct Answer: '{q.correct_answer}'")
        print("-----")
    
    print(f"=== PREPARED {len(questions_list)} QUESTIONS FOR TEMPLATE ===")
    print(f"Number of questions: {questions_queryset.count()}")
    return render(request, 'take_quiz.html', {
        'quiz': quiz,
        'quiz_history_id': quiz_history.id,
        'time_limit': quiz.time_limit_minutes * 60,
        'questions': questions_list  # Pass the list directly
    })
   

# ---------------- Submit Quiz ----------------
@csrf_exempt
@login_required
def submit_quiz_view(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = {
                    'quiz_history_id': request.POST.get('quiz_history_id'),
                    'answers': request.POST.get('answers'),
                    'time_taken': request.POST.get('time_taken')
                }

            answers = data.get('answers', {})
            if isinstance(answers, str):
                answers = json.loads(answers)

            quiz_history_id = data.get('quiz_history_id')
            time_taken = data.get('time_taken', 0)

            quiz_history = get_object_or_404(QuizHistory, id=quiz_history_id, user=request.user)
            correct_answers = 0

            for question_id, answer_data in answers.items():
                question = get_object_or_404(Question, id=question_id)
                selected_option = answer_data.get('selected_option')
                is_correct = selected_option == question.correct_answer
                if is_correct:
                    correct_answers += 1
                UserAnswer.objects.create(
                    history=quiz_history,
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct,
                    time_taken=answer_data.get('time_taken', 0)
                )

            quiz_history.correct_answers = correct_answers
            quiz_history.score = (correct_answers / quiz_history.total_questions) * 100 if quiz_history.total_questions > 0 else 0
            quiz_history.completed_at = timezone.now()
            quiz_history.save()

            # ✅ Instead of returning JSON, redirect to results page
            return redirect('quiz_results', quiz_history_id=quiz_history.id)

        except Exception as e:
            print("Error in submit_quiz_view:", e)
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
# ---------------- Quiz Results ----------------
@login_required
def quiz_results_view(request, quiz_history_id):
    quiz_history = get_object_or_404(QuizHistory, id=quiz_history_id, user=request.user)
    user_answers = quiz_history.user_answers.select_related('question')
    
    return render(request, 'quiz_results.html', {
        'quiz_history': quiz_history,
        'user_answers': user_answers
    })

# ---------------- Quiz History ----------------
@login_required
def quiz_history_view(request):
    quiz_histories = QuizHistory.objects.filter(user=request.user).select_related('quiz').order_by('-created_at')
    return render(request, 'quiz_history.html', {'quiz_histories': quiz_histories})

# ---------------- Home ----------------
@login_required
def home_view(request):
    return render(request, 'home.html')

# ---------------- Chatbot API ----------------
@csrf_exempt
@login_required
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"reply": "⚠️ Please type something."})

            # Use gemini_generator (your helper) to get a response
            bot_reply = gemini_generator.generate_chat_response(user_message, request.user)

            # Fallback if bot gives empty
            if not bot_reply:
                bot_reply = "🤖 Sorry, I couldn’t generate a response right now."

            return JsonResponse({"reply": bot_reply})

        except Exception as e:
            print("Chatbot error:", e)
            return JsonResponse({"reply": "⚠️ Something went wrong on the server."}, status=500)

    return JsonResponse({"reply": "Invalid request method."}, status=405)
