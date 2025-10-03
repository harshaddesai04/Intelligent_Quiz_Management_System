from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Category, SubCategory, Quiz, Question, QuizHistory, UserAnswer, AIGenerationLog, Profile, CustomUser

# Remove this line - it's causing the duplicate registration
# admin.site.register(Profile)

# Register your custom user with UserAdmin
admin.site.register(CustomUser, UserAdmin)

# Register your models here
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subcategory', 'difficulty', 'is_ai_generated', 'created_at']
    list_filter = ['category', 'difficulty', 'is_ai_generated']
    search_fields = ['title']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'difficulty', 'correct_answer', 'is_ai_generated']
    list_filter = ['difficulty', 'is_ai_generated']
    search_fields = ['text']

@admin.register(QuizHistory)
class QuizHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'correct_answers', 'total_questions', 'created_at']
    list_filter = ['quiz', 'selected_difficulty']
    search_fields = ['user__username']

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['history', 'question', 'selected_option', 'is_correct']
    list_filter = ['is_correct']

@admin.register(AIGenerationLog)
class AIGenerationLogAdmin(admin.ModelAdmin):
    list_display = ['category', 'subcategory', 'difficulty', 'questions_generated', 'created_at']
    list_filter = ['difficulty']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name']
    search_fields = ['user__username']

