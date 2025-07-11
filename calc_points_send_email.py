import csv
import matplotlib.pyplot as plt
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# read the picks of each player from a csv file and return a dictionary with everyone's picks
def read_picks_from_csv(filename):
    picks = {}

    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            # the first item in the row list is used as the key
            # and the rest of the items in the row are used as the value
            picks[row[0]] = row[1:]

    return picks


# read the winners of each competition from a csv file and return the appropriate lists, dictionaries and strings
def read_winners_from_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)

    hoh_winners = [x for x in data[0][1:] if x != '']
    veto_winners = [x for x in data[1][1:] if x != '']
    off_block = [x for x in data[2][1:] if x != ''] 
    other_comp_winners_raw = [x for x in data[3][1:] if x != '']
    evictions = [x for x in data[4][1:] if x != ''] 
    
    # parse didnt_lose dictionary
    other_comp_winners = {int(other_comp_winners_raw[i]): (other_comp_winners_raw[i+1]) for i in range(0, len(other_comp_winners_raw), 2) if other_comp_winners_raw[i].isdigit()}
    
    # parse the buy_back dictionary
    buy_back_raw = [x for x in data[5][1:] if x != ''] 
    buy_back = {int(buy_back_raw[i]): (buy_back_raw[i+1]) for i in range(0, len(buy_back_raw), 2) if buy_back_raw[i].isdigit()}

    americas_favorite = data[6][1] 
    
    return hoh_winners, veto_winners, off_block, other_comp_winners, evictions, buy_back, americas_favorite


# calculate the points of the competition given the competion winners and each person's picks
def calc_points(hoh_winners=list, veto_winners=list, off_block=list, other_comp_winners=list, evictions=list, americas_favorite=str, buy_back=dict, picks=dict):

    # initialize scores
    # the plus one after len(hoh_winners) was added because of a twist regarding two vetos in one week, delete after bb25
    weekly_scores = {player: [0] * (len(hoh_winners) + 1) for player in picks.keys()}
    total_scores = {player: 0 for player in picks.keys()}
    number_of_players = 17
    # iterate through all players in the game
    for player in picks:

        # iterate through hoh_winners
        for index_of_winner in range(len(hoh_winners)):
            # iterate through players ranking
            for ranking in range(len(picks[player])):
                # add points according to ranking
                if picks[player][ranking] == hoh_winners[index_of_winner]:
                    weekly_scores[player][index_of_winner] += 10 - ranking

        # iterate through veto_winners
        for index_of_winner in range(len(veto_winners)):
            # iterate through players ranking
            for ranking in range(len(picks[player])):
                # add points according to ranking
                if picks[player][ranking] == veto_winners[index_of_winner]:
                    weekly_scores[player][index_of_winner] += 10 - ranking

        # iterate through veto_winners
        for index_of_winner in range(len(off_block)):
            # iterate through players ranking
            for ranking in range(len(picks[player])):
                # add points according to ranking
                if picks[player][ranking] == off_block[index_of_winner]:
                    weekly_scores[player][index_of_winner] += 7.5 - (ranking * 0.75)

        # iterate through other_comp_winners
        for week, winner in other_comp_winners.items():
            # iterate through players ranking
            for ranking in range(len(picks[player])):
                # add points according to ranking to the appropriate week
                if picks[player][ranking] == winner:
                    weekly_scores[player][week] += 5 - (ranking * 0.5)

        # iterate through buy_back
        for week, winner in buy_back.items():
            # iterate through players ranking
            for ranking in range(len(picks[player])):
                # add points according to ranking to the appropriate week
                if picks[player][ranking] == winner:
                    weekly_scores[player][week] += 10 - ranking
        
        # at the end of the game
        if len(evictions) == number_of_players + len(buy_back): # add one to 16 if there was a buy-back because that person will be evicted twice
            # see if the eviction list exactly matches someone's guesses and award a bonus
            if picks[player] == evictions[::-1]:
                weekly_scores[player][-1] += 100

            # give bonus for americas favorite
            if picks[player][0] == americas_favorite:
                weekly_scores[player][-1] += 75
            elif picks[player][1] == americas_favorite:
                weekly_scores[player][-1] += 50
            elif picks[player][2] == americas_favorite:
                weekly_scores[player][-1] += 25
            # penalize if americas favorite was in last three spots
            elif picks[player][-1] == americas_favorite:
                weekly_scores[player][-1] -= 50
            elif picks[player][-2] == americas_favorite:
                weekly_scores[player][-1] -= 25
            elif picks[player][-3] == americas_favorite:
                weekly_scores[player][-1] -= 10
            
            # give bonus to winner
            if picks[player][0] == evictions[-1]:
                weekly_scores[player][-1] += 100
            elif picks[player][1] == evictions[-1]:
                weekly_scores[player][-1] += 75
            elif picks[player][2] == evictions[-1]:
                weekly_scores[player][-1] += 50
            # penalize if winner was in last three spots
            elif picks[player][-1] == evictions[-1]:
                weekly_scores[player][-1] -= 75
            elif picks[player][-2] == evictions[-1]:
                weekly_scores[player][-1] -= 50
            elif picks[player][-3] == evictions[-1]:
                weekly_scores[player][-1] -= 25
            

            # give bonus to runner up
            if picks[player][0] == evictions[-2]:
                weekly_scores[player][-1] += 75
            elif picks[player][1] == evictions[-2]:
                weekly_scores[player][-1] += 50
            elif picks[player][2] == evictions[-2]:
                weekly_scores[player][-1] += 25
            # penalize if runner up was in last three spots
            elif picks[player][-1] == evictions[-2]:
                weekly_scores[player][-1] -= 50
            elif picks[player][-2] == evictions[-2]:
                weekly_scores[player][-1] -= 25
            elif picks[player][-3] == evictions[-2]:
                weekly_scores[player][-1] -= 10
            
            
            # give bonus to third
            if picks[player][0] == evictions[-3]:
                weekly_scores[player][-1] += 50
            elif picks[player][1] == evictions[-3]:
                weekly_scores[player][-1] += 25
            elif picks[player][2] == evictions[-3]:
                weekly_scores[player][-1] += 10
            # penalize if third place was in last three spots
            elif picks[player][-1] == evictions[-3]:
                weekly_scores[player][-1] -= 25
            elif picks[player][-2] == evictions[-3]:
                weekly_scores[player][-1] -= 10
            elif picks[player][-3] == evictions[-3]:
                weekly_scores[player][-1] -= 5

        # add the weekly scores up and set equal to the total scores
        for player_scores in weekly_scores.values():
            total_scores[player] = sum(weekly_scores[player])
    return weekly_scores, total_scores


# write the scores to a csv file
def write_scores_to_csv(filename, total_scores, weekly_scores):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['name', 'total_points', 'week1_points', 'week2_points', 'week3_points', 'week4_points', 'week5_points', 'week6_points', 'week7_points', 'week8_points', 'week9_points', 'week10_points', 'week11_points', 'week12_points', 'week13_points', 'week14_points', 'week15_points', 'week16_points'])
        
        # Loop through each player and their scores
        for player, total_score in total_scores.items():
            # Get the weekly scores for this player
            player_weekly_scores = weekly_scores[player]

            # Write a row for this player with their name, total score and weekly scores
            writer.writerow([player, total_score] + player_weekly_scores)


# plot the total scores to a bar graph
def plot_total_scores(total_scores):
    # sort players by score in descending order
    sorted_scores = {k: v for k, v in sorted(total_scores.items(), key=lambda item: item[1], reverse=True)}

    # create a bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(sorted_scores.keys(), sorted_scores.values(), color='blue')

    # calculate and plot the average score
    average_score = np.mean(list(sorted_scores.values()))
    plt.axhline(y=average_score, color='r', linestyle='-', label=f'Average Score: {average_score:.2f}')

    # plot the x axis
    plt.axhline(y=0, color='black', linestyle='-')

    # add labels and title
    plt.xlabel('Players')
    plt.ylabel('Total Points')
    plt.title('Total Points per Player')
    plt.legend()

    # rotate x-axis labels for visibility
    plt.xticks(rotation=45)

    # save the plot to a file
    plt.savefig('total_scores.png', bbox_inches='tight')


# make a line graph of the cumulative scores over time
def plot_scores_over_time(weekly_scores):
    # set the figure size
    plt.figure(figsize=(12, 6))
    
    # get the list of players
    players = list(weekly_scores.keys())
    
    # for each player, calculate cumulative score and plot it
    for player in players:
        cumulative_score = np.cumsum(weekly_scores[player])
        plt.plot(cumulative_score, label=player)

    # calculate and plot the average score for each week
    weekly_averages = np.mean([weekly_scores[player] for player in players], axis=0)
    cumulative_average = np.cumsum(weekly_averages)
    plt.plot(cumulative_average, label='Average', color='black', linestyle='--')

    # add labels, legend and title
    plt.xlabel('Week')
    plt.ylabel('Cumulative Points')
    plt.legend()
    plt.title('Cumulative Points over Time per Player')

    # save the plot to a file
    plt.savefig('cumulative_scores.png')


# send emails to everyone involved
def send_email_with_attachments(subject, body, to, email, password, files):
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    for file in files:
        attachment = open(file, 'rb')

        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % file)

        msg.attach(part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email, password)
        text = msg.as_string()
        server.sendmail(email, to, text)
        server.quit()
        print('Email sent!')
    except Exception as e:
        print(f'Failed to send email, reason: {e}')

# execute the code
if __name__ == '__main__':
    # get picks from csv file
    csv_picks = read_picks_from_csv('/Users/richie/Documents/git_hub/big_brother/big_brother/data/picks.csv')
    # get winners from csv file
    hoh_winners_csv, veto_winners_csv, off_block_csv, other_comp_winners_csv, evictions_csv, buy_back_csv, americas_favorite_csv  = read_winners_from_csv('/Users/richie/Documents/git_hub/big_brother/big_brother/data/winners.csv')
    # get scores from calc_points function
    weekly_scores, total_scores = calc_points(hoh_winners_csv, veto_winners_csv, off_block_csv, other_comp_winners_csv, evictions_csv,americas_favorite_csv, buy_back_csv,csv_picks)
    # write the scores to the csv file
    write_scores_to_csv('/Users/richie/Documents/git_hub/big_brother/big_brother/data/new_points.csv', total_scores, weekly_scores)
    print('Points have been calculated.')
    # plot the total scores as well as the cumulative weekly scores
    plot_total_scores(total_scores)
    plot_scores_over_time(weekly_scores)
    print('Points have been graphed.')

    '''
    # email the update to everyone in the email list
    files = ['cumulative_scores.png', 'total_scores.png', 'picks.csv', 'points.csv', 'winners.csv']
    subject = "Big Brother 25 Draft"
    body = "Hello everyone and welcome to the final email of the Big Brother 25 Draft! After last night's finale we have our winner, so congratulations to Peggy Shea! Peggy won with 257.25 points, almost double the average amount of points, 133.21! In second was Tia with 226 points, and Shannon came in third with 219.25. I hope to see you all again next year! \n\nPoint Scoring: \n1: Everytime someone wins Head of Houshold you will be awarded points based on the following formula: 10-ranking. Ranking is the order you picked the contestant in with '0' being your favorite player and '15' being your least favorite. \n2: Everytime someone wins The Veto Competition they will be awarded points based on the following formula: 10-ranking. \n3: Everytime someone gets off the block (by any means, whether they were veto holder or not, or if there was a twist) they will be awarded points based off the following formula: 7.5 - 0.75ranking. \n4: Anytime a player wins a competition not otherwise mentioned here they will be awarded points based off the following formula: 5 - 0.5ranking. \n5: In the event a houseguest is evicted from the house, and then returns to play they will be awarded points based on the following formula: 10 - ranking. If the houseguest won a competition to be brought back to the game, points will be awarded for the other competition as well as being brought back to the game. \n6: If you perfectly predict the order in which everyone was evicted in your list, you will be awarded 100 points. \n7:If America's Favorite is your first, second, or third ranked housegust, you will be awarded 75, 50 or 25 points respectively. If they are your sixteenth, fifteenth, or fourteenth choice 50, 25, or 10 points will be subtracted respictively. \n8:If the winner of the game was your first, second, or third ranked houseguest, you will be awarded 100, 75, or 50 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 75, 50, or 25 points will be subtracted respectively. \n9:If the runner-up of the game was your first, second, or third ranked houseguest, you will be awarded 75, 50, or 25 points respectively. If the runner-up of the game was your sixteenth, fifteenth, or fourteenth ranked houseguest, 50, 25, or 10 points will be subtracted respectively.\n10:If the third place houseguest was your first, second, or third ranked houseguest, you will be awarded 50, 25, or 10 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 25, 10, or 5 points will be subtracted respectively. Please note that although the third place houseguest may be known an episode before the winner and runner up, the points for the top three places, America's Favorite, and the perfect line-up will all be awarded at the same time. \nChanges from last year: \n1: You now get a bonus if your list lines up perfectly with the order of evictions. \n2: Now there is only one spot in your list where the housguest will earn you zero points as opposed to in the last few years where only the top six and bottom four positions would add/subtract points.\n3: Getting taken off the block is worth slightly less points. \n4: You can now earn points and have points subtracted from an evicted houseguest getting back into the game.\n5:America's Favorite is now worth slightly more points.  \n\nThanks everyone for playing! \nRichard Lavey "
    to = ["liste emails here"] 
    email = 'redacted'
    password = 'redacted'
    # send the email
    #send_email_with_attachments(subject, body, to, email, password, files)
'''

'''
Useful copy and pastes:ss
\n \nPoint Scoring: \n1: Everytime someone wins Head of Houshold you will be awarded points based on the following formula: 10-ranking. Ranking is the order you picked the contestant in with '0' being your favorite player and '15' being your least favorite. \n2: Everytime someone wins The Veto Competition they will be awarded points based on the following formula: 10-ranking. \n3: Everytime someone gets off the block (by any means, whether they were veto holder or not, or if there was a twist) they will be awarded points based off the following formula: 7.5 - 0.75ranking. \n4: Anytime a player wins a competition not otherwise mentioned here they will be awarded points based off the following formula: 5 - 0.5ranking. \n5: In the event a houseguest is evicted from the house, and then returns to play they will be awarded points based on the following formula: 10 - ranking. If the houseguest won a competition to be brought back to the game, points will be awarded for the other competition as well as being brought back to the game. \n6: If you perfectly predict the order in which everyone was evicted in your list, you will be awarded 100 points. \n7:If America's Favorite is your first, second, or third ranked housegust, you will be awarded 75, 50 or 25 points respectively. If they are your sixteenth, fifteenth, or fourteenth choice 50, 25, or 10 points will be subtracted respictively. \n8:If the winner of the game was your first, second, or third ranked houseguest, you will be awarded 100, 75, or 50 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 75, 50, or 25 points will be subtracted respectively. \n9:If the runner-up of the game was your first, second, or third ranked houseguest, you will be awarded 75, 50, or 25 points respectively. If the runner-up of the game was your sixteenth, fifteenth, or fourteenth ranked houseguest, 50, 25, or 10 points will be subtracted respectively.\n10:If the third place houseguest was your first, second, or third ranked houseguest, you will be awarded 50, 25, or 10 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 25, 10, or 5 points will be subtracted respectively. Please note that although the third place houseguest may be known an episode before the winner and runner up, the points for the top three places, America's Favorite, and the perfect line-up will all be awarded at the same time. 
first message: Hello everyone and welcome to the Big Brother Draft! \n \nFor those of you that have played in the past this is essentially the same game that we have played for the last couple of years, I just spent a little more time automating it this year so it would be easier for me and have less arithmetic errors. There are, however, a couple of changes to how I will be calculating points so be sure to read that section below! For those of you who are new this year: this is a Fantasy Football-style draft for the game show 'Big Brother.' To play, all you need to do is look at the list of contestants on this year's Big Brother, order ALL of the contestants from who you think is most likely to win to who you think is least likely to win (see point scoring below for more details), and send me the list (preferably by phone: 617-999-8985). Then send $20 to my venmo (@rclavey), winner takes all! When sending your list, also let me know if you're interested in being included in a group chat or not. It looks like we have 13 interested this year which means a pot of $260 if that number doesn't change. In the event of a tie, anyone who is tied for first will split the pot evenly, although this hasn't happened yet. That's it! That's all you need to do, however I'll make a group chat for those interested in talking about the game, and there are three episodes per week you can watch to stay up-to-date. An email like this one will come out after each episode detailing how everyone is doing and reminding everyone how they can recieve points. To ensure the game is fair and for the sake of transparency, I have this code posted on my github, (https://github.com/rclavey/git_hub/tree/master/big_brother). Feel free to check the code and bring any issues to my attention, its all in python. Because this file will contain everyone's email as well as the password to the sender email I decided to make the code private. Just text me at the phone number listed above and I can give permission for you to view the file.\n \nThe cast can be found at several websites, here is one: https://variety.com/gallery/big-brother-25-cast-photos/big-brother-25-16/  \n \nPoint Scoring: \n1: Everytime someone wins Head of Houshold you will be awarded points based on the following formula: 10-ranking. Ranking is the order you picked the contestant in with '0' being your favorite player and '15' being your least favorite. \n2: Everytime someone wins The Veto Competition they will be awarded points based on the following formula: 10-ranking. \n3: Everytime someone gets off the block (by any means, whether they were veto holder or not, or if there was a twist) they will be awarded points based off the following formula: 7.5 - 0.75ranking. \n4: Anytime a player wins a competition not otherwise mentioned here they will be awarded points based off the following formula: 5 - 0.5ranking. \n5: In the event a houseguest is evicted from the house, and then returns to play they will be awarded points based on the following formula: 10 - ranking. If the houseguest won a competition to be brought back to the game, points will be awarded for the other competition as well as being brought back to the game. \n6: If you perfectly predict the order in which everyone was evicted in your list, you will be awarded 100 points. \n7:If America's Favorite is your first, second, or third ranked housegust, you will be awarded 75, 50 or 25 points respectively. If they are your sixteenth, fifteenth, or fourteenth choice 50, 25, or 10 points will be subtracted respictively. \n8:If the winner of the game was your first, second, or third ranked houseguest, you will be awarded 100, 75, or 50 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 75, 50, or 25 points will be subtracted respectively. \n9:If the runner-up of the game was your first, second, or third ranked houseguest, you will be awarded 75, 50, or 25 points respectively. If the runner-up of the game was your sixteenth, fifteenth, or fourteenth ranked houseguest, 50, 25, or 10 points will be subtracted respectively.\n10:If the third place houseguest was your first, second, or third ranked houseguest, you will be awarded 50, 25, or 10 points respectively. If the winner was your sixteenth, fifteenth, or fourteenth ranked houseguest, 25, 10, or 5 points will be subtracted respectively. Please note that although the third place houseguest may be known an episode before the winner and runner up, the points for the top three places, America's Favorite, and the perfect line-up will all be awarded at the same time. \nChanges from last year: \n1: You now get a bonus if your list lines up perfectly with the order of evictions. \n2: Now there is only one spot in your list where the housguest will earn you zero points as opposed to in the last few years where only the top six and bottom four positions would add/subtract points.\n3: Getting taken off the block is worth slightly less points. \n4: You can now earn points and have points subtracted from an evicted houseguest getting back into the game.\n5:America's Favorite is now worth slightly more points. \n\nTL/DR: Welcome to the big brother draft, send a list of your favorite candidates to 617-999-8985 and check out the point scoring system. \n\nThanks everyone for playing! \nRichard Lavey
'''
