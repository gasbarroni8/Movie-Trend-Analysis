from apikeys import TMDB_KEY
from datetime import datetime
from bokeh.plotting import figure, output_file, show
from bokeh.models import Title
import requests
import calendar
import datetime
from collections import OrderedDict


def last_day_of_month(any_day):
    """Takes in a date value and returns the last day for that particular month.
    Input: Any date value"""
    next_month = any_day.replace(day = 28) + datetime.timedelta(days = 4)
    return next_month - datetime.timedelta(days = next_month.day)


def releasecount_bygenre(genre_id, start_date, end_date):
    """Counts and returns the total number of Releases occurred between a start date and an end date for a particular genre.
    Input: Genre_ID, Start date and End Date"""
    resource_uri = "https://api.themoviedb.org/3/discover/movie"
    query_params = {'api_key': TMDB_KEY, 'language': 'en-US', 'primary_release_date.gte': start_date,
                    'primary_release_date.lte': end_date, 'with_genres': genre_id}
    print(".", flush=True, end=" ")
    response = requests.get(resource_uri, params=query_params)
    movie_dict = response.json()
    return movie_dict['total_results']


def get_genrecountlist(genre_list,year):
    """Takes the user provided genre list and a year and returns a list of Genres with release count
    for each month of the year.
    Input:Genre list(Names in list format) ,Year"""
    print("Sit back and relax till we get your output!",flush = True)
    resource_uri = "https://api.themoviedb.org/3/genre/movie/list"
    query_params = {'api_key': TMDB_KEY, 'language': 'en-US'}
    response = requests.get(resource_uri, params=query_params)
    genre = response.json()
    genres_dict = dict()
    genre_count_list = list()
    for i in genre.values():
        j = 0
        while j < len(i):
            genres_dict[i[j]["id"]] = i[j]['name']
            j += 1
    genre_list = [k for l in genre_list for k,v in genres_dict.items() if v.lower() == l.lower() ]
    for v in genre_list:
        d = dict()
        d1 = dict()
        for month in range(1, 13):
            sdate = str(year)+'-' + str(month) + '-01'  # Set sdate as 1st day of the month
            edate = last_day_of_month(datetime.date(year, month, 1))  # Set edate as the last date of the month
            d1[calendar.month_abbr[month]] = releasecount_bygenre(v,sdate,edate)
        d = {genres_dict[v]: d1}
        genre_count_list.append(d)
    return genre_count_list


def plot_graph(genre_list,year):
    """Plot a multi-line graph for a Genrelist returned from GetGenreRecordCount function. Uses year variable for the label."""
    col_count = 1  # A variable to count the genres and assign colors accordingly.
    color_pal = {1:"red",2:"blue",3:"green",4:"pink",5:"orange"} # A predefined color palette for 5 Genres.
    # output to static HTML file
    output_file("genre_by_season.html")
    # create a new plot with a title and axis labels
    p = figure(title = "Releases by Genre - " + str(year) , x_axis_label = 'Month', y_axis_label = 'Releases',
    x_range = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    print("We are Done!", flush=True)
    for rec in genre_list:  # For each record in Genre_List
        for k, v in rec.items():  # For key and values in rec distionary
            leg = k                 # Set legend as the Genre in leg variable
            x = list()
            y = list()
            for k, v in v.items():
                x.append(k)
                y.append(v)
            p.line(x, y, legend = leg, line_width = 2, line_color=color_pal[col_count])
            col_count += 1
    show(p)


def get_person_id(str):
    """This function takes in Person's Name as input and returns the actors ID from the TMDB"""
    person_search_url = "https://api.themoviedb.org/3/search/person"
    query_params = {'api_key': TMDB_KEY, 'query': str}
    response = requests.get(person_search_url, params=query_params)
    person = response.json()
    if person['total_results'] == 0:
        return -1
    else:
        person_id = person['results'][0]['id']
        return person_id


def get_person_movies(p_id, job):
    """This function takes Person ID as input and computes his/her popularity in his career
    The Popularity is calculated by summing up the popularity of individual movies of the person in a calender year.
    The popularity metric for each individual movie the person features in, is extracted from the TMDB"""
    credit_url = "http://api.themoviedb.org/3/person/" + str(p_id) + "/movie_credits"
    query_params = {'api_key': TMDB_KEY}
    response = requests.get(credit_url, params=query_params)
    #Get all the movies the person has starred in
    movie_credits = response.json()
    popu_dict = dict()
    if job == 'Actor':
        if movie_credits['cast'] == []:
            return -1
        else:
            for c in movie_credits['cast']:
                if 'release_date' in c and c['release_date'] != '' and c['release_date'] < '2018-01-1':
                    release_date = c['release_date'].split('-')
                    if release_date[0] in list(popu_dict.keys()):
                        popu_dict[release_date[0]] += c['popularity']
                    else:
                        popu_dict[release_date[0]] = c['popularity']
    #For Crew Jobs (Director/Producer/Writer)
    else:
        if movie_credits['crew'] == []:
            return -1
        else:
            for c in movie_credits['crew']:
                if 'release_date' in c and c['release_date'] != '' and c['release_date'] < '2018-01-1' and c['job'] == job:
                    release_date = c['release_date'].split('-')
                    if release_date[0] in list(popu_dict.keys()):
                        popu_dict[release_date[0]] += c['popularity']
                    else:
                        popu_dict[release_date[0]] = c['popularity']
    return popu_dict


def dict_sort(in_d):
    """This Function takes an unsorted dictionary and returns a sorted one."""
    d = OrderedDict(sorted(in_d.items()))
    return d


def bokeh_plot(d, name, opt):
    """This function takes a dictionary, a Name(a string) and job title as input for the line chart"""
    x = list(d.keys())
    y = list(d.values())
    output_file("popularity_trend.html")
    p = figure(width=800, x_axis_label='Year', y_axis_label='Popularity Score of '+ opt)
    p.title.text = name + "'s Popularity Over Time as a " + opt
    p.line(x, y, legend="Popularity Trend", line_width=2)
    p.add_layout(Title(text="Note: Popularity Score is the sum of popularity scores of the "+ opt +"'s movie "
                       "releases in a calender year", align="left"), "below")
    print("Chart is Ready!")
    show(p)


def main():
    print("#---------------Hello! Welcome to the Most Advanced Movie Analytics Tool--------------#\n")
    a_type = int(input("To get started, please select an analysis you'd like to perform:\n"
                       " 1. Release Trend by Genre\n 2. Actor's Popularity\n[Enter 1 or 2]: "))
    #Analysis 1: Genre Releases
    if a_type == 1:
        print('Action        Adventure     Animation     Comedy      Crime') 
        print('Documentary   Drama         Family        Fantasy     History') 
        print('Horror        Music         Mystery       Romance     Science Fiction') 
        print('TV Movie      Thriller      War           Western','\n')
        ip_list =  input('Please provide at most 5 Genres separated by a comma(,) that you want to analyze: \n')
        ip_year = int(input("Which Year would you want to analyze?"))
        ip_list = [value.strip() for value in ip_list.split(',')][:5]  #Reduce the list to top 5 values
        plot_graph(get_genrecountlist(ip_list,ip_year),ip_year)
    elif a_type == 2:
        #Analysis 2: Popularity
        job_dict = {'1': 'Actor', '2': 'Director', '3': 'Producer', '4': 'Writer'}
        opt = input("Please select ONE search criteria 1.Actor  2.Director  3.Producer  4.Writer [Enter (1-4]] ")
        if opt not in job_dict.keys():
            print('INVALID OPTION SELECTED!')
            exit(0)
        opt = job_dict[opt]
        name = input("Enter Name of " + opt + ": ")
        person_id = get_person_id(name)
        if person_id == -1:
            print("Person's record does NOT exist!")
        else:
            person_movies = get_person_movies(person_id, opt)
            if person_movies == -1:
                print(opt + ' has not been credited in any movie yet!')
            else:
                bokeh_plot(dict_sort(person_movies), name, opt)
    else:
        print('INVALID OPTION SELECTED! Please run again with proper options.')
        exit(0)

if __name__ == '__main__':  
    main()