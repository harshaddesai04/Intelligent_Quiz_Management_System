from django.urls import path
from . import views
from .views import dashboard_view
from .views import GenerateQuizView, get_subcategories, submit_quiz_view

urlpatterns = [
    # Authentication URLs
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard & Profile URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Chatbot URL
    path("chatbot-response/", views.chatbot_response, name="chatbot_response"),
    
    # Quiz URLs
    path('quiz/selection/', views.quiz_selection_view, name='quiz_selection'),
    path('api/get-subcategories/<int:category_id>/', get_subcategories, name='get_subcategories'),
    path('get-next-question/<int:quiz_history_id>/', views.get_next_question, name='get_next_question'),
    path('api/generate-quiz/', GenerateQuizView.as_view(), name='generate_quiz'),
    path('quiz/take/<int:quiz_id>/', views.take_quiz_view, name='take_quiz'),
    path('api/submit-quiz/', submit_quiz_view, name='submit_quiz'),
    path('quiz/results/<int:quiz_history_id>/', views.quiz_results_view, name='quiz_results'),
    path('quiz/history/', views.quiz_history_view, name='quiz_history'),
]
