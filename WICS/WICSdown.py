import random
from django.shortcuts import render

def WICSdown(req):
        randsvg = random.randint(1,5)
        randsvg = f'{randsvg:02}'

        templt = "UnderMaintenance.html"
        cntext = {
            'randsvg': randsvg, 
            }
        return render(req, templt, cntext)
