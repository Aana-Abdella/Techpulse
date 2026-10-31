def is_technology_news(title):
    keywords = ["AI", "Python", "Linux", "software"]

    return any(
        keyword.lower() in title.lower()
        for keyword in keywords
    )