from datetime import date, timedelta


def sm2(ease_factor: float, interval: int, rating: int) -> tuple[float, int, date]:
    """
    SM-2 spaced repetition algorithm.
    
    Args:
        ease_factor: current ease factor (starts at 2.5)
        interval: current interval in days
        rating: user's rating 0-5 (0-2 = forgot, 3-5 = remembered)
    
    Returns:
        new_ease_factor, new_interval, next_review_date
    """
    # If user forgets card then reset interval to 1 day and keep ease factor the same
    if rating < 3:
        new_interval = 1
        new_ease_factor = ease_factor
    # otherwise if user remembers card then calculate new interval and ease factor based on rating
    else:
        if interval == 1:
            new_interval = 6
        elif interval == 6:
            new_interval = round(interval * ease_factor)
        else:
            new_interval = round(interval * ease_factor)

        new_ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        new_ease_factor = max(1.3, new_ease_factor)

    next_review = date.today() + timedelta(days=new_interval)

    return new_ease_factor, new_interval, next_review