import pdblp
import pandas as pd
import math

def compare_ratings_fitch(first,second):
    
    "Returns 1 if first fitch rating greater, -1 if second is greater and 0 otherwise"
    if (first!=first or second!=second):
        return 0
    
    L_first = first[0]
    L_second = second[0]
    if (L_first>L_second):
        return -1
    elif (L_first<L_second):
        return 1
    else:
        #Same letters
        stripped_first = first.strip('+').strip('-')
        stripped_second = second.strip('+').strip('-')
        if(len(stripped_first)>len(stripped_second)):
            return 1
        elif (len(stripped_first)<len(stripped_second)):
            return -1
        #Same letters and same length of letters
        else:
            #Same length of rating
            if(len(first)==len(second)):
                sign_first = first[-1]
                sign_second = second[-1]
                if(sign_first=='+' and sign_second == '-'):
                    return 1
                elif (sign_first=='-' and sign_second == '+'):
                    return -1
                else:
                    return 0
            else:
                if(len(first)>len(second) and first[-1]=='-'):
                    return -1
                elif(len(first)>len(second) and first[-1]=='+'):
                    return 1
                elif(len(first)<len(second) and second[-1]=='+'):
                    return 1
                elif(len(first)<len(second) and second[-1]=='-'):
                    return -1
                else:
                    return 0

def compare_ratings_moody(first,second):

    "Returns 1 if first moody rating greater, -1 if second is greater and 0 otherwise"
    if (first!=first or second!=second):
        return 0
    
    L_first = first[0]
    L_second = second[0]
    if (L_first>L_second):
        return -1
    elif (L_first<L_second):
        return 1
    else:
    #Same first letter
        if(len(first)>len(second)):
            return 1
        elif(len(first)<len(second)):
            return -1
        else:
        #Same length
            Last_first = first[-1]
            Last_second = second[-1]
            if(Last_first.isalpha() and Last_second.isalpha()==False):
                return 1
            elif(Last_first.isalpha()==False and Last_second.isalpha()):
                return -1
            else:
                if(Last_first>Last_second):
                    return -1
                elif(Last_first<Last_second):
                    return 1
                else:
                    return 0

def collect_data_from_ticker(ticker,intermediate_dates):

    con = pdblp.BCon(timeout=50000)
    con.start()
    df = pd.DataFrame(columns=['Ticker','Date','RTG_FITCH','RTG_FITCH_CHANGE'])

    # D/E ratio, Curr_Assets/Curr_Liabilities, EPS, ROA, ROE, EBITDA/REVENUE
    features = ['TOT_DEBT_TO_TOT_EQY','CUR_RATIO','IS_EPS','RETURN_ON_ASSET','RETURN_COM_EQY','EBITDA_TO_REVENUE']

    # Fitch ratings + changes 
    print('**** Collecting fitch ratings ****')
    for i,day in enumerate(intermediate_dates):
        
        row = con.ref(Ticker,'RTG_FITCH',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        if(i>0):
            previous_rating = df['RTG_FITCH'][i-1]
            current_rating = row['value'][0]
            comparison = compare_ratings_fitch(current_rating,previous_rating)

            if comparison==1:
                print('Upgrade from',previous_rating,'to',current_rating)
                df = df.append({'Ticker': row['ticker'],'Date':day,'RTG_FITCH':row['value'][0],'RTG_FITCH_CHANGE':1},ignore_index=True)
            elif (comparison==-1):
                print('Downgrade from',previous_rating,'to',current_rating)
                df = df.append({'Ticker': row['ticker'],'Date':day,'RTG_FITCH':row['value'][0],'RTG_FITCH_CHANGE':-1},ignore_index=True)
            else :
                df = df.append({'Ticker': row['ticker'],'Date':day,'RTG_FITCH':row['value'][0],'RTG_FITCH_CHANGE':0},ignore_index=True)
        else:
            df = df.append({'Ticker': row['ticker'],'Date':day,'RTG_FITCH':row['value'][0],'RTG_FITCH_CHANGE':0},ignore_index=True)

    # Moody ratings + changes
    print('**** Collecting moodys ratings ****')
    for i,day in enumerate(intermediate_dates):
    
        row = con.ref(Ticker,'RTG_MOODY',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        current_rating = row['value'][0]
        df.loc[i,'RTG_MOODY'] = current_rating

        if(i>0):
            previous_rating = df['RTG_MOODY'][i-1]
            comparison = compare_ratings_moody(current_rating,previous_rating)
            df['RTG_MOODY_CHANGE'][i]=comparison

    # S&P ratings + changes
    print('**** Collecting S&P ratings ****')
    for i,day in enumerate(intermediate_dates):
    
        row = con.ref(Ticker,'RTG_SP',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        current_rating = row['value'][0]
        df.loc[i,'RTG_SP'] = current_rating

        if(i>0):
            previous_rating = df['RTG_SP'][i-1]
            comparison = compare_ratings_moody(current_rating,previous_rating)
            df['RTG_SP_CHANGE'][i]=comparison
    
    #Adding features to the dataframe
    for feature in features :
        print('**** Collecting', feature ,'****')
        for i,day in enumerate(intermediate_dates):
    
            row = con.ref(Ticker,feature,ovrds=[('FUNDAMENTAL_DATABASE_DATE', day)])
            value = row['value'][0]
            df.loc[i,feature] = value

    print('Collection of data for ticker',ticker,': done')
    return df


