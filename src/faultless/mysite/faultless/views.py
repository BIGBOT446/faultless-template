from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template import loader
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import reverse

from .forms import DocumentForm, RuleForm
from .models import Document, Rules, Trace
from .prompt import send_prompt
from django.core.cache import cache
from . import sort
from faultless.marker.llm import ai_output
from faultless.marker.scripts.spire.grammar_spelling import grammar_spelling
from faultless.marker.scripts.spire.rules import rules 
from pathlib import Path
from .summary import summary

import os
import json
import threading
import time


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
    return render(request, "faultless/file_manager.html", {"form": form, "documents": documents, "document_count": Document.objects.count(), "rule_count": Rules.objects.count(), "review_count": Trace.objects.count()})


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
            return star_process(request, selected_ids)
        
    return render(request, "faultless/details.html", context)


def get_response(request, rule_ids):
    report = cache.get('selected')
    report_name = Document.objects.get(path=report).file.name
    new_trace = Trace(file_name = report_name)
    new_trace.save()
    cache.set('trace_id', new_trace.id, timeout=600)

    if request.method == "POST":

        cache.set("process_stage", 1, timeout=300)
        rule_list = []
        for i in range(len(rule_ids)):
            rule_list.append(Rules.objects.get(id=rule_ids[i]))

        text = send_prompt(rule_list, report)

        cache.set("process_stage", 2, timeout=300)

        input_file = Path(report)
        output_file = input_file.with_stem(f"{input_file.stem}_modified")
        cache.set('output_file', output_file, timeout=600)
        if output_file.exists():
            output_file.unlink()

        for rule in rule_list:
            output = ai_output(rule.name, text)
            rules(output, report)
        cache.set("process_stage", 3, timeout=300)

        summary()
        cache.set("process_stage", 4, timeout=300)
        time.sleep(3)
        cache.set("status", "completed", timeout=300)


def star_process(request, rule_ids):
    cache.set("status", "processing", timeout=300)
    thread = threading.Thread(target=get_response, args=(request, rule_ids))
    thread.start()

    return render(request, "faultless/loading.html")


def check_status(request):
    status = cache.get("status")
    if status == "processing":
        process_stage = cache.get("process_stage")
        return JsonResponse({
            'status': "processing",
            'process_stage': process_stage,
        })
    elif status == "completed":
        return JsonResponse({
            'status': 'completed',
            'url': reverse('process_result')
        })
    else:
    # Default response if status is neither processing nor completed
        return JsonResponse({
            'status': 'unknown',
            'message': 'No active process found'
    })


def process_result(request):
    trace_id = cache.get('trace_id')
    trace = Trace.objects.get(id=trace_id)
    output_file = cache.get('output_file')
    relative_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
    file_url = settings.MEDIA_URL + relative_path.replace(os.sep, '/')
    
    context = {
        "matches": trace.review_output["matches"],
        "url": file_url,
    }
    return render(request, "faultless/output.html", context)
    
