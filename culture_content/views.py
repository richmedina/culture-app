from .models import *
from .models import lang_choices
from django.conf import settings
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.http import HttpResponse
import simplejson
from django.http import JsonResponse, HttpResponseForbidden, Http404
from course.models import Course
from glob import glob
import random
import os

IMAGE_PATH = settings.IMAGE_PATH
TEMP_ACCESS_GROUP = settings.TEMP_ACCESS_GROUP


approved_lang_modules = [v['code'] for k, v in settings.LANGUAGE_DATA.items() if v['status'] == 'active' or v['status'] == 'temp_access']
temporary_lang_access = [v['code'] for k, v in settings.LANGUAGE_DATA.items() if v['status'] == 'temp_access']

# Assemble list of possible images for each language.
lang_img_paths = {
    lang: [data['img_home'] + '/' + os.path.basename(r) for r in glob(IMAGE_PATH + r'/' + data['img_home'] + r'/*.*g')]
    for lang, data in settings.LANGUAGE_DATA.items()
}    

@login_required
def home(request):
    language_list = []
    for lang, data in settings.LANGUAGE_DATA.items():
        if data['status'] == 'active':
            p = random.choice(lang_img_paths[lang])
            language_list.append({'url': lang, 'image_url': p, 'lang_name': data['display']})
        elif request.user.groups.filter(name=TEMP_ACCESS_GROUP).exists() and data['status'] == 'temp_access':
            p = random.choice(lang_img_paths[lang])
            language_list.append({'url': lang, 'image_url': p, 'lang_name': data['display'] + ' (Temporary Access)'})
 
    template_context = {'languages': language_list}
    return render(request, 'culture_content/home.html', template_context)

@login_required
def staff_review(request):
    if not request.user.is_staff:
        raise Http404("Page not found")
    language_list = []
    for lang, data in settings.LANGUAGE_DATA.items():
        if data['status'] == 'pending' or data['status'] == 'active' or data['status'] == 'temp_access':
            p = random.choice(lang_img_paths[lang])
            language_list.append({'url': lang, 'image_url': p, 'lang_name': data['display']})
 
    template_context = {'languages': language_list}
    return render(request, 'culture_content/home_review.html', template_context)

@login_required
def get_navbar(request):
    language_object = []
    for lang, data in settings.LANGUAGE_DATA.items():
        if data['status'] == 'active':
            language_object.append({ 'lang': lang, 'display': data['human_readable'], 'lang_modules': Module.objects.filter(language=lang) })

    return render(request, 'culture_content/navbar.html', { 'language_object': language_object })

@login_required
def get_modules(request, lang):
    if lang not in approved_lang_modules and request.user.is_staff==False:
        raise Http404("Page not found") 
    elif lang in temporary_lang_access and request.user.groups.filter(name=TEMP_ACCESS_GROUP).exists()==False and request.user.is_staff==False:
        raise Http404("Page not found")
    else:
        p = random.choice(lang_img_paths[lang])
        modules = Module.objects.filter(language=lang).order_by('module_number')
        lang_display = settings.LANGUAGE_DATA[lang]['human_readable']
        html_dir = settings.LANGUAGE_DATA[lang]['html_dir']
        html_lang = settings.LANGUAGE_DATA[lang]['html_lang']
    return render(request, 'culture_content/modules.html', {'modules': modules, 'img_url': p, 'lang_display': lang_display, 'html_dir': html_dir, 'html_lang': html_lang})


@login_required
def get_topic_scenarios(request, top_id):
    topic = get_object_or_404(Topic, pk=top_id)
    module = Module.objects.get(topics__in=[top_id])
    if module.language not in approved_lang_modules and request.user.is_staff==False:
        raise Http404("Page not found")
    lang_display = settings.LANGUAGE_DATA[module.language]['human_readable']
    html_dir = settings.LANGUAGE_DATA[module.language]['html_dir']
    html_lang = settings.LANGUAGE_DATA[module.language]['html_lang']
    scenario_results = get_scenarios_responses(top_id, request.user)
    return render(request, 'culture_content/topics.html', {'topic': topic, 'module': module, 'lang_display': lang_display, 'html_dir': html_dir, 'html_lang': html_lang, 'scenario_results': scenario_results})


@login_required
def get_scenario_detail(request, scenario_id):
    scenario = get_object_or_404(Scenario, pk=scenario_id)
    topic = get_object_or_404(Topic, scenarios__in=[scenario_id]) # when a scenario is unattached (made unavailable) from a topic, this forces the 404.
    module = Module.objects.get(topics__in=[topic.id])
    if module.language not in approved_lang_modules and request.user.is_staff==False:
        raise Http404("Page not found")
    elif module.language in temporary_lang_access and request.user.groups.filter(name=TEMP_ACCESS_GROUP).exists()==False and request.user.is_staff==False and request.user.is_staff==False:
        raise Http404("Page not found")
    else:
        lang_display = settings.LANGUAGE_DATA[module.language]['human_readable']
    html_dir = settings.LANGUAGE_DATA[module.language]['html_dir']
    html_lang = settings.LANGUAGE_DATA[module.language]['html_lang']
    return render(request, 'culture_content/scenario.html', {'scenario': scenario, 'topic':topic, 'module':module, 'lang_display': lang_display, 'html_dir': html_dir, 'html_lang': html_lang, 'ajax_save_resp': settings.SITE_ROOT+'save_response/',})


@login_required
def save_response(request, answer_id, response):
    if request.is_ajax() and request.method=='POST':
        answer = Answer.objects.get(pk=answer_id)
        response = Response.objects.create(answer=answer, response= response, user=request.user)
        expert ={}
        expert['answer_id'] = answer_id
        expert['content'] = answer.content
        expert['feedback'] = answer.feedback_final
        expert['from']=answer.rating_from
        expert['to'] = answer.rating_to
        expert['response_id'] = response.pk
        expert['response'] = response.response
        return JsonResponse(expert, content_type='application/json')


@login_required
def get_user_responses(request, lang):
    statistics = []
    user_profile = Profile.objects.get(user=request.user)
    modules = Module.objects.filter(language=lang)
    topics = Module.objects.filter(id__in=modules).values('topics')
    scenarios = Topic.objects.filter(id__in=topics).values('scenarios')
    scenarios = Scenario.objects.filter(id__in=scenarios)
    for scene in scenarios:
        options_stats, scenario_stats = get_scenario_results(scene.id)
        statistics.append([scene, scenario_stats])
    return render(request, 'culture_content/responses.html', {'stats': statistics, 'user_language': user_profile.language})


@login_required
def get_user_responses_in_course(request, course_id):
    statistics = []
    course = Course.objects.get(id=course_id)
    participants = Course.objects.filter(id=course_id).values_list('participants__user')
    scenarios = Topic.objects.filter(language=course.language).values('scenarios')
    scenarios = Scenario.objects.filter(id__in=scenarios)
    for scene in scenarios:
        options_stats, scenario_stats = get_scenario_results(scene.id, users=participants)
        statistics.append ([scene, scenario_stats])
    return render (request, 'culture_content/responses_course.html',{'stats': statistics, 'course': course})

#Total number of scenarios in a course attempted by user.
@login_required
def get_count_total_attempts_scenarios(request, course_id):
    counts = []
    course = Course.objects.get(id=course_id)
    participants = Course.objects.filter(id=course_id).values_list('participants__user')
    scenarios = Topic.objects.filter(language=course.language).values('scenarios')
    scenarios = Scenario.objects.filter(id__in=scenarios)
    for participant in participants:
        scenario_count=0
        user = User.objects.get(id=participant[0])
        for scene in scenarios:
            stats=get_scenario_results(scene.id, user=user)
            if stats[1][0]>0:
                scenario_count+=1
        counts.append((user.username, scenario_count))
    return render(request, 'culture_content/responses_by_participants.html',{'counts':counts, 'course':course})


@login_required
def get_student_results_in_course(request, course_id):
    results = []
    course = Course.objects.get(id=course_id)
    participants = Course.objects.filter(id=course_id).values_list('participants__user')
    scenarios = Topic.objects.filter(language=course.language).values('scenarios')
    scenarios = Scenario.objects.filter(id__in=scenarios)
    for participant in participants:
        user = User.objects.get(id=participant[0])
        for scene in scenarios:
            for judgement in scene.judgment_task.get_answers():
                answer_responses = judgement.get_user_responses([user.id])
                if answer_responses is not None:
                    for res in answer_responses:
                        results.append((user.username, scene, judgement, res, strip_tags(judgement.content)))
    return render(request, 'culture_content/student_responses_in_course.html',{'results': results, 'course':course})

def get_scenarios_responses(topic_id, current_user):
    statistics = []
    scenarios = Topic.objects.filter(id=topic_id).values('scenarios')
    scenarios = Scenario.objects.filter(id__in=scenarios).order_by('order')
    for scene in scenarios:
        options_stats, scenario_stats = get_scenario_results(scene.id, user=current_user)
        statistics.append([scene, scenario_stats])
    return statistics


@login_required
def get_options_results(request, scenario_id, course_id=None):
    scenario = Scenario.objects.get (id=scenario_id)
    user_profile = Profile.objects.get(user=request.user)
    if course_id is not None:
        participants = Course.objects.filter(id=course_id).values_list('participants__user')
        options_stats, scenario_stats = get_scenario_results(scenario_id, users=participants)
        return render(request, 'culture_content/options_course_responses.html',
                      {'stats': options_stats, 'course_id': course_id, 'user_language': user_profile.language})
    else:
        options_stats, scenario_stats = get_scenario_results(scenario_id)
        return render (request, 'culture_content/options_responses.html', {'stats': options_stats, 'user_language': user_profile.language, 'scenario_language': scenario.get_scenario_language()})


def get_scenario_results(scenario_id, user=None, users=None):
    scenario = Scenario.objects.get(pk=scenario_id)
    options = []
    attempts = []
    stats = []
    for answer in scenario.judgment_task.get_answers():
        options.append(answer)
        results = []
        responses = 0
        if user is not None:
            answer_responses=answer.get_user_responses([user.id])
        elif users is not None:
            answer_responses=answer.get_user_responses(users)
        else:
            answer_responses=answer.get_responses()

        if answer_responses is not None:

            for res in answer_responses:
                responses += 1
                if res.response >= res.answer.rating_from and res.response <= res.answer.rating_to:
                    results.append(1)
                else:
                    results.append(0)
        else:
            results= 0
        attempts.append(round(len(results)))
        if len(results)>0:
            stats.append(round(100 * (sum (results)/len(results))))
        else:
            stats.append(0)
    output = zip(options, attempts, stats)
    scenario_stats=(attempts[0], round(sum(stats)/len(stats)))
    return(output, scenario_stats)


@login_required
def get_profile(request):
    if request.user.is_staff:
        profile = Profile.objects.get(user=request.user)
        return render(request, 'culture_content/dashboard.html', {'profile': profile})
    else:
        return HttpResponseForbidden()