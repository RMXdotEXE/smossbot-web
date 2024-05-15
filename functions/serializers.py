from rest_framework import serializers
from .models import ChannelPointReward


class ChannelPointRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelPointReward
        fields = ['reward_id', 'user', 'reward_title', 'color', 'image', 'bot_created', 'binded_to']