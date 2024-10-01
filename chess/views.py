from django.shortcuts import render

# chess/views.py
from django.contrib.auth import authenticate
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Player, Tournament, TournamentResult, Campus
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import (UserSerializer,LoginSerializer,
    PlayerSerializer, PlayerCreateUpdateSerializer,
    TournamentSerializer, TournamentCreateSerializer,
    TournamentResultSerializer, TournamentResultCreateSerializer,
    LeaderboardEntrySerializer
)
from .models import GameInvitation
from .models import Tournament, Match
from rest_framework.views import APIView
from .models import PlayerStats
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

class SignupView(APIView):
    # Allow anyone to access this view (no authentication needed)
    permission_classes = [AllowAny]

    def post(self, request):
        # Deserialize incoming data using UserSerializer
        serializer = UserSerializer(data=request.data)
        # Validate the data
        if serializer.is_valid():
            # Save the new user (this will call the overridden create method)
            user = serializer.save()
            # Generate a token for the newly created user
            token = Token.objects.create(user=user)
            # Return the user's data along with the authentication token
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        # If validation fails, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    # Allow anyone to access this view (no authentication needed)
    permission_classes = [AllowAny]

    def post(self, request):
        # Deserialize the login data
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Authenticate the user using the provided credentials
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            # If authentication is successful
            if user is not None:
                # Get or create an authentication token for the user
                token, created = Token.objects.get_or_create(user=user)
                # Return the user data and the token
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key
                }, status=status.HTTP_200_OK)
            # If authentication fails, return an error
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        # If validation fails, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlayerDetailView(generics.RetrieveAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    lookup_field = 'chess_com_username'
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # Retrieve the Player instance
        
        # Fetch data from Chess.com
        chess_com_data = self.get_chess_com_data(instance.chess_com_username)

        # Use get_or_create to ensure the player exists in the database
        player, created = Player.objects.get_or_create(
            chess_com_username=instance.chess_com_username
        )

        # Serialize the player instance
        serializer = self.get_serializer(player)
        return Response(serializer.data)

# @api_view(['GET'])
# def player_game_archives(request, username):
#     archives = get_chess_com_data(f"player/{username}/games/archives")
#     return Response(archives)

class PlayerCampusView(generics.RetrieveAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    lookup_field = 'chess_com_username'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"campus": instance.campus.name if instance.campus else None})

class CreateTournamentView(generics.CreateAPIView):
    serializer_class = TournamentCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        serializer.save()

class SubmitTournamentResultView(generics.CreateAPIView):
    serializer_class = TournamentResultCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class LeaderboardView(generics.ListAPIView):
    queryset = Player.objects.all().order_by('-local_rating')
    serializer_class = LeaderboardEntrySerializer

    def get_queryset(self):
        return super().get_queryset()[:10]  # Top 10 players


# def get_chess_com_data(endpoint):
#     response = requests.get(f"{settings.CHESS_COM_API_BASE}/{endpoint}")
#     return response.json()

# @api_view(['GET'])
# def player_profile(request, username):
#     profile = get_chess_com_data(f"player/{username}")
#     stats = get_chess_com_data(f"player/{username}/stats")
    
#     player = get_object_or_404(Player, chess_com_username=username)
#     campus = player.campus.name if player.campus else None
    
#     return Response({
#         "profile": profile,
#         "stats": stats,
#         "local_rating": player.local_rating,
#         "campus": campus
#     })

# @api_view(['GET'])
# def player_game_archives(request, username):
#     archives = get_chess_com_data(f"player/{username}/games/archives")
#     return Response(archives)

@api_view(['GET'])
def player_campus(request, username):
    player = get_object_or_404(Player, chess_com_username=username)
    return Response({
        "campus": player.campus.name if player.campus else None
    })

@api_view(['POST'])
def create_tournament(request):
    name = request.data.get('name')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    campus_id = request.data.get('campus_id')
    
    campus = get_object_or_404(Campus, id=campus_id)
    
    tournament = Tournament.objects.create(
        name=name,
        start_date=start_date,
        end_date=end_date,
        campus=campus
    )
    
    return Response({
        "id": tournament.id,
        "name": tournament.name,
        "start_date": tournament.start_date,
        "end_date": tournament.end_date,
        "campus": tournament.campus.name
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def submit_tournament_result(request):
    tournament_id = request.data.get('tournament_id')
    player_id = request.data.get('player_id')
    position = request.data.get('position')
    points = request.data.get('points')
    
    tournament = get_object_or_404(Tournament, id=tournament_id)
    player = get_object_or_404(Player, id=player_id)
    
    result = TournamentResult.objects.create(
        tournament=tournament,
        player=player,
        position=position,
        points=points
    )
    
    return Response({
        "id": result.id,
        "tournament": result.tournament.name,
        "player": result.player.user.username,
        "position": result.position,
        "points": result.points
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def leaderboard(request):
    players = Player.objects.all().order_by('-local_rating')[:10]
    return Response([
        {
            "username": player.user.username,
            "chess_com_username": player.chess_com_username,
            "local_rating": player.local_rating,
            "campus": player.campus.name if player.campus else None
        }
        for player in players
    ])


class PlayerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            player = User.objects.get(username=username)
            stats = player.stats
            data = {
                "games_played": stats.games_played,
                "wins": stats.wins,
                "losses": stats.losses,
                "draws": stats.draws,
                "win_ratio": stats.win_ratio,
                "average_game_time": stats.average_game_time
            }
            return Response(data)
        except User.DoesNotExist:
            return Response({"error": "Player not found"}, status=404)


class TournamentBracketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tournament_id):
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            matches = tournament.matches.filter(round_number=tournament.current_round)
            bracket = [{"player1": match.player1.username, "player2": match.player2.username, "winner": match.winner.username if match.winner else None} for match in matches]
            data = {
                "tournament": tournament.name,
                "round": tournament.current_round,
                "bracket": bracket,
            }
            return Response(data)
        except Tournament.DoesNotExist:
            return Response({"error": "Tournament not found"}, status=404)

class TournamentProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tournament_id):
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            for match in tournament.matches.filter(round_number=tournament.current_round):
                match.progress_tournament()
            return Response({"success": "Tournament progressed to the next round."})
        except Tournament.DoesNotExist:
            return Response({"error": "Tournament not found"}, status=404)
        

@api_view(['POST'])
def send_invitation(request):
    sender = request.user
    receiver_username = request.data.get('receiver')
    
    try:
        receiver = User.objects.get(username=receiver_username)
    except User.DoesNotExist:
        return Response({'error': 'Receiver does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    if GameInvitation.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
        return Response({'error': 'You have already sent an invitation to this player.'}, status=status.HTTP_400_BAD_REQUEST)

    invitation = GameInvitation.objects.create(sender=sender, receiver=receiver)
    return Response({'message': 'Invitation sent successfully!'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def respond_to_invitation(request, invitation_id):
    user = request.user
    try:
        invitation = GameInvitation.objects.get(id=invitation_id, receiver=user)
    except GameInvitation.DoesNotExist:
        return Response({'error': 'Invitation not found.'}, status=status.HTTP_404_NOT_FOUND)

    response = request.data.get('response')
    if response == 'accept':
        invitation.status = 'accepted'
        invitation.save()
        # Logic to start a game can be added here (integrate with Chess.com API)
        return Response({'message': 'Invitation accepted! Game starting soon.'}, status=status.HTTP_200_OK)
    elif response == 'reject':
        invitation.status = 'rejected'
        invitation.save()
        return Response({'message': 'Invitation rejected.'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid response.'}, status=status.HTTP_400_BAD_REQUEST)

def chess_home(request):
    return render(request, 'chess/home.html')