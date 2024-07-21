# Extract events from corpus by ASER.

import pandas as pd
import tqdm
import joblib
import re

def load_data():
    nRowsRead = 1000000  # specify 'None' if want to read whole file
    df = pd.read_csv('Data/amazon_food_review/Reviews.csv', delimiter=',', nrows=nRowsRead)
    df.dataframeName = 'Reviews.csv'
    nRow, nCol = df.shape
    print(f'There are {nRow} rows and {nCol} columns')

    return df

# extract events from text by ASER
# https://hkust-knowcomp.github.io/ASER/html/index.html
def extract_event(df,start,end):
    aser_event = {}

    input_df = df[start:end]
    texts = input_df['Text'].tolist()
    ID = input_df['Id'].tolist()

    for text_id, review_text in tqdm.tqdm(zip(ID, texts)):
        # split review_text into sentences
        review_text_s = re.split('[.!\?]', review_text)
        # pop '' out and remove heading whitespace in sentence
        review_text_s_new=[]
        for s in review_text_s:
            if s=='':
                continue
            review_text_s_new.append(s.strip())

        # get eventualities by ASER
        s_list=[]
        aser_list=[]
        for s in review_text_s_new:
            try:
                review_events = client.extract_eventualities(s)
            except:
                review_events = [[]]
            if isinstance(review_events,list):
                s_list.append(s)
                aser_list.append(review_events[0])

        aser_event[text_id] = {}
        aser_event[text_id]['sentences'] = s_list  # list of str
        aser_event[text_id]['aser'] = aser_list  # list of list of aser_event

    return aser_event

if __name__=="__main__":

    from aser.client import ASERClient
    client = ASERClient(port=8000, port_out=8001)

    tags = ['0_100000', '100000_200000', '200000_300000', '300000_400000', '400000_500000',
            '500000_600000']

    for t in tqdm.tqdm(tags):
        start=int(t.split('_')[0])
        end=int(t.split('_')[1])

        df=load_data()
        aser_event=extract_event(df,start,end)

        joblib.dump(aser_event, 'Data/amazon_food_review_aser_event_%d_%d.v2' % (start, end))

    exit(0)



