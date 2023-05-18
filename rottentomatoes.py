from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime


def legible_numbers(num):
    if num < 1000:
        return num
    else:
        mults = [0.001, 'K'] if num <= 1000000 else [0.000001, 'M']
        rounded = round(num*mults[0])
        return '${}{}'.format(rounded, mults[1])


def work_with_rt(actor_name_list):
    try:
        rt_name = '_'.join(actor_name_list)
        rt_url = f'https://www.rottentomatoes.com/celebrity/{rt_name}'
        rt_page = requests.get(rt_url)
        rt_page.raise_for_status()
    except requests.exceptions.HTTPError:
        return False
    else:
        rt_doc = BeautifulSoup(rt_page.text, 'html.parser')
        rt_table = rt_doc.find('tbody', class_='celebrity-filmography__tbody').find_all('tr')
        return rt_table


def get_info_from_wiki(actor_name_list):
    wiki_name = '_'.join(actor_name_list).title()
    wiki_url = f'https://en.wikipedia.org/wiki/{wiki_name}'
    wiki_page = requests.get(wiki_url)
    wiki_doc = BeautifulSoup(wiki_page.text, 'html.parser')
    wiki_table_bio = wiki_doc.find('table', class_='infobox biography vcard').find_all('tr')
    wiki_birth_year = wiki_doc.find('span', class_='bday').text[:4]
    wiki_dead = True if wiki_table_bio[3].th.text == 'Died' else False
    year_of_death = False
    if wiki_dead:
        year_of_death = int(wiki_table_bio[3].find('td', class_='infobox-data').find('span').text[1:5])
    actress_or_actor = wiki_doc.find('td', class_='infobox-data role').text.lower()
    pronouns = ['he', 'his', 'actor'] if 'actor' in actress_or_actor else ['she', 'her', 'actress']
    return wiki_dead, year_of_death, pronouns


def create_pandas(rt_table):
    allinfo = {}
    for item in rt_table:
        allinfo.setdefault('title', []).append(item['data-title'])
        allinfo.setdefault('year', []).append(int(item['data-year']))
        score_nums = 0 if item['data-audiencescore'] == '0' else int(item['data-audiencescore'])
        allinfo.setdefault('score', []).append(score_nums)
        box_office_nums = 0 if not item['data-boxoffice'] else int(item['data-boxoffice'])
        allinfo.setdefault('box office', []).append(box_office_nums)
    pandas_table = pd.DataFrame(allinfo)
    pandas_table.index += 1
    return pandas_table


def analyze_table(pandas_table):
    # find the total amount of the movies
    total_movies = pandas_table.index[-1]
    print("There are totally {} movies in {}'s filmography.".format(total_movies, actor_name))


    # get length of the career, considering the actor is dead or alive
    end_year = datetime.now().year
    set_of_years = set(pandas_table['year'].values.tolist())

    if wiki_dead:
        end_year = year_of_death
        set_of_years = set(pandas_table[pandas_table['year'] <= end_year]['year'].values.tolist())
        last_movie_during_life = pandas_table[pandas_table['year'] <= end_year].sort_values(by=['year']).iloc[-1, 1]

    debut_year = pandas_table.iloc[-1, 1]
    career_length = end_year - debut_year if not wiki_dead else last_movie_during_life - debut_year
    all_years = set([x for x in range(debut_year, end_year+1)])

    print('{} debut was in {}'.format(pronouns[1].title(), debut_year), end=' ')
    if wiki_dead:
        print('and {} last lifetime movie was released in {}'.format(pronouns[1], last_movie_during_life), end=' ')
    lasts_or_lasted = 'lasted' if wiki_dead else 'lasts'
    print('which means {} career {} for {} years.'.format(pronouns[1], lasts_or_lasted, career_length))


    # find the average amount of the movies
    average_amount_movies = round(total_movies / career_length, 1)
    print('{} averaged {} movie per year.'.format(pronouns[0].title(), average_amount_movies))

    # find all of the years there were no premieres of the movies with the actor (show them if len less than 5)
    no_premiere_years = set_of_years ^ all_years
    str_no_premiere = ', '.join(str(v) for v in no_premiere_years)
    if len(no_premiere_years) < 6:
        print('Only in {} no movies with the {} were released.'.format(str_no_premiere, pronouns[2]))


    # find the average value of the actor's movie score
    filt_score = pandas_table[pandas_table['score'] != 0]
    print('The simple average score of all the movies with known score the {} was cast is {} out of 100.'.format(pronouns[2], int(pandas_table['score'].sum()/filt_score['score'].count())))


    # find all of the highest values in a 'score' column
    highest_score = filt_score[filt_score['score'] == filt_score['score'].max()].sort_values(by=['year'])
    highest_score_list = highest_score.values.tolist()
    if len(highest_score_list) == 1:
        print("The highest rated movie is '{}' ({})".format(highest_score_list[0][0], highest_score_list[0][1]), end='')
    else:
        highest_score_movies = ''
        for i in range(0, len(highest_score_list)):
            highest_score_movies += "'" + highest_score_list[i][0] + "' (" + str(highest_score_list[i][1]) + ')' + ', '
        print("Highest rated movies are", highest_score_movies.rstrip(', '), end='')
    print(' - {}% of users rated it positively.'.format(highest_score_list[0][2]))


    # show all of the movie titles with the score > 85 except the one/s with the highest value
    higher85_score = filt_score[(filt_score['score'] >= 85) & (filt_score['score'] != filt_score['score'].max())].sort_values(by=['score'], ascending=False)
    amount_higher85 = higher85_score.title.count()
    is_or_are = 'is' if amount_higher85 == 1 else 'are'
    sg_or_pl = '' if amount_higher85 == 1 else 's'
    if amount_higher85 > 0:
        higher85_score_list = higher85_score[['title', 'year', 'score']].values.tolist()
        print('There {} {} more high-rated (85% or more) movie{}:'.format(is_or_are, higher85_score.title.count(), sg_or_pl), end = ' ')
        list_amount_higher85 = ''
        for i in range(0, len(higher85_score_list)):
            list_amount_higher85 += "'" + higher85_score_list[i][0] + "' (" + str(higher85_score_list[i][1]) + ") - " + str(higher85_score_list[i][2]) + "%, "
        print(list_amount_higher85.rstrip(', '), end='.')
    else:
        print('There are no other movies rated higher than 85% score.')


    # find all of the lowest values in a 'score' column
    lowest_score = filt_score[filt_score['score'] == filt_score['score'].min()]
    lowest_score_list = lowest_score.values.tolist()
    if len(lowest_score_list) == 1:
        print("\nLowest rated movie is '{}' ({})".format(lowest_score_list[0][0], lowest_score_list[0][1]), end='')
    else:
        lowest_score_movies = ''
        for i in range(0, len(lowest_score_list)):
            lowest_score_movies += "'" + lowest_score_list[i][0] + "' (" + str(lowest_score_list[i][1]) + ')' + ', '
        print("Lowest rated movies are", lowest_score_movies.rstrip(', '), end='')
    print(' - only {}% of users rated it positively.'.format(lowest_score_list[0][2]))


    # find all of the highest values in a 'box office' column
    filt_bo = pandas_table[pandas_table['box office'] != 0]
    highest_bo = filt_bo[filt_bo['box office'] == filt_bo['box office'].max()]
    highest_bo_list = highest_bo.values.tolist()
    if len(highest_bo_list) == 1:
        print("'{}' ({}) is the {}'s most fiscally fruitful film. It".format(highest_bo_list[0][0], highest_bo_list[0][1], pronouns[2]), end='')
    else:
        highest_bo_movies = ''
        for i in range(len(highest_bo_list)):
            highest_bo_movies += f"'{highest_bo_list[i][0]}' ({highest_bo_list[i][1]}),"
        print(highest_bo_movies.rstrip(', '), f"are the {pronouns[2]}'s most fiscally fruitful films. They ", end='')
    print(' grossed {} worldwide.'.format(legible_numbers(highest_bo_list[0][3])))


    # find all of the lowest values in a 'box office' column
    times_less = round(filt_bo['box office'].max() / filt_bo['box office'].min())
    if times_less > 1:
        print('On the contrary, ', end='')
        lowest_bo = filt_bo[filt_bo['box office'] == filt_bo['box office'].min()]
        lowest_bo_list = lowest_bo.values.tolist()
        if len(lowest_bo_list) == 1:
            print("'{}' ({})".format(lowest_bo_list[0][0], lowest_bo_list[0][1]), end='')
        else:
            lowest_bo_movies = ''
            for i in range(0, len(lowest_bo_list)):
                lowest_bo_movies += "'" + lowest_bo_list[i][0] + "' (" + str(lowest_bo_list[i][1]) + ')' + ', '
            print(lowest_bo_movies.rstrip(', '), end='')
        print(' earned just {} - {} times less!'.format(legible_numbers(lowest_bo_list[0][3]), times_less))


    # find all of the highest amounts of elements in the 'year' groups
    grouped_years = pandas_table.groupby('year')
    most_premieres = grouped_years.filter(lambda x: len(x) == grouped_years.size().max()).groupby('year').year.count()
    print('In', end=' ')
    for item in most_premieres.index:
        print(item, ', ', sep='', end='')
    print('we could see the {} more often than usual - there were {} premieres of the movies with {} starring.'.format(pronouns[2], most_premieres.values[0], actor_name))


status = False
while not status:
    input_actor = input('Please enter the name of the actor/actress you want to know more about: ')
    actor_name_list = [x.lower() for x in input_actor.split()]
    if work_with_rt(actor_name_list):
        status = True
    else:
        print("1I've never heard of this person. Please try again.")
        continue
    actor_name = ' '.join(actor_name_list).title()
    rt_table = work_with_rt(actor_name_list)


wiki_dead, year_of_death, pronouns = get_info_from_wiki(actor_name_list)
pandas_table = create_pandas(rt_table)
info = analyze_table(pandas_table)

print()
answer = ''
while answer not in ('y', 'n'):
    answer = input('Do you want a csv file with the filmography? Type Y for Yes / N for No: ').lower()
    if answer == 'y':
        pandas_table.to_csv(f"{'_'.join(actor_name_list)}_filmography.csv")
    elif answer == 'n':
        print('Ok, bye!')
    else:
        print('Wrong input. Please type Y or N: ')

# и сравнить даты рождения в википедии и роттен томатос
#rt_birth_year = rt_doc.find(attrs={'class': 'celebrity-bio__item', 'data-qa': 'celebrity-bio-bday'}).get_text(strip=True)[-4:]
# global and local
# функция в функции