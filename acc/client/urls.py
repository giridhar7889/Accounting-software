from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('save-edits/', views.save_edits, name='save_edits'),  # Endpoint for saving edits
    path('review-account/', views.review_account, name='review_account'),  # New endpoint for account info
    path('update_account/', views.update_account, name='update_account'),
    path('download/', views.download_page, name='download_page'),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('download_excel/', views.download_excel, name='download_excel'),

]
