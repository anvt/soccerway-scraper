from datetime import datetime

import requests
from bs4 import BeautifulSoup


def scrape_match(url_path):
    """
    Create soup and scrape match data.
    :param url_path: Soccerway URL path for match.
    :return: Dictionary containing match data
    """
    response = requests.get("https://us.soccerway.com" + url_path)
    soup = BeautifulSoup(response.text, "html.parser")

    game_data = {
        "week": game_week(soup),
        "date": date(soup),
        "home_team": team_names(soup)[0],
        "away_team": team_names(soup)[1],
        "referee": referee(soup),
        "home_goal_total": len(home_goals(soup)),
        "away_goal_total": len(away_goals(soup)),
        "home_goal_times": home_goals(soup),
        "away_goal_times": away_goals(soup),
        "home_yellow_times": home_yellow_cards(soup),
        "away_yellow_times": away_yellow_cards(soup),
        "home_red_times": home_red_cards(soup),
        "away_red_times": away_red_cards(soup),
    }

    # Add corners, fouls etc
    game_data.update(scrape_iframe(soup))

    return game_data


def game_week(match_soup):
    week_elem = match_soup.find(text="Game week")
    if week_elem:
        return int(week_elem.find_next("dd").text)
    return None


def date(match_soup):
    page_title = match_soup.title.text
    date_string = page_title.split(" - ")[1]
    datetime_object = datetime.strptime(date_string, "%d %B %Y").date()
    return datetime_object


def team_names(match_soup):
    page_title = match_soup.title.text
    teams = page_title.split(" - ")[0]
    home = teams.split("vs.")[0].strip()
    away = teams.split("vs.")[1].strip()
    return home, away


def referee(match_soup):
    referee_elem = match_soup.find(text="Referee:")
    if referee_elem:
        return referee_elem.find_next("dd").text
    return None


def clean_string(time):
    time = str(time.text)
    if "+" in time:
        return int(time.split("+")[0].replace("'", ""))
    return int(time[:-1])


def home_goals(match_soup):
    goal_times = []
    for goal in match_soup.select(".player.player-a .minute"):
        goal_time = clean_string(goal)
        if goal_time <= 90:
            goal_times.append(goal_time)
    return goal_times


def away_goals(match_soup):
    goal_times = []
    for goal in match_soup.select(".player.player-b .minute"):
        goal_time = clean_string(goal)
        if goal_time <= 90:
            goal_times.append(goal_time)
    return goal_times


def home_red_cards(match_soup):
    red_times = []

    for card in match_soup.select("div.container.left span"):
        if "events/RC.png" in str(card) or "events/Y2C.png" in str(card):
            red_time = clean_string(card)
            if red_time <= 90:
                red_times.append(red_time)
    return sorted(red_times)


def home_yellow_cards(match_soup):
    yellow_times = []

    for card in match_soup.select("div.container.left span"):
        if "events/YC.png" in str(card):
            yellow_time = clean_string(card)
            if yellow_time <= 90:
                yellow_times.append(yellow_time)
    return sorted(yellow_times)


def away_yellow_cards(match_soup):
    yellow_times = []

    for card in match_soup.select("div.container.right span"):
        if "events/YC.png" in str(card):
            yellow_time = clean_string(card)
            if yellow_time <= 90:
                yellow_times.append(yellow_time)
    return sorted(yellow_times)


def away_red_cards(match_soup):
    red_times = []

    for card in match_soup.select("div.container.right span"):
        if "events/RC.png" in str(card) or "events/Y2C.png" in str(card):
            red_time = clean_string(card)
            if red_time <= 90:
                red_times.append(red_time)
    return sorted(red_times)


def scrape_iframe(match_soup):
    match_stats = []
    for elem in match_soup.find_all("iframe"):
        if elem["src"].startswith("/charts"):
            iframe_url = "https://www.soccerway.com" + elem["src"]
            response = requests.get(iframe_url)
            iframe_soup = BeautifulSoup(response.text, "html.parser")
            for stat in iframe_soup.select(".legend"):
                if "title" not in stat.attrs["class"]:
                    try:
                        match_stats.append(int(stat.text))
                    except ValueError:
                        break

    keys = (
        "home_corners",
        "away_corners",
        "home_shots_on",
        "away_shots_on",
        "home_shots_wide",
        "away_shots_wide",
        "home_fouls",
        "away_fouls",
        "home_offsides",
        "away_offsides",
    )

    if len(match_stats) == 10:
        return dict(zip(keys, match_stats))
    else:
        return dict.fromkeys(keys, None)
