# frontend/main.py

from django.shortcuts import render
from django.http import HttpResponse, FileResponse
import requests
import io

FASTAPI_URL = "http://localhost:8001/redact"  # Update with your FastAPI endpoint

def home(request):
    return render(request, "home.html")

def upload_file(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist("documents")
        files = [("documents", (f.name, f.read(), f.content_type)) for f in uploaded_files]
        response = requests.post(FASTAPI_URL, files=files)
        if response.status_code == 200:
            # Stream the redacted zip file to user
            redacted_file = response.content
            return FileResponse(io.BytesIO(redacted_file), as_attachment=True, filename="redacted.zip")
        else:
            return HttpResponse("Redaction failed.", status=500)
    return render(request, "upload.html")

# In your urls.py, add:
# from . import views
# urlpatterns = [
#     path('', views.home, name='home'),
#     path('upload/', views.upload_file, name='upload_file'),
# ]

# Example templates (to be placed in your templates directory):
# home.html:
# <h1>Welcome to DocSanct Redaction System</h1>
# <a href="/upload/">Upload Documents</a>

# upload.html:
# <h2>Upload Documents for Redaction</h2>
# <form method="post" enctype="multipart/form-data">
#   {% csrf_token %}
#   <input type="file" name="documents" multiple required><br><br>
#   <button type="submit">Redact & Download</button>
# </form>