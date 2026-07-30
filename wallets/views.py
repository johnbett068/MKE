from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from .models import Wallet
from .serializers import WalletSerializer, TransactionSerializer


class MyWalletsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallets = Wallet.objects.filter(account=request.user)
        serializer = WalletSerializer(wallets, many=True)
        return Response(serializer.data)


class WalletTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, wallet_id):
        wallet = get_object_or_404(Wallet, id=wallet_id, account=request.user)
        transactions = wallet.transactions.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
