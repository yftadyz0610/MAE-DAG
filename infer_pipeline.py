# Pipeline of extracting MAE-DAGs given ASER events.


import joblib
import pickle


if __name__=="__main__":
    from config import belief_setting, aser_setting
    from belief import Belief
    from engine import Engine
    VERSION = 'v3.2'

    belief = Belief(belief_setting)
    belief.load_belief()
    belief.revise_belief()

    # pre-running:
    # (1) `extract_event.py` get ASER events
    # (2) `restore_event.py` get event-restores
    event_processed_map=joblib.load('Data/amazon_food_review_aser_event_restore_map')

    tags=['0_100000','100000_200000','200000_300000','300000_400000','400000_500000','500000_600000']
    for tag in tags:
        print('Processing %s ......'%tag)
        aser = joblib.load('Data/amazon_food_review_aser_event_%s.v2'%tag)

        aser_events=dict([(text_id, info['aser']) for text_id, info in aser.items()])

        res = Engine.aser_process(aser_events, belief, event_processed_map, aser_setting)

        with open("Data/experience_%s.%s"%(tag,VERSION), "wb") as outfile:
            pickle.dump(res, outfile)

    exit(0)