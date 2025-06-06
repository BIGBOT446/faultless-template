import logging
import os
import threading
import time
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from faultless.marker.llm import ai_output
from faultless.marker.rules import rules

from .forms import DocumentForm, RuleForm
from .models import Document, Rules, Trace
from .prompt import send_prompt
from .summary import summary

logger = logging.getLogger(__name__)


# Create your views here.pip
def file_manager(request):
    success_message = None

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            success_message = f"Successfully uploaded '{document.file.name}'"
            form = DocumentForm()  
        else:
            pass
    else:
        form = DocumentForm()

    documents = Document.objects.all().order_by("-uploaded_at")
    context = {
        "form": form,
        "documents": documents,
        "report_count": Document.objects.count(),
        "rule_count": Rules.objects.count(),
        "review_count": Trace.objects.count(),
        "success_message": success_message,
    }
    return render(request, "faultless/file_manager.html", context)


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


def edit_rule(request, rule_id):
    rule = get_object_or_404(Rules, pk=rule_id)

    if request.method == "POST":
        form_data = {}
        
        if request.POST.get("name", "").strip():
            form_data["name"] = request.POST["name"].strip()
        else:
            form_data["name"] = rule.name  
            
        if request.POST.get("scale"):
            form_data["scale"] = request.POST["scale"]
        else:
            form_data["scale"] = rule.scale  
            
        if request.POST.get("description", "").strip():
            form_data["description"] = request.POST["description"].strip()
        else:
            form_data["description"] = rule.description  
            
        if request.POST.get("output_format", "").strip():
            form_data["output_format"] = request.POST["output_format"].strip()
        else:
            form_data["output_format"] = rule.output_format  

        form = RuleForm(form_data, instance=rule)
        
        if form.is_valid():
            form.save()
            return redirect("get_rule")
        else:
            data = Rules.objects.all().values()
            context = {
                "allrules": data, 
                "editing_rule": rule, 
                "is_editing": True,
                "form": form  
            }
            return render(request, "faultless/rule.html", context)

    data = Rules.objects.all().values()
    context = {"allrules": data, "editing_rule": rule, "is_editing": True}
    return render(request, "faultless/rule.html", context)

def view_details(request):
    data = Rules.objects.all().values()
    documents = Document.objects.all().order_by("-uploaded_at")
    report = None

    context = {
        "allrules": data,
        "document": documents,
    }

    if request.method == "POST":
        if "select_file" in request.POST:
            file_name = request.POST.get("select_file")
            report = get_object_or_404(Document, file=file_name).path
            cache.set("selected", report, timeout=600)

        if "delete_id" in request.POST:
            document = get_object_or_404(Document, pk=request.POST["delete_id"])
            document.delete()
            return redirect(view_details)

        if "delete_rule_id" in request.POST:
            rule = get_object_or_404(Rules, pk=request.POST["delete_rule_id"])
            rule.delete()
            return redirect(view_details)

        if "view_details" in request.POST:
            selected_ids = request.POST.getlist("selected_rules")
            if cache.get("selected") == None:
                context["message"] = "Please submit a report for review!"
                return render(request, "faultless/details.html", context)
            return star_process(request, selected_ids)

    return render(request, "faultless/details.html", context)


def get_response(request, rule_ids):
    try:
        report = cache.get("selected")
        report_name = Document.objects.get(path=report).file.name
        new_trace = Trace(file_name=report_name)
        new_trace.save()
        cache.set("trace_id", new_trace.id, timeout=600)

        try:
            cache.set("process_stage", 1, timeout=300)
            logger.info("1 cached")
        except Exception as e:
            logger.error("cannot cache process stage 1: %s", e)
            raise e

        time.sleep(1)
        rule_list = []
        for i in range(len(rule_ids)):
            rule_list.append(Rules.objects.get(id=rule_ids[i]))

        text = send_prompt(rule_list, report)

        cache.set("process_stage", 2, timeout=300)
        time.sleep(1)
        input_file = Path(report)
        output_file = input_file.with_stem(f"{input_file.stem}_modified")
        cache.set("output_file", output_file, timeout=600)
        if output_file.exists():
            output_file.unlink()

        for rule in rule_list:
            output = ai_output(rule.name, text)
            rules(output, report)

        cache.set("process_stage", 3, timeout=300)
        time.sleep(1)
        summary()
        cache.set("process_stage", 4, timeout=300)
        time.sleep(1)
        time.sleep(3)
        cache.set("status", "completed", timeout=300)

    except Exception as e:
        logger.error("Error in get_response: %s", e)
        # Set error status and message in cache
        cache.set("status", "error", timeout=300)
        cache.set("error_message", str(e), timeout=300)


def star_process(request, rule_ids):
    try:
        # Clear any previous error status
        cache.delete("error_message")
        cache.set("status", "processing", timeout=300)
        logger.info("process cached")
    except Exception as e:
        logger.error("cannot cache process status: %s", e)
    try:
        logger.info("Thread running")
        thread = threading.Thread(target=get_response, args=(request, rule_ids))
        thread.start()
    except Exception as e:
        logger.error("cannot create thread: %s", e)
        cache.set("status", "error", timeout=300)
        cache.set("error_message", "Failed to start processing thread", timeout=300)

    return render(request, "faultless/loading.html")


def check_status(request):
    status = cache.get("status")
    if status == "processing":
        process_stage = cache.get("process_stage")
        return JsonResponse(
            {
                "status": "processing",
                "process_stage": process_stage,
            }
        )
    elif status == "completed":
        return JsonResponse({"status": "completed", "url": reverse("process_result")})
    elif status == "error":
        error_message = cache.get("error_message", "An unknown error occurred")
        return JsonResponse({"status": "error", "error_message": error_message})
    else:
        return JsonResponse({"status": "unknown", "message": "No active process found"})


def process_result(request):
    trace_id = cache.get("trace_id")
    trace = Trace.objects.get(id=trace_id)
    output_file = cache.get("output_file")
    relative_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
    file_url = settings.MEDIA_URL + relative_path.replace(os.sep, "/")

    context = {
        "matches": trace.review_output["matches"],
        "url": file_url,
    }
    return render(request, "faultless/output.html", context)
