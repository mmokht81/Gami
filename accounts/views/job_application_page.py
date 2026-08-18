from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework.exceptions import ValidationError

from ..models import JobPosition, Question
from ..serializers import JobApplicationSerializer


@login_required
def job_application_page(request, pk):

    job_position = get_object_or_404(
        JobPosition,
        pk=pk,
        is_active=True,
    )

    questions = Question.objects.filter(
        job_position=job_position,
        is_active=True,
    ).order_by("order")

    if request.method == "POST":

        answers = []

        for question in questions:

            answer = request.POST.get(
                f"question_{question.id}",
                ""
            ).strip()

            answers.append({
                "question_id": question.id,
                "answer": answer,
            })

        data = {
            "job_position": job_position.id,
            "answers": answers,
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": request,
            },
        )

        if serializer.is_valid():

            serializer.save(
                user=request.user
            )

            messages.success(
                request,
                "درخواست استخدام شما با موفقیت ثبت شد."
            )

            return redirect("dashboard")

        for field, errors in serializer.errors.items():

            for error in errors:

                messages.error(
                    request,
                    str(error)
                )

    return render(
        request,
        "accounts/job_application.html",
        {
            "job_position": job_position,
            "questions": questions,
        },
    )