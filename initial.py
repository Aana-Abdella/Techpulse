def clean_title(title):
    return title.strip()


def is_technology_news(title):
    keywords = ["AI", "Python", "Linux", "software"]

    for keyword in keywords:
        if keyword.lower() in title.lower():
            return True

    return False