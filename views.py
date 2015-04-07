# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.core.mail import send_mail, EmailMessage

def index(request):
	obj = dict()
	if (request.method == "POST"):
		email = request.POST["email"]
		try:
			send = send_mail("Testing", "Hello! It's testing letter for all.", 'sigorilla@gmail.com', [email])
		except Exception, e:
			send = False
		obj = {
			'email': send
		}
	return render(request, "mipt_hack_server/index.html", obj)
