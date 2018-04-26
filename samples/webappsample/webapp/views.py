from django.shortcuts import render
from django.http import HttpResponse
import configcatclient


# Create your views here.
def index(request):
    key_sample_text = configcatclient.get().get_value('keySampleText', 'default value')
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(key_sample_text))