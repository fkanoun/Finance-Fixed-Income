import pdblp
import pandas as pd
import math

START_DATE = '20100101'
TODAY_DATE = '20190730'

def get_date_range(start,end):
    dates = pd.date_range(start=start,end=end)
    intermediate_dates = [elem.strftime("%Y%m%d") for elem in dates]
    return intermediate_dates

def compare_ratings_fitch(first_rating,second_rating):
    
    "Returns 1 if first fitch rating greater, -1 if second is greater and 0 otherwise"
    if (first_rating!=first_rating or second_rating!=second_rating):
        return 0
    
    #Find first occurence of blank
    blank_first = first_rating.find(' ')
    blank_second = second_rating.find(' ')
    
    #empty data
    if(blank_first==0 or blank_second==0):
        print('No rating')
        return 0
    
    #no blanks
    if(blank_first==-1):
        blank_first=len(first_rating)
        
    if(blank_second==-1):
        blank_second=len(second_rating)
    
    #Remove extra blank after the rating if it exists
    first = first_rating[:blank_first]
    second = second_rating[:blank_second]
    
    if(first==second):
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
            #Same stripped length
            else:
                if(first[-1]=='+' and second[-1]=='-'):
                    return 1
                if(first[-1]=='-' and second[-1]=='+'):
                    return -1
                if(len(stripped_first)<len(first) and first[-1]=='+'):
                    return 1
                if(len(stripped_first)<len(first) and first[-1]=='-'):
                    return -1
                if(len(stripped_second)<len(second) and second[-1]=='-'):
                    return +1
                if(len(stripped_second)<len(second) and second[-1]=='+'):
                    return -1

def compare_ratings_moody(first_rating,second_rating):

    "Returns 1 if first moody rating greater, -1 if second is greater and 0 otherwise"
    if (first_rating!=first_rating or second_rating!=second_rating):
        return 0

    blank_first = first_rating.find(' ')
    blank_second = second_rating.find(' ')
    
    #empty data
    if(blank_first==0 or blank_second==0):
        print('No rating')
        return 0
    
    #no blanks
    if(blank_first==-1):
        blank_first=len(first_rating)
        
    if(blank_second==-1):
        blank_second=len(second_rating)
    
    #Remove extra blank after the rating if it exists
    first = first_rating[:blank_first]
    second = second_rating[:blank_second]

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

def collect_data_from_ticker(ticker):

    con = pdblp.BCon(timeout=50000)
    con.start()
    df = pd.DataFrame(columns=['Date'])
    
    print('Collecting data of', con.ref(ticker,'ID_BB_ULTIMATE_PARENT_CO_NAME')['value'][0],'for bond :',con.ref(ticker,'SECURITY_NAME')['value'][0],'\n')
    
    issue_date = con.ref(ticker,'ISSUE_DT')['value'][0].strftime("%Y%m%d")
    intermediate_dates = get_date_range(issue_date,TODAY_DATE)
    
    
    # D/E ratio, Curr_Assets/Curr_Liabilities, EPS, ROA, ROE, EBITDA/REVENUE,
    # DAYS TO MATURITY, DAYS TO NEXT COUPON, CALLABILITY, SENIORITY, COUPON TYPE
    # VOLATILITY_360D,VOLATILITY_90D,VOLATILITY_30D
    features = ['TOT_DEBT_TO_TOT_EQY','CUR_RATIO','IS_EPS','RETURN_ON_ASSET','RETURN_COM_EQY','EBITDA_TO_REVENUE',
                'DAYS_TO_MTY_TDY','DAYS_TO_NEXT_COUPON','CALLABLE','NORMALIZED_PAYMENT_RANK','CPN_TYP','CPN_FREQ',
               'VOLATILITY_360D','VOLATILITY_90D','VOLATILITY_30D']

    # S&P ratings + changes
    print('**** Collecting S&P ratings ****')
    for i,day in enumerate(intermediate_dates):
    
        row = con.ref(ticker,'RTG_SP',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        current_rating = row['value'][0]
        df.loc[i,'RTG_SP'] = current_rating

        if(i>0):
            previous_rating = df['RTG_SP'][i-1]
            comparison = compare_ratings_moody(current_rating,previous_rating)
            if(comparison==1):
                print('Upgrade from S&P on',day,'from',previous_rating,'to',current_rating)
            if(comparison==-1):
                print('Downgrade from S&P on',day,'from',previous_rating,'to',current_rating)
                
            df.loc[i,'RTG_SP_CHANGE']=comparison
    
    # Fitch ratings + changes 
    print('**** Collecting fitch ratings ****')
    for i,day in enumerate(intermediate_dates):
        
        row = con.ref(ticker,'RTG_FITCH',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        current_rating = row['value'][0]
        df.loc[i,'RTG_FITCH'] = current_rating
        
        if(i>0):
            previous_rating = df['RTG_FITCH'][i-1]
            comparison = compare_ratings_fitch(current_rating,previous_rating)
            
            if(comparison==1):
                print('Upgrade from Fitch on',day,'from',previous_rating,'to',current_rating)
            if(comparison==-1):
                print('Downgrade from Fitch on',day,'from',previous_rating,'to',current_rating)
         
            df.loc[i,'RTG_FITCH_CHANGE']=comparison
    
    # Moodys ratings + changes 
    print('**** Collecting moodys ratings ****')
    for i,day in enumerate(intermediate_dates):
    
        row = con.ref(ticker,'RTG_MOODY',ovrds=[('RATING_AS_OF_DATE_OVERRIDE', day)])
        current_rating = row['value'][0]
        df.loc[i,'RTG_MOODY'] = current_rating

        if(i>0):
            previous_rating = df['RTG_MOODY'][i-1]
            comparison = compare_ratings_moody(current_rating,previous_rating)
            
            if(comparison==1):
                print('Upgrade from Moody on',day,'from',previous_rating,'to',current_rating)
            if(comparison==-1):
                print('Downgrade from Moody on',day,'from',previous_rating,'to',current_rating)
            
            df.loc[i,'RTG_MOODY_CHANGE']=comparison
    
    #Adding features to the dataframe
    for feature in features :
        print('**** Collecting', feature ,'****')
        for i,day in enumerate(intermediate_dates):
    
            row = con.ref(ticker,feature,ovrds=[('FUNDAMENTAL_DATABASE_DATE', day)])
            value = row['value'][0]
            df.loc[i,feature] = value
    
    df.to_csv('no_price'+ticker+'.csv')
    
    #Adding the price of the security at the end of the day
    print('**** Collecting historical prices **** ')
    price_df = con.bdh(ticker, 'PX_LAST',issue_date, TODAY_DATE)
    price_df.to_csv('price'+ticker+'.csv')
    
    final_df = df.join(price_df)
    
    final_df.to_csv(ticker+'.csv')
    print('CSV file for ticker ',ticker,'created')


