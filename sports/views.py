from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from .models import Team, Player, Event, Game, Legend, Coach
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse

# Create your views here.
def index(request):
    events = Event.objects.all().order_by('-date')[:4]  
    results = Game.objects.all().order_by('-date')[:4]
    upcomings = Game.objects.filter(is_finished=False).order_by('-date')[:4]

    context = {
        'events':events,
        'results':results,
        'upcomings':upcomings,
    }
    return render(request, 'index.html', context)

def teams(request):
    teams = Team.objects.all()
    return render(request, 'team_list.html', {'teams': teams})


def rooster(request, team_name):
    team = get_object_or_404(Team, name=team_name)
    players = Player.objects.filter(team=team).exclude(is_captain=True).order_by('-shirt_number').reverse()
    captain = Player.objects.filter(is_captain=True).first()
    results = Game.objects.filter(dcb_team=team).order_by('-date')[:2]
    upcomings = Game.objects.filter(is_finished=False, dcb_team=team).order_by('-date')[:2]


    context = {
        'team':team,
        'players':players,
        'captain':captain,
        'results':results,
        'upcomings': upcomings,
    }

    return render(request, 'player_list.html', context)


def profile(request, team_name, pk):
    player = get_object_or_404(Player, pk=pk)
    teamIn = get_object_or_404(Team, name=team_name)
    teamates = Player.objects.filter(team=teamIn).exclude(pk=pk).order_by('?')[:4]

    context = {
        'teamates': teamates,
        'player': player
    }

    return render(request, 'player_profile.html', context)


def legends(request):
    legends = Legend.objects.all()
    
    # Paginator
    paginator = Paginator(legends, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'legends.html', {'page_obj':page_obj})

@ratelimit(key='ip', rate="100/min")
def get_more_results(request, team_name, amount):
    results = Game.objects.filter(dcb_team__name=team_name, is_finished=True).order_by('-date')[amount: amount + 4]
    result_data = []
    for result in results:
        result_data.append({
            'dcb_team':str(result.dcb_team),
            'opposition':str(result.opposition),
            'time':result.datetime_combined.strftime('%Y-%m-%d %H:%M'),
            'location':result.location,
            'dcb_score':result.dcb_score,
            'opp_score':result.opp_score,
        })

    return JsonResponse({'games':result_data})
    
@ratelimit(key='ip', rate="100/min")
def get_more_upcomings(request, team_name, amount):
    upcomings = Game.objects.filter(dcb_team__name=team_name, is_finished=False).order_by('-date')[amount: amount + 4]
    upcoming_data = []

    for upcoming in upcomings:
        upcoming_data.append({
            'pk': upcoming.pk,
            'time':upcoming.datetime_combined.strftime('%Y-%m-%d %H:%M'),
            'location':upcoming.location,
            'dcb_team':str(upcoming.dcb_team),
            'opposition':str(upcoming.opposition)
        })

    return JsonResponse({'games':upcoming_data})