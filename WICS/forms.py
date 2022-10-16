from django.forms import ModelChoiceField, ModelForm
from WICS.models import MaterialList
import WICS.globals


class MaterialForm(ModelForm):
    gotoItem = ModelChoiceField(queryset=MaterialList.objects.filter(org=WICS.globals.WICSOrgKey))
    class Meta:
        model = MaterialList
#        fields = ['gotoItem', 'ID', 'oldID', 'org', 'Material', 'Description','PartType', 'SAPMaterialType', 'SAPMaterialGroup', 'Price', 'PriceUnit', 'Notes']
#        ID can't be on form because it's non-editable.  How do I get it on the form anyway?
        fields = ['gotoItem', 'oldID', 'org', 'Material', 'Description','PartType', 'SAPMaterialType', 'SAPMaterialGroup', 'Price', 'PriceUnit', 'Notes']

def FormBrowse(formname):
    theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    if formname == 'frmcount-schedulehistory-by-counterdate': pass
    elif formname == 'frmCountEntry': pass
    elif formname == 'frmCountSummaryPreview': pass
    elif formname == 'frmExportCMCounts': pass
    elif formname == 'frmImportSAP': pass
    elif formname == 'frmmaterial': 
        theForm = '<form>' + MaterialForm().as_p() + '</form><p><p><h1>How do I get the first record to load?</h1>'
    elif formname == 'frmPartTypes with CountInfo': pass
    elif formname == 'frmPrintAgendas': pass
    elif formname == 'frmRandCountScheduler': pass
    elif formname == 'frmSchedule AddPicks': pass
    elif formname == 'zutilShowColor': pass
    else: pass

    return theForm