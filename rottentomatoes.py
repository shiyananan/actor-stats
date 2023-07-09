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
        return f'${rounded}{mults[1]}'


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
    print(f"There are totally {total_movies} movies in {actor_name}'s filmography.")


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

    print(f'{pronouns[1].title()} debut was in {debut_year}', end=' ')
    if wiki_dead:
        print(f'and {pronouns[1]} last lifetime movie was released in {last_movie_during_life}', end=' ')
    lasts_or_lasted = 'lasted' if wiki_dead else 'lasts'
    print(f'which means {pronouns[1]} career {lasts_or_lasted} for {career_length} years.')


    # find the average amount of the movies
    average_amount_movies = round(total_movies / career_length, 1)
    print(f'{pronouns[0].title()} averaged {average_amount_movies} movie per year.')

    # find all of the years there were no premieres of the movies with the actor (show them if len less than 5)
    no_premiere_years = set_of_years ^ all_years
    str_no_premiere = ', '.join(str(v) for v in no_premiere_years)
    if len(no_premiere_years) < 6:
        print(f'Only in {str_no_premiere} no movies with the {pronouns[2]} were released.')


    # find the average value of the actor's movie score
    filt_score = pandas_table[pandas_table['score'] != 0]
    av_score = int(pandas_table['score'].sum()/filt_score['score'].count())
    print(f'The simple average score of all the movies with known score the {pronouns[2]} was cast is {av_score} out of 100.')


    # find all of the highest values in a 'score' column
    highest_score = filt_score[filt_score['score'] == filt_score['score'].max()].sort_values(by=['year'])
    highest_score_list = highest_score.values.tolist()
    if len(highest_score_list) == 1:
        print(f"The highest rated movie is '{highest_score_list[0][0]}' ({highest_score_list[0][1]})", end='')
    else:
        highest_score_movies = ''
        for i in range(0, len(highest_score_list)):
            highest_score_movies += "'" + highest_score_list[i][0] + "' (" + str(highest_score_list[i][1]) + ')' + ', '
        print("Highest rated movies are", highest_score_movies.rstrip(', '), end='')
    print(f' - {highest_score_list[0][2]}% of users rated it positively.')


    # show all of the movie titles with the score > 85 except the one/s with the highest value
    higher85_score = filt_score[(filt_score['score'] >= 85) & (filt_score['score'] != filt_score['score'].max())].sort_values(by=['score'], ascending=False)
    amount_higher85 = higher85_score.title.count()
    is_or_are = 'is' if amount_higher85 == 1 else 'are'
    sg_or_pl = '' if amount_higher85 == 1 else 's'
    if amount_higher85 > 0:
        higher85_score_list = higher85_score[['title', 'year', 'score']].values.tolist()
        print(f'There {is_or_are} {higher85_score.title.count()} more high-rated (85% or more) movie{sg_or_pl}:', end = ' ')
        list_amount_higher85 = ''
        for i in range(0, len(higher85_score_list)):
            list_amount_higher85 += f"'{higher85_score_list[i][0]}' ({str(higher85_score_list[i][1])}) - {str(higher85_score_list[i][2])}%, "
        print(list_amount_higher85.rstrip(', '), end='.')
    else:
        print('There are no other movies rated higher than 85% score.')


    # find all of the lowest values in a 'score' column
    lowest_score = filt_score[filt_score['score'] == filt_score['score'].min()]
    lowest_score_list = lowest_score.values.tolist()
    if len(lowest_score_list) == 1:
        print(f"\nLowest rated movie is '{lowest_score_list[0][0]}' ({lowest_score_list[0][1]})", end='')
    else:
        lowest_score_movies = ''
        for i in range(0, len(lowest_score_list)):
            lowest_score_movies += "'" + lowest_score_list[i][0] + "' (" + str(lowest_score_list[i][1]) + ')' + ', '
        print("Lowest rated movies are", lowest_score_movies.rstrip(', '), end='')
    print(f' - only {lowest_score_list[0][2]}% of users rated it positively.')


    # find all of the highest values in a 'box office' column
    filt_bo = pandas_table[pandas_table['box office'] != 0]
    highest_bo = filt_bo[filt_bo['box office'] == filt_bo['box office'].max()]
    highest_bo_list = highest_bo.values.tolist()
    if len(highest_bo_list) == 1:
        print(f"'{highest_bo_list[0][0]}' ({highest_bo_list[0][1]}) is the {pronouns[2]}'s most fiscally fruitful film. It", end='')
    else:
        highest_bo_movies = ''
        for i in range(len(highest_bo_list)):
            highest_bo_movies += f"'{highest_bo_list[i][0]}' ({highest_bo_list[i][1]}),"
        print(highest_bo_movies.rstrip(', '), f"are the {pronouns[2]}'s most fiscally fruitful films. They ", end='')
    print(f' grossed {legible_numbers(highest_bo_list[0][3])} worldwide.')


    # find all of the lowest values in a 'box office' column
    times_less = round(filt_bo['box office'].max() / filt_bo['box office'].min())
    if times_less > 1:
        print('On the contrary, ', end='')
        lowest_bo = filt_bo[filt_bo['box office'] == filt_bo['box office'].min()]
        lowest_bo_list = lowest_bo.values.tolist()
        if len(lowest_bo_list) == 1:
            print(f"'{lowest_bo_list[0][0]}' ({lowest_bo_list[0][1]})", end='')
        else:
            lowest_bo_movies = ''
            for i in range(len(lowest_bo_list)):
                lowest_bo_movies += f"'{lowest_bo_list[i][0]}' ({lowest_bo_list[i][1]}), "
            print(lowest_bo_movies.rstrip(', '), end='')
        print(f' earned just {legible_numbers(lowest_bo_list[0][3])} - {times_less} times less!')


    # find all of the highest amounts of elements in the 'year' groups
    grouped_years = pandas_table.groupby('year')
    most_premieres = grouped_years.filter(lambda x: len(x) == grouped_years.size().max()).groupby('year').year.count()
    print('In', end=' ')
    for item in most_premieres.index:
        print(item, ', ', sep='', end='')
    print(f'we could see the {pronouns[2]} more often than usual - there were {most_premieres.values[0]} premieres of the movies with {actor_name} starring.')


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