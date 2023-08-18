from datetime import datetime
from django.db import models


# I'm quite happy with automaintained pk fields, so I don't specify any

class async_comm(models.Model):
    reqid = models.CharField(max_length=255, primary_key=True)
    timestamp = models.CharField(max_length=30, null=True)
    processname = models.CharField(max_length=256, null=True, blank=True)
    statecode = models.CharField(max_length=64, null=True, blank=True)
    statetext = models.CharField(max_length=512, null=True, blank=True)
    result = models.CharField(max_length=2048, null=True, blank=True)
    extra1 = models.CharField(max_length=2048, null=True, blank=True)

def set_async_comm_state(
        reqid, 
        statecode,
        statetext,
        processname = None,
        result = None,
        extra1 = None,
        new_async = False
    ):
    if new_async:
        acomm = async_comm.objects.get_or_create(pk=reqid)
    else:
        acomm = async_comm.objects.get(pk=reqid)
    # why does acomm sometimes come back as a tuple???
    if isinstance(acomm, tuple): acomm = acomm[0]
    
    acomm.statecode = statecode
    acomm.statetext = statetext
    acomm.result = result
    acomm.extra1 = extra1
    if processname is not None: acomm.processname = processname
    acomm.timestamp = datetime.now().__str__()
    acomm.save()

    return acomm
