def filter_events_by_location(events, location):
    return [
        event for event in events
        if location.casefold() in event["location"].casefold()
    ]


def filter_events_by_title(events, title):
    return [
        event for event in events
        if title.casefold() in event["title"].casefold()
    ]


def has_available_capacity(current_count, max_capacity):
    return current_count < max_capacity


def check_duplicate_registration(registered_ids, new_id):
    if new_id in registered_ids:
        raise ValueError("Participant already registered")

    return True