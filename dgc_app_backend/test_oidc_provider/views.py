from django.shortcuts import render

# Create your views here.
def mtest_view(request):
    return render(request, 'test_oidc_provider/test.html', {})