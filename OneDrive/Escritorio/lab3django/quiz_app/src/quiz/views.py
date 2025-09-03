from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django import forms

from .models import Exam, Question, Choice
from .forms import ExamForm, QuestionForm, ChoiceForm


def exam_list(request):
    """Lista todos los exámenes"""
    exams = Exam.objects.all().order_by('-created_date')
    return render(request, 'quiz/exam_list.html', {'exams': exams})


def exam_detail(request, exam_id):
    """Detalle de un examen con sus preguntas"""
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all().prefetch_related('choices')
    return render(request, 'quiz/exam_detail.html', {'exam': exam, 'questions': questions})


def exam_create(request):
    """Crear examen"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, 'Examen creado correctamente.')
            return redirect('question_create', exam_id=exam.id)
    else:
        form = ExamForm()
    return render(request, 'quiz/exam_form.html', {'form': form})


def exam_edit(request, exam_id):
    """Editar examen"""
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Examen actualizado correctamente.')
            return redirect('exam_detail', exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)
    return render(request, 'quiz/exam_form.html', {'form': form, 'exam': exam})


def question_create(request, exam_id):
    """Añadir pregunta a un examen"""
    exam = get_object_or_404(Exam, id=exam_id)

    ChoiceFormSetDynamic = forms.inlineformset_factory(
        Question, Choice, form=ChoiceForm, extra=4, can_delete=False
    )

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        formset = ChoiceFormSetDynamic(request.POST)

        if question_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.exam = exam
                question.save()

                formset.instance = question
                formset.save()

                correct_count = question.choices.filter(is_correct=True).count()
                if correct_count != 1:
                    messages.warning(request, 'Debe haber exactamente una respuesta correcta.')
                else:
                    messages.success(request, 'Pregunta añadida correctamente.')

                if 'add_another' in request.POST:
                    return redirect('question_create', exam_id=exam.id)
                return redirect('exam_detail', exam_id=exam.id)
    else:
        question_form = QuestionForm()
        formset = ChoiceFormSetDynamic(queryset=Choice.objects.none())

    return render(request, 'quiz/question_form.html', {
        'exam': exam,
        'question_form': question_form,
        'formset': formset,
        'edit_mode': False
    })


def question_edit(request, question_id):
    """Editar pregunta existente"""
    question = get_object_or_404(Question, id=question_id)
    total_choices = question.choices.count()
    extra_forms = max(0, 4 - total_choices)

    ChoiceFormSetDynamic = forms.inlineformset_factory(
        Question, Choice, form=ChoiceForm, extra=extra_forms, can_delete=False
    )

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSetDynamic(request.POST, instance=question)
        if question_form.is_valid() and formset.is_valid():
            question_form.save()
            formset.save()
            messages.success(request, 'Pregunta actualizada correctamente.')
            return redirect('exam_detail', exam_id=question.exam.id)
    else:
        question_form = QuestionForm(instance=question)
        formset = ChoiceFormSetDynamic(instance=question)

    return render(request, 'quiz/question_form.html', {
        'exam': question.exam,
        'question_form': question_form,
        'formset': formset,
        'edit_mode': True
    })


def question_delete(request, question_id):
    """Eliminar pregunta"""
    question = get_object_or_404(Question, id=question_id)
    exam_id = question.exam.id
    question.delete()
    messages.success(request, 'Pregunta eliminada correctamente.')
    return redirect('exam_detail', exam_id=exam_id)


@csrf_exempt
@require_POST
def question_reorder(request, exam_id):
    """Guardar orden de preguntas vía AJAX"""
    exam = get_object_or_404(Exam, id=exam_id)
    order = request.POST.getlist('order[]')
    return JsonResponse({'status': 'ok'})

def exam_play(request, exam_id):
    """Vista para jugar un examen"""
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        score = 0
        total = questions.count()
        results = []

        for question in questions:
            selected = request.POST.get(f"question_{question.id}")
            correct_choice = question.choices.filter(is_correct=True).first()
            is_correct = str(correct_choice.id) == selected if selected else False
            if is_correct:
                score += 1

            results.append({
                'question': question.text,
                'selected': Choice.objects.filter(id=selected).first(),
                'correct': correct_choice,
                'is_correct': is_correct,
            })

        return render(request, 'quiz/exam_result.html', {
            'exam': exam,
            'score': score,
            'total': total,
            'results': results
        })

    return render(request, 'quiz/exam_play.html', {
        'exam': exam,
        'questions': questions,
        'time_limit': exam.duration if hasattr(exam, 'duration') else 60
    })
