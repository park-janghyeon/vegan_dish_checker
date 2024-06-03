from django.urls import path
from .views import render_vege_camera, analyze_and_process_image

urlpatterns = [
    path('', render_vege_camera, name='render_vege_camera'),
    path('analyze-image/', analyze_and_process_image, name='analyze_image'),
]
