from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template import loader
from django.conf import settings
from django.conf.urls.static import static

from .forms import DocumentForm, RuleForm
from .models import Document, Rules, Trace
from .prompt import send_prompt
from django.core.cache import cache
from . import sort
from faultless.marker.llm import ai_output
from faultless.marker.scripts.spire.grammar_spelling import grammar_spelling
from faultless.marker.scripts.spire.rules import rules 
from faultless.marker.scripts.spire.summary import insert_text_new_page 
from pathlib import Path


import os
import json


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
    data = Rules.objects.all().values()

    if request.method == "POST":
        
        if "delete_rule_id" in request.POST:
            rule = get_object_or_404(Rules, pk=request.POST["delete_rule_id"])
            rule.delete()
            return redirect("get_rule")
        
        form = RuleForm(request.POST)
        if form.is_valid():
            form.save()
            data = Rules.objects.all().values()
            form = RuleForm()
            return redirect("get_rule")
        else:
            return render(request, "faultless/rule.html", {"form": form, "allrules": data})
    

    else:
        form = RuleForm()
    context = {"form": form, "allrules": data}
    return render(request, "faultless/rule.html", context)


def view_details(request):
    data = Rules.objects.all().values()
    documents = Document.objects.all().order_by("-uploaded_at")
    report = None

    context = {
        "allrules": data,
        "document": documents,
    }

    """if len(documents) > 0:
        report = documents[0].path"""
    if request.method == "GET":
        if "select_file" in request.GET:
            file_name = request.GET.get("select_file", "")
            report = get_object_or_404(Document, file=file_name).path
            cache.set('selected', report, timeout=600)
            
    if request.method == "POST":

        if "delete_id" in request.POST:
            document = get_object_or_404(Document, pk=request.POST["delete_id"])
            document.delete()
            return redirect(view_details)
        
        if "delete_rule_id" in request.POST:
            rule = get_object_or_404(Rules, pk=request.POST["delete_rule_id"])
            rule.delete()
            return redirect(view_details)
 
        if "view_details" in request.POST:
            selected_ids = request.POST.getlist('selected_rules')
            if cache.get('selected') == None:
                context["message"] = 'Please submit a report for review!'
                return render(request, "faultless/details.html", context)
            return get_response(request, selected_ids)
        
    return render(request, "faultless/details.html", context)


def get_response(request, rule_ids):
    report = cache.get('selected')
    report_name = Document.objects.get(path=report).file.name
    new_trace = Trace(file_name = report_name)
    new_trace.save()
    cache.set('trace_id', new_trace.id, timeout=600)

    if request.method == "POST":

        rule_list = []
        for i in range(len(rule_ids)):
            rule_list.append(Rules.objects.get(id=rule_ids[i]))

        text = send_prompt(rule_list, report)

        input_file = Path(report)
        output_file = input_file.with_stem(f"{input_file.stem}_modified")
        if output_file.exists():
            output_file.unlink()

        for rule in rule_list:
            output = ai_output(rule.name, text)
            rules(output, report)

        # get trace that stored in the database
        trace = Trace.objects.get(id=cache.get('trace_id'))
        relative_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
        file_url = settings.MEDIA_URL + relative_path.replace(os.sep, '/')
        trace = trace.review_output
        context = {
            "matches": trace["matches"],
            "url": file_url,
        }
        return render(request, "faultless/output.html", context)
    context = {
        "message": "There is no review history yet.",
    }

    return render(request, "faultless/output.html", context)

def user_view(request, p_num):
    words = [
        {"was": 0, "say": 0},
        {"dont": 0},
        {"3": 0},
        {"content": 0},
    ]
    paragraphs = [
        "I was trying to say hello world.",
        "Everyday i dont want to wake up.",
        "Paragraph 3 content...",
        "Paragraph 8 content..."
    ]

    context = {
        "words": words[p_num-1],
        "p": paragraphs[p_num-1],
        "current": p_num,
        "total": len(paragraphs),
    }
    return render(request, "faultless/test.html", context)
