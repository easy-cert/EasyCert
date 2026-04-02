def notifications_processor(request):
    """
    Injects the user's latest notifications into templates globally.
    Shows all unread count, but the list shows a mix of the 10 latest (unread + read).
    """
    if request.user.is_authenticated:
        from apps.accounts.models import Notification
        # Full count for the red badge
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        # Latest 10 notifications for the dropdown list (both read and unread)
        latest_notifs = Notification.objects.filter(user=request.user).order_by("-timestamp")[:10]
        
        return {
            'my_notifications': latest_notifs,
            'unread_notifications_count': unread_count
        }
    return {
        'my_notifications': [],
        'unread_notifications_count': 0
    }
