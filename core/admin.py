from django.contrib import admin
from .models import User, Place, Queue, Ticket

admin.site.register(User)
admin.site.register(Place)
admin.site.register(Queue)
admin.site.register(Ticket)
