from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
from PIL import Image
import base64
import io
import time
import json

# Configuration for AI model
api_key = "AIzaSyAGWE9NYRKn-TReMckj_-dkneVzvhJPuFE"

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
]

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  safety_settings=safety_settings,
  generation_config=generation_config,
)

@csrf_exempt
def analyze_and_process_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        print("분석이 시작 됐습니다. 이미지는", image)    
        if not image:
            return JsonResponse({'error': 'No image provided'}, status=400)

        try:
            image = Image.open(image)
            prompt_parts = construct_prompt(image)
        except Exception as e:
            print(f"Error processing image: {e}")
            return JsonResponse({'error': '이미지 처리에 실패하였습니다.'}, status=500)

        try:
            start_time = time.time()  # Start timing before the model call
            response = model.generate_content(prompt_parts)
            print(response.text)
            end_time = time.time()  # End timing after receiving the response
            print(f"gemini에서 응답 받는데 {end_time - start_time:.2f} seconds 걸렸음")

            response_text = response.text.strip()
            # response_text를 JSON 객체로 변환
            response_data = json.loads(response_text)
            return JsonResponse(response_data)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return JsonResponse({'error': 'Invalid JSON response from model'}, status=500)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'error': 'An error occurred during image analysis'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def construct_prompt(image):
    # 메모리 내의 바이트 스트림 객체 생성
    buffered = io.BytesIO()
    
    try:
        # 이미지를 JPEG 포맷으로 버퍼에 저장
        image.save(buffered, format="JPEG")
    except Exception as e:
        print(f"Error saving image to buffer: {e}")
        raise

    # 버퍼의 내용을 Base64로 인코딩
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 프롬프트 생성
    task_details = (
        "Let's think step by step. Use of Chain of Thought. 엄격하고 까다롭게 채식주의 음식을 판별하라. 한국음식에는 멸치 육수, 젓갈이 많이 사용된다는 사실을 참고해서 채식 음식을 판별하라. "
        "ROLE: 너는 채식 음식 판별가야; "
        "YOUR TASK IS: "
        "1. 이 음식이 무엇인지 추론하라. 이 음식은 한국 음식일 확률이 높다. ONLY 고유 한국음식명만 한 단어로 출력하라. ex) 된장찌개, 잡채, 김치, 송편 등등. Write in English"
        "2. 사진의 음식이 비건 푸드일 확률을 100점 만점으로 나타내라. 예를 들면 채소면 매우 높을 확률, 스테이크면 매우 낮을 확률이다., ONLY NUMERIC VALUES ARE ACCEPTED. Write in English"
        "3. 왜 그렇게 생각하는지 이유를 구체적으로 설명하라. Write in English"
        "4. 이 사진에 대한 비건 관련 질문을 생성하라. ex) 이 요리에 고기, 생선, 유제품, 계란 같은 동물성 재료가 들어가나요?. Write in Korean"
        "Ensure that your answer is unbiased, detailed and avoids relying on stereotypes. Demonstrate deep expertise in food safety."
    )
    response_format = ( 
      "1. dishName: <phrase>"
      "2. veganPossibility: <number>"
      "3. reasoning: <phrase>"
      "4. question: <phrase>"
    )
    full_prompt = f"{task_details}\n{response_format}\n\nBase64 Image: {image_base64}"
    return full_prompt

# Create your views here.
def render_vege_camera(request):
    return render(request, 'camera.html')
