from rest_framework_simplejwt.views import TokenObtainPairView

from ..token_serializers import (
    GamiTokenObtainPairSerializer
)


class GamiTokenObtainPairView(TokenObtainPairView):

    serializer_class = GamiTokenObtainPairSerializer