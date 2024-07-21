# Restore the extracted event text from the raw sentence.
# e.g. event text: 'the chocolate be the best', restore text: 'the chocolate are the best', raw sentence text: 'however the chocolate are the best'

import joblib
import tqdm
from textblob import TextBlob
import re
from utils import get_verb_forms,clean_sent

def restore_event(text_id, sentences, aser, personal_pronoun, conjugator):
# Input:
#       sentences: [str]
#       aser: [[aser_events]]

    event_sent_list = []
    for s, event_list in zip(sentences, aser):
        for e in event_list:
            event_sent_list.append((text_id, e, s))

    # get all verbs from events
    verbs = set()

    for text_id, event, sent in tqdm.tqdm(event_sent_list):

        for w, pt in zip(event.__repr__().split(' '), event.pos_tags):

            if 'VB' in pt:
                verbs.add(w)

    verbs = list(verbs)
    #print("Total verbs: %d" % len(verbs))

    verb_tense = {}
    fail = []
    for v in tqdm.tqdm(verbs):
        tmp, status = get_verb_forms(conjugator, v)
        if status == -1:
            fail.append(v)
        else:
            verb_tense[v] = tmp
    #print("Failing verbs: %d" % len(fail))


    event_processed = []  # (text_id, event, raw_event_text, sub_sent, sent)
    event_unprocessed = []  # (text_id, event,'', '', sent)

    for text_id, event, sent in tqdm.tqdm(event_sent_list):
        event_text = event.__repr__()
        hw = event_text.split(' ')[0]
        hw_pos = event.pos_tags[0]
        tw = event_text.split(' ')[-1]
        tw_pos = event.pos_tags[-1]

        sub_sents = re.split('\.|,', clean_sent(sent))

        match_res = []

        for ss in sub_sents:
            ss_cut = ss.split(' ')

            start_inds = set()
            end_inds = set()

            for i, sw in enumerate(ss_cut):
                sw = sw.lower()

                # (1) head word and tail word matching
                if sw == hw:
                    start_ind = i
                    start_inds.add(start_ind)
                if sw == tw:
                    end_ind = i
                    end_inds.add(end_ind)
                # (2) upper/lower case matching
                # if sw.lower()==hw:
                #     start_ind=i
                #     start_inds.add(start_ind)

                # if sw.lower()==tw:
                #     end_ind=i
                #     end_inds.add(end_ind)

                # (3) plural matching
                if 'NN' in hw_pos:
                    blob = TextBlob(hw)
                    tmp = [word.pluralize() for word in blob.words]
                    hw_plural = tmp[0] if len(tmp) > 0 else ''
                    if sw == hw_plural:
                        start_ind = i
                        start_inds.add(start_ind)

                if 'NN' in tw_pos:
                    blob = TextBlob(tw)
                    tmp = [word.pluralize() for word in blob.words]
                    tw_plural = tmp[0] if len(tmp) > 0 else ''
                    if sw == tw_plural:
                        end_ind = i
                        end_inds.add(end_ind)

                # (4) verb-tense matching
                if 'VB' in hw_pos and hw in verb_tense:
                    tmp = verb_tense[hw]
                    for t in tmp:
                        if sw == t:
                            start_ind = i
                            start_inds.add(start_ind)

                if 'VB' in tw_pos and tw in verb_tense:
                    tmp = verb_tense[tw]
                    for t in tmp:
                        if sw == t:
                            end_ind = i
                            end_inds.add(end_ind)

                # (5) personal pronoun matching
                if hw in personal_pronoun:
                    tmp = personal_pronoun[hw]
                    for t in tmp:
                        if sw == t:
                            start_ind = i
                            start_inds.add(start_ind)

                if tw in personal_pronoun:
                    tmp = personal_pronoun[tw]
                    for t in tmp:
                        if sw == t:
                            end_ind = i
                            end_inds.add(end_ind)

            match_res.append((ss_cut, start_inds, end_inds))

        # determine the final start and end indices
        # loop over all possible combinations of start and end indices and find the one with the maximum overlap inside
        event_inner_cut = event_text.split(' ')[1:-1]
        start_ind = -1
        end_ind = -1
        best_ss_cnt = []
        inner_match_cnt = 0
        for ss_cut, start_inds, end_inds in match_res:
            for s in start_inds:
                for e in end_inds:
                    if s < e:
                        cnt = 0
                        for _x in event_inner_cut:
                            if _x in ss_cut[s + 1:e]:
                                cnt += 1
                        if cnt >= inner_match_cnt:
                            inner_match_cnt = cnt
                            start_ind = s
                            end_ind = e
                            best_ss_cnt = ss_cut

        event_raw_text = ' '.join(best_ss_cnt[start_ind:end_ind + 1])

        if len(event_raw_text) > 0:
            event_processed.append((text_id, event, event_raw_text, ' '.join(best_ss_cnt), sent))
        if len(event_raw_text) == 0:
            event_unprocessed.append((text_id, event, '', '', sent))

    # tracking
    print("Total events: %d, processed events: %d, ratio: %.2f%%" % (
    len(event_sent_list), len(event_processed), 100 * len(event_processed) / len(event_sent_list)))

    event_processed_map = {}

    for text_id, event, event_raw_text, sub_sent, sent in event_processed:
        if text_id not in event_processed_map:
            event_processed_map[text_id] = {}
        event_processed_map[text_id][event.__repr__()] = [event_raw_text, sub_sent]

    return event_processed_map,event_processed, event_unprocessed


if __name__=="__main__":
    from config import personal_pronoun
    from mlconjug3 import Conjugator
    conjugator = Conjugator(language='en')

    aser_events, sentences=joblib.load('Data/debug_textID_452556_dataset')

    event_processed_map, event_processed, event_unprocessed =restore_event(sentences, aser_events, personal_pronoun, conjugator)

    exit(0)








