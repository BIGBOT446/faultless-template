from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template import loader

from .forms import DocumentForm, RuleForm
from .models import Document, rules
from .prompt import send_prompt


# Create your views here.pip
def file_manager(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("file_manager")
    else:
        form = DocumentForm()

    documents = Document.objects.all().order_by("-uploaded_at")
    return render(request, "faultless/file_manager.html", {"form": form, "documents": documents})


def get_rule(request):
    file_name = request.GET.get("file_name", "")

    if request.method == "POST":
        form = RuleForm(request.POST)
        form.save()
        return redirect("get_rule")
    else:
        form = RuleForm()
    context = {"form": form, "file_name": file_name}
    return render(request, "faultless/rule.html", context)


def view_details(request):
    data = rules.objects.all().values()
    documents = Document.objects.all().order_by("-uploaded_at")
    report = documents[0].path
    if request.method == "GET":
        if "select_file" in request.GET:
            file_name = request.GET.get("select_file", "")
            report = get_object_or_404(Document, file=file_name)
    if request.method == "POST":
        if "delete_id" in request.POST:
            document = get_object_or_404(Document, pk=request.POST["delete_id"])
            document.delete()
            return redirect(view_details)
        if "review_report" in request.POST:
            return redirect(get_response(report))
    context = {
        "allrules": data,
        "document": documents,
        #'selected': report,
    }
    return render(request, "faultless/details.html", context)


def get_response(request, report):
    data = rules.objects.all().values()
    output = ""
    for i in range(len(data)):
        output += str(i + 1) + ". Name: " + data[i]["name"] + "\n"
        output += "Scale: " + str(data[i]["scale"]) + "\n"
        output += "Description: " + data[i]["description"] + "\n"
    template = loader.get_template("faultless/output.html")
    trace = send_prompt(output, report)
    context = {
        "modified": trace,
    }
    return HttpResponse(template.render(context, request))
