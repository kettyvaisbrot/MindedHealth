
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from insights.services.log_fetcher import fetch_user_logs
from insights.services.prompt_builder import build_insight_prompt
from insights.services.ai_client import get_ai_insight

@login_required
def ai_insights_view(request):
    logs = fetch_user_logs(request.user)

    if not any(log.exists() for log in logs.values()):
        message = "😊 It’s time to get to know each other! Start documenting your day-to-day life via the dashboard."
        return render(request, "insights/insights.html", {"insights": message})

    prompt = build_insight_prompt(logs)
    ai_response = get_ai_insight(prompt)

    return render(request, "insights/insights.html", {"insights": ai_response})
