import json, string
from tokenize import String
from .models import *
from django.contrib.auth.models import User

user = User.objects.get(username='admin')

def dump_module_content(file_name):
  modules = Module.objects.exclude(language='L')
  data = []
  for module in modules:
    module_data = {
      'name': module.name,
      'module_number': module.module_number,
      'introduction': module.introduction,
      'blurb': module.blurb,
      'language': module.language,
      'image_for_topics': module.image_for_topics.url if module.image_for_topics else None,
      'author': module.author.username,
      'objectives': [obj.objectives for obj in LearningObjectives.objects.filter(module=module)],
      'topics': [],
    }
    for topic in module.topics.all():
      topic_data = {
        'name': topic.name,
        'order': topic.order,
        'activation': topic.activation,
        'new_information': topic.new_information,
        'reflection': topic.reflection,
        'roleplay': topic.roleplay,
        'extension': topic.extension,
        'language': topic.language,
        'topic_image': topic.topic_image.url if topic.topic_image else None,
        'author': topic.author.username,
        'objectives': [obj.objectives for obj in LearningObjectives.objects.filter(topic=topic)],
        'scenarios': [],
      }
      for scenario in topic.scenarios.all():
        scenario_data = {
          'name': scenario.name,
          'description': scenario.description,
          'initial_information': scenario.initial_information,
          'context_after_feedback': scenario.context_after_feedback,
          'context_before_and_after_feedback': scenario.context_before_and_after_feedback,
          'language_note': scenario.language_note,
          'culture_note': scenario.culture_note,
          'language_note_after_feedback': scenario.language_note_after_feedback,
          'language_note_before_and_after_feedback': scenario.language_note_before_and_after_feedback,
          'culture_note_after_feedback': scenario.culture_note_after_feedback,
          'culture_note_before_and_after_feedback': scenario.culture_note_before_and_after_feedback,
          'reflection_task': scenario.reflection_task,
          'extension_task': scenario.extension_task,          
          'author': scenario.author.username,
          'order': scenario.order,
          'judgment_task': {
             'name': scenario.judgment_task.name, 
             'description': scenario.judgment_task.description,
          },
          'answers': [{
            'content': answer.content, 
            'feedback_initial': answer.feedback_initial, 
            'feedback_final': answer.feedback_final,
            'rating_from': str(answer.rating_from), 
            'rating_to': str(answer.rating_to),
            } 
            for answer in Answer.objects.filter(task=scenario.judgment_task)
            ],
        }
        topic_data['scenarios'].append(scenario_data)
      module_data['topics'].append(topic_data)
    data.append(module_data)

  with open(file_name, 'w') as f:
    json.dump(data, f, indent=4)

def import_module_content(file_name):
  print(f"Importing content from {file_name}...")
  with open(file_name, 'r', newline='') as f:
    data = json.load(f)  
    for module in data:
      # Create Learning Objectives for the Module object
      learning_objectives = LearningObjectives.objects.create(
          name = module['name'] + " Learning Objectives",
          objectives = ' '.join([i for i in module['objectives']]),
          language = module['language'],
      )
      # Create Module Object
      module_obj = Module.objects.create(
          name = module['name'],
          module_number = module['module_number'],
          introduction = module['introduction'],
          blurb = module['blurb'],
          objectives = learning_objectives,
          language = module['language'],
          image_for_topics = module['image_for_topics'],
          author = user,   
      )

      for topic in module['topics']:
        topic_learning_objectives = LearningObjectives.objects.create(
          name = topic['name'] + " Topic Learning Objectives",
          objectives = '<br>'.join([i for i in topic['objectives']]),
          language = module['language'],
        )

        topic_obj = Topic.objects.create(
          name = topic['name'],
          order = topic['order'],
          activation = topic['activation'],
          new_information = topic['new_information'],
          reflection = topic['reflection'],
          roleplay = topic['roleplay'],
          extension = topic['extension'],
          language = module['language'],
          topic_image = topic['topic_image'],
          author = user,
          objectives = topic_learning_objectives,
        )

        module_obj.topics.add(topic_obj)

        for scenario_data in topic['scenarios']:
          judgement_task_obj = JudgmentTask.objects.create(
            name = scenario_data['name'] + " Judgment Task",
            description = scenario_data['judgment_task']['description'],          
          )

          for answer_data in scenario_data['answers']:
             Answer.objects.create(
               content = answer_data['content'],
               feedback_initial = answer_data['feedback_initial'],
               feedback_final = answer_data['feedback_final'],
               rating_from = float(answer_data['rating_from']),
               rating_to = float(answer_data['rating_to']),
               task = judgement_task_obj,
            )
         
          scenario_obj = Scenario.objects.create(
              name = scenario_data['name'],
              description = scenario_data['description'],
              initial_information = scenario_data['initial_information'],
              context_after_feedback = scenario_data['context_after_feedback'],
              context_before_and_after_feedback = scenario_data['context_before_and_after_feedback'],
              language_note = scenario_data['language_note'],
              culture_note = scenario_data['culture_note'],
              language_note_after_feedback = scenario_data['language_note_after_feedback'],
              language_note_before_and_after_feedback = scenario_data['language_note_before_and_after_feedback'],
              culture_note_after_feedback = scenario_data['culture_note_after_feedback'],
              culture_note_before_and_after_feedback = scenario_data['culture_note_before_and_after_feedback'],
              reflection_task = scenario_data['reflection_task'],
              extension_task = scenario_data['extension_task'],
              author = user,
              order = scenario_data['order'],
              judgment_task=judgement_task_obj,
          )
          topic_obj.scenarios.add(scenario_obj)
          

# CLEANUP DURING TESTING (Deletes all on cascade)       

          judgement_task_obj.delete()
        topic_learning_objectives.delete()
      learning_objectives.delete()          

""" Running in the interactive django shell:
from culture_content import content_loader as cl
cl.import_module_content("dump_module_content.json")

cl.dump_module_content("dump_module_content.json")

jfiles = ["jpn-mod-1.json", "jpn-mod-2.json", "jpn-mod-3.json", "jpn-mod-4.json", "jpn-mod-5.json"]
nfiles = ["jpn-mod-1-jpn.json", "jpn-mod-2-jpn.json", "jpn-mod-3-jpn.json", "jpn-mod-4-jpn.json", "jpn-mod-5-jpn.json"]

for i in jfiles:
  cl.load_module_content(i, 'J')

for i in nfiles:
  cl.load_module_content(i, 'N')

"""

